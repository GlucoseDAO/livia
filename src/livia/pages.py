"""Page definitions and content state for the Livia website."""

import json
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
    load_folder_raw_md,
    load_page_meta,
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

_BIOGRAPHY_TEXT = load_content("biography")
_HOME_TEXT = load_content("home")

# Rich tab content loaded once at module level for JSON-LD and the content-map page.
_ART_DESIGN_RAW: list[tuple[str, str, str]] = load_folder_raw_md("art-design")   # (slug, label, raw)
_SCI_TECH_RAW: list[tuple[str, str, str]] = load_folder_raw_md("science-tech")
_PIECES_INTRO, _PIECES_ENTRIES = parse_pieces_tab_entries()


def _json_ld_script(schema: dict) -> rx.Component:
    """Return a <script type="application/ld+json"> component for structured data."""
    return rx.el.script(
        json.dumps(schema, ensure_ascii=False, indent=2),
        type="application/ld+json",
    )


_PERSON_SCHEMA: dict = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "Livia Zaharia",
    "alternateName": ["Parametric Livia", "Paral Design"],
    "description": (
        "Romanian architect and parametric jewellery artist. Works at the intersection "
        "of generative art, speculative design for health/longevity, and experimental "
        "contemporary jewellery. Founder of GlucoseDAO."
    ),
    "url": "https://livia.glucosedao.org",
    "sameAs": [
        "https://www.instagram.com/paral_design/",
        "https://www.facebook.com/byLiviaZaharia/",
        "https://www.linkedin.com/in/livia-zaharia-4b1425a0",
        "https://github.com/GlucoseDAO/",
    ],
    "knowsAbout": [
        "parametric design",
        "computational architecture",
        "generative art",
        "jewellery making",
        "digital health",
        "longevity research",
        "glucose prediction",
        "machine learning",
        "Grasshopper",
        "COMPAS",
    ],
    "affiliation": [
        {"@type": "Organization", "name": "GlucoseDAO", "url": "https://glucosedao.org"},
        {"@type": "Organization", "name": "Longevity Genie", "url": "https://longevity-genie.github.io"},
        {"@type": "Organization", "name": "HEALES"},
        {"@type": "Organization", "name": "Universitätsmedizin Rostock (IBIMA)"},
    ],
}

def _preload_first_tab(folder: str) -> dict[str, str]:
    """Build initial state with only the first (default) tab pre-loaded for SSR.

    Crawlers see the default tab content in pre-rendered HTML; all other tabs
    remain empty and are lazy-loaded on click — preserving the original perf profile.
    """
    empty = {
        slug: ""
        for _, _, slug, st in scan_tab_slugs(folder)
        if st.startswith("md:")
    }
    for _, _, slug, st in scan_tab_slugs(folder):
        if st.startswith("md:"):
            content = load_single_tab_md_content(folder, slug)
            if content is not None:
                return {**empty, slug: content}
            break
    return empty


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

# First tab pre-loaded for SSR/prerendering; rest stay lazy.
_ART_DESIGN_INITIAL: dict[str, str] = _preload_first_tab("art-design")
_SCIENCE_TECH_INITIAL: dict[str, str] = _preload_first_tab("science-tech")
_PIECES_INITIAL: dict[str, str] = {
    **_PIECES_EMPTY,
    **({} if _intro_pieces is None else {
        "overview": load_single_piece_tab_content("overview") or "",
    }),
}


# ---------------------------------------------------------------------------
# Content state classes — initial state pre-loaded for SSR; on_load is a no-op
# when content is already present (crawlers never need WebSocket for content).
# ---------------------------------------------------------------------------

class ArtDesignContentState(rx.State):
    """Markdown content for Art & Design tabs, pre-loaded for SSR/prerendering."""
    tab_content: dict[str, str] = _ART_DESIGN_INITIAL

    def load_content(self) -> None:
        """Ensure the first tab has content (no-op when already pre-loaded via SSR)."""
        for _, _, slug, st in scan_tab_slugs("art-design"):
            if st.startswith("md:") and not self.tab_content.get(slug):
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
    """Markdown content for Science & Tech tabs, pre-loaded for SSR/prerendering."""
    tab_content: dict[str, str] = _SCIENCE_TECH_INITIAL

    def load_content(self) -> None:
        """Ensure the first tab has content (no-op when already pre-loaded via SSR)."""
        for _, _, slug, st in scan_tab_slugs("science-tech"):
            if st.startswith("md:") and not self.tab_content.get(slug):
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
    """Per-tab markdown for Pieces, pre-loaded for SSR/prerendering."""
    tab_content: dict[str, str] = _PIECES_INITIAL

    def load_content(self) -> None:
        """Ensure overview/first tab has content (no-op when already pre-loaded via SSR)."""
        if not self.tab_content.get("overview"):
            intro, entries = parse_pieces_tab_entries()
            if intro is not None:
                self.tab_content = {**self.tab_content, "overview": preprocess_markdown_for_state(intro)}
            elif entries:
                first_key = entries[0].tab_key
                if not self.tab_content.get(first_key):
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
    static_overrides: dict[str, str] | None = None,
) -> list[TabSpec]:
    """Build TabSpecs where markdown tabs render content from a state dict.

    Tab structure (labels, slugs) is discovered at compile time.
    Markdown content comes from the state var and is re-read from disk on each page load.
    Special tabs (instagram_embed, link_list) are still built statically.

    When static_overrides is provided, those slugs use a baked-in Python string instead of
    the state var — no hydration mismatch, and no extra data loaded for the other tabs.
    """
    entries = scan_tab_slugs(folder)
    folder_path = CONTENT_DIR / folder
    tabs: list[TabSpec] = []

    for _order, label, slug, source_type in entries:
        if source_type.startswith("md:"):
            if static_overrides and slug in static_overrides:
                md_content: rx.Component = rx.markdown(
                    static_overrides[slug],
                    component_map=MARKDOWN_COMPONENT_MAP,
                    use_unwrap_images=False,
                )
            else:
                md_content = rx.markdown(
                    content_state.tab_content[slug],
                    component_map=MARKDOWN_COMPONENT_MAP,
                    use_unwrap_images=False,
                )
            tabs.append(TabSpec(label=label, value=slug, content=panel(md_content)))
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


def _make_tab_sub_page(
    folder: str,
    content_state: type[ArtDesignContentState] | type[ScienceTechContentState],
    active_slug: str,
    active_content: str,
) -> rx.Component:
    """Build a page component with the active tab's content baked in statically.

    Only the active tab embeds a plain Python string — no state var, so no hydration
    mismatch and no bundle bloat from loading all tabs upfront. All other tabs remain
    empty state vars and lazy-load on click exactly as on the main page route.
    """
    meta = load_page_meta(folder)
    heading: str = meta.get("heading", folder.replace("-", " ").title())
    accent_key: str = meta.get("accent", "amber")
    accent = ACCENT_MAP.get(accent_key, AMBER)
    bg_key: str = meta.get("background", "default")
    bg_func = BG_FUNC_MAP.get(bg_key, fullscreen_bg)
    sidebar_side: Literal["left", "right"] = meta.get("sidebar_side", "right")  # type: ignore[assignment]

    tabs = tuple(_build_dynamic_tab_specs(
        folder, content_state, static_overrides={active_slug: active_content},
    ))
    return rx.box(
        bg_func(),
        page_content(
            section_heading(heading, accent),
            sidebar_tabs(
                tabs=tabs,
                accent=accent,
                sidebar_side=sidebar_side,
                default_value=active_slug,
                on_tab_select=content_state.load_tab,
            ),
        ),
        bottom_nav(),
        min_height="100vh",
        font_family=SANS_FONT,
    )


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
# Content map page (for bots / LLMs — not in user navigation)
# ---------------------------------------------------------------------------

def _content_section(title: str, markdown_text: str) -> rx.Component:
    """A heading + rendered markdown block for the content map page."""
    return rx.box(
        rx.heading(title, size="4", margin_bottom="0.5rem", margin_top="1.5rem"),
        rx.markdown(markdown_text, component_map=MARKDOWN_COMPONENT_MAP, use_unwrap_images=False),
        width="100%",
    )


def content_map_page() -> rx.Component:
    """Flat HTML page containing all site content for search bots and LLMs.

    Not linked from the user-facing navigation. Registered in the sitemap so
    crawlers find it. All markdown is embedded at compile time so it appears
    fully in the pre-rendered HTML without JavaScript or WebSocket.
    """
    art_sections = [_content_section(label, raw) for _slug, label, raw in _ART_DESIGN_RAW]
    sci_sections = [_content_section(label, raw) for _slug, label, raw in _SCI_TECH_RAW]

    pieces_sections: list[rx.Component] = []
    if _PIECES_INTRO:
        pieces_sections.append(_content_section("Pieces — Overview", _PIECES_INTRO))
    for entry in _PIECES_ENTRIES:
        pieces_sections.append(_content_section(entry.raw_heading, entry.body_md))

    return rx.box(
        rx.box(
            rx.heading("Livia Zaharia — Full Content Index", size="6", margin_bottom="0.5rem"),
            rx.text(
                "This page provides all site content in a single document for search engines and AI assistants.",
                color="gray",
                margin_bottom="2rem",
            ),
            rx.divider(),
            rx.heading("Biography", size="5", margin_top="1.5rem"),
            _content_section("Biography", _BIOGRAPHY_TEXT),
            rx.divider(margin_top="2rem"),
            rx.heading("Art & Design", size="5", margin_top="1.5rem"),
            *art_sections,
            rx.divider(margin_top="2rem"),
            rx.heading("Science & Tech", size="5", margin_top="1.5rem"),
            *sci_sections,
            rx.divider(margin_top="2rem"),
            rx.heading("Pieces", size="5", margin_top="1.5rem"),
            *pieces_sections,
            max_width="860px",
            margin="0 auto",
            padding="2rem 1.5rem 4rem",
            font_family=SANS_FONT,
        ),
        background="white",
        color="#1a1a1a",
        min_height="100vh",
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
            rx.el.meta(
                name="google-site-verification",
                content="rwVg_JOvfmsKPIt2j1kcJ3wT7XW-vTCtajAd4p5i7Ts",
            ),
            rx.script(_LIVIA_NAV_JS),
            _json_ld_script(_PERSON_SCHEMA),
        ],
    )
    application.add_page(
        home_page,
        route="/",
        title="Livia Zaharia",
        description="Between living systems and generative form. Computational Design, Science Art & Digital Health.",
        meta=[
            {"property": "og:type", "content": "website"},
            {"property": "og:title", "content": "Livia Zaharia"},
            {"property": "og:description", "content": "Romanian architect and parametric jewellery artist. Generative art, speculative design for longevity, experimental contemporary jewellery. Founder of GlucoseDAO."},
            {"property": "og:image", "content": "/livia.jpg"},
            {"name": "twitter:card", "content": "summary_large_image"},
            {"name": "twitter:title", "content": "Livia Zaharia"},
            {"name": "twitter:description", "content": "Between living systems and generative form. Computational Design, Science Art & Digital Health."},
        ],
    )
    application.add_page(
        biography_page,
        route="/biography",
        title="Biography | Livia Zaharia",
        description="Livia Zaharia — Romanian architect, parametric jewellery artist, and citizen scientist. Founder of GlucoseDAO, contributor to Longevity Genie, exhibited at Romanian Jewelry Week since 2021.",
        meta=[
            {"property": "og:type", "content": "profile"},
            {"property": "og:title", "content": "Biography | Livia Zaharia"},
            {"property": "og:description", "content": _BIOGRAPHY_TEXT[:300].replace("\n", " ")},
            {"property": "og:image", "content": "/livia.jpg"},
            {"name": "twitter:card", "content": "summary_large_image"},
            _json_ld_script({
                "@context": "https://schema.org",
                "@type": "AboutPage",
                "name": "Biography — Livia Zaharia",
                "description": "Biography of Livia Zaharia, Romanian architect and parametric jewellery artist.",
                "mainEntity": {**_PERSON_SCHEMA, "description": _BIOGRAPHY_TEXT},
            }),
        ],
    )
    application.add_page(
        pieces_page,
        route="/pieces",
        title="Pieces | Livia Zaharia",
        description="Wearable objects and jewellery by Livia Zaharia — parametric, script-driven pieces cast in silver, incorporating amber, walnut, and natural materials. Exhibited at Romanian Jewelry Week since 2021.",
        on_load=[PiecesContentState.load_content, MobileTabRailState.collapse_expanded],
        meta=[
            {"property": "og:type", "content": "website"},
            {"property": "og:title", "content": "Pieces | Livia Zaharia"},
            {"property": "og:description", "content": "Wearable objects and jewellery by Livia Zaharia — parametric, script-driven pieces cast in silver, amber, and natural materials."},
            {"property": "og:image", "content": "/yellow_side.jpg"},
            {"name": "twitter:card", "content": "summary_large_image"},
            _json_ld_script({
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": "Pieces — Livia Zaharia",
                "description": "Wearable objects and jewellery by Livia Zaharia. Parametric, script-driven designs cast in silver and mixed materials.",
                "creator": {"@type": "Person", "name": "Livia Zaharia"},
                "keywords": "parametric jewellery, silver, generative design, Paral Design, Romanian Jewelry Week",
                "hasPart": [
                    {"@type": "VisualArtwork", "name": e.raw_heading, "description": e.body_md}
                    for e in _PIECES_ENTRIES
                ],
            }),
        ],
    )
    application.add_page(
        art_design_page,
        route="/art-design",
        title="Art & Design | Livia Zaharia",
        description="Art & Design practice of Livia Zaharia (Paral Design). Parametric jewellery, generative architecture, and wearable art using Grasshopper, COMPAS, and Python — exhibited internationally since 2019.",
        on_load=[ArtDesignContentState.load_content, MobileTabRailState.collapse_expanded],
        meta=[
            {"property": "og:type", "content": "website"},
            {"property": "og:title", "content": "Art & Design | Livia Zaharia"},
            {"property": "og:description", "content": "Parametric jewellery and generative art by Livia Zaharia (Paral Design). Script-driven 3D design, cast in silver, amber, and natural materials."},
            {"property": "og:image", "content": "/yellow_side.jpg"},
            {"name": "twitter:card", "content": "summary_large_image"},
            _json_ld_script({
                "@context": "https://schema.org",
                "@type": "CreativeWork",
                "name": "Art & Design — Livia Zaharia / Paral Design",
                "description": (
                    "Parametric jewellery and generative art practice by Livia Zaharia, working under the label Paral Design. "
                    "Uses Grasshopper, COMPAS, and Python scripts to design nature-evoking wearable artefacts — rings, pendants, "
                    "earrings — cast in silver and mixed with natural materials. Exhibited at Romanian Jewelry Week 2021–2025, "
                    "Berlin Longevity Week, ARDD, and Data as Wearable Art."
                ),
                "creator": {"@type": "Person", "name": "Livia Zaharia", "alternateName": "Paral Design"},
                "keywords": "parametric jewellery, generative art, Grasshopper, COMPAS, silver casting, Romanian Jewelry Week, Paral Design",
                "hasPart": [
                    {"@type": "CreativeWork", "name": label, "description": raw}
                    for _slug, label, raw in _ART_DESIGN_RAW
                ],
            }),
        ],
    )
    application.add_page(
        science_tech_page,
        route="/science-tech",
        title="Science & Tech | Livia Zaharia",
        description="Livia Zaharia as citizen scientist: founder of GlucoseDAO (open glucose prediction research), contributor to Longevity Genie, ML practitioner, and bioinformatics workshop instructor.",
        on_load=[ScienceTechContentState.load_content, MobileTabRailState.collapse_expanded],
        meta=[
            {"property": "og:type", "content": "website"},
            {"property": "og:title", "content": "Science & Tech | Livia Zaharia"},
            {"property": "og:description", "content": "Citizen scientist: founder of GlucoseDAO, contributor to Longevity Genie open-source ecosystem, ML practitioner in digital health and longevity research."},
            {"property": "og:image", "content": "/green_side.jpg"},
            {"name": "twitter:card", "content": "summary_large_image"},
            _json_ld_script({
                "@context": "https://schema.org",
                "@type": "ProfilePage",
                "name": "Science & Tech — Livia Zaharia",
                "description": (
                    "Livia Zaharia as citizen scientist and open-source contributor. "
                    "Founder of GlucoseDAO — building open tools for glucose prediction benchmarking and comparing ML models "
                    "against human intuition (Sugar-Sugar Game at sugar-sugar.glucosedao.org). "
                    "Contributor to Longevity Genie open-source ecosystem. "
                    "Affiliated with HEALES and Universitätsmedizin Rostock (IBIMA). "
                    "Technical stack: Python, PyTorch, Polars, NeuralForecaster, Reflex. "
                    "Has taught AI agentic workshops in bioinformatics."
                ),
                "mainEntity": {
                    "@type": "Person",
                    "name": "Livia Zaharia",
                    "founder": [
                        {"@type": "Organization", "name": "GlucoseDAO", "url": "https://glucosedao.org", "description": "Decentralized autonomous organization for open-source glucose prediction benchmarking"},
                    ],
                    "memberOf": [
                        {"@type": "Organization", "name": "Longevity Genie", "url": "https://longevity-genie.github.io"},
                        {"@type": "Organization", "name": "HEALES"},
                        {"@type": "Organization", "name": "Universitätsmedizin Rostock (IBIMA)"},
                    ],
                },
                "hasPart": [
                    {"@type": "CreativeWork", "name": label, "description": raw}
                    for _slug, label, raw in _SCI_TECH_RAW
                ],
            }),
        ],
    )
    application.add_page(
        content_map_page,
        route="/content",
        title="Full Content Index | Livia Zaharia",
        description="All content from livia.glucosedao.org in a single page: biography, art & design collections, science & tech projects, and pieces — for search engines and AI assistants.",
        context={"sitemap": {"changefreq": "weekly", "priority": 0.3}},
    )

    # Per-tab sub-routes — each prerenders with only its own content baked in.
    # Other tabs on these pages still lazy-load on click (no extra bundle cost).
    _raw_by_slug: dict[str, tuple[str, str]] = {
        slug: (label, raw) for slug, label, raw in _ART_DESIGN_RAW
    }
    for _order, label, slug, source_type in scan_tab_slugs("art-design"):
        if not source_type.startswith("md:"):
            continue
        content = load_single_tab_md_content("art-design", slug) or ""
        slug_label, raw = _raw_by_slug.get(slug, (label, ""))
        description = raw[:300].replace("\n", " ").strip()

        def _art_tab_page(s: str = slug, c: str = content) -> rx.Component:
            return _make_tab_sub_page("art-design", ArtDesignContentState, s, c)

        application.add_page(
            _art_tab_page,
            route=f"/art-design/{slug}",
            title=f"{slug_label} | Art & Design | Livia Zaharia",
            description=description or f"{slug_label} — parametric jewellery and generative art by Livia Zaharia.",
            on_load=[MobileTabRailState.collapse_expanded],
            meta=[
                {"property": "og:type", "content": "website"},
                {"property": "og:title", "content": f"{slug_label} | Art & Design | Livia Zaharia"},
                {"property": "og:description", "content": description or slug_label},
                {"property": "og:image", "content": "/yellow_side.jpg"},
                {"name": "twitter:card", "content": "summary_large_image"},
            ],
        )

    _sci_raw_by_slug: dict[str, tuple[str, str]] = {
        slug: (label, raw) for slug, label, raw in _SCI_TECH_RAW
    }
    for _order, label, slug, source_type in scan_tab_slugs("science-tech"):
        if not source_type.startswith("md:"):
            continue
        content = load_single_tab_md_content("science-tech", slug) or ""
        slug_label, raw = _sci_raw_by_slug.get(slug, (label, ""))
        description = raw[:300].replace("\n", " ").strip()

        def _sci_tab_page(s: str = slug, c: str = content) -> rx.Component:
            return _make_tab_sub_page("science-tech", ScienceTechContentState, s, c)

        application.add_page(
            _sci_tab_page,
            route=f"/science-tech/{slug}",
            title=f"{slug_label} | Science & Tech | Livia Zaharia",
            description=description or f"{slug_label} — citizen science and digital health work by Livia Zaharia.",
            on_load=[MobileTabRailState.collapse_expanded],
            meta=[
                {"property": "og:type", "content": "website"},
                {"property": "og:title", "content": f"{slug_label} | Science & Tech | Livia Zaharia"},
                {"property": "og:description", "content": description or slug_label},
                {"property": "og:image", "content": "/green_side.jpg"},
                {"name": "twitter:card", "content": "summary_large_image"},
            ],
        )

    return application
