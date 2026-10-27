"""Serve prerendered pages at their sitemap URLs without a redirect.

The production server (``uv run serve``) serves the built frontend with
Starlette's ``StaticFiles(html=True)``. It answers ``/biography`` with a 307 to
``/biography/`` and builds that URL with the scheme it sees behind Caddy, which
is ``http``. Every sitemap URL then took two redirects before it loaded.

The build also writes each page as ``biography.html``, so ``/biography`` is
rewritten to that file and answered directly.
"""

from pathlib import Path

from reflex.config import get_config
from reflex.constants import Dirs
from reflex.utils.prerequisites import get_web_dir
from starlette.types import ASGIApp, Receive, Scope, Send


def _static_dir() -> Path:
    """Return the folder the production server serves the built frontend from."""
    return (get_web_dir() / Dirs.STATIC / get_config().frontend_path.strip("/")).resolve()


def serve_pages_without_redirect(app: ASGIApp) -> ASGIApp:
    """Wrap the Reflex ASGI app so ``/page`` serves ``page.html`` when the build has it."""
    static_dir = _static_dir()

    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] in ("GET", "HEAD"):
            path: str = scope["path"]
            if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
                page = (static_dir / f"{path.lstrip('/')}.html").resolve()
                if page.is_relative_to(static_dir) and page.is_file():
                    scope = {**scope, "path": f"{path}.html"}
        await app(scope, receive, send)

    return asgi
