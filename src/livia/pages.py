"""Page definitions and content state for the Livia website."""

from typing import Literal

import reflex as rx
import yaml

from livia.constants import (
    ACCENT_MAP,
    AMBER,
    BACKGROUND,
    BIOGRAPHY_LINKS,
    CONTENT_DIR,
    GREEN,
    MARKDOWN_COMPONENT_MAP,
    SANS_FONT,
    TEXT_LIGHT,
    TabSpec,
)
from livia.content import (
    _label_to_slug,
    load_folder_md_content,
    load_page_meta,
    scan_tab_slugs,
)
from livia.components import (
    BG_FUNC_MAP,
    _build_special_tab,
    bottom_nav,
    bubble_overlay,
    fullscreen_bg,
    fullscreen_bg_dimmed,
    github_sidebar,
    instagram_embed_panel,
    instagram_sidebar,
    link_list,
    markdown_panel,
    screen_aware_sidebar_opener,
    page_content,
    panel,
    section_heading,
    sidebar_tabs,
)


# ---------------------------------------------------------------------------
# Content state classes — re-read markdown from disk on every page load
# ---------------------------------------------------------------------------

class ArtDesignContentState(rx.State):
    """Markdown content for each Art & Design tab, re-read from disk on page load."""
    tab_content: dict[str, str] = load_folder_md_content("art-design")

    def load_content(self) -> None:
        self.tab_content = load_folder_md_content("art-design")


class ScienceTechContentState(rx.State):
    """Markdown content for each Science & Tech tab, re-read from disk on page load."""
    tab_content: dict[str, str] = load_folder_md_content("science-tech")

    def load_content(self) -> None:
        self.tab_content = load_folder_md_content("science-tech")


# ---------------------------------------------------------------------------
# Tab building (static structure, dynamic content)
# ---------------------------------------------------------------------------

def _build_dynamic_tab_specs(
    folder: str,
    content_state: type[ArtDesignContentState] | type[ScienceTechContentState],
) -> list[TabSpec]:
    """Build TabSpecs where markdown tabs render content from a state dict.

    Tab structure (labels, slugs) is discovered at compile time.
    Markdown content comes from the state var and is re-read from disk on each page load.
    Special tabs (instagram_embed, link_list) are still built statically.
    """
    entries = scan_tab_slugs(folder)
    folder_path = CONTENT_DIR / folder
    tabs: list[TabSpec] = []

    for _order, label, slug, source_type in entries:
        if source_type.startswith("md:"):
            tabs.append(TabSpec(
                label=label,
                value=slug,
                content=panel(
                    rx.markdown(
                        content_state.tab_content[slug],
                        component_map=MARKDOWN_COMPONENT_MAP,
                    ),
                ),
            ))
        elif source_type == "instagram_embed":
            tabs.append(TabSpec(label=label, value=slug, content=instagram_embed_panel()))
        elif source_type == "link_list":
            yaml_file = next(
                (f for f in folder_path.glob("_*.yaml")
                 if f.stem != "_meta" and _label_to_slug(
                     (yaml.safe_load(f.read_text()) or {}).get("label", "")
                 ) == slug),
                None,
            )
            if yaml_file:
                spec = yaml.safe_load(yaml_file.read_text()) or {}
                tabs.append(TabSpec(label=label, value=slug, content=_build_special_tab(spec)))
            else:
                tabs.append(TabSpec(label=label, value=slug, content=panel(rx.text("Links", color=TEXT_LIGHT))))
        else:
            tabs.append(TabSpec(
                label=label,
                value=slug,
                content=panel(rx.text(f"Unknown type: {source_type}", color=TEXT_LIGHT)),
            ))

    return tabs


# ---------------------------------------------------------------------------
# Page functions
# ---------------------------------------------------------------------------

def home_page() -> rx.Component:
    """Homepage: fullscreen portrait + name overlay + floating bubbles + bottom nav."""
    return rx.box(
        fullscreen_bg(),
        rx.box(
            position="fixed",
            inset="0",
            background=(
                "linear-gradient(180deg, transparent 40%, rgba(10, 8, 6, 0.65) 85%, "
                "rgba(10, 8, 6, 0.85) 100%)"
            ),
            z_index="2",
        ),
        bubble_overlay(),
        instagram_sidebar(),
        github_sidebar(),
        screen_aware_sidebar_opener(),
        bottom_nav(),
        min_height="100vh",
        font_family=SANS_FONT,
    )


def biography_page() -> rx.Component:
    return rx.box(
        fullscreen_bg_dimmed(),
        page_content(
            section_heading("Biography", GREEN),
            markdown_panel("biography"),
            link_list("Links", BIOGRAPHY_LINKS, GREEN),
        ),
        bottom_nav(),
        min_height="100vh",
        font_family=SANS_FONT,
    )


def art_design_page() -> rx.Component:
    meta = load_page_meta("art-design")
    heading = meta.get("heading", "Art & Design")
    accent_key = meta.get("accent", "amber")
    accent = ACCENT_MAP.get(accent_key, AMBER)
    bg_key = meta.get("background", "default")
    bg_func = BG_FUNC_MAP.get(bg_key, fullscreen_bg)
    sidebar_side: Literal["left", "right"] = meta.get("sidebar_side", "right")  # type: ignore[assignment]

    tabs = tuple(_build_dynamic_tab_specs("art-design", ArtDesignContentState))
    default_value = tabs[0].value if tabs else "overview"

    return rx.box(
        bg_func(),
        page_content(
            section_heading(heading, accent),
            sidebar_tabs(tabs=tabs, accent=accent, sidebar_side=sidebar_side, default_value=default_value),
        ),
        bottom_nav(),
        min_height="100vh",
        font_family=SANS_FONT,
    )


def science_tech_page() -> rx.Component:
    meta = load_page_meta("science-tech")
    heading = meta.get("heading", "Science & Tech")
    accent_key = meta.get("accent", "green")
    accent = ACCENT_MAP.get(accent_key, GREEN)
    bg_key = meta.get("background", "default")
    bg_func = BG_FUNC_MAP.get(bg_key, fullscreen_bg)
    sidebar_side: Literal["left", "right"] = meta.get("sidebar_side", "left")  # type: ignore[assignment]

    tabs = tuple(_build_dynamic_tab_specs("science-tech", ScienceTechContentState))
    default_value = tabs[0].value if tabs else "overview"

    return rx.box(
        bg_func(),
        page_content(
            section_heading(heading, accent),
            sidebar_tabs(tabs=tabs, accent=accent, sidebar_side=sidebar_side, default_value=default_value),
        ),
        github_sidebar(),
        screen_aware_sidebar_opener(),
        bottom_nav(),
        min_height="100vh",
        font_family=SANS_FONT,
    )


# ---------------------------------------------------------------------------
# App registration
# ---------------------------------------------------------------------------

def create_app() -> rx.App:
    """Create and configure the Reflex app with all pages."""
    application = rx.App(
        stylesheets=[
            "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700&display=swap",
            "/bubbles.css",
        ],
        style={
            "background": BACKGROUND,
            "color": TEXT_LIGHT,
            "font_family": SANS_FONT,
        },
        head_components=[
            rx.el.meta(
                name="viewport",
                content="width=1280",
            ),
            rx.script(
                """
                (function() {
                    if (window.screen && window.screen.width < 1024) {
                        window.__livia_narrow_device = true;
                        var style = document.createElement('style');
                        style.textContent =
                            '.livia-bottom-nav a { font-size: 2.8rem !important; }' +
                            '.livia-bottom-nav { padding: 1.2rem 2rem !important; }' +
                            '.livia-bottom-nav .rt-HStack { gap: 1.2rem !important; }' +
                            '[role="tablist"] button { font-size: 3rem !important; padding: 0.5rem 0.8rem !important; }';
                        document.head.appendChild(style);
                    }

                    function highlightActiveNav() {
                        var path = window.location.pathname;
                        if (path === '' || path === '/index') path = '/';
                        var links = document.querySelectorAll('.livia-bottom-nav a[data-href]');
                        links.forEach(function(a) {
                            var href = a.getAttribute('data-href');
                            var isActive = (href === path);
                            if (isActive) {
                                a.style.color = '#f5f0e8';
                                a.style.fontWeight = '700';
                                var bar = a.querySelector('.livia-nav-indicator');
                                if (bar) bar.style.width = '100%';
                            }
                        });
                    }

                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', highlightActiveNav);
                    } else {
                        highlightActiveNav();
                    }
                    // Re-run after a short delay to catch React hydration
                    setTimeout(highlightActiveNav, 500);
                    setTimeout(highlightActiveNav, 1500);
                })();
                """
            ),
        ],
    )
    application.add_page(home_page, route="/", title="Livia Zaharia")
    application.add_page(biography_page, route="/biography", title="Biography | Livia Zaharia")
    application.add_page(
        art_design_page,
        route="/art-design",
        title="Art & Design | Livia Zaharia",
        on_load=ArtDesignContentState.load_content,
    )
    application.add_page(
        science_tech_page,
        route="/science-tech",
        title="Science & Tech | Livia Zaharia",
        on_load=ScienceTechContentState.load_content,
    )
    return application
