# Livia Zaharia — Personal Website

A minimal personal website for **Livia Zaharia**, built with [Reflex](https://reflex.dev/) and managed with [uv](https://docs.astral.sh/uv/).

The site presents two connected facets of one practice:

- **Parametric art, jewellery, and computational design** (presented under [@paral_design](https://www.instagram.com/paral_design/))
- **GlucoseDAO — digital health, glucose prediction, and open technical experimentation** ([GitHub](https://github.com/GlucoseDAO/) · [Hugging Face Spaces](https://huggingface.co/spaces/GlucoseDao))

## Recent additions

- **Romanian Jewelry Week 2025 photos** — 12 exhibition photographs in `assets/RJW2025/`, documenting Livia's science-inspired jewellery line at ROJW 2025 (Nanot-of-Power, Mitochondria, Embryo, and more).
- **Artist knowledge base** — comprehensive reference document at `docs/livia-zaharia-knowledge-base.md` covering identity, practice, materials, collections catalogue, exhibition history, ecosystem connections (GlucoseDAO, Longevity Genie, HEALES, ARDD), and RPG lore.

## Prerequisites

### Git LFS

This repository uses [Git LFS](https://git-lfs.github.com/) to store image assets (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`). After cloning, you must pull the actual binary content:

```bash
git lfs install
git lfs pull
```

Without this step, image files (e.g. `assets/livia.jpg`) will be small text pointer files instead of real images, and the site background will be broken.

## Quick start

```bash
uv sync
uv run start
```

The site will be available at `http://localhost:3000/`.

## Content system (folder-based tabs)

Page content lives under `content/`. Standalone pages (`home.md`, `biography.md`) sit at the root. Tabbed pages are subfolders — each markdown file inside becomes a tab automatically.

### Directory layout

```
content/
  home.md                              # standalone (homepage)
  biography.md                         # standalone
  art-design/                          # tabbed page → /art-design
    _meta.yaml                         # page heading, accent colour, background, sidebar side
    _instagram.yaml                    # special tab (Instagram embed)
    1_Overview.md
    2_Materialized Enhancements.md     # reference → _shared/materialized_enhancements.md
    3_Cell Life.md
    4_Survival.md
    5_Science-Inspired.md
    6_Cry, Dance, Repeat.md
    7_Spotlight Pavilion.md
  science-tech/                        # tabbed page → /science-tech
    _meta.yaml
    _links.yaml                        # special tab (link list)
    1_Overview.md
    2_GlucoseDAO.md
    3_Materialized Enhancements.md     # reference → _shared/
    4_Longevity Genie.md
  _shared/                             # shared content reused across pages
    materialized_enhancements.md
```

### Naming convention

Files are named `N_Label Name.md` where `N` controls sort order and `Label Name` becomes the tab title. The `N_` prefix is stripped for display; you only see "Overview", "Cell Life", etc.

### Adding a new tab

1. Drop a file like `8_My New Tab.md` into the page's folder.
2. Restart the dev server (`uv run start`).

No Python code changes needed.

### Shared content (reference files)

To reuse the same markdown on multiple pages, put the content in `_shared/` and create a reference file in each page folder:

```yaml
---
ref: _shared/materialized_enhancements.md
---
```

### Special (non-markdown) tabs

YAML files prefixed with `_` (other than `_meta.yaml`) define special UI tabs like Instagram embeds or link lists. See `AGENTS.md` for the full schema.

### Supported markdown features

The app renders markdown with a custom component map. Standard markdown is supported:

- Paragraphs, links (`[label](url)`), headings (`#`, `##`)
- Standalone YouTube links are auto-rendered as embedded videos

After editing any markdown file, reload the page in the browser. If changes do not appear, restart the dev server:

```bash
uv run start
```

## Project structure

```
livia/
├── src/
│   └── livia/
│       ├── __init__.py
│       ├── livia.py       # Pages, components, styling, and content loader
│       └── start.py       # CLI entry point (typer)
├── content/
│   ├── home.md            # Homepage tagline
│   ├── biography.md       # Biography page
│   ├── art-design/        # Tabbed page: Art & Design (each .md = one tab)
│   ├── science-tech/      # Tabbed page: Science & Tech
│   └── _shared/           # Shared markdown referenced by multiple pages
├── assets/
│   ├── livia.jpg          # Full-screen portrait used as the background
│   └── RJW2025/           # Romanian Jewelry Week 2025 exhibition photos (12 images)
├── docs/
│   └── livia-zaharia-knowledge-base.md  # Artist knowledge base & catalogue
├── rxconfig.py            # Reflex configuration
├── pyproject.toml         # Python project / dependencies
├── .python-version        # Pinned to 3.13 (Reflex does not yet support 3.14)
└── README.md
```

Tabbed pages auto-discover tabs from their content subfolder. See the "Content system" section above for naming conventions and how to add tabs.

## Pages

| Route           | Purpose |
|-----------------|---------|
| `/`             | Homepage — full-screen portrait, floating bubbles, bottom nav |
| `/biography`    | Biography + external links |
| `/art-design`   | Art & Design — tabbed page (auto-discovered from `content/art-design/`) |
| `/science-tech` | Science & Tech — tabbed page (auto-discovered from `content/science-tech/`) |

## Design principles

### Portrait-first layout

The site is built around a single full-screen portrait photograph (`assets/livia.jpg`). The image fills the entire viewport on every page. On the homepage it appears with only a subtle gradient overlay; on inner pages it is dimmed so text panels remain readable.

There is no traditional page background colour, header image, or hero card. The face **is** the site.

### Dark glass panels

All text content sits inside dark translucent panels (`rgba(18, 15, 12, 0.82)` + `backdrop-filter: blur(20px)`). This ensures:

- Text is always readable against the photograph
- The portrait remains visible through the panel edges
- Panels feel layered on the image rather than replacing it

No text is ever placed directly on the photograph without a backing panel.

### Bottom navigation dock

Navigation is a single floating pill fixed to the bottom of the viewport. It contains four page links — no logo, no subtitle, no duplicate content. The dock uses the same dark glass treatment as the content panels.

The top of the page is completely clear so the portrait is unobstructed.

### Colour system

The palette is derived from the portrait itself:

| Token        | Value                          | Use |
|--------------|--------------------------------|-----|
| `BACKGROUND` | `#120f0c`                      | Page background behind the image |
| `PANEL_BG`   | `rgba(18, 15, 12, 0.82)`      | Content panel background |
| `TEXT_LIGHT`  | `#f5f0e8`                      | Primary text |
| `TEXT_MUTED`  | `rgba(245, 240, 232, 0.7)`    | Secondary text |
| `GREEN`      | `#5ea882`                      | GlucoseDAO / biology accent |
| `AMBER`      | `#d4943a`                      | Art / design accent |

Green and amber map to the two sides of the practice:

- **Green** — biology, digital health, GlucoseDAO, living systems
- **Amber** — parametric art, jewellery, fabrication, organic form

### Typography

- **Headlines**: Cormorant Garamond (serif) — elegant, editorial
- **Body / UI**: Manrope (sans-serif) — clean, geometric

Both are loaded from Google Fonts.

### Responsive behaviour

Reflex responsive arrays are used throughout. The general pattern:

- **Mobile**: full-width panels, centered text, compact nav
- **Desktop**: left-aligned content column (max 42rem), portrait visible on the right

Content is a single column; the portrait fills the remaining space.

### Instagram integration

The Art & Design page features a collapsible Instagram sidebar for the `@paral_design` profile. A vertical tab handle is always visible on the right edge of the viewport; clicking it slides open a panel with the live Instagram embed. The sidebar uses the same dark glass styling as the rest of the site and works on both mobile (overlay) and desktop (float alongside).

No API key or third-party widget system is required — the embed uses Instagram's public `/embed` endpoint.

## Components

The component set is deliberately small:

| Component            | Purpose |
|----------------------|---------|
| `bottom_nav`         | Fixed floating navigation pill |
| `fullscreen_bg`      | Homepage portrait + subtle gradient |
| `fullscreen_bg_dimmed` | Inner page portrait + dark overlay |
| `panel`              | Dark glass content container |
| `markdown_panel`     | Panel that renders markdown from `content/` |
| `feature_card`       | Project card (extends `panel`) |
| `link_list`          | Labelled link group (extends `panel`) |
| `instagram_sidebar`  | Collapsible right-edge `@paral_design` embed |
| `page_content`       | Centered content wrapper with bottom padding |
| `section_heading`    | Page title with accent gradient underline |

## Data model

Content text is loaded from `content/` at import time:
- Standalone pages use `load_content(name)` to read a single `.md` file.
- Tabbed pages use `load_tabs_from_folder(folder)` to scan a subfolder and build tabs automatically.

Structured data is defined as frozen dataclasses at the top of `livia.py`:

- `LinkItem(label, href, external)` — a single link
- `TabSpec(label, value, content)` — a single tab definition
- `BubbleItem(icon_label, title, tooltip, preview, href, angle, accent)` — a floating navigation bubble

The app has minimal Reflex state: `InstagramSidebarState` and `GithubSidebarState` (each a single `is_open` boolean).

## Links

### Design / personal presence

- Instagram: https://www.instagram.com/paral_design/
- LinkedIn: https://ro.linkedin.com/in/livia-zaharia-4b1425a0
- Romanian Jewelry Week 2021: https://www.romanianjewelryweek.com/participants-2021/livia-zaharia
- Romanian Jewelry Week 2023: https://www.romanianjewelryweek.com/participants-2023/livia-zaharia
- Romanian Jewelry Week 2024: https://www.romanianjewelryweek.com/participants-2024/livia-zaharia
- Romanian Jewelry Week 2025: https://www.romanianjewelryweek.com/participants-2025/livia-zaharia

### Longevity / science collaborations

- Materialized Enhancements: https://materialized-enhancements.longevity-genie.info/
- Longevity Genie: https://longevity-genie.github.io
- Longevity Genie GitHub: https://github.com/longevity-genie

### GlucoseDAO

- GitHub organization: https://github.com/GlucoseDAO/
- Hugging Face Spaces: https://huggingface.co/spaces/GlucoseDao

## License

See [LICENSE](LICENSE).
