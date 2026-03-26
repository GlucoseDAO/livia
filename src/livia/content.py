"""Content loading, markdown preprocessing, and tab scanning for the Livia website."""

import re
from pathlib import Path

import yaml

from livia.constants import (
    AMBER_DIM,
    ASSETS_DIR,
    CONTENT_DIR,
    GALLERY_DIRECTIVE_RE,
    ARTIFACT_IMAGE_RE,
    MARKDOWN_LINK_RE,
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
            folder = gallery_match.group(1)
            images = collect_gallery_images(folder)
            if images:
                img_tags = "".join(
                    f'<div style="border-radius:0.6rem;overflow:hidden;border:1px solid rgba(255,248,238,0.12)">'
                    f'<img src="{src}" style="width:100%;height:auto;object-fit:cover;border-radius:0.6rem" loading="lazy"/>'
                    f'</div>'
                    for src in images
                )
                output_lines.append(
                    f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:0.8rem;width:100%">'
                    f'{img_tags}</div>'
                )
            continue

        artifact_match = ARTIFACT_IMAGE_RE.match(stripped)
        if artifact_match is not None:
            src = artifact_match.group(1)
            output_lines.append(
                f'<div style="display:flex;justify-content:center;width:100%;margin:1rem 0">'
                f'<img src="{src}" style="max-width:400px;width:100%;height:auto;object-fit:contain;'
                f'border-radius:0.8rem;border:2px solid {AMBER_DIM};'
                f'box-shadow:0 4px 24px rgba(154,101,39,0.3)" loading="lazy"/></div>'
            )
            continue

        output_lines.append(line)

    return "\n".join(output_lines)


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


def load_folder_md_content(folder: str) -> dict[str, str]:
    """Read all markdown tab files from a content subfolder, returning {slug: preprocessed_content}."""
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
