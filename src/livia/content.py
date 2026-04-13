"""Content loading, markdown preprocessing, and tab scanning for the Livia website."""

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import yaml

from livia.constants import (
    AMBER_DIM,
    ASSETS_DIR,
    CONTENT_DIR,
    GALLERY_DIRECTIVE_RE,
    ARTIFACT_IMAGE_RE,
    MARKDOWN_LINK_RE,
    SEQUENCE_DIRECTIVE_RE,
    YOUTUBE_WATCH_RE,
    YOUTUBE_SHORT_RE,
    _REF_FRONTMATTER_RE,
    _TAB_PREFIX_RE,
)


def load_content(name: str) -> str:
    """Read a standalone markdown file from content/."""
    return (CONTENT_DIR / f"{name}.md").read_text()


def load_page_meta(folder: str) -> dict[str, str]:
    """Read _meta.yaml from a content subfolder. Returns defaults if absent."""
    meta_path = CONTENT_DIR / folder / "_meta.yaml"
    if meta_path.exists():
        return yaml.safe_load(meta_path.read_text()) or {}
    return {}


def _resolve_md_content(md_path: Path) -> str:
    """Read a markdown file, following ref: pointers in YAML front-matter."""
    raw = md_path.read_text()
    fm_match = _REF_FRONTMATTER_RE.fullmatch(raw.strip())
    if fm_match:
        meta = yaml.safe_load(fm_match.group(1)) or {}
        ref = meta.get("ref")
        if ref:
            return (CONTENT_DIR / ref).read_text()
    return raw


def _parse_tab_filename(stem: str) -> tuple[int, str]:
    """Parse 'N_Label Name' into (order, label). Falls back to (999, stem)."""
    m = _TAB_PREFIX_RE.match(stem)
    if m:
        return int(m.group(1)), m.group(2)
    return 999, stem


def _label_to_slug(label: str) -> str:
    """Convert a human label to a URL-friendly slug."""
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def extract_youtube_id(line: str) -> str | None:
    """Extract a YouTube video ID from a markdown line."""
    stripped = line.strip()
    if not stripped:
        return None

    candidate_url = stripped
    link_match = MARKDOWN_LINK_RE.fullmatch(stripped)
    if link_match:
        candidate_url = link_match.group(1)

    watch_match = YOUTUBE_WATCH_RE.fullmatch(candidate_url)
    if watch_match:
        return watch_match.group(1)

    short_match = YOUTUBE_SHORT_RE.fullmatch(candidate_url)
    if short_match:
        return short_match.group(1)

    return None


def encode_url_path(url_path: str) -> str:
    """Percent-encode each segment of a site-root URL path (spaces in filenames, etc.)."""
    if not url_path.startswith("/"):
        return url_path
    segments = [quote(segment, safe="") for segment in url_path.split("/") if segment]
    return "/" + "/".join(segments)


def collect_gallery_images(folder: str) -> list[str]:
    """Collect image paths from an assets subfolder, sorted by name."""
    folder_path = ASSETS_DIR / folder
    if not folder_path.is_dir():
        return []
    extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    images = sorted(
        p.name for p in folder_path.iterdir()
        if p.suffix.lower() in extensions
    )
    return [f"/{folder}/{name}" for name in images]


_RJW_IMAGE_INDEX: dict[str, list[str]] | None = None


def _split_trailing_paren_label(label: str) -> tuple[str, str | None]:
    """Split ``Title (subtitle)`` on the last pair of parentheses (mirrors ``components``)."""
    s = label.rstrip()
    if not s.endswith(")"):
        return label, None
    depth = 0
    for i in range(len(s) - 1, -1, -1):
        ch = s[i]
        if ch == ")":
            depth += 1
        elif ch == "(":
            depth -= 1
            if depth == 0:
                primary = s[:i].strip()
                subtitle = s[i + 1 : -1].strip()
                if primary and subtitle:
                    return primary, subtitle
                return label, None
    return label, None


_TITLE_SMALL_WORDS = frozenset(
    "a an the and or but of at to in for on by with from as per via".split()
)


def _title_case_phrase(s: str) -> str:
    """Title case with small words lowercased in the middle."""
    words = re.split(r"(\s+)", s.strip())
    out: list[str] = []
    for i, w in enumerate(words):
        if not w.strip():
            out.append(w)
            continue
        lw = w.lower()
        if i > 0 and lw in _TITLE_SMALL_WORDS:
            out.append(lw)
        else:
            out.append(w[:1].upper() + w[1:].lower() if len(w) > 1 else w.upper())
    return "".join(out)


def heading_to_rail_title(raw: str) -> str:
    """Readable tab-rail label: title case, keep trailing (…) for two-line stack in the rail."""
    s = raw.strip()
    primary, subtitle = _split_trailing_paren_label(s)
    if subtitle is None:
        return _title_case_phrase(primary)
    return f"{_title_case_phrase(primary)} ({subtitle})"


def extract_posting_date_hint(body_md: str) -> str | None:
    """Parse ``*Mentioned on Facebook between YYYY and YYYY.*`` into a short caption."""
    m = re.search(
        r"\*Mentioned on Facebook between (\d{4}) and (\d{4})\.\*",
        body_md,
    )
    if not m:
        return None
    a, b = m.group(1), m.group(2)
    if a == b:
        return f"Estimated from posts: {a}"
    return f"Estimated from posts: {a}–{b}"


def resolve_piece_date_hint(body_md: str, tab_key: str, gallery_slug: str) -> str | None:
    """Prefer Facebook posting range; if absent and images come from RJW only, use exhibition year."""
    fb = extract_posting_date_hint(body_md)
    if fb is not None:
        return fb
    if collect_gallery_images(f"pieces/{gallery_slug}"):
        return None
    for u in resolve_piece_gallery_urls(tab_key, gallery_slug):
        m = re.match(r"^/RJW(\d{4})/", u)
        if m:
            return f"Estimated from exhibition photographs: RJW {m.group(1)}"
    return None


def _strip_facebook_mention_line(body_md: str) -> str:
    return re.sub(
        r"\n*\*Mentioned on Facebook between \d{4} and \d{4}\.\*\s*",
        "\n",
        body_md,
        count=1,
    ).strip()


def _piece_field_slugs(piece_field: str) -> set[str]:
    slugs: set[str] = set()
    if "(" in piece_field and ")" in piece_field:
        inner = re.search(r"\(([^)]+)\)", piece_field)
        if inner:
            slugs.add(_label_to_slug(inner.group(1)))
    cleaned = re.sub(r"[()]", "", piece_field)
    slugs.add(_label_to_slug(cleaned.strip()))
    return {s for s in slugs if s}


def _rjw_slug_tokens_from_stem(stem: str) -> set[str]:
    """Derive piece slug keys from Romanian Jewelry Week filenames."""
    slugs: set[str] = set()
    if stem.startswith("LiviaZaharia-"):
        rest = stem[len("LiviaZaharia-") :]
        m = re.match(
            r"(?:pendant|ring|earings-and-rings)-(.+?)-(\d+)-(\d{4})",
            rest,
            re.I,
        )
        if m:
            piece = m.group(1).strip()
            slugs.add(_label_to_slug(piece))
    parts = stem.split("_")
    if len(parts) >= 4 and parts[0] == "LiviaZaharia" and parts[3].isdigit():
        slugs |= _piece_field_slugs(parts[2])
    if len(parts) >= 7 and parts[0] == "LiviaZaharia" and parts[1] == "ring":
        if parts[2] == "deep" and parts[3] == "sea" and parts[4] == "pearl":
            slugs.add(_label_to_slug("deep sea pearl Karmazina"))
    if len(parts) >= 5 and parts[0] == "LiviaZaharia" and parts[1] == "ring":
        if parts[2] == "rotary" and parts[3] == "magneticfields":
            slugs.add(_label_to_slug("rotary magnetic fields"))
    return {s for s in slugs if s}


def _rjw_extra_keys_from_stem(stem: str) -> set[str]:
    """Map non-standard stems to ``pieces.md`` gallery tab keys (``_label_to_slug`` of folder labels)."""
    s = stem.lower().replace(" ", "_")
    out: set[str] = set()
    if "eye_of_winter" in s or "ringpendant_eye" in s:
        out.add("eye-of-winter-double-ring-and-pendant")
    if "deep_sea_pearl" in s or "karmazina" in s:
        out.add("deep-sea-pearl-karmazina")
    if "rotary_magneticfields" in s or "rotary_magnetic" in s:
        out.add("rotary-magnetic-ring")
    return out


# ``pieces/…`` folder labels in pieces.md → RJW index key produced from filenames (suffix-stripped, spelling).
_RJW_TAB_KEY_ALIASES: dict[str, str] = {
    "ammonite-ring": "amonite",
    "beanut-fasolaluna-pendant": "beanut",
    "hollywood-pendant": "hollywood",
    "timeface-pendant": "timeface",
    "la-navette-pendant": "la-navette",
    "mountain-of-gold-double-ring": "mountain-of-gold",
    "piguen-nonaltra-pendant": "piguen",
    "sticks-and-stones-pendant": "sticks-and-stones",
    "the-nest-ring": "nest",
}

# RJW2025 booth photos (``IMG_*.jpg``) keyed by stem number → ``pieces.md`` tab key.
_RJW2025_IMG_TAB_KEYS: dict[str, str] = {
    "3493": "nut-of-power-pendant",
    "3496": "nut-of-power-pendant",
    "3481": "the-dark-nut-of-power-pendant",
    "3485": "the-dark-nut-of-power-pendant",
    "3433": "nanot-pendant",
    "3434": "nanot-pendant",
    "3438": "nanot-pendant",
    "3439": "nanot-pendant",
    "3475": "mitoring-mitochondria-ring",
    "3480": "mitoring-mitochondria-ring",
    "3465": "embryo-ring",
    "3466": "embryo-ring",
}


def _build_rjw_piece_image_index() -> dict[str, list[str]]:
    """Map normalized piece slug → image URL paths under ``assets/RJWYYYY/``."""
    index: dict[str, list[str]] = defaultdict(list)
    extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    for rjw_dir in sorted(ASSETS_DIR.glob("RJW[0-9][0-9][0-9][0-9]")):
        if not rjw_dir.is_dir():
            continue
        prefix = rjw_dir.name
        for p in rjw_dir.iterdir():
            if p.suffix.lower() not in extensions:
                continue
            stem = p.stem
            rel_url = f"/{prefix}/{p.name}"
            if prefix == "RJW2025" and stem.startswith("IMG_"):
                num = stem.split("_")[-1]
                tab = _RJW2025_IMG_TAB_KEYS.get(num)
                if tab:
                    index[tab].append(rel_url)
                continue
            for slug in _rjw_slug_tokens_from_stem(stem):
                index[slug].append(rel_url)
            for slug in _rjw_extra_keys_from_stem(stem):
                index[slug].append(rel_url)
    for slug in list(index.keys()):
        index[slug] = sorted(set(index[slug]))
    for tab_key, rjw_key in _RJW_TAB_KEY_ALIASES.items():
        if rjw_key in index and tab_key not in index:
            index[tab_key] = list(index[rjw_key])
    return dict(index)


def get_rjw_piece_image_index() -> dict[str, list[str]]:
    global _RJW_IMAGE_INDEX
    if _RJW_IMAGE_INDEX is None:
        _RJW_IMAGE_INDEX = _build_rjw_piece_image_index()
    return _RJW_IMAGE_INDEX


def resolve_piece_gallery_urls(tab_key: str, raw_subpath: str) -> list[str]:
    """Prefer ``assets/pieces/<raw_subpath>``; otherwise Romanian Jewelry Week images for that work."""
    local = collect_gallery_images(f"pieces/{raw_subpath}")
    if local:
        return local
    return list(get_rjw_piece_image_index().get(tab_key, []))


def collect_sequence_images(folder: str, filename_prefix: str = "UG_") -> list[str]:
    """Collect image paths for assembly-style cycling (e.g. Untold stage UG_* frames)."""
    folder_path = ASSETS_DIR / folder
    if not folder_path.is_dir():
        return []
    extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    images = sorted(
        p.name for p in folder_path.iterdir()
        if p.suffix.lower() in extensions and p.name.startswith(filename_prefix)
    )
    return [f"/{folder}/{name}" for name in images]


def preprocess_markdown_for_state(content: str) -> str:
    """Convert custom directives (YouTube, gallery, artifact) into HTML that rx.markdown can render.

    This allows markdown content to be stored as a plain string in rx.State
    and rendered dynamically without building an rx.Component tree at compile time.
    """
    output_lines: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()

        video_id = extract_youtube_id(stripped)
        if video_id is not None:
            output_lines.append(
                f'<div style="position:relative;width:100%;padding-top:56.25%;border-radius:0.9rem;overflow:hidden;background:#000;margin:1rem 0">'
                f'<iframe src="https://www.youtube.com/embed/{video_id}" '
                f'style="position:absolute;top:0;left:0;width:100%;height:100%;border:none;border-radius:0.8rem" '
                f'allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture;web-share" '
                f'allowfullscreen></iframe></div>'
            )
            continue

        gallery_match = GALLERY_DIRECTIVE_RE.match(stripped)
        if gallery_match is not None:
            folder = gallery_match.group(1).strip()
            if folder.startswith("pieces/"):
                raw_sub = folder[len("pieces/") :]
                tab_key = _label_to_slug(raw_sub)
                images = resolve_piece_gallery_urls(tab_key, raw_sub)
            else:
                images = collect_gallery_images(folder)
            if images:
                img_tags = "".join(
                    f'<div class="livia-lightbox-thumb-wrap" style="border-radius:0.6rem;overflow:hidden;border:1px solid rgba(255,248,238,0.12)">'
                    f'<img class="livia-lightbox-thumb" src="{encode_url_path(src)}" data-full-src="{encode_url_path(src)}" '
                    f'style="width:100%;height:auto;object-fit:cover;border-radius:0.6rem" loading="lazy" alt=""/>'
                    f"</div>"
                    for src in images
                )
                output_lines.append(
                    f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:0.8rem;width:100%">'
                    f'{img_tags}</div>'
                )
            continue

        artifact_match = ARTIFACT_IMAGE_RE.match(stripped)
        if artifact_match is not None:
            raw_path = artifact_match.group(1).strip()
            src = encode_url_path(raw_path) if raw_path.startswith("/") else raw_path
            output_lines.append(
                f'<div class="livia-artifact-wrap livia-lightbox-thumb-wrap">'
                f'<img class="livia-lightbox-thumb" src="{src}" data-full-src="{src}" alt="" '
                f'style="max-width:400px;width:100%;height:auto;object-fit:contain;'
                f"border-radius:0.8rem;border:2px solid {AMBER_DIM};"
                f'box-shadow:0 4px 24px rgba(154,101,39,0.3)" loading="lazy"/>'
                f"</div>"
            )
            continue

        sequence_match = SEQUENCE_DIRECTIVE_RE.match(stripped)
        if sequence_match is not None:
            folder = sequence_match.group(1).strip()
            images = collect_sequence_images(folder)
            if images:
                img_tags = "".join(
                    f'<img src="{encode_url_path(src)}" alt="" loading="lazy" '
                    f'style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;'
                    f'opacity:{1 if i == 0 else 0};transition:opacity 0.45s ease" />'
                    for i, src in enumerate(images)
                )
                output_lines.append(
                    f'<div class="livia-sequence" style="position:relative;width:100%;'
                    f"max-width:min(960px,100%);margin:1rem auto;border-radius:0.85rem;"
                    f"overflow:hidden;background:rgba(0,0,0,0.35);aspect-ratio:16/9;"
                    f'min-height:min(52vh,520px)">{img_tags}</div>'
                )
            continue

        output_lines.append(line)

    return "\n".join(output_lines)


_PIECES_GALLERY_IN_BODY_RE = re.compile(
    r"<!--\s*gallery:\s*pieces/(.+?)\s*-->",
)


@dataclass(frozen=True)
class PiecesTabEntry:
    """One piece section in ``pieces.md`` with a gallery or RJW exhibition images."""

    tab_key: str
    raw_heading: str
    body_md: str
    date_hint: str | None


def title_to_camel_case(raw: str) -> str:
    """Convert a piece ``##`` heading to lowerCamelCase for prominent titles."""
    words = re.findall(r"[A-Za-z0-9]+", raw)
    if not words:
        return raw.strip()
    first = words[0].lower()
    rest_parts: list[str] = []
    for w in words[1:]:
        if w.isdigit():
            rest_parts.append(w)
        else:
            rest_parts.append(w[:1].upper() + w[1:].lower())
    return first + "".join(rest_parts)


def parse_pieces_tab_entries() -> tuple[str | None, list[PiecesTabEntry]]:
    """Split ``content/pieces.md`` into an optional intro and piece sections with photo galleries.

    Uses ``assets/pieces/<slug>/`` when present; otherwise matches Romanian Jewelry Week files
    under ``assets/RJWYYYY/`` for the same work.
    """
    raw = load_content("pieces")
    sections = re.split(r"(?m)^## ", raw)
    intro = sections[0].strip() if sections else ""
    intro_out: str | None = intro if intro else None

    entries: list[PiecesTabEntry] = []
    seen_keys: set[str] = set()
    for chunk in sections[1:]:
        lines = chunk.splitlines()
        if not lines:
            continue
        raw_heading = lines[0].strip()
        body_md = "\n".join(lines[1:]).strip()
        m = _PIECES_GALLERY_IN_BODY_RE.search(body_md)
        if m is None:
            continue
        gallery_slug = m.group(1).strip()
        tab_key = _label_to_slug(gallery_slug)
        if not resolve_piece_gallery_urls(tab_key, gallery_slug):
            continue
        if tab_key in seen_keys:
            continue
        seen_keys.add(tab_key)
        entries.append(
            PiecesTabEntry(
                tab_key=tab_key,
                raw_heading=raw_heading,
                body_md=body_md,
                date_hint=resolve_piece_date_hint(body_md, tab_key, gallery_slug),
            ),
        )

    return intro_out, entries


def load_pieces_tab_content() -> dict[str, str]:
    """Preprocessed markdown per tab key for the Pieces page (overview + one entry per work)."""
    intro, entries = parse_pieces_tab_entries()
    out: dict[str, str] = {}
    if intro is not None:
        out["overview"] = preprocess_markdown_for_state(intro)
    for e in entries:
        body = _strip_facebook_mention_line(e.body_md)
        out[e.tab_key] = preprocess_markdown_for_state(body)
    return out


def scan_tab_slugs(folder: str) -> list[tuple[int, str, str, str]]:
    """Scan a content subfolder and return (order, label, slug, source_type) tuples.

    source_type is 'md:<filename>' for markdown tabs or the YAML type string for special tabs.
    """
    folder_path = CONTENT_DIR / folder
    entries: list[tuple[int, str, str, str]] = []

    for md_file in sorted(folder_path.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        order, label = _parse_tab_filename(md_file.stem)
        slug = _label_to_slug(label)
        entries.append((order, label, slug, f"md:{md_file.name}"))

    for yaml_file in sorted(folder_path.glob("_*.yaml")):
        if yaml_file.stem == "_meta":
            continue
        spec = yaml.safe_load(yaml_file.read_text()) or {}
        order = spec.get("order", 999)
        label = spec.get("label", yaml_file.stem.lstrip("_").replace("_", " ").title())
        slug = _label_to_slug(label)
        tab_type = spec.get("type", "")
        entries.append((order, label, slug, tab_type))

    entries.sort(key=lambda t: t[0])
    return entries


def load_folder_raw_md(folder: str) -> list[tuple[str, str, str]]:
    """Read raw (unprocessed) markdown for each tab in a folder.

    Returns a list of (slug, label, raw_markdown) tuples in tab order (N_ prefix).
    Used for building JSON-LD structured data and the content-map page, where
    clean text is preferred over preprocessed HTML.
    """
    folder_path = CONTENT_DIR / folder
    entries: list[tuple[int, str, str, str]] = []  # (order, slug, label, raw)
    for md_file in folder_path.glob("*.md"):
        if md_file.name.startswith("_"):
            continue
        order, label = _parse_tab_filename(md_file.stem)
        slug = _label_to_slug(label)
        entries.append((order, slug, label, _resolve_md_content(md_file)))
    entries.sort(key=lambda t: t[0])
    return [(slug, label, raw) for _order, slug, label, raw in entries]


def load_folder_md_content(folder: str) -> dict[str, str]:
    """Read all markdown tab files from a content subfolder, returning {slug: preprocessed markdown}.

    Artifacts become markdown images (for ``component_map`` ``img`` + lightbox); galleries and
    YouTube stay as embedded HTML processed for ``rx.markdown`` + rehype-raw.
    """
    folder_path = CONTENT_DIR / folder
    data: dict[str, str] = {}
    for md_file in sorted(folder_path.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        _, label = _parse_tab_filename(md_file.stem)
        slug = _label_to_slug(label)
        content_text = _resolve_md_content(md_file)
        data[slug] = preprocess_markdown_for_state(content_text)
    return data


def load_single_tab_md_content(folder: str, slug: str) -> str | None:
    """Read and preprocess a single markdown tab file by slug. Returns None if not found."""
    folder_path = CONTENT_DIR / folder
    for md_file in sorted(folder_path.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        _, label = _parse_tab_filename(md_file.stem)
        if _label_to_slug(label) == slug:
            return preprocess_markdown_for_state(_resolve_md_content(md_file))
    return None


def load_single_piece_tab_content(tab_key: str) -> str | None:
    """Read and preprocess a single piece's markdown by tab_key. Returns None if not found."""
    intro, entries = parse_pieces_tab_entries()
    if tab_key == "overview" and intro is not None:
        return preprocess_markdown_for_state(intro)
    for e in entries:
        if e.tab_key == tab_key:
            body = _strip_facebook_mention_line(e.body_md)
            return preprocess_markdown_for_state(body)
    return None
