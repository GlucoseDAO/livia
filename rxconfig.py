import os
import re
from pathlib import Path

import reflex as rx
import yaml
from dotenv import load_dotenv
from reflex import constants
from reflex.config import get_config
from reflex.plugins import Plugin
from reflex.utils.prerequisites import get_web_dir

# Load .env from the project root before reading any env vars.
load_dotenv()

_ROOT = Path(__file__).parent
_CONTENT_DIR = _ROOT / "content"
_ASSETS_DIR = _ROOT / "assets"

_TAB_PREFIX_RE = re.compile(r"^(\d+)_(.*)")
_REF_FM_RE = re.compile(r"^\s*---\s*\n(.*?)\n---\s*$", re.DOTALL)


def _read_md(path: Path) -> str:
    """Read a markdown file, following a single-level ref: frontmatter pointer."""
    raw = path.read_text(encoding="utf-8")
    m = _REF_FM_RE.fullmatch(raw.strip())
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        ref = meta.get("ref")
        if ref:
            target = _CONTENT_DIR / ref
            if target.exists():
                return target.read_text(encoding="utf-8")
    return raw


def _tab_order(path: Path) -> int:
    m = _TAB_PREFIX_RE.match(path.stem)
    return int(m.group(1)) if m else 999


def _tab_label(path: Path) -> str:
    m = _TAB_PREFIX_RE.match(path.stem)
    return m.group(2) if m else path.stem


def _build_llms_txt() -> str:
    """Build full llms.txt content from the content directory."""
    lines: list[str] = []

    lines.append("# Livia Zaharia\n\n")
    lines.append(
        "> Romanian architect, parametric jewellery artist, and citizen scientist.\n"
        "> Website: https://livia.glucosedao.org\n"
        "> Instagram: https://www.instagram.com/paral_design/\n"
        "> GitHub (GlucoseDAO): https://github.com/GlucoseDAO/\n\n"
    )

    # Biography
    bio = _CONTENT_DIR / "biography.md"
    if bio.exists():
        lines.append("## Biography\n\n")
        lines.append(_read_md(bio))
        lines.append("\n\n")

    # Tabbed folders
    for folder, heading in [("art-design", "Art & Design"), ("science-tech", "Science & Tech")]:
        folder_path = _CONTENT_DIR / folder
        if not folder_path.is_dir():
            continue
        lines.append(f"## {heading}\n\n")
        md_files = sorted(
            [f for f in folder_path.glob("*.md") if not f.name.startswith("_")],
            key=_tab_order,
        )
        for md_file in md_files:
            label = _tab_label(md_file)
            lines.append(f"### {label}\n\n")
            lines.append(_read_md(md_file))
            lines.append("\n\n")

    # Pieces — split pieces.md on ## headings
    pieces_file = _CONTENT_DIR / "pieces.md"
    if pieces_file.exists():
        lines.append("## Pieces\n\n")
        raw = pieces_file.read_text(encoding="utf-8")
        lines.append(raw)
        lines.append("\n\n")

    return "".join(lines)


class LlmsTxtPlugin(Plugin):
    """Generate /llms.txt at compile time so bots can read all site content without JS."""

    def post_compile(self, **context: object) -> None:
        txt = _build_llms_txt()
        # Write to assets/ so it's version-controlled and picked up on next compile
        (_ASSETS_DIR / "llms.txt").write_text(txt, encoding="utf-8")
        # Also write directly to .web/public/ so it's served immediately
        web_public = get_web_dir() / "public"
        if web_public.exists():
            (web_public / "llms.txt").write_text(txt, encoding="utf-8")


class ViteDevServerPlugin(Plugin):
    """Plugin that patches vite.config.js with host, allowedHosts, and SSR fixes."""

    def post_compile(self, **context: object) -> None:
        vite_path = get_web_dir() / constants.ReactRouter.VITE_CONFIG_FILE
        if not vite_path.exists():
            return

        content = vite_path.read_text()
        new_content = content

        # --- server.host / server.allowedHosts ---
        rx_config = get_config()
        allowed_hosts = getattr(rx_config, "vite_allowed_hosts", None)
        host = getattr(rx_config, "vite_host", None)
        if host is not None and "host:" not in new_content:
            new_content = re.sub(
                r"(port: process\.env\.PORT,)",
                rf"\1\n    host: \"{host}\",",
                new_content,
                count=1,
            )
        if allowed_hosts is True and "allowedHosts" not in new_content:
            new_content = re.sub(
                r"(port: process\.env\.PORT,)",
                r"\1\n    allowedHosts: true,",
                new_content,
                count=1,
            )

        # --- SSR / CJS-ESM fix for react-syntax-highlighter ---
        # react-syntax-highlighter (CJS) tries to require() refractor (ESM-only).
        # Listing it in ssr.noExternal forces Vite to bundle it for SSR, handling
        # the conversion internally instead of letting Node.js hit the require() error.
        if "noExternal" not in new_content:
            new_content = new_content.rstrip()
            # Insert before the closing })); of defineConfig
            new_content = new_content[: new_content.rfind("}));")] + (
                "  ssr: {\n"
                "    noExternal: ['react-syntax-highlighter'],\n"
                "  },\n"
                "  optimizeDeps: {\n"
                "    include: ['react-syntax-highlighter'],\n"
                "  },\n"
                "}));"
            )

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
        LlmsTxtPlugin(),
        ViteDevServerPlugin(),
    ],
)
