"""Build object-centric ``content/pieces.md`` from ``content/not_shared/`` (Facebook export).

Each **object** (work) gets an English blurb and ``<!-- gallery: pieces/<slug> -->`` when
images are copied from ``not_shared/media/<folder>/`` into ``assets/pieces/<slug>/``.

    uv run python scripts/generate_pieces_from_fb_export.py

Does not print upload IPs. Romanian text is dropped from descriptions and merged snippets.
"""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True)

ROOT = Path(__file__).resolve().parents[1]
NOT_SHARED = ROOT / "content" / "not_shared"
ALBUM_DIR = NOT_SHARED / "album"
MEDIA_ROOT = NOT_SHARED / "media"
POSTS_JSON = NOT_SHARED / "profile_posts_1.json"
ASSETS_PIECES = ROOT / "assets" / "pieces"
OUTPUT = ROOT / "content" / "pieces.md"

FB_PROFILE = "https://www.facebook.com/byLiviaZaharia/"

_RO_DIACRITICS = frozenset("ăâîșțĂÂÎȘȚ")

_RO_FUNC = re.compile(
    r"\b(și|să|suntem|pentru|este|sunt|ca |că |cu |din |am |nu |mai |tot |aici|acum|"
    r"lui|lor|fiecare|într|însă|deja|pornind|realizarea|verticala|suprafetei)\b",
    re.I,
)

_EN_COMMON = frozenset(
    "the an and with for from ring silver gold pendant cast stone which that this its here "
    "each strip model vertical ellipse layer same starting idea wrapping light settings into "
    "when what your more there where stage client studio galaxy surface division textile "
    "extracted numbered assembly situ large scale parametrics".split()
)

_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _dt(ts: int | None) -> datetime | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)


def _md_escape_line(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n").strip()


def _diacritic_ratio(s: str) -> float:
    if not s:
        return 0.0
    n = sum(1 for c in s if c in _RO_DIACRITICS)
    return n / max(len(s), 1)


def _split_bilingual(text: str) -> list[str]:
    """Split on long dash separators (common RO | EN blocks in Facebook exports)."""
    parts = re.split(r"[-]{20,}", text)
    return [p.strip() for p in parts if p.strip()]


def _english_word_hits(s: str) -> int:
    return sum(
        1
        for w in re.findall(r"[a-zA-Z]+", s.lower())
        if len(w) >= 3 and w in _EN_COMMON
    )


def _looks_english_paragraph(para: str) -> bool:
    if len(para) < 20:
        return False
    if _diacritic_ratio(para) > 0.02:
        return False
    if _RO_FUNC.search(para):
        return False
    if _english_word_hits(para) < 2 and len(para) > 80:
        return False
    return True


def _english_chunks_from_paragraph(para: str) -> list[str]:
    """Split mixed RO/EN blocks on long dash runs; keep English chunks only."""
    para = para.strip()
    if not para:
        return []
    if re.search(r"[-]{12,}", para):
        out: list[str] = []
        for chunk in re.split(r"[-]{12,}", para):
            c = chunk.strip()
            if c and _looks_english_paragraph(c):
                out.append(c)
        return out
    if _looks_english_paragraph(para):
        return [para]
    return []


def _english_paragraphs(text: str) -> str:
    """Keep only English-leaning paragraphs (Romanian blocks dropped)."""
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return ""
    blocks = _split_bilingual(text)
    candidates: list[str] = blocks if len(blocks) > 1 else [text]
    good: list[str] = []
    for block in candidates:
        for para in re.split(r"\n\s*\n", block):
            para = para.strip()
            if not para:
                continue
            good.extend(_english_chunks_from_paragraph(para))
    if not good and blocks:
        last = blocks[-1]
        for para in re.split(r"\n\s*\n", last):
            para = para.strip()
            if not para:
                continue
            good.extend(_english_chunks_from_paragraph(para))
    return "\n\n".join(good).strip()


def _english_title_from_album_name(name: str) -> str:
    """Prefer the English segment in ``RO / EN``, ``RO_EN``, or ``RO - EN``."""
    name = name.strip()
    if not name:
        return "Untitled"

    def score_part(p: str) -> tuple[int, float, int]:
        return (
            _english_word_hits(p),
            _diacritic_ratio(p),
            -len(p),
        )

    if "_" in name and "/" not in name:
        left, right = name.split("_", 1)
        if _english_word_hits(right) >= _english_word_hits(left) + 1:
            name = right.strip()

    if " / " in name:
        parts = [p.strip() for p in name.split(" / ") if p.strip()]
        if parts:
            return max(parts, key=score_part)
    if "/" in name and " / " not in name:
        parts = [p.strip() for p in name.split("/") if p.strip()]
        if parts:
            return max(parts, key=score_part)
    m = re.match(r"^[^–\-]+[–\-]\s*(.+)$", name)
    if m and len(m.group(1).strip()) > 2:
        return m.group(1).strip()
    return name


def slugify(label: str, used: set[str]) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", label.lower()).strip("-")
    if not s:
        s = "piece"
    base = s[:72]
    out = base
    n = 2
    while out in used:
        out = f"{base}-{n}"
        n += 1
    used.add(out)
    return out


def _words(s: str) -> set[str]:
    raw = re.findall(r"[a-zA-Z]{4,}", (s or "").lower())
    return set(raw)


def _split_camel_name(folder: str) -> str:
    base = folder.split("_")[0]
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", base)
    return spaced.lower()


def _media_folders(post: dict) -> list[str]:
    folders: list[str] = []
    for att in post.get("attachments") or []:
        for x in att.get("data") or []:
            if not isinstance(x, dict):
                continue
            m = x.get("media")
            if isinstance(m, dict):
                uri = m.get("uri") or ""
                if "/media/" in uri:
                    folders.append(uri.split("/media/")[1].split("/")[0])
    out: list[str] = []
    seen: set[str] = set()
    for f in folders:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _extract_post_text(post: dict) -> str:
    parts: list[str] = []
    for block in post.get("data") or []:
        if isinstance(block, dict) and "post" in block:
            parts.append(str(block["post"]).strip())
    return "\n\n".join(p for p in parts if p)


def _post_full_text(post: dict) -> str:
    return f"{post.get('title') or ''}\n{_extract_post_text(post)}"


def _extract_attachment_urls(post: dict) -> list[str]:
    urls: list[str] = []
    for att in post.get("attachments") or []:
        for d in att.get("data") or []:
            if not isinstance(d, dict):
                continue
            ext = d.get("external_context") or {}
            u = ext.get("url")
            if isinstance(u, str) and u.startswith("http"):
                urls.append(u)
    return urls


def _urls_in_text(s: str) -> list[str]:
    return re.findall(r"https?://[^\s\)\]\"<>]+", s or "")


@dataclass
class AlbumPiece:
    folder: str
    name: str
    description: str
    last_modified: int | None
    photo_count: int


class UnionFind:
    def __init__(self, n: int) -> None:
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def _skip_album(folder: str, name: str) -> bool:
    n = name.strip().lower()
    if n == "mobile uploads":
        return True
    if folder.startswith("Mobileuploads_"):
        return True
    return False


def _load_albums() -> dict[str, AlbumPiece]:
    out: dict[str, AlbumPiece] = {}
    if not ALBUM_DIR.is_dir():
        return out
    for fp in sorted(ALBUM_DIR.glob("*.json")):
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(d, dict):
            continue
        photos = d.get("photos") or []
        if not photos:
            continue
        uri = photos[0].get("uri") or ""
        if "/media/" not in uri:
            continue
        folder = uri.split("/media/")[1].split("/")[0]
        name = str(d.get("name") or folder)
        if _skip_album(folder, name):
            continue
        out[folder] = AlbumPiece(
            folder=folder,
            name=name,
            description=str(d.get("description") or "").strip(),
            last_modified=d.get("last_modified_timestamp"),
            photo_count=len(photos),
        )
    return out


def _album_match_score(text: str, piece: AlbumPiece) -> float:
    if not text.strip():
        return 0.0
    t = text.lower()
    name_l = piece.name.lower()
    score = 0.0
    if len(name_l) > 4 and name_l in t:
        score += 3.0
    for w in re.findall(r"[a-zA-ZăâîșțĂÂÎȘȚ]{4,}", name_l):
        if len(w) > 4 and w in t:
            score += 1.0
    desc = (piece.description or "")[:400].lower()
    for w in re.findall(r"[a-zA-ZăâîșțĂÂÎȘȚ]{5,}", desc):
        if len(w) > 5 and w in t:
            score += 0.35
    camel = _split_camel_name(piece.folder)
    for token in camel.split():
        if len(token) > 4 and token in t:
            score += 0.8
    if "mountain" in t and "gold" in t and "mountain" in _split_camel_name(piece.folder):
        score += 2.0
    return score


def _cluster_indices(
    indices: list[int],
    posts: list[dict],
    album_names: list[str],
) -> dict[int, list[int]]:
    if not indices:
        return {}
    n = len(indices)
    uf = UnionFind(n)
    texts = [_post_full_text(posts[i]) for i in indices]
    word_sets = [_words(t) for t in texts]
    times = [int(posts[i].get("timestamp") or 0) for i in indices]
    phrases = sorted({a for a in album_names if len(a) >= 8}, key=len, reverse=True)

    for a in range(n):
        for b in range(a + 1, n):
            ta, tb = texts[a].lower(), texts[b].lower()
            if len(word_sets[a] & word_sets[b]) >= 2:
                uf.union(a, b)
                continue
            for ph in phrases:
                pl = ph.lower()
                if pl in ta and pl in tb:
                    uf.union(a, b)
                    break
            else:
                if re.search(r"(?i)eye\s+of\s+winter", ta) and re.search(
                    r"(?i)eye\s+of\s+winter", tb
                ):
                    uf.union(a, b)
                    continue
                dt_sec = abs(times[a] - times[b])
                if dt_sec <= 14 * 86400:
                    long_a = {w for w in word_sets[a] if len(w) >= 6}
                    long_b = {w for w in word_sets[b] if len(w) >= 6}
                    if long_a & long_b:
                        uf.union(a, b)

    clusters: dict[int, list[int]] = defaultdict(list)
    for j in range(n):
        clusters[uf.find(j)].append(j)
    return clusters


def _english_sentence_snippets(posts: list[dict], max_chars: int = 420) -> str:
    """Merge English-leaning sentences from posts into one short paragraph (no list)."""
    snippets: list[str] = []
    for post in posts:
        raw = _post_full_text(post)
        for line in raw.replace("\r", "").split("\n"):
            line = line.strip()
            if len(line) < 28:
                continue
            if re.match(r"^https?://", line):
                continue
            if re.search(r"[-]{12,}", line):
                for chunk in re.split(r"[-]{12,}", line):
                    c = chunk.strip()
                    if len(c) < 28:
                        continue
                    if not _looks_english_paragraph(c):
                        continue
                    snippets.append(c)
                continue
            if not _looks_english_paragraph(line):
                continue
            snippets.append(line)
    merged = " ".join(snippets)
    merged = re.sub(r"\s+", " ", merged).strip()
    if len(merged) > max_chars:
        merged = merged[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return merged


def _cluster_english_title(posts: list[dict]) -> str:
    for post in posts:
        for line in _extract_post_text(post).split("\n"):
            line = line.strip()
            if len(line) < 8:
                continue
            if not _looks_english_paragraph(line):
                continue
            return line[:72] + ("…" if len(line) > 72 else "")
    return "Studio update"


def copy_folder_images(src_folder: Path, dest_dir: Path) -> int:
    """Copy image files into ``dest_dir``; return count."""
    if not src_folder.is_dir():
        return 0
    dest_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted(src_folder.iterdir()):
        if p.is_file() and p.suffix.lower() in _IMAGE_EXT:
            shutil.copy2(p, dest_dir / p.name)
            n += 1
    return n


def copy_images_from_posts(post_indices: list[int], posts: list[dict], dest_dir: Path) -> int:
    """Copy image files referenced by post attachments into ``dest_dir``."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    n = 0
    for i in post_indices:
        post = posts[i]
        for att in post.get("attachments") or []:
            for x in att.get("data") or []:
                if not isinstance(x, dict):
                    continue
                m = x.get("media")
                if not isinstance(m, dict):
                    continue
                uri = str(m.get("uri") or "")
                if "media/" not in uri:
                    continue
                rel = uri.split("media/", 1)[1].replace("\\", "/")
                src = MEDIA_ROOT / rel
                if not src.is_file() or src.suffix.lower() not in _IMAGE_EXT:
                    continue
                key = str(src.resolve())
                if key in seen:
                    continue
                seen.add(key)
                shutil.copy2(src, dest_dir / src.name)
                n += 1
    return n


@dataclass
class WorkObject:
    slug: str
    title_en: str
    body_en: str
    gallery_subpath: str  # e.g. pieces/mountain-of-gold
    kind: str
    post_indices: list[int] = field(default_factory=list)


@app.command()
def main(
    posts_path: Path = typer.Option(POSTS_JSON, "--posts"),
    output: Path = typer.Option(OUTPUT, "-o", "--output"),
    skip_copy: bool = typer.Option(False, "--skip-copy", help="Do not copy images to assets/pieces/"),
) -> None:
    if not posts_path.is_file():
        typer.echo(f"Missing export file: {posts_path}", err=True)
        raise typer.Exit(code=1)

    posts: list[dict] = json.loads(posts_path.read_text(encoding="utf-8"))
    albums = _load_albums()
    album_names = [p.name for p in albums.values()]

    assigned_album: dict[int, str] = {}
    video_only: list[int] = []
    mobile_pool: list[int] = []

    for i, post in enumerate(posts):
        folders = _media_folders(post)
        non_v = [f for f in folders if f != "videos"]
        has_named = any(f in albums for f in non_v)
        only_mobile = bool(non_v) and all(f.startswith("Mobileuploads_") for f in non_v)
        has_video = "videos" in folders

        if has_named:
            for f in folders:
                if f in albums:
                    assigned_album[i] = f
                    break
            continue
        if has_video:
            video_only.append(i)
            continue
        if only_mobile:
            mobile_pool.append(i)
            continue

    for i, post in enumerate(posts):
        if i in assigned_album or i in video_only or i in mobile_pool:
            continue
        text = _extract_post_text(post)
        if not text.strip():
            continue
        best_folder: str | None = None
        best_score = 1.5
        for folder, piece in albums.items():
            s = _album_match_score(text, piece)
            if s > best_score:
                best_score = s
                best_folder = folder
        if best_folder is not None:
            assigned_album[i] = best_folder

    remaining: list[int] = []
    for i in range(len(posts)):
        if i in assigned_album:
            continue
        if i in video_only:
            continue
        if i in mobile_pool:
            continue
        remaining.append(i)

    mobile_clusters = _cluster_indices(mobile_pool, posts, album_names)
    other_clusters = _cluster_indices(remaining, posts, album_names)

    album_posts: dict[str, list[int]] = defaultdict(list)
    for i, f in assigned_album.items():
        album_posts[f].append(i)

    def album_sort_key(folder: str) -> tuple[int, str]:
        piece = albums[folder]
        times: list[int] = []
        if piece.last_modified:
            times.append(int(piece.last_modified))
        for idx in album_posts.get(folder, []):
            ts = posts[idx].get("timestamp")
            if ts:
                times.append(int(ts))
        return (-max(times) if times else 0, piece.name.lower())

    folder_order = sorted(albums.keys(), key=album_sort_key)
    base_titles = [_english_title_from_album_name(albums[f].name) for f in folder_order]
    title_counts = Counter(base_titles)
    used_slugs: set[str] = set()

    work_objects: list[WorkObject] = []

    # Album-backed objects
    for folder in folder_order:
        piece = albums[folder]
        indices = sorted(
            album_posts.get(folder, []),
            key=lambda ii: int(posts[ii].get("timestamp") or 0),
            reverse=True,
        )
        title = _english_title_from_album_name(piece.name)
        if title_counts[title] > 1:
            title = f"{title} ({piece.folder.split('_')[-1][:8]})"
        desc = _english_paragraphs(piece.description)
        slug = slugify(title, used_slugs)
        sub = f"pieces/{slug}"
        dest = ASSETS_PIECES / slug
        src = MEDIA_ROOT / folder
        n_img = 0 if skip_copy else copy_folder_images(src, dest)
        if n_img == 0 and not skip_copy and src.is_dir():
            typer.echo(f"Note: no images copied for {folder} -> {dest}", err=True)

        extra = _english_sentence_snippets([posts[i] for i in indices]) if indices else ""
        body_parts: list[str] = []
        if desc:
            body_parts.append(desc)
        if extra and extra[:80] not in desc and extra not in desc:
            body_parts.append(extra)
        body_en = "\n\n".join(body_parts).strip()

        work_objects.append(
            WorkObject(
                slug=slug,
                title_en=title,
                body_en=body_en,
                gallery_subpath=sub,
                kind="album",
                post_indices=indices,
            )
        )

    # Mobile-upload clusters → objects
    for _, members in sorted(
        mobile_clusters.items(),
        key=lambda x: max(int(posts[mobile_pool[j]].get("timestamp") or 0) for j in x[1]),
        reverse=True,
    ):
        if not members:
            continue
        cluster_posts = [posts[mobile_pool[j]] for j in members]
        idxs = [mobile_pool[j] for j in members]
        title = _cluster_english_title(cluster_posts)
        slug = slugify(title, used_slugs)
        body_en = _english_sentence_snippets(cluster_posts, max_chars=650)
        if not skip_copy:
            copy_images_from_posts(idxs, posts, ASSETS_PIECES / slug)
        work_objects.append(
            WorkObject(
                slug=slug,
                title_en=title,
                body_en=body_en,
                gallery_subpath=f"pieces/{slug}",
                kind="mobile",
                post_indices=idxs,
            )
        )

    # Video → one object (English blurbs only; gallery only if copied images exist)
    if video_only:
        vposts = [posts[i] for i in video_only]
        title = "Video clips"
        slug = slugify("video-clips", used_slugs)
        body_en = _english_sentence_snippets(vposts, max_chars=800)
        if not skip_copy:
            copy_images_from_posts(video_only, posts, ASSETS_PIECES / slug)
        work_objects.append(
            WorkObject(
                slug=slug,
                title_en=title,
                body_en=body_en,
                gallery_subpath=f"pieces/{slug}",
                kind="video",
                post_indices=video_only,
            )
        )

    # Other clusters
    for _, members in sorted(
        other_clusters.items(),
        key=lambda x: max(int(posts[remaining[j]].get("timestamp") or 0) for j in x[1]),
        reverse=True,
    ):
        if not members:
            continue
        cluster_posts = [posts[remaining[j]] for j in members]
        idxs = [remaining[j] for j in members]
        title = _cluster_english_title(cluster_posts)
        slug = slugify(title, used_slugs)
        body_en = _english_sentence_snippets(cluster_posts, max_chars=650)
        urls: list[str] = []
        for p in cluster_posts:
            urls.extend(_extract_attachment_urls(p))
            urls.extend(_urls_in_text(_extract_post_text(p)))
        urls = list(dict.fromkeys(urls))[:6]
        if urls:
            body_en = (body_en + "\n\n" if body_en else "") + " ".join(f"[{u}]({u})" for u in urls)
        if not skip_copy:
            copy_images_from_posts(idxs, posts, ASSETS_PIECES / slug)
        work_objects.append(
            WorkObject(
                slug=slug,
                title_en=title,
                body_en=body_en,
                gallery_subpath=f"pieces/{slug}",
                kind="other",
                post_indices=idxs,
            )
        )

    # Markdown
    lines: list[str] = [
        "Each section is one object (work). Posts were grouped by topic and attached to that object. "
        "Text is English only when the export allowed it. "
        f"For updates, see [Facebook]({FB_PROFILE}).",
        "",
    ]

    for wo in work_objects:
        lines.append(f"## {wo.title_en}")
        lines.append("")
        if wo.body_en:
            lines.append(wo.body_en)
            lines.append("")
        else:
            lines.append("*No English description was extracted for this piece in the export.*")
            lines.append("")
        gal_dir = ASSETS_PIECES / wo.slug
        has_images = gal_dir.is_dir() and any(
            p.suffix.lower() in _IMAGE_EXT for p in gal_dir.iterdir()
        )
        if has_images:
            lines.append(f"<!-- gallery: {wo.gallery_subpath} -->")
            lines.append("")
        ts_list = sorted(
            int(posts[i].get("timestamp") or 0) for i in wo.post_indices if posts[i].get("timestamp")
        )
        if ts_list:
            y0 = _dt(ts_list[0])
            y1 = _dt(ts_list[-1])
            if y0 and y1:
                lines.append(
                    f"*Mentioned on Facebook between {y0.strftime('%Y')} and {y1.strftime('%Y')}.*"
                )
                lines.append("")
        lines.append("")

    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    typer.echo(f"Wrote {output} ({len(work_objects)} objects)")


if __name__ == "__main__":
    app()
