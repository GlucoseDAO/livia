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
  - `assets/bubbles.css`: Chrome UI — `--livia-ui-scale` is `1` on `html.livia-wide` and `2.5` on `html.livia-narrow`. The **bottom nav** on narrow is **one row of equal-width buttons** at the **same font size as laptop**; long labels **wrap inside** the button (typically up to two lines). Home **edge tool rails** (Instagram / GitHub) use `--livia-tool-rail-scale` (**1.5** on narrow) instead of the full `2.5`. Page tabs and other chrome use `--livia-ui-scale` (or capped tab rules). Hover glows, tab rail expand-on-hover.
  - `assets/livia_nav.js`: sets `livia-narrow` when **`screen.width < 1024` OR `innerWidth < 1024`** (so Firefox/Chrome responsive mode works: `screen.width` often stays desktop-sized while `innerWidth` matches the emulated device). Sets `livia-wide` otherwise. Active nav highlighting, stale session key cleanup. Listens to `resize` and `visualViewport.resize`.
- `content/`: page content organised as a **folder-based tab system** (see "Content System" below). Standalone pages (`home.md`, `biography.md`, `pieces.md` → `/pieces`) live at the root; tabbed pages live in subfolders (`art-design/`, `science-tech/`). Shared content lives in `_shared/`. **`content/not_shared/`** is gitignored: local Facebook exports and private notes only — not read by the app and not for GitHub. Regenerate `pieces.md` after updating the export: `uv run python scripts/generate_pieces_from_fb_export.py`.
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
  pieces.md                            # → /pieces; split on ``##`` into sidebar tabs; images from ``assets/pieces/<folder>/`` (folder name may contain spaces; must match the ``<!-- gallery: pieces/… -->`` path) or, when that folder is empty, matched files under ``assets/RJWYYYY/`` (Romanian Jewelry Week)
  art-design/                          # tabbed page → /art-design
    _meta.yaml                         # page-level config
    _instagram.yaml                    # special (non-markdown) tab
    1_Overview.md
    2_Livia Lore.md
    3_Materialized Enhancements.md     # reference file
    4_A world for everyone (RJW 2026).md
    5_Death Yes No Maybe (Berlin 2026).md   # A Hidden Variable festival (not RJW)
    6_It's Just a Cell Life (RJW 2025).md
    7_Shine bright like a star (Osmium 2025).md
    8_Beloved Food (RJW 2024).md
    … then reverse-chronological competition and context tabs through 19_iMAPP (iMapp 2017-2018).md
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

Use normal markdown links in tab markdown. Example: `[View on Instagram](https://www.instagram.com/p/POST_ID/)`. For Facebook, use the post permalink from [byLiviaZaharia](https://www.facebook.com/byLiviaZaharia/) (open the post → **···** or **Share** → copy link). You can add multiple lines such as `[View on Facebook](https://www.facebook.com/...)` next to collection descriptions.

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
- The deployment server runs Caddy as a reverse proxy; Caddy is not on the local dev machine. The production site URL is https://livia.glucosedao.org (set as DEPLOY_URL in .env).
- Content panels and text must fill available screen space with generous sizing and large fonts; never render small, narrow text boxes that waste screen real estate.
- When asked to act (e.g. "do stuff for me"), proceed decisively without asking for further confirmation.
- Edge tool rails (Instagram on the right, GitHub & Tech on the left) stay **collapsed** to a grip strip whose minimum width scales with `--livia-ui-scale`. They **expand** on fine-pointer **hover** or when the rail has **`:focus-within`** (tap the strip on touch). Bottom nav never auto-hides.
- On large screens, content pages should use sidebar tabs (left for Science & Tech, right for Art & Design) rather than full-width vertical layouts that cause super-wide, hard-to-read text lines.
- Contest and collection tabs: put the work or collection name first, then the competition and year in parentheses (for example `… (RJW YYYY)`, `… (Osmium YYYY)`, `… (Vinca YYYY)`, `… (Spotlight YYYY)`); detailed per-piece writeups follow the Livia Lore pattern (`## Pieces`, `###` headings, metadata lines, grouped `<!-- artifact: /path/to/file.jpg -->` directives). When adding multiple dated competition tabs, order them reverse chronologically (newest first) unless the user specifies otherwise.
- When changing active-tab or selection visuals (side rails, tab triggers), adjust position, padding, or offset so the indicator remains visible; avoid clearing the theme border or box-shadow in a way that removes the selected state entirely. The active page/tab highlight must also be visible on initial page load (not just after user clicks) — drive it from `rx.State.router.page.path` or the current tab slug, not from a click-only handler.
- Sidebar tab labels must accommodate long names by wrapping or stretching the rail — never truncate/clip tab text. Keep the stacking rule for titles ending in `(Competition YYYY)` / trailing `(YYYY)`, and allow normal word-wrap for other long labels.
- The site must be bot- and SEO-friendly: prefer Reflex's built-in SSR / prerender and compile-time HTML generation (sitemap, `llms.txt`, per-page `meta`) over client-only rendering. Avoid introducing content that is only reachable via WebSocket hydration or `on_load`-only fetches if that content should be indexable.

## Learned Workspace Facts

- `rxconfig.py` must not import from the `src/livia/` package because Reflex's `get_config()` strips `sys.path` during early init; `ViteDevServerPlugin` and similar must be inlined there (the old `src/livia/plugins.py` was removed for this reason).
- The user-visible port is controlled by `frontend_port` in Reflex config, not `backend_port`; default is 3010 with backend at 3011. Bind address defaults to `0.0.0.0` for both the Reflex backend and the Vite dev server; set `HOST` in `.env` (loaded at the top of `rxconfig.py` via `load_dotenv()`) to override. `rxconfig.py` patches Reflex’s startup banners so “App running at” / “Backend running at” use that host (upstream Reflex otherwise prints `localhost` / hardcoded `0.0.0.0`).
- Git LFS is configured (`.gitattributes`) to track `*.jpg`, `*.jpeg`, `*.png`, `*.gif`, `*.webp`.
- `encode_url_path()` in `src/livia/content.py` percent-encodes path segments for `gallery` and `artifact` image URLs so path segments resolve in the browser; still prefer simple URL-safe names under `assets/` (no spaces; avoid `+` in filenames) because static hosting and tooling can fail on awkward paths even when encoded.
- `github_sidebar()` is used on the home page only; the Science & Tech page layout does not include that left rail.
- The site uses per-page-category background images: `green_side.jpg` for Science & Tech pages, `yellow_side.jpg` for Art & Design and Pieces (`/pieces`) pages, `livia.jpg` for neutral/home pages. Site navigation: Home (`/`), Biography (`/biography`), Art & Design (`/art-design`), Science & Tech (`/science-tech`), Pieces (`/pieces`); no external links in top-level nav. Home uses the portrait background and bottom nav only (no duplicate floating arc nav). Art & Design and Science & Tech use folder-based tabs auto-discovered from `content/art-design/` and `content/science-tech/`; bottom nav highlights the active page via `rx.State.router.page.path`.
- Art & Design expanded desktop tab list scrolls vertically in CSS so many rail tabs (including the last special tab from `_instagram.yaml`) stay reachable; `order` in `_instagram.yaml` is sort-only and is not shown as a visible tab number.
- Sidebar tab labels stack when the tab title ends with `(RJW YYYY)`, `(Berlin YYYY)`, `(Osmium YYYY)`, `(Vinnca YYYY)` / `(Vinca YYYY)`, `(Spotlight YYYY)`, or a trailing year-only `(YYYY)`; the second line is centered (class `livia-tab-label-sub` in `assets/bubbles.css`, split logic in `components.py`).
- The site uses `<meta name="viewport" content="width=device-width, initial-scale=1">` in `head_components`. Narrow layouts are detected via `livia_nav.js` (`html.livia-narrow` / `livia-wide`, including `matchMedia("(max-width: 1023px)")`). The bottom nav on narrow is **one row** of four flex-equal links at **laptop text size**; labels **wrap inside** each pill when needed. Home-page tool rails use `--livia-tool-rail-scale` (`1.5` on narrow). Other chrome uses `--livia-ui-scale` (`2.5` on narrow); page tab buttons cap that scale (see `assets/bubbles.css`). Bottom-nav and related chrome use CSS `max()` / `clamp()` with pixel minimums so controls stay tappable on narrow viewports.
- Edge sidebars (`instagram_sidebar`, `github_sidebar`) are fixed tool rails: a narrow grip (`@paral_design` on the right, `GITHUB / TECH` on the left) with the same typography as before; on fine pointers they **expand on hover** (and `focus-within` for keyboard) via `assets/bubbles.css`. On coarse pointers they stay at a usable width (`min(360px, 88vw)`). No Reflex state for open/close.
- Folder-tab page bodies use `rx.markdown(..., use_unwrap_images=False)` in `pages.py` so HTML injected during markdown preprocessing (gallery grids, artifacts, `sequence` blocks) is not broken by Reflex’s default rehype-unwrap-images pass.
- SSR/prerendering is enabled by default via `os.environ.setdefault("REFLEX_SSR", "true")` in `rxconfig.py` so production builds emit pre-rendered HTML for bots; this only affects `reflex export` / production builds, not the Vite dev server (`uv run start` stays client-hydrated). Set `REFLEX_SSR=false` to disable. `rx.plugins.SitemapPlugin()` and a custom `LlmsTxtPlugin` (in `rxconfig.py`) emit `/sitemap.xml` and `/llms.txt` at compile time so crawlers and LLM fetchers can read all site content without JavaScript.
- Art & Design includes a **Livia Lore** tab (`content/art-design/2_Livia Lore.md`, positioned after Overview) that renders the artifact connection schema using real artifact images (not ASCII diagrams) and Livia's RPG-style character card with sub-headings separating artifact lore from character stats. Source material is `docs/livia-zaharia-knowledge-base.md`; the Nanot of Power references [nanotics.com](https://www.nanotics.com/).
- Sub-routes exist for each md tab (`/art-design/{slug}`, `/science-tech/{slug}`) — registered in `create_app()` in `pages.py`. Each prerenders with only its own tab's content baked in as a static Python string (`static_overrides` in `_build_dynamic_tab_specs`); all other tabs remain empty state vars and lazy-load on click. Tab triggers are `<a href>` links (via `as_child=True` on `rx.tabs.trigger` + `rx.el.a` in `_tab_trigger` in `components.py`) so crawlers can follow them. These sub-routes appear in `sitemap.xml` automatically via `SitemapPlugin`.

## Making a Reflex App Crawlable (Universal Guidelines)

These rules apply to any Reflex project, not just this site. Copy-paste to another project's AGENTS.md and adapt.

### Why Reflex is hard for crawlers by default

Reflex is a WebSocket-first framework. Without extra work:
- The initial HTML is an empty shell (`<div id="app"></div>`)
- All content loads only after a WebSocket connection to the backend
- Crawlers (including Googlebot) get empty pages or WebSocket errors

### The fix: prerendering + static initial state

**Step 1 — Enable prerendering** in `rxconfig.py`:
```python
os.environ.setdefault("REFLEX_SSR", "true")
```
This sets `prerender: true` in `react-router.config.js`, causing `reflex export` to generate a static HTML file for each registered route. No effect on the dev server.

**Step 2 — Pre-populate initial state with content crawlers need.**
Reflex pre-renders each page using the *default values* of `rx.State` vars — `on_load` handlers do NOT run at prerender time (they require WebSocket). Any content stored in state as empty strings will appear empty in the prerendered HTML.

Rule: **content that must be indexable must be in the state's default value, not loaded by `on_load`.**

For a tab layout where loading all tabs would bloat the bundle, pre-load only the first (default) tab:
```python
# Pre-load just the first tab at module level; others lazy-load on click.
_INITIAL: dict[str, str] = {slug: "" for slug in all_slugs}
for slug in all_slugs:
    content = load_tab_content(slug)
    if content:
        _INITIAL[slug] = content
        break  # first tab only

class MyContentState(rx.State):
    tab_content: dict[str, str] = _INITIAL  # first tab pre-loaded for SSR
```

For pages where content is fully static (biography, home), load it at module level and pass it directly to the component — no state needed.

**Step 3 — Register per-tab sub-routes** so each tab has its own crawlable URL.
Each sub-route bakes only its own tab's content as a plain Python string (not a state var) — no hydration mismatch, no extra bundle size:
```python
# In _build_dynamic_tab_specs: use static_overrides for the active slug
if static_overrides and slug in static_overrides:
    content_component = rx.markdown(static_overrides[slug], ...)  # Python string — no state
else:
    content_component = rx.markdown(state.tab_content[slug], ...)  # state var — lazy

# In create_app: register one sub-route per md tab
for slug in md_tab_slugs:
    static_content = load_tab_content(slug) or ""
    def page_fn(s=slug, c=static_content):
        return build_page_with_active(s, c)
    app.add_page(page_fn, route=f"/section/{slug}", on_load=[MobileTabRailState.collapse_expanded])
```

**Step 4 — Make tab triggers render as `<a href>` links.**
Radix `rx.tabs.trigger` renders as `<button>` by default — crawlers cannot follow buttons. Use `as_child=True` to make the trigger render as its child element:
```python
rx.tabs.trigger(
    rx.el.a(
        label,
        href=f"/section/{slug}",
        style={"text_decoration": "none", "color": "inherit", "display": "block"},
    ),
    value=slug,
    as_child=True,
    style=trigger_style,
)
```
Add `href: str | None = None` to `TabSpec`. Set it on md tabs in `_build_dynamic_tab_specs`. Special tabs (instagram embeds, link lists) don't need hrefs. Clicking the link triggers client-side React Router navigation to the prerendered sub-route — smooth, no full page reload.

**Step 5 — Add compile-time SEO assets.**
In `rxconfig.py`, add `rx.plugins.SitemapPlugin()` to `plugins=` — it auto-includes every registered Reflex route in `/sitemap.xml`. All sub-routes registered in `create_app()` appear automatically. Add a custom plugin to emit `/llms.txt` for AI crawlers.

**Step 6 — Add JSON-LD structured data** per page in `app.add_page(meta=[...])`. Use `rx.el.script(json.dumps(schema), type="application/ld+json")` as a meta entry. At minimum: `Person` schema on the home page, `CreativeWork` or `CollectionPage` on content pages.

### What crawlers get after all steps

| Crawler behaviour | Result |
|---|---|
| Reads raw HTML (no JS) | Full first-tab content + all page text from prerendered HTML |
| Follows links | Finds all tab sub-routes via `<a href>` in the page + sitemap.xml |
| Visits sub-route URL | Gets that tab's content prerendered in HTML, no WebSocket needed |
| Executes JS (Googlebot) | React hydrates, WebSocket may fail but content already visible — no blank flash |

### What NOT to do

- Don't put indexable content only in `on_load` handlers — they need WebSocket.
- Don't rely on `rx.tabs.trigger` for navigation without `as_child=True` — buttons are not followed.
- Don't load all tab content into the initial state if tabs are heavy — it bloats every page's bundle.
- Don't hide links with `display: none` — Google deprioritises hidden content.

---

## Production Deployment (Universal Guidelines)

### Architecture

```
Internet → Caddy (HTTPS, static files, compression)
               └── reverse_proxy /_event /_upload /ping /_health … → localhost:3011  (Reflex backend, WebSocket)
               └── file_server from .web/build/client/                               (prerendered HTML + assets)
```

The Node.js frontend server (port 3010) is **not needed in production** — Caddy serves the static files directly, which is faster and eliminates one process.

### Caddyfile

```
yourdomain.com {
    @backend path /ping /_event /_event/* /_upload /_upload/* /_health /_all_routes /auth-codespace /api /api/*
    reverse_proxy @backend localhost:3011

    root * /path/to/project/.web/build/client
    encode gzip zstd
    file_server
}
```

Caddy adds ETags, gzip/zstd compression, and proper cache headers automatically. No extra config needed.

### Commands

Add these to `pyproject.toml` `[project.scripts]` and implement in `src/<app>/start.py`:

```toml
[project.scripts]
start = "myapp.start:app"       # dev server
build = "myapp.start:build_app" # export static files
prod  = "myapp.start:prod_app"  # production backend only
```

```python
# build: export prerendered static HTML
export_utils.export(zipping=False, frontend=True, backend=False, env=constants.Env.PROD, ...)

# prod: run backend only (Caddy handles static)
from reflex.constants.base import RunningMode

_run(env=constants.Env.PROD, running_mode=RunningMode.BACKEND_ONLY)
```

Workflow on deploy:
1. Pull latest code
2. `uv run build` — regenerates `.web/build/client/`
3. Restart `uv run prod` (or its systemd service)

### Scaling

- **< ~100 concurrent WebSocket users**: one uvicorn worker, no Redis needed. Each user's session state is isolated in-memory per process.
- **> 100 concurrent users or multiple workers**: add `REDIS_URL=redis://localhost:6379` to `.env` and run `reflex run --env prod --backend-workers N`. Redis shares session state across workers.
- With prerendered static files served by Caddy, most users never touch the backend at all (only interactive state changes need WebSocket).

### Environment variables (`.env`)

| Variable | Purpose |
|---|---|
| `PORT` | Frontend port (default 3010; unused in prod when Caddy serves files directly) |
| `BACKEND_PORT` | Backend WebSocket port (default `PORT + 1`) |
| `HOST` | Bind address (default `0.0.0.0`) |
| `DEPLOY_URL` | Public HTTPS URL — used by Reflex to generate correct `wss://` WebSocket URL in the client bundle |
| `REDIS_URL` | Redis connection string — only needed with multiple backend workers |

`DEPLOY_URL` is critical: without it, the client bundle hard-codes `ws://localhost:PORT/_event`, which breaks in production.
