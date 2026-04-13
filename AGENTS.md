# Livia Project Agent Guide

## Project Layout (src layout)

- `src/livia/livia.py`: thin app entrypoint — imports `create_app()` from `pages.py` and exposes `app`.
- `src/livia/constants.py`: shared constants (colors, fonts, paths, regexes), data classes (`LinkItem`, `TabSpec`), and static config data (nav links with optional `accent` / `tooltip`).
- `src/livia/content.py`: content loading from the `content/` directory — markdown file reading, YAML front-matter ref resolution, tab slug scanning, YouTube/gallery/artifact directive preprocessing for dynamic state rendering.
- `src/livia/components.py`: reusable UI components — backgrounds, panels, navigation, sidebars (CSS hover-expand tool rails, no sidebar state), tabs layout, gallery/lightbox, markdown rendering with custom embeds. Also contains `GalleryState` for the lightbox.
- `src/livia/pages.py`: page functions (`home_page`, `biography_page`, `art_design_page`, `science_tech_page`), content state classes (`ArtDesignContentState`, `ScienceTechContentState`), dynamic tab spec building, and `create_app()` which registers all pages.
- `src/livia/__init__.py`: package init (do not hardcode package version here).
- `src/livia/plugins.py`: removed; `ViteDevServerPlugin` is now inlined in `rxconfig.py`.
- `src/livia/start.py`: CLI entry point (`uv run start`); uses `typer`.
- `assets/`: static assets used by the app (for example, background images).
  - `assets/livia.jpg`: full-screen portrait used as the site background.
  - `assets/RJW2025/`: Romanian Jewelry Week 2025 exhibition photographs (12 images).
  - `assets/bubbles.css`: Chrome UI — `--livia-ui-scale` is `1` on `html.livia-wide` and `2.5` on `html.livia-narrow`. The **bottom nav** on narrow is **one row of four equal-width buttons** at the **same font size as laptop**; long labels **wrap inside** the button (typically up to two lines). Home **edge tool rails** (Instagram / GitHub) use `--livia-tool-rail-scale` (**1.5** on narrow) instead of the full `2.5`. Page tabs and other chrome use `--livia-ui-scale` (or capped tab rules). Hover glows, tab rail expand-on-hover.
  - `assets/livia_nav.js`: sets `livia-narrow` when **`screen.width < 1024` OR `innerWidth < 1024`** (so Firefox/Chrome responsive mode works: `screen.width` often stays desktop-sized while `innerWidth` matches the emulated device). Sets `livia-wide` otherwise. Active nav highlighting, stale session key cleanup. Listens to `resize` and `visualViewport.resize`.
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
    1_Overview.md
    2_Livia Lore.md
    3_Materialized Enhancements.md     # reference file
    4_It's Just a Cell Life (RJW 2025).md
    5_Beloved Food (RJW 2024).md
    6_Survival (RJW 2023).md
    7_Paths. Memories. Guides (RJW 2022).md
    8_Parametric (by) nature (RJW 2021).md
    9_Cry, Dance, Repeat.md
    10_Spotlight Pavilion.md
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

### Markdown directives (tabbed pages)

- `<!-- gallery: Subfolder -->` — responsive grid of all images in `assets/Subfolder/` (click to enlarge).
- `<!-- artifact: /path/under/assets.jpg -->` — one centered image (click to enlarge); path is site-root under `assets/`.
- `<!-- sequence: Subfolder -->` — opacity slideshow of files in `assets/Subfolder/` whose names start with `UG_` (assembly-style preview; no lightbox).

### Reference files (shared content)

A `.md` file whose entire content is YAML front-matter with a `ref` key:

```yaml
---
ref: _shared/materialized_enhancements.md
---
```

The loader follows the pointer and renders content from the referenced path. This allows the same content to appear as a tab on multiple pages without duplication.

### Linking Instagram or Facebook posts

Use normal markdown links in tab markdown. Example (see `content/art-design/9_Cry, Dance, Repeat.md`): `[View on Instagram](https://www.instagram.com/p/POST_ID/)`. For Facebook, use the post permalink from [byLiviaZaharia](https://www.facebook.com/byLiviaZaharia/) (open the post → **···** or **Share** → copy link). You can add multiple lines such as `[View on Facebook](https://www.facebook.com/...)` next to collection descriptions.

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
- Edge tool rails (Instagram on the right, GitHub & Tech on the left) stay **collapsed** to a grip strip whose minimum width scales with `--livia-ui-scale`. They **expand** on fine-pointer **hover** or when the rail has **`:focus-within`** (tap the strip on touch). Bottom nav never auto-hides.
- On large screens, content pages should use sidebar tabs (left for Science & Tech, right for Art & Design) rather than full-width vertical layouts that cause super-wide, hard-to-read text lines.
- Contest and collection tabs: put the work or collection name first, then the competition and year in parentheses (for example `… (RJW YYYY)`, `… (Osmium YYYY)`, `… (Vinca YYYY)`, `… (Spotlight YYYY)`); detailed per-piece writeups follow the Livia Lore pattern (`## Pieces`, `###` headings, metadata lines, grouped `<!-- artifact: /path/to/file.jpg -->` directives). When adding multiple dated competition tabs, order them reverse chronologically (newest first) unless the user specifies otherwise.
- When changing active-tab or selection visuals (side rails, tab triggers), adjust position, padding, or offset so the indicator remains visible; avoid clearing the theme border or box-shadow in a way that removes the selected state entirely.

## Learned Workspace Facts

- `rxconfig.py` must not import from the `src/livia/` package because Reflex's `get_config()` strips `sys.path` during early init; `ViteDevServerPlugin` and similar must be inlined there (the old `src/livia/plugins.py` was removed for this reason).
- The user-visible port is controlled by `frontend_port` in Reflex config, not `backend_port`; default is 3010 with backend at 3011.
- Git LFS is configured (`.gitattributes`) to track `*.jpg`, `*.jpeg`, `*.png`, `*.gif`, `*.webp`.
- `encode_url_path()` in `src/livia/content.py` percent-encodes path segments for `gallery` and `artifact` image URLs so asset filenames with spaces resolve correctly in the browser.
- `github_sidebar()` is used on the home page only; the Science & Tech page layout does not include that left rail.
- The site uses per-page-category background images: `green_side.jpg` for Science & Tech pages, `yellow_side.jpg` for Art & Design pages, `livia.jpg` for neutral/home pages.
- Site navigation: Home (`/`), Biography (`/biography`), Art & Design (`/art-design`), Science & Tech (`/science-tech`); no external links in top-level nav. Home uses the portrait background and bottom nav only (no duplicate floating arc nav). Art & Design and Science & Tech use folder-based tabs auto-discovered from `content/art-design/` and `content/science-tech/`; bottom nav highlights the active page via `rx.State.router.page.path`.
- Art & Design expanded desktop tab list scrolls vertically in CSS so many rail tabs (including the last special tab from `_instagram.yaml`) stay reachable; `order` in `_instagram.yaml` is sort-only and is not shown as a visible tab number.
- Sidebar tab labels stack when the tab title ends with `(RJW YYYY)`, `(Osmium YYYY)`, `(Vinnca YYYY)` / `(Vinca YYYY)`, `(Spotlight YYYY)`, or a trailing year-only `(YYYY)`; the second line is centered (class `livia-tab-label-sub` in `assets/bubbles.css`, split logic in `components.py`).
- The site uses `<meta name="viewport" content="width=device-width, initial-scale=1">` in `head_components`. Narrow layouts are detected via `livia_nav.js` (`html.livia-narrow` / `livia-wide`, including `matchMedia("(max-width: 1023px)")`). The bottom nav on narrow is **one row** of four flex-equal links at **laptop text size**; labels **wrap inside** each pill when needed. Home-page tool rails use `--livia-tool-rail-scale` (`1.5` on narrow). Other chrome uses `--livia-ui-scale` (`2.5` on narrow); page tab buttons cap that scale (see `assets/bubbles.css`).
- Edge sidebars (`instagram_sidebar`, `github_sidebar`) are fixed tool rails: a narrow grip (`@paral_design` on the right, `GITHUB / TECH` on the left) with the same typography as before; on fine pointers they **expand on hover** (and `focus-within` for keyboard) via `assets/bubbles.css`. On coarse pointers they stay at a usable width (`min(360px, 88vw)`). No Reflex state for open/close.
- Bottom nav and bubble labels use CSS `max()` / `clamp()` with pixel minimums to ensure tappability on scaled-down mobile viewports.
