import ipaddress
import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

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


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


class ViteDevServerPlugin(Plugin):
    """Plugin that patches vite.config.js with host, allowedHosts, and SSR fixes."""

    def post_compile(self, **context: object) -> None:
        vite_path = get_web_dir() / constants.ReactRouter.VITE_CONFIG_FILE
        if not vite_path.exists():
            return

        raw = vite_path.read_text(encoding="utf-8")
        # Strip any ANSI escape codes that may have been embedded by Reflex's
        # console output (they cause rolldown/Vite parse errors).
        content = _ANSI_RE.sub("", raw)
        new_content = content

        # --- server.host / server.allowedHosts ---
        rx_config = get_config()
        allowed_hosts = getattr(rx_config, "vite_allowed_hosts", None)
        host = getattr(rx_config, "vite_host", None)
        if host is not None and '"host"' not in new_content and "host:" not in new_content:
            new_content = new_content.replace(
                "port: process.env.PORT,",
                f'port: process.env.PORT,\n    host: "{host}",',
                1,
            )
        if allowed_hosts is True and "allowedHosts" not in new_content:
            new_content = new_content.replace(
                "port: process.env.PORT,",
                "port: process.env.PORT,\n    allowedHosts: true,",
                1,
            )

        # --- SSR / CJS-ESM fix for react-syntax-highlighter ---
        # react-syntax-highlighter (CJS) tries to require() refractor (ESM-only).
        # ssr.noExternal forces Vite/rolldown to bundle them together so it handles
        # the CJS→ESM conversion.  The resolve.alias is a belt-and-suspenders fallback
        # that redirects the CJS prism-light import directly to the ESM build, which
        # is needed when rolldown doesn't do CJS interop (Vite 7+).
        _CORRECT_NO_EXT = "noExternal: ['react-syntax-highlighter', 'refractor']"
        if _CORRECT_NO_EXT not in new_content:
            if "noExternal" in new_content:
                # Outdated entry from a previous deploy (e.g. missing refractor):
                # replace whatever noExternal value is there with the correct one.
                new_content = re.sub(
                    r"noExternal:\s*\[[^\]]*\]",
                    _CORRECT_NO_EXT,
                    new_content,
                    count=1,
                )
            else:
                closing = "}));"
                idx = new_content.rfind(closing)
                if idx != -1:
                    new_content = (
                        new_content[:idx]
                        + "  ssr: {\n"
                        f"    {_CORRECT_NO_EXT},\n"
                        "  },\n"
                        "  optimizeDeps: {\n"
                        "    include: ['react-syntax-highlighter'],\n"
                        "  },\n"
                        + closing
                    )

        # Belt-and-suspenders alias: redirect CJS prism-light to its ESM twin so
        # Node.js never hits the require()-of-ESM error even without bundling interop.
        _RSH_ALIAS = (
            "      {\n"
            "        find: 'react-syntax-highlighter/dist/cjs/prism-light',\n"
            "        replacement: fileURLToPath(new URL("
            "'./node_modules/react-syntax-highlighter/dist/esm/prism-light.js', import.meta.url)),\n"
            "      },\n"
        )
        if "prism-light" not in new_content:
            # Insert as the first entry of the resolve.alias array
            new_content = new_content.replace(
                "    alias: [\n",
                f"    alias: [\n{_RSH_ALIAS}",
                1,
            )

        if new_content != raw:
            vite_path.write_text(new_content, encoding="utf-8")


def _host_for_url_netloc(host: str) -> str:
    """Bracket IPv6 literals so they are valid in http://… URLs."""
    try:
        if isinstance(ipaddress.ip_address(host), ipaddress.IPv6Address):
            return f"[{host}]"
    except ValueError:
        pass
    return host


def _rewrite_listen_url(url: str, bind_host: str) -> str:
    """Replace hostname in a parsed listen URL; keep port and path from Vite."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    port = parsed.port
    host_lit = _host_for_url_netloc(bind_host)
    netloc = f"{host_lit}:{port}" if port is not None else host_lit
    return urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )


def _patch_reflex_console_bind_urls() -> None:
    """Reflex hardcodes localhost / 0.0.0.0 in startup banners; align with HOST / vite_host."""

    from reflex.utils import console
    from reflex.utils import exec as reflex_exec

    def notify_backend() -> None:
        cfg = get_config()
        h = _host_for_url_netloc(cfg.backend_host)
        console.print(
            f"Backend running at: [bold green]http://{h}:{cfg.backend_port}[/bold green]"
        )

    def notify_frontend(url: str, backend_present: bool) -> None:
        cfg = get_config()
        bind = getattr(cfg, "vite_host", None) or cfg.backend_host
        display_url = _rewrite_listen_url(url, bind)
        console.print(
            f"App running at: [bold green]{display_url.rstrip('/')}/[/bold green]"
            f"{' (Frontend-only mode)' if not backend_present else ''}"
        )

    reflex_exec.notify_backend = notify_backend
    reflex_exec.notify_frontend = notify_frontend


FRONTEND_PORT = int(os.getenv("PORT", "3010"))
BACKEND_PORT = int(os.getenv("BACKEND_PORT", str(FRONTEND_PORT + 1)))
_HOST: str = os.getenv("HOST", "0.0.0.0")
_DEPLOY_URL: str | None = os.getenv("DEPLOY_URL")

# Enable SSR/prerendering by default so bots and search engines get
# pre-rendered HTML. No effect in Vite dev server; kicks in on production
# builds. Set REFLEX_SSR=false in the environment to disable.
os.environ.setdefault("REFLEX_SSR", "true")

config = rx.Config(
    app_name="livia",
    frontend_port=FRONTEND_PORT,
    backend_port=BACKEND_PORT,
    backend_host=_HOST,
    **({} if _DEPLOY_URL is None else {"deploy_url": _DEPLOY_URL}),
    vite_allowed_hosts=True,
    vite_host=_HOST,
    plugins=[
        rx.plugins.SitemapPlugin(),
        LlmsTxtPlugin(),
        ViteDevServerPlugin(),
    ],
)

_patch_reflex_console_bind_urls()
