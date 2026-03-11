# Livia Zaharia — Personal Website

A minimal personal website for **Livia Zaharia**, built with [Reflex](https://reflex.dev/) and managed with [uv](https://docs.astral.sh/uv/).

The site presents two connected facets of one practice:

- **Parametric art, jewellery, and computational design** (presented under [@paral_design](https://www.instagram.com/paral_design/))
- **GlucoseDAO — digital health, glucose prediction, and open technical experimentation** ([GitHub](https://github.com/GlucoseDAO/) · [Hugging Face Spaces](https://huggingface.co/spaces/GlucoseDao))

## Quick start

```bash
uv sync
uv run start
```

The site will be available at `http://localhost:3000/`.

## Updating website content

All editable page copy lives in `content/*.md`:

- `content/home.md` - homepage tagline text
- `content/about.md` - About page body
- `content/art_design.md` - Art & Design page body
- `content/glucosedao.md` - GlucoseDAO page body

The app renders these files through `rx.markdown` with a custom component map. In practice, this means standard markdown is supported and styled consistently:

- Paragraphs
- Links like `[label](https://example.com)`
- Headings `#` and `##`

There is also one custom behavior: a standalone YouTube link (either `youtube.com/watch?...` or `youtu.be/...`) is auto-rendered as an embedded video.

After editing markdown:

1. Save the file.
2. Reload the page in the browser.
3. If changes do not appear, restart the dev server:

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
│       ├── plugins.py     # Reflex plugins (Vite dev-server patching)
│       └── start.py       # CLI entry point (typer)
├── content/
│   ├── home.md            # Homepage tagline text
│   ├── about.md           # Bio paragraph
│   ├── art_design.md      # Art & Design intro
│   └── glucosedao.md      # GlucoseDAO description
├── assets/
│   └── livia.jpg          # Full-screen portrait used as the background
├── rxconfig.py            # Reflex configuration
├── pyproject.toml         # Python project / dependencies
├── .python-version        # Pinned to 3.13 (Reflex does not yet support 3.14)
└── README.md
```

Page text lives in `content/*.md` files. The `load_content()` helper reads them at import time and feeds them to `rx.markdown` with a styled `component_map`.

## Pages

| Route          | Purpose |
|----------------|---------|
| `/`            | Homepage — full-screen portrait, name overlay, bottom nav |
| `/about`       | Bio + links connecting art and GlucoseDAO work |
| `/art-design`  | Selected collections + collapsible Instagram sidebar |
| `/glucosedao`  | GlucoseDAO description with links to the org |

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

Content text lives in `content/*.md` files and is loaded by `load_content()` at import time.

Structured data is defined as frozen dataclasses at the top of `livia.py`:

- `LinkItem(label, href, external)` — a single link
- `CardItem(title, body, href, link_label, accent, external)` — a project card

The Instagram sidebar uses `InstagramSidebarState` (a single boolean `is_open`) — the only piece of Reflex state in the app.

## Links

### Design / personal presence

- Instagram: https://www.instagram.com/paral_design/
- LinkedIn: https://ro.linkedin.com/in/livia-zaharia-4b1425a0
- Romanian Jewelry Week 2022: https://www.romanianjewelryweek.com/participants-2022/livia-zaharia
- Romanian Jewelry Week 2024: https://www.romanianjewelryweek.com/participants-2024/livia-zaharia

### GlucoseDAO

- GitHub organization: https://github.com/GlucoseDAO/
- Hugging Face Spaces: https://huggingface.co/spaces/GlucoseDao

## License

See [LICENSE](LICENSE).
