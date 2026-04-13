"""Regenerate content/pieces.md: one ## section per assets/pieces folder (except Generic photos)."""

from __future__ import annotations

import re
from pathlib import Path

from livia.content import _title_case_phrase

REPO = Path(__file__).resolve().parents[1]
PIECES_ASSETS = REPO / "assets" / "pieces"
PIECES_MD = REPO / "content" / "pieces.md"

INTRO = """Each section is one object (work). Posts were grouped by topic and attached to that object. Text is English only when the export allowed it. For updates, see [Facebook](https://www.facebook.com/byLiviaZaharia/).

<!-- gallery: pieces/Generic photos -->
"""


def nice_heading_from_folder(folder: str) -> str:
    """Readable title matching folder name (used for ## and rail)."""
    s = folder.strip()
    s = s.replace("(", " (").replace("  (", " (")
    s = s.replace("-", " ")
    s = re.sub(r" +", " ", s)
    return _title_case_phrase(s)


def parse_old_sections(raw: str) -> dict[str, str]:
    """Map gallery folder path -> body markdown (no gallery directive)."""
    parts = re.split(r"(?m)^## ", raw)
    folder_to_body: dict[str, str] = {}
    for chunk in parts[1:]:
        lines = chunk.splitlines()
        if not lines:
            continue
        body = "\n".join(lines[1:]).strip()
        m = re.search(r"<!--\s*gallery:\s*pieces/(.+?)\s*-->", body)
        if not m:
            continue
        folder = m.group(1).strip()
        body_wo = re.sub(
            r"\n*<!--\s*gallery:\s*pieces/.+?\s*-->\s*",
            "\n\n",
            body,
            count=1,
        ).strip()
        folder_to_body[folder] = body_wo
    return folder_to_body


def main() -> None:
    old_raw = PIECES_MD.read_text()
    folder_to_body = parse_old_sections(old_raw)

    # Merge helix gold narrative into Helix wedding rings folder
    if "helix-gold" in folder_to_body:
        extra = folder_to_body.pop("helix-gold")
        prev = folder_to_body.get("Helix wedding rings", "").strip()
        folder_to_body["Helix wedding rings"] = (prev + "\n\n" + extra).strip() if prev else extra

    folders = sorted(
        p.name for p in PIECES_ASSETS.iterdir() if p.is_dir() and p.name != "Generic photos"
    )

    # Screw earrings copy lived under gallery `Star earings`; physical folder is `Horn earings`.
    horn_body = folder_to_body.pop("Star earings", "").strip()

    blocks: list[str] = [INTRO.strip(), ""]

    for folder in folders:
        heading = nice_heading_from_folder(folder)
        if folder == "Horn earings":
            body = horn_body or folder_to_body.get(folder, "").strip()
        else:
            body = folder_to_body.get(folder, "").strip()
        if not body:
            body = "Photographs from the studio archive."
        blocks.append(f"## {heading}\n\n{body}\n\n<!-- gallery: pieces/{folder} -->\n")

    PIECES_MD.write_text("\n".join(blocks).strip() + "\n")
    print(f"Wrote {PIECES_MD}: {len(folders)} folder sections.")


if __name__ == "__main__":
    main()
