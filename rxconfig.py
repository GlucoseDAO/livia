import os
import re
from pathlib import Path

import reflex as rx
from reflex import constants
from reflex.config import get_config
from reflex.plugins import Plugin
from reflex.utils.prerequisites import get_web_dir


class ViteDevServerPlugin(Plugin):
    """Plugin that patches vite.config.js with host and allowedHosts from rxconfig."""

    def post_compile(self, **context: object) -> None:
        config = get_config()
        allowed_hosts = getattr(config, "vite_allowed_hosts", None)
        host = getattr(config, "vite_host", None)
        if allowed_hosts is None and host is None:
            return

        vite_path = get_web_dir() / constants.ReactRouter.VITE_CONFIG_FILE
        if not vite_path.exists():
            return

        content = vite_path.read_text()
        needs_host = host is not None and "host:" not in content
        needs_allowed_hosts = allowed_hosts is True and "allowedHosts" not in content
        if not needs_host and not needs_allowed_hosts:
            return

        insert_after = "port: process.env.PORT,"
        additions: list[str] = []
        if needs_host:
            additions.append(f'    host: "{host}",')
        if needs_allowed_hosts:
            additions.append("    allowedHosts: true,")

        pattern = re.compile(rf"({re.escape(insert_after)})", re.MULTILINE)
        replacement = insert_after + "\n" + "\n".join(additions)
        new_content = pattern.sub(replacement, content, count=1)

        if new_content != content:
            vite_path.write_text(new_content)


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
        ViteDevServerPlugin(),
    ],
)
