import reflex as rx

import livia.plugins
import os
from pathlib import Path


def _port_from_dotenv(dotenv_path: Path) -> str | None:
    if not dotenv_path.exists():
        return None
    for raw_line in dotenv_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != "PORT":
            continue
        return value.strip().strip("\"'")
    return None


def _resolve_frontend_port() -> int:
    raw_value = os.getenv("PORT")
    if raw_value is None:
        raw_value = _port_from_dotenv(Path(__file__).parent / ".env")
    if not raw_value:
        return 3010
    try:
        return int(raw_value)
    except ValueError:
        return 3010


FRONTEND_PORT = _resolve_frontend_port()
BACKEND_PORT = int(os.getenv("BACKEND_PORT", str(FRONTEND_PORT + 1)))

config = rx.Config(
    app_name="livia",
    frontend_port=FRONTEND_PORT,
    backend_port=BACKEND_PORT,
    vite_allowed_hosts=True,
    vite_host="0.0.0.0",
    plugins=[
        rx.plugins.SitemapPlugin(),
        livia.plugins.ViteDevServerPlugin(),
    ],
)
