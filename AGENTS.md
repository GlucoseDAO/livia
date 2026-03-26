# Livia Project Agent Guide

## Project Layout (src layout)

- `src/livia/livia.py`: primary Reflex app module containing pages, UI components, and styles.
- `src/livia/__init__.py`: package init (do not hardcode package version here).
- `src/livia/plugins.py`: Reflex plugins (Vite dev-server patching).
- `src/livia/start.py`: CLI entry point (`uv run start`); uses `typer`.
- `assets/`: static assets used by the app (for example, background images).
  - `assets/livia.jpg`: full-screen portrait used as the site background.
  - `assets/RJW2025/`: Romanian Jewelry Week 2025 exhibition photographs (12 images).
  - `assets/bubbles.css`: CSS for the floating navigation bubble overlay (keyframes, glass-morphism, tooltips, preview cards, responsive breakpoints).
  - `assets/bubbles.js`: vanilla JS for bubble interactions (periodic shiver, click expand/collapse, click-outside dismiss, resize repositioning, touch support).
- `content/`: markdown files with page text, loaded by `load_content()`.
- `docs/`: reference documentation not rendered by the app.
  - `docs/livia-zaharia-knowledge-base.md`: comprehensive artist knowledge base covering identity, practice, collections catalogue, exhibition history, and ecosystem connections.
- `rxconfig.py`: Reflex runtime/config entrypoint.
- `pyproject.toml`: Python project metadata and dependency source of truth.
- `uv.lock`: dependency lockfile managed by `uv`.
- `.python-version`: interpreter pin used by local tooling.
- `.web/`: generated frontend/build output from Reflex toolchain; treat as generated artifacts unless a task explicitly requires editing them. Note: Reflex copies assets to `.web/public/` and stylesheets to `.web/styles/` at compile time; during dev, CSS/JS asset changes may need manual copy to `.web/styles/` and `.web/public/` if hot-reload does not pick them up.
- `.states/`: local state artifacts.

## Major Design and Coding Principles

- Always write Python code with explicit type hints for function/method parameters and return values.
- Avoid unnecessary `try/except` blocks; prefer straightforward error propagation unless recovery is intentional and justified.
- Keep architecture and coding style consistent with existing patterns in `src/livia/livia.py` unless the task requires a refactor.
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

## Learned Workspace Facts

- `rxconfig.py` must not import from the `src/livia/` package because Reflex's `get_config()` strips `sys.path` during early init; any plugins must be inlined directly in `rxconfig.py`.
- The user-visible port is controlled by `frontend_port` in Reflex config, not `backend_port`; default is 3010 with backend at 3011.
- Git LFS is configured (`.gitattributes`) to track `*.jpg`, `*.jpeg`, `*.png`, `*.gif`, `*.webp`.
- During dev, Reflex hot-reload may not pick up changes to CSS/JS files in `assets/`; manually copy to `.web/public/` and `.web/styles/` if needed.
- The `src/livia/plugins.py` file was removed; `ViteDevServerPlugin` is now inlined in `rxconfig.py` to avoid the import isolation issue.
