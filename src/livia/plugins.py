"""Reflex plugins for the Livia app."""

from __future__ import annotations

import re
from pathlib import Path

from reflex import constants
from reflex.config import get_config
from reflex.plugins import Plugin
from reflex.utils.prerequisites import get_web_dir


class ViteDevServerPlugin(Plugin):
    """Plugin that patches vite.config.js with host and allowedHosts from rxconfig."""

    def post_compile(self, **context: object) -> None:
        """Patch vite.config.js after compile to add host and allowedHosts."""
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

        # Insert host and allowedHosts after "port: process.env.PORT,"
        insert_after = "port: process.env.PORT,"
        additions: list[str] = []
        if needs_host:
            additions.append(f'    host: "{host}",')
        if needs_allowed_hosts:
            additions.append("    allowedHosts: true,")

        pattern = re.compile(
            rf"({re.escape(insert_after)})",
            re.MULTILINE,
        )
        replacement = insert_after + "\n" + "\n".join(additions)
        new_content = pattern.sub(replacement, content, count=1)

        if new_content != content:
            vite_path.write_text(new_content)
