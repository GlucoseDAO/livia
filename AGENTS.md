# Livia Project Agent Guide

## Project Layout (src layout)

- `src/livia/livia.py`: thin app entrypoint — imports `create_app()` from `pages.py` and exposes `app`.
- `src/livia/constants.py`: shared constants (colors, fonts, paths, regexes), data classes (`LinkItem`, `BubbleItem`, `TabSpec`), and static config data (nav links, bubble items).
- `src/livia/content.py`: content loading from the `content/` directory — markdown file reading, YAML front-matter ref resolution, tab slug scanning, YouTube/gallery/artifact directive preprocessing for dynamic state rendering.
- `src/livia/components.py`: reusable UI components — backgrounds, panels, navigation, sidebars, tabs layout, gallery/lightbox, bubble overlay, markdown rendering with custom embeds. Also contains interactive state classes (`GalleryState`, `InstagramSidebarState`, `GithubSidebarState`).
- `src/livia/pages.py`: page functions (`home_page`, `biography_page`, `art_design_page`, `science_tech_page`), content state classes (`ArtDesignContentState`, `ScienceTechContentState`), dynamic tab spec building, and `create_app()` which registers all pages.
- `src/livia/__init__.py`: package init (do not hardcode package version here).
- `src/livia/plugins.py`: removed; `ViteDevServerPlugin` is now inlined in `rxconfig.py`.
- `src/livia/start.py`: CLI entry point (`uv run start`); uses `typer`.
- `assets/`: static assets used by the app (for example, background images).
  - `assets/livia.jpg`: full-screen portrait used as the site background.
  - `assets/RJW2025/`: Romanian Jewelry Week 2025 exhibition photographs (12 images).
  - `assets/bubbles.css`: CSS for the floating navigation bubble overlay (keyframes, glass-morphism, tooltips, preview cards, responsive breakpoints).
  - The bubble JS logic (arc positioning, periodic shiver, resize repositioning) is implemented as a React `useEffect` hook via the `BubbleHooks` component in `components.py`, not as an external JS file.
- `content/`: page content organised as a **folder-based tab system** (see "Content System" below). Standalone pages (`home.md`, `biography.md`) live at the root; tabbed pages live in subfolders (`art-design/`, `science-tech/`). Shared content lives in `_shared/`.
- `docs/`: reference documentation not rendered by the app.
  - `docs/livia-zaharia-knowledge-base.md`: comprehensive artist knowledge base covering identity, practice, collections catalogue, exhibition history, and ecosystem connections.
- `rxconfig.py`: Reflex runtime/config entrypoint.
- `pyproject.toml`: Python project metadata and dependency source of truth.
- `uv.lock`: dependency lockfile managed by `uv`.
- `.python-version`: interpreter pin used by local tooling.
- `.web/`: generated frontend/build output from Reflex toolchain; treat as generated artifacts unless a task explicitly requires editing them. Note: Reflex copies assets to `.web/public/` and stylesheets to `.web/styles/` at compile time; during dev, CSS/JS asset changes may need manual copy to `.web/styles/` and `.web/public/` if hot-reload does not pick them up.
- `.states/`: local state artifacts.

## Content System (folder-based tabs)

Each tabbed page corresponds to a subfolder under `content/`. Tabs are auto-discovered from the files inside — no Python code changes needed to add, remove, or reorder tabs.

### Directory layout

```
content/
  home.md                              # standalone page (no tabs)
  biography.md                         # standalone page (no tabs)
  art-design/                          # tabbed page → /art-design
    _meta.yaml                         # page-level config
    _instagram.yaml                    # special (non-markdown) tab
    1_Overview.md                      # tab 1
    2_Materialized Enhancements.md     # tab 2 (reference file)
    3_Cell Life.md                     # tab 3
    ...
  science-tech/                        # tabbed page → /science-tech
    _meta.yaml
    _links.yaml                        # special tab
    1_Overview.md
    ...
  _shared/                             # shared markdown reused across pages
    materialized_enhancements.md
```

### Naming convention for tab files

- Format: `N_Label Name.md` where N is an integer that controls ordering.
- The prefix `N_` is stripped; the remaining stem becomes the tab label verbatim.
- The tab slug (internal value) is auto-derived by lowercasing and hyphenating the label.
- Files starting with `_` are metadata/config, never rendered as tabs.

### Adding a new tab

Drop a file like `8_New Tab Name.md` into the page's folder. The number sets its position among existing tabs. **Adding a new tab file** requires a server restart (the tab structure is built at compile time). **Editing existing tab content** is picked up on the next page load without restart — markdown content is stored in `rx.State` and re-read from disk via `on_load`.

### Reference files (shared content)

A `.md` file whose entire content is YAML front-matter with a `ref` key:

```yaml
---
ref: _shared/materialized_enhancements.md
---
```

The loader follows the pointer and renders content from the referenced path. This allows the same content to appear as a tab on multiple pages without duplication.

### `_meta.yaml` (page config)

Each tabbed page folder has a `_meta.yaml` with:

| Field          | Type   | Description                                            |
|----------------|--------|--------------------------------------------------------|
| `heading`      | string | Page heading text                                      |
| `accent`       | string | Colour key: `amber` or `green`                        |
| `background`   | string | Background variant: `yellow`, `green`, `dimmed`, `default` |
| `sidebar_side` | string | Tab sidebar position: `left` or `right`                |

### Special tab convention files (`_*.yaml`)

YAML files (other than `_meta.yaml`) that start with `_` define non-markdown tabs:

| Field    | Type   | Description                                    |
|----------|--------|------------------------------------------------|
| `label`  | string | Tab label text                                 |
| `order`  | int    | Position among all tabs                        |
| `type`   | string | Component type: `instagram_embed` or `link_list` |

For `link_list` type, additional fields:

| Field    | Type   | Description                          |
|----------|--------|--------------------------------------|
| `accent` | string | Colour key for the link list         |
| `links`  | list   | List of `{label, href}` objects      |

## Major Design and Coding Principles

- Always write Python code with explicit type hints for function/method parameters and return values.
- Avoid unnecessary `try/except` blocks; prefer straightforward error propagation unless recovery is intentional and justified.
- Keep architecture and coding style consistent with existing patterns in `src/livia/` modules unless the task requires a refactor.
- Prefer focused, minimal changes over broad rewrites.
- Use absolute imports; do not introduce relative imports.
- For CLI additions, use `typer`.
- Use `uv` workflow for this project (`uv sync`, `uv add`, `uv run ...`).

## Documentation Freshness Rule

- If any instruction in `AGENTS.md` becomes outdated due to code or tooling changes, update `AGENTS.md` in the same work cycle as the code change.
- Treat this file as a living source of truth for contributors and coding agents.

## UI Change Verification Rule

When a change affects UI/UX, validation is required before considering the task complete:

1. Check terminal output for build/runtime errors and warnings relevant to the changed UI.
2. Verify the change in a browser (or browser automation) to confirm behavior and visual result match intent.
3. If verification fails, fix and re-check before finalizing.

## Learned User Preferences

- Never use cryptic abbreviations or acronyms in UI labels or navigation; always use full readable words (e.g. "YouTube" not "YT", "GitHub" not "GH", "About" not "Ab").
- All text rendered over background images must have a sufficiently opaque panel or backdrop behind it to ensure readability; never place gray or low-contrast text directly on a photo.
- Do not bloat the homepage with all content at once; show content only when the user navigates to it.
- Prefer Reflex internal Python APIs (e.g. `_init`, `_run` from `reflex.reflex`) over spawning subprocesses for Reflex commands.
- The deployment server (agingkills.eu) runs Caddy as a reverse proxy; Caddy is not on the local dev machine.
- Content panels and text must fill available screen space with generous sizing and large fonts; never render small, narrow text boxes that waste screen real estate.
- When asked to act (e.g. "do stuff for me"), proceed decisively without asking for further confirmation.
- Sidebars (Instagram on right, GitHub/LinkedIn on left) must be open/visible by default on the home page; users can close them, but they should not be hidden requiring a click to reveal.
- On large screens, content pages should use sidebar tabs (left for Science & Tech, right for Art & Design) rather than full-width vertical layouts that cause super-wide, hard-to-read text lines.

## Learned Workspace Facts

- `rxconfig.py` must not import from the `src/livia/` package because Reflex's `get_config()` strips `sys.path` during early init; any plugins must be inlined directly in `rxconfig.py`.
- The user-visible port is controlled by `frontend_port` in Reflex config, not `backend_port`; default is 3010 with backend at 3011.
- Git LFS is configured (`.gitattributes`) to track `*.jpg`, `*.jpeg`, `*.png`, `*.gif`, `*.webp`.
- During dev, Reflex hot-reload may not pick up changes to CSS/JS files in `assets/`; manually copy to `.web/public/` and `.web/styles/` if needed.
- The `src/livia/plugins.py` file was removed; `ViteDevServerPlugin` is now inlined in `rxconfig.py` to avoid the import isolation issue.
- The site uses per-page-category background images: `green_side.jpg` for Science & Tech pages, `yellow_side.jpg` for Art & Design pages, `livia.jpg` for neutral/home pages.
- Site navigation structure: Home (`/`), Biography (`/biography`), Art & Design (`/art-design`), Science & Tech (`/science-tech`). No external links in top-level nav.
- The GitHub remote is `github.com:GlucoseDAO/livia.git`; diverged histories from LFS migration may require `--force` push.
- Bubble positions: Science & Tech = left arc (green border), Biography = top center, Art & Design = right arc (yellow border); the Home bubble was removed as redundant since bubbles only appear on the home page.
- Art & Design and Science & Tech pages use the folder-based tab system; tabs are auto-discovered from `content/art-design/` and `content/science-tech/` respectively. Bottom nav uses `rx.State.router.page.path` to highlight the active page.
- GitHub and LinkedIn do not offer embeddable iframe widgets; a custom "tech sidebar" component is used instead with links and icons.
- The site forces desktop rendering on mobile via `<meta name="viewport" content="width=1280">` in `head_components`. Mobile-specific CSS breakpoints are intentionally bypassed; the page is always rendered as a 1280px-wide desktop layout and scaled down on phones.
- Sidebars (`InstagramSidebarState`, `GithubSidebarState`) default to **closed** (`is_open=False`). On wide screens (≥1024px physical), `ScreenWidthDetector.open_sidebars_if_wide` opens them via `on_mount` + `rx.call_script("window.screen.width")`. This prevents sidebars from crowding the view on phones.
- Bottom nav and bubble labels use CSS `max()` / `clamp()` with pixel minimums to ensure tappability on scaled-down mobile viewports.
