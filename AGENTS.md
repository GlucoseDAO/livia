# Livia Project Agent Guide

## Project Layout

- `livia/livia.py`: primary Reflex app module containing pages, UI components, and styles.
- `livia/__init__.py`: package init (do not hardcode package version here).
- `assets/`: static assets used by the app (for example, background images).
- `rxconfig.py`: Reflex runtime/config entrypoint.
- `pyproject.toml`: Python project metadata and dependency source of truth.
- `uv.lock`: dependency lockfile managed by `uv`.
- `.python-version`: interpreter pin used by local tooling.
- `.web/`: generated frontend/build output from Reflex toolchain; treat as generated artifacts unless a task explicitly requires editing them.
- `.states/`: local state artifacts.

## Major Design and Coding Principles

- Always write Python code with explicit type hints for function/method parameters and return values.
- Avoid unnecessary `try/except` blocks; prefer straightforward error propagation unless recovery is intentional and justified.
- Keep architecture and coding style consistent with existing patterns in `livia/livia.py` unless the task requires a refactor.
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
