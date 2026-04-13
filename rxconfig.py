import os
import re

import reflex as rx
from dotenv import load_dotenv
from reflex import constants
from reflex.config import get_config
from reflex.plugins import Plugin
from reflex.utils.prerequisites import get_web_dir

# Load .env from the project root before reading any env vars.
load_dotenv()


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


FRONTEND_PORT = int(os.getenv("PORT", "3010"))
BACKEND_PORT = int(os.getenv("BACKEND_PORT", str(FRONTEND_PORT + 1)))
_DEPLOY_URL: str | None = os.getenv("DEPLOY_URL")

# Enable SSR/prerendering by default so bots and search engines get
# pre-rendered HTML. No effect in Vite dev server; kicks in on production
# builds. Set REFLEX_SSR=false in the environment to disable.
os.environ.setdefault("REFLEX_SSR", "true")

config = rx.Config(
    app_name="livia",
    frontend_port=FRONTEND_PORT,
    backend_port=BACKEND_PORT,
    **({} if _DEPLOY_URL is None else {"deploy_url": _DEPLOY_URL}),
    vite_allowed_hosts=True,
    vite_host="0.0.0.0",
    plugins=[
        rx.plugins.SitemapPlugin(),
        ViteDevServerPlugin(),
    ],
)
