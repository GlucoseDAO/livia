"""Page definitions and content state for the Livia website."""

from typing import Literal

import reflex as rx
import yaml

from livia.constants import (
    ACCENT_MAP,
    AMBER,
    ASSETS_DIR,
    BACKGROUND,
    BIOGRAPHY_LINK_GROUPS,
    CONTENT_DIR,
    GREEN,
    MARKDOWN_COMPONENT_MAP,
    PIECES_MARKDOWN_COMPONENT_MAP,
    SANS_FONT,
    TEXT_LIGHT,
    TEXT_MUTED,
    TabSpec,
)
from livia.content import (
    _label_to_slug,
    heading_to_rail_title,
    load_content,
    load_folder_md_content,
    load_page_meta,
    load_pieces_tab_content,
    load_single_piece_tab_content,
    load_single_tab_md_content,
    parse_pieces_tab_entries,
    preprocess_markdown_for_state,
    scan_tab_slugs,
)
from livia.components import (
    BG_FUNC_MAP,
    MobileTabRailState,
    _build_special_tab,
    bottom_nav,
    fullscreen_bg,
    fullscreen_bg_dimmed,
    github_sidebar,
    instagram_embed_panel,
    instagram_sidebar,
    link_list_grouped,
    markdown_panel,
    page_content,
    panel,
    section_heading,
    sidebar_tabs,
)

_LIVIA_NAV_JS = (ASSETS_DIR / "livia_nav.js").read_text(encoding="utf-8")

# Empty-string sentinel dicts keyed by all known md slugs — avoids KeyErrors in
# state-var subscript expressions before content is loaded on demand.
_ART_DESIGN_EMPTY: dict[str, str] = {
    slug: ""
    for _, _, slug, st in scan_tab_slugs("art-design")
    if st.startswith("md:")
}
_SCIENCE_TECH_EMPTY: dict[str, str] = {
    slug: ""
    for _, _, slug, st in scan_tab_slugs("science-tech")
    if st.startswith("md:")
}
_intro_pieces, _entries_pieces = parse_pieces_tab_entries()
_PIECES_EMPTY: dict[str, str] = {
    **({} if _intro_pieces is None else {"overview": ""}),
    **{e.tab_key: "" for e in _entries_pieces},
}


# ---------------------------------------------------------------------------
# Content state classes — lazy: only the active tab's markdown is fetched
# ---------------------------------------------------------------------------

class ArtDesignContentState(rx.State):
    """Markdown content for Art & Design tabs. Only the selected tab is loaded from disk."""
    tab_content: dict[str, str] = _ART_DESIGN_EMPTY

    def load_content(self) -> None:
        """On page load: reset to empty then load only the first (default) tab."""
        self.tab_content = _ART_DESIGN_EMPTY.copy()
        for _, _, slug, st in scan_tab_slugs("art-design"):
            if st.startswith("md:"):
                content = load_single_tab_md_content("art-design", slug)
                if content is not None:
                    self.tab_content = {**self.tab_content, slug: content}
                break

    def load_tab(self, slug: str) -> None:
        """On tab select: load that tab's markdown on demand (no-op if already cached)."""
        if not self.tab_content.get(slug):
            content = load_single_tab_md_content("art-design", slug)
            if content is not None:
                self.tab_content = {**self.tab_content, slug: content}


class ScienceTechContentState(rx.State):
    """Markdown content for Science & Tech tabs. Only the selected tab is loaded from disk."""
    tab_content: dict[str, str] = _SCIENCE_TECH_EMPTY

    def load_content(self) -> None:
        """On page load: reset to empty then load only the first (default) tab."""
        self.tab_content = _SCIENCE_TECH_EMPTY.copy()
        for _, _, slug, st in scan_tab_slugs("science-tech"):
            if st.startswith("md:"):
                content = load_single_tab_md_content("science-tech", slug)
                if content is not None:
                    self.tab_content = {**self.tab_content, slug: content}
                break

    def load_tab(self, slug: str) -> None:
        """On tab select: load that tab's markdown on demand (no-op if already cached)."""
        if not self.tab_content.get(slug):
            content = load_single_tab_md_content("science-tech", slug)
            if content is not None:
                self.tab_content = {**self.tab_content, slug: content}


class PiecesContentState(rx.State):
    """Per-tab markdown for Pieces. Only the selected tab is loaded from disk."""
    tab_content: dict[str, str] = _PIECES_EMPTY

    def load_content(self) -> None:
        """On page load: reset to empty then load only the first (default) tab."""
        self.tab_content = _PIECES_EMPTY.copy()
        intro, entries = parse_pieces_tab_entries()
        if intro is not None:
            self.tab_content = {**self.tab_content, "overview": preprocess_markdown_for_state(intro)}
        elif entries:
            first_key = entries[0].tab_key
            content = load_single_piece_tab_content(first_key)
            if content is not None:
                self.tab_content = {**self.tab_content, first_key: content}

    def load_tab(self, tab_key: str) -> None:
        """On tab select: load that tab's markdown on demand (no-op if already cached)."""
        if not self.tab_content.get(tab_key):
            content = load_single_piece_tab_content(tab_key)
            if content is not None:
                self.tab_content = {**self.tab_content, tab_key: content}


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
                        use_unwrap_images=False,
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


def _build_pieces_tab_specs() -> tuple[TabSpec, ...]:
    """Sidebar tabs for Pieces: optional overview plus one tab per gallery with images."""
    intro, entries = parse_pieces_tab_entries()
    tabs: list[TabSpec] = []
    if intro is not None:
        tabs.append(
            TabSpec(
                label="Overview",
                value="overview",
                content=panel(
                    rx.markdown(
                        PiecesContentState.tab_content["overview"],
                        component_map=PIECES_MARKDOWN_COMPONENT_MAP,
                        use_unwrap_images=False,
                    ),
                ),
            ),
        )
    for e in entries:
        rail = heading_to_rail_title(e.raw_heading)
        stack_children: list[rx.Component] = [
            rx.heading(
                rail,
                font_family=SANS_FONT,
                font_weight="700",
                color=TEXT_LIGHT,
                font_size=["1.85rem", "2.25rem", "2.75rem"],
                line_height="1.15",
                letter_spacing="0.02em",
                margin_bottom="0.85rem",
                width="100%",
                class_name="livia-pieces-title",
            ),
        ]
        if e.date_hint:
            stack_children.append(
                rx.text(
                    e.date_hint,
                    color=TEXT_MUTED,
                    font_size="0.95rem",
                    font_style="italic",
                    margin_bottom="0.75rem",
                    class_name="livia-pieces-date",
                ),
            )
        stack_children.append(
            rx.markdown(
                PiecesContentState.tab_content[e.tab_key],
                component_map=PIECES_MARKDOWN_COMPONENT_MAP,
                use_unwrap_images=False,
            ),
        )
        tabs.append(
            TabSpec(
                label=rail,
                value=e.tab_key,
                content=panel(
                    rx.vstack(
                        *stack_children,
                        spacing="3",
                        width="100%",
                        align_items="stretch",
                    ),
                ),
            ),
        )
    return tuple(tabs)


# ---------------------------------------------------------------------------
# Page functions
# ---------------------------------------------------------------------------

def home_page() -> rx.Component:
    """Homepage: fullscreen portrait + bottom navigation."""
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
        instagram_sidebar(),
        github_sidebar(),
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
            link_list_grouped("Links", BIOGRAPHY_LINK_GROUPS, GREEN),
        ),
        bottom_nav(),
        min_height="100vh",
        font_family=SANS_FONT,
    )


def pieces_page() -> rx.Component:
    """Object-centric list of works: one sidebar tab per piece (like Art & Design)."""
    tabs = _build_pieces_tab_specs()
    default_value = tabs[0].value if tabs else "overview"
    body = (
        rx.box(
            sidebar_tabs(
                tabs=tabs,
                accent=AMBER,
                sidebar_side="right",
                default_value=default_value,
                collapsed_label="WORKS",
                rail_variant="pieces",
                on_tab_select=PiecesContentState.load_tab,
            ),
            class_name="livia-pieces",
            width="100%",
        )
        if tabs
        else panel(rx.text("No pieces with photos are available yet.", color=TEXT_LIGHT))
    )
    return rx.box(
        BG_FUNC_MAP["yellow"](),
        page_content(
            section_heading("Pieces", AMBER),
            body,
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
            sidebar_tabs(
                tabs=tabs,
                accent=accent,
                sidebar_side=sidebar_side,
                default_value=default_value,
                on_tab_select=ArtDesignContentState.load_tab,
            ),
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
            sidebar_tabs(
                tabs=tabs,
                accent=accent,
                sidebar_side=sidebar_side,
                default_value=default_value,
                on_tab_select=ScienceTechContentState.load_tab,
            ),
        ),
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
                content="width=device-width, initial-scale=1",
            ),
            rx.script(_LIVIA_NAV_JS),
        ],
    )
    application.add_page(home_page, route="/", title="Livia Zaharia")
    application.add_page(biography_page, route="/biography", title="Biography | Livia Zaharia")
    application.add_page(
        pieces_page,
        route="/pieces",
        title="Pieces | Livia Zaharia",
        on_load=[PiecesContentState.load_content, MobileTabRailState.collapse_expanded],
    )
    application.add_page(
        art_design_page,
        route="/art-design",
        title="Art & Design | Livia Zaharia",
        on_load=[ArtDesignContentState.load_content, MobileTabRailState.collapse_expanded],
    )
    application.add_page(
        science_tech_page,
        route="/science-tech",
        title="Science & Tech | Livia Zaharia",
        on_load=[ScienceTechContentState.load_content, MobileTabRailState.collapse_expanded],
    )
    return application
