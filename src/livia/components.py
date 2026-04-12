"""Reusable UI components for the Livia website."""

from typing import Literal

import reflex as rx
import yaml

from livia.constants import (
    ACCENT_MAP,
    AMBER,
    AMBER_DIM,
    CONTENT_DIR,
    GREEN,
    LinkItem,
    MARKDOWN_COMPONENT_MAP,
    NAV_LINKS,
    PANEL_BG,
    PANEL_BORDER,
    SANS_FONT,
    SERIF_FONT,
    SHADOW,
    TEXT_LIGHT,
    TEXT_MUTED,
    TabSpec,
)
from livia.content import (
    collect_gallery_images,
    extract_youtube_id,
    load_content,
    GALLERY_DIRECTIVE_RE,
    ARTIFACT_IMAGE_RE,
)

# re-import the directive regexes via content (which re-exports from constants)
from livia.constants import GALLERY_DIRECTIVE_RE, ARTIFACT_IMAGE_RE


# ---------------------------------------------------------------------------
# State classes for interactive UI elements
# ---------------------------------------------------------------------------

class GalleryState(rx.State):
    lightbox_src: str = ""
    lightbox_open: bool = False

    def open_lightbox(self, src: str) -> None:
        self.lightbox_src = src
        self.lightbox_open = True

    def close_lightbox(self) -> None:
        self.lightbox_open = False


# ---------------------------------------------------------------------------
# Backgrounds
# ---------------------------------------------------------------------------

def fullscreen_bg() -> rx.Component:
    """Full-viewport portrait background layer."""
    return rx.fragment(
        rx.box(
            position="fixed",
            inset="0",
            background_image='url("/livia.jpg")',
            background_size="cover",
            background_position="center 18%",
            z_index="0",
        ),
        rx.box(
            position="fixed",
            inset="0",
            background=(
                "linear-gradient(90deg, rgba(24, 62, 44, 0.45) 0%, "
                "rgba(15, 12, 10, 0.06) 35%, rgba(15, 12, 10, 0.06) 65%, "
                "rgba(120, 79, 26, 0.45) 100%)"
            ),
            z_index="1",
        ),
    )


def fullscreen_bg_dimmed() -> rx.Component:
    """Dimmed background with Livia portrait for neutral/contact pages."""
    return rx.fragment(
        rx.box(
            position="fixed",
            inset="0",
            background_image='url("/livia.jpg")',
            background_size="cover",
            background_position="center 18%",
            z_index="0",
        ),
        rx.box(
            position="fixed",
            inset="0",
            background="rgba(10, 8, 6, 0.62)",
            z_index="1",
        ),
    )


def fullscreen_bg_green() -> rx.Component:
    """Green-tinted background for science/GlucoseDAO pages."""
    return rx.fragment(
        rx.box(
            position="fixed",
            inset="0",
            background_image='url("/green_side.jpg")',
            background_size="cover",
            background_position="center center",
            z_index="0",
        ),
        rx.box(
            position="fixed",
            inset="0",
            background="rgba(10, 8, 6, 0.55)",
            z_index="1",
        ),
    )


def fullscreen_bg_yellow() -> rx.Component:
    """Yellow/amber background for art & design pages."""
    return rx.fragment(
        rx.box(
            position="fixed",
            inset="0",
            background_image='url("/yellow_side.jpg")',
            background_size="cover",
            background_position="center center",
            z_index="0",
        ),
        rx.box(
            position="fixed",
            inset="0",
            background="rgba(10, 8, 6, 0.55)",
            z_index="1",
        ),
    )


BG_FUNC_MAP: dict[str, "callable"] = {
    "yellow": fullscreen_bg_yellow,
    "green": fullscreen_bg_green,
    "dimmed": fullscreen_bg_dimmed,
    "default": fullscreen_bg,
}


# ---------------------------------------------------------------------------
# Low-level building blocks
# ---------------------------------------------------------------------------

def panel(*children: rx.Component) -> rx.Component:
    """Opaque readable content panel."""
    return rx.box(
        *children,
        background=PANEL_BG,
        backdrop_filter="blur(20px)",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="1.2rem",
        padding=["1.6rem", "2.5rem", "3.5rem"],
        box_shadow=SHADOW,
        width="100%",
    )


def section_heading(title: str, accent: str) -> rx.Component:
    """Page section heading."""
    return rx.vstack(
        rx.heading(
            title,
            font_family=SERIF_FONT,
            color=TEXT_LIGHT,
            font_size=["2.2rem", "2.8rem", "3.4rem"],
            letter_spacing="0.03em",
        ),
        rx.box(
            height="3px",
            width="6rem",
            border_radius="999px",
            background=f"linear-gradient(90deg, {accent}, transparent)",
        ),
        align_items="start",
        spacing="2",
        width="100%",
    )


def page_content(*children: rx.Component) -> rx.Component:
    """Centered content wrapper for inner pages."""
    return rx.box(
        rx.vstack(
            *children,
            spacing="8",
            width="100%",
            align_items="stretch",
        ),
        position="relative",
        z_index="3",
        width="100%",
        max_width="110rem",
        margin="0 auto",
        padding_x=["1rem", "2.5rem", "4rem"],
        padding_top=["1.5rem", "2rem", "3rem"],
        padding_bottom=["6rem", "6.5rem", "7rem"],
    )


def link_list(title: str, links: tuple[LinkItem, ...], accent: str) -> rx.Component:
    """Compact link list panel."""
    return panel(
        rx.text(
            title,
            text_transform="uppercase",
            letter_spacing="0.14em",
            font_size=["0.85rem", "0.95rem", "1rem"],
            color=accent,
            font_weight="700",
            margin_bottom="1rem",
        ),
        rx.vstack(
            *(
                rx.link(
                    link.label,
                    href=link.href,
                    is_external=link.external,
                    color=TEXT_LIGHT,
                    text_decoration="none",
                    font_size=["1.15rem", "1.25rem", "1.35rem"],
                    _hover={"color": accent},
                )
                for link in links
            ),
            align_items="start",
            spacing="4",
        ),
    )


# ---------------------------------------------------------------------------
# Markdown rendering (with custom embed directives)
# ---------------------------------------------------------------------------

def youtube_embed(video_id: str) -> rx.Component:
    """Render a responsive YouTube iframe embed."""
    return rx.box(
        rx.el.iframe(
            src=f"https://www.youtube.com/embed/{video_id}",
            width="100%",
            height="100%",
            frameborder="0",
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
            allowfullscreen="true",
            style={
                "border": "none",
                "border_radius": "0.8rem",
                "display": "block",
                "position": "absolute",
                "top": "0",
                "left": "0",
                "width": "100%",
                "height": "100%",
            },
        ),
        position="relative",
        width="100%",
        padding_top="56.25%",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="0.9rem",
        overflow="hidden",
        background="#000",
    )


def image_gallery(folder: str) -> rx.Component:
    """Responsive masonry-style image gallery with lightbox."""
    images = collect_gallery_images(folder)
    if not images:
        return rx.text(f"No images found in {folder}", color=TEXT_MUTED)

    def gallery_thumb(src: str) -> rx.Component:
        return rx.box(
            rx.image(
                src=src,
                width="100%",
                height="auto",
                object_fit="cover",
                border_radius="0.6rem",
                loading="lazy",
                transition="transform 0.3s ease, box-shadow 0.3s ease",
                _hover={
                    "transform": "scale(1.03)",
                    "box_shadow": "0 8px 32px rgba(0,0,0,0.5)",
                },
            ),
            cursor="pointer",
            on_click=GalleryState.open_lightbox(src),
            overflow="hidden",
            border_radius="0.6rem",
            border=f"1px solid {PANEL_BORDER}",
        )

    lightbox = rx.cond(
        GalleryState.lightbox_open,
        rx.box(
            rx.box(
                rx.text(
                    "✕",
                    color="white",
                    font_size="2rem",
                    cursor="pointer",
                    position="absolute",
                    top="1rem",
                    right="1.5rem",
                    z_index="102",
                    _hover={"opacity": "0.7"},
                ),
                rx.image(
                    src=GalleryState.lightbox_src,
                    max_width="90vw",
                    max_height="85vh",
                    object_fit="contain",
                    border_radius="0.8rem",
                ),
                on_click=GalleryState.close_lightbox,
                display="flex",
                align_items="center",
                justify_content="center",
                position="relative",
                width="100%",
                height="100%",
            ),
            on_click=GalleryState.close_lightbox,
            position="fixed",
            inset="0",
            z_index="200",
            background="rgba(0, 0, 0, 0.88)",
            backdrop_filter="blur(8px)",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )

    return rx.fragment(
        rx.box(
            *[gallery_thumb(src) for src in images],
            display="grid",
            grid_template_columns=[
                "repeat(2, 1fr)",
                "repeat(3, 1fr)",
                "repeat(4, 1fr)",
            ],
            gap="0.8rem",
            width="100%",
        ),
        lightbox,
    )


def artifact_image(src: str) -> rx.Component:
    """Render a single artifact image, centered and clickable for lightbox."""
    return rx.box(
        rx.image(
            src=src,
            max_width="400px",
            width="100%",
            height="auto",
            object_fit="contain",
            border_radius="0.8rem",
            border=f"2px solid {AMBER_DIM}",
            box_shadow="0 4px 24px rgba(154, 101, 39, 0.3)",
            loading="lazy",
            cursor="pointer",
            transition="transform 0.3s ease, box-shadow 0.3s ease",
            _hover={
                "transform": "scale(1.03)",
                "box_shadow": "0 8px 36px rgba(154, 101, 39, 0.5)",
            },
        ),
        on_click=GalleryState.open_lightbox(src),
        display="flex",
        justify_content="center",
        width="100%",
        margin_top="1rem",
        margin_bottom="1rem",
    )


def markdown_with_embeds(content: str) -> rx.Component:
    """Render markdown while converting standalone YouTube links into embeds."""
    components: list[rx.Component] = []
    markdown_buffer: list[str] = []

    def flush_markdown_buffer() -> None:
        if not markdown_buffer:
            return
        components.append(
            rx.markdown(
                "\n".join(markdown_buffer).strip(),
                component_map=MARKDOWN_COMPONENT_MAP,
            )
        )
        markdown_buffer.clear()

    for line in content.splitlines():
        video_id = extract_youtube_id(line)
        if video_id is not None:
            flush_markdown_buffer()
            components.append(youtube_embed(video_id))
            continue

        gallery_match = GALLERY_DIRECTIVE_RE.match(line.strip())
        if gallery_match is not None:
            flush_markdown_buffer()
            components.append(image_gallery(gallery_match.group(1)))
            continue

        artifact_match = ARTIFACT_IMAGE_RE.match(line.strip())
        if artifact_match is not None:
            flush_markdown_buffer()
            components.append(artifact_image(artifact_match.group(1)))
            continue

        markdown_buffer.append(line)

    flush_markdown_buffer()
    return rx.vstack(*components, spacing="4", width="100%", align_items="stretch")


def markdown_panel(content_name: str) -> rx.Component:
    """Panel that renders markdown loaded from the content/ directory."""
    return panel(markdown_with_embeds(load_content(content_name)))


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

def _nav_link(link: LinkItem) -> rx.Component:
    """Single bottom-nav link with active-page highlight."""
    if link.href == "/":
        is_active = (rx.State.router.page.path == "/") | (rx.State.router.page.path == "")
    else:
        is_active = rx.State.router.page.path == link.href
    accent_attr = link.accent or "neutral"
    return rx.link(
        rx.vstack(
            rx.hstack(
                rx.cond(
                    bool(link.icon),
                    rx.icon(tag=link.icon or "link", size=16),
                    rx.fragment(),
                ),
                rx.text(link.label, class_name="livia-nav-label"),
                spacing="2",
                align="center",
                wrap="nowrap",
            ),
            rx.el.span(link.tooltip or "", class_name="livia-nav-tooltip"),
            rx.box(
                class_name="livia-nav-indicator",
                height="2px",
                width=rx.cond(is_active, "100%", "0%"),
                background=f"linear-gradient(90deg, {AMBER}, {GREEN})",
                border_radius="999px",
                transition="width 0.3s ease",
            ),
            spacing="1",
            align="center",
        ),
        href=link.href,
        is_external=link.external,
        color=rx.cond(is_active, TEXT_LIGHT, TEXT_MUTED),
        font_weight=rx.cond(is_active, "700", "500"),
        text_decoration="none",
        transition="color 0.2s ease",
        custom_attrs={"data-href": link.href, "data-accent": accent_attr},
    )


def _nav_divider() -> rx.Component:
    """Thin vertical separator between nav links."""
    return rx.box(
        class_name="livia-nav-divider",
        width="1px",
        background="rgba(255, 248, 238, 0.25)",
        flex_shrink="0",
    )


def bottom_nav() -> rx.Component:
    """Floating bottom navigation dock."""
    nav_items: list[rx.Component] = []
    for i, link in enumerate(NAV_LINKS):
        if i > 0:
            nav_items.append(_nav_divider())
        nav_items.append(_nav_link(link))
    return rx.box(
        rx.hstack(
            *nav_items,
            spacing="0",
            wrap="nowrap",
            justify="center",
            align="center",
            class_name="livia-bottom-nav-row",
        ),
        class_name="livia-bottom-nav",
        position="fixed",
        bottom="1rem",
        left="50%",
        z_index="50",
        width="auto",
        backdrop_filter="blur(24px)",
        background="rgba(18, 15, 12, 0.72)",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="999px",
        box_shadow=SHADOW,
    )


# ---------------------------------------------------------------------------
# Sidebars (hover-expand tool rails; labels @paral_design and GITHUB / TECH)
# ---------------------------------------------------------------------------

def instagram_sidebar() -> rx.Component:
    """Instagram tool rail on the right: narrow grip with @paral_design; expands on hover."""
    grip = rx.box(
        rx.text(
            "@paral_design",
            white_space="nowrap",
            style={"writing_mode": "vertical-rl", "text_orientation": "mixed"},
        ),
        class_name="livia-tool-rail-grip livia-tool-rail-grip--instagram",
        display="flex",
        align_items="center",
        justify_content="center",
        flex_shrink="0",
        padding_y="0.85rem",
        padding_x="0.35rem",
        background=PANEL_BG,
    )
    body = rx.box(
        rx.vstack(
            rx.text(
                "@paral_design",
                class_name="livia-tool-rail-heading livia-tool-rail-heading--instagram",
                width="100%",
            ),
            rx.box(
                rx.el.iframe(
                    src="https://www.instagram.com/paral_design/embed",
                    width="115%",
                    height="600px",
                    frameborder="0",
                    scrolling="no",
                    style={
                        "border": "none",
                        "background": "#1a1714",
                        "color_scheme": "dark",
                        "margin_top": "-1rem",
                        "margin_left": "-7.5%",
                        "filter": "saturate(1.1) brightness(0.65)",
                    },
                ),
                rx.box(
                    position="absolute",
                    top="0",
                    left="0",
                    right="0",
                    height="1.5rem",
                    background="linear-gradient(to top, transparent, rgba(18, 15, 12, 0.95))",
                    pointer_events="none",
                    z_index="1",
                ),
                rx.box(
                    position="absolute",
                    bottom="0",
                    left="0",
                    right="0",
                    height="3rem",
                    background="linear-gradient(to bottom, transparent, rgba(18, 15, 12, 0.95))",
                    pointer_events="none",
                    z_index="1",
                ),
                position="relative",
                overflow="hidden",
                border_radius="0.8rem",
                height="340px",
                width="100%",
            ),
            rx.link(
                "Open on Instagram",
                href="https://www.instagram.com/paral_design/",
                is_external=True,
                color=AMBER,
                text_decoration="none",
                font_weight="600",
                class_name="livia-tool-rail-cta",
            ),
            spacing="3",
            width="100%",
            align_items="start",
        ),
        class_name="livia-tool-rail-body",
        padding="1rem",
        width="100%",
        min_width="0",
        max_height="85vh",
        overflow_y="auto",
    )
    inner = rx.box(
        body,
        grip,
        class_name="livia-tool-rail-inner livia-tool-rail-inner--right",
    )
    return rx.box(
        inner,
        class_name="livia-tool-rail livia-tool-rail--right",
        position="fixed",
        top="50%",
        right="0",
        transform="translateY(-50%)",
        max_height="85vh",
        overflow="hidden",
        backdrop_filter="blur(20px)",
        background=PANEL_BG,
        border=f"1px solid {PANEL_BORDER}",
        border_radius="1.2rem 0 0 1.2rem",
        box_shadow=SHADOW,
        z_index="51",
        custom_attrs={"tabindex": "0"},
    )


def github_sidebar() -> rx.Component:
    """GitHub & Tech tool rail on the left: narrow grip GITHUB / TECH; expands on hover."""
    grip = rx.box(
        rx.text(
            "GITHUB / TECH",
            white_space="nowrap",
            style={"writing_mode": "vertical-rl", "text_orientation": "mixed"},
        ),
        class_name="livia-tool-rail-grip livia-tool-rail-grip--github",
        display="flex",
        align_items="center",
        justify_content="center",
        flex_shrink="0",
        padding_y="0.85rem",
        padding_x="0.35rem",
        background=PANEL_BG,
    )
    body = rx.box(
        rx.vstack(
            rx.text(
                "GITHUB & TECH",
                class_name="livia-tool-rail-heading livia-tool-rail-heading--github",
                width="100%",
            ),
            rx.vstack(
                rx.box(
                    rx.hstack(
                        rx.icon(tag="github", size=18, color=GREEN, flex_shrink="0"),
                        rx.text("GlucoseDAO", font_size="1rem", font_weight="bold", color=TEXT_LIGHT),
                        align="center",
                        spacing="2",
                    ),
                    rx.text("Open-source tools for glucose prediction and metabolic health.", font_size="0.85rem", color=TEXT_MUTED, margin_top="0.2rem"),
                    rx.link("View GitHub ↗", href="https://github.com/GlucoseDAO/", is_external=True, color=GREEN, font_size="0.85rem", margin_top="0.5rem", display="block"),
                    background="rgba(255, 255, 255, 0.03)",
                    border=f"1px solid {PANEL_BORDER}",
                    border_radius="0.6rem",
                    padding="1rem",
                    width="100%",
                    _hover={"background": "rgba(255, 255, 255, 0.06)"},
                    transition="background 0.2s",
                ),
                rx.box(
                    rx.hstack(
                        rx.icon(tag="github", size=18, color=GREEN, flex_shrink="0"),
                        rx.text("Longevity Genie", font_size="1rem", font_weight="bold", color=TEXT_LIGHT),
                        align="center",
                        spacing="2",
                    ),
                    rx.text("AI-driven tools and open-source ecosystem for longevity biology.", font_size="0.85rem", color=TEXT_MUTED, margin_top="0.2rem"),
                    rx.link("View GitHub ↗", href="https://github.com/longevity-genie", is_external=True, color=GREEN, font_size="0.85rem", margin_top="0.5rem", display="block"),
                    background="rgba(255, 255, 255, 0.03)",
                    border=f"1px solid {PANEL_BORDER}",
                    border_radius="0.6rem",
                    padding="1rem",
                    width="100%",
                    _hover={"background": "rgba(255, 255, 255, 0.06)"},
                    transition="background 0.2s",
                ),
                rx.box(
                    rx.hstack(
                        rx.icon(tag="linkedin", size=18, color=GREEN, flex_shrink="0"),
                        rx.text("LinkedIn", font_size="1rem", font_weight="bold", color=TEXT_LIGHT),
                        align="center",
                        spacing="2",
                    ),
                    rx.text("Professional network & recent activity.", font_size="0.85rem", color=TEXT_MUTED, margin_top="0.2rem"),
                    rx.link("View Profile ↗", href="https://ro.linkedin.com/in/livia-zaharia-4b1425a0", is_external=True, color=GREEN, font_size="0.85rem", margin_top="0.5rem", display="block"),
                    background="rgba(255, 255, 255, 0.03)",
                    border=f"1px solid {PANEL_BORDER}",
                    border_radius="0.6rem",
                    padding="1rem",
                    width="100%",
                    _hover={"background": "rgba(255, 255, 255, 0.06)"},
                    transition="background 0.2s",
                ),
                spacing="4",
                width="100%",
                margin_top="1rem",
            ),
            spacing="4",
            width="100%",
            align_items="start",
        ),
        class_name="livia-tool-rail-body",
        padding="1rem",
        width="100%",
        min_width="0",
        max_height="80vh",
        overflow_y="auto",
    )
    inner = rx.box(
        grip,
        body,
        class_name="livia-tool-rail-inner livia-tool-rail-inner--left",
    )
    return rx.box(
        inner,
        class_name="livia-tool-rail livia-tool-rail--left",
        position="fixed",
        top="50%",
        left="0",
        transform="translateY(-50%)",
        max_height="85vh",
        overflow="hidden",
        backdrop_filter="blur(20px)",
        background=PANEL_BG,
        border=f"1px solid {PANEL_BORDER}",
        border_radius="0 1.2rem 1.2rem 0",
        box_shadow=SHADOW,
        z_index="100",
        custom_attrs={"tabindex": "0"},
    )


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

def sidebar_tabs(
    tabs: tuple[TabSpec, ...],
    accent: str,
    sidebar_side: Literal["left", "right"],
    default_value: str,
) -> rx.Component:
    """Desktop: vertical sidebar tabs; mobile: horizontal tabs."""
    tab_trigger_style = {
        "font_family": SERIF_FONT,
        "font_size": ["1.8rem", "2rem", "2.2rem"],
        "font_weight": "600",
        "color": TEXT_MUTED,
        "cursor": "pointer",
        "white_space": "normal",
        "word_break": "break-word",
        "text_align": sidebar_side,
        "width": "100%",
        "padding": "0.3rem 0.6rem",
        "_selected": {
            "color": accent,
        },
    }
    desktop_sidebar = rx.box(
        rx.tabs.list(
            *(rx.tabs.trigger(tab.label, value=tab.value, style=tab_trigger_style) for tab in tabs),
            display="flex",
            flex_direction="column",
            align_items="flex-start" if sidebar_side == "left" else "flex-end",
            justify_content="flex-start",
            gap="0.6rem",
            width="100%",
        ),
        class_name="livia-tab-rail",
        display=["none", "none", "flex"],
        flex_direction="column",
        align_items="stretch",
        flex_shrink="0",
        position="sticky",
        top="1.5rem",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="1rem",
        background="rgba(18, 15, 12, 0.78)",
        backdrop_filter="blur(16px)",
        padding="0.45rem",
    )
    mobile_tabs = rx.tabs.list(
        *(rx.tabs.trigger(tab.label, value=tab.value, style=tab_trigger_style) for tab in tabs),
        display=["flex", "flex", "none"],
        gap="0.4rem",
        flex_wrap="wrap",
        justify_content="flex-start",
        border_bottom=f"1px solid {PANEL_BORDER}",
        padding_bottom="0.5rem",
        width="100%",
    )
    contents = tuple(rx.tabs.content(tab.content, value=tab.value, width="100%") for tab in tabs)
    content_stack = rx.vstack(
        mobile_tabs,
        *contents,
        spacing="4",
        width="100%",
        flex="1",
        min_width="0",
        align_items="stretch",
    )
    desktop_row = (
        rx.hstack(desktop_sidebar, content_stack, spacing="5", width="100%", align="start")
        if sidebar_side == "left"
        else rx.hstack(content_stack, desktop_sidebar, spacing="5", width="100%", align="start")
    )
    return rx.tabs.root(
        desktop_row,
        default_value=default_value,
        width="100%",
        class_name="livia-page-tabs",
    )


def _build_special_tab(spec: dict) -> rx.Component:
    """Build a component for a special (non-markdown) tab from its YAML spec."""
    tab_type = spec.get("type", "")
    if tab_type == "instagram_embed":
        return instagram_embed_panel()
    if tab_type == "link_list":
        accent = ACCENT_MAP.get(spec.get("accent", ""), GREEN)
        links = tuple(
            LinkItem(label=link["label"], href=link["href"], external=True)
            for link in spec.get("links", [])
        )
        return link_list("Links", links, accent)
    return panel(rx.text(f"Unknown tab type: {tab_type}", color=TEXT_LIGHT))


def instagram_embed_panel() -> rx.Component:
    """Full-width Instagram embed for the Art & Design Instagram tab."""
    return panel(
        rx.vstack(
            rx.link(
                rx.text(
                    "@paral_design",
                    font_family=SERIF_FONT,
                    font_size=["1.4rem", "1.6rem", "1.8rem"],
                    color=AMBER,
                    font_weight="600",
                ),
                href="https://www.instagram.com/paral_design/",
                is_external=True,
                text_decoration="none",
            ),
            rx.box(
                rx.el.iframe(
                    src="https://www.instagram.com/paral_design/embed",
                    width="100%",
                    height="200vh",
                    frameborder="0",
                    scrolling="no",
                    style={
                        "border": "none",
                        "background": "#1a1714",
                        "color_scheme": "dark",
                        "margin_top": "-1rem",
                    },
                ),
                overflow="hidden",
                border_radius="0.8rem",
                height="75vh",
                width="100%",
            ),
            rx.link(
                "Open on Instagram",
                href="https://www.instagram.com/paral_design/",
                is_external=True,
                color=AMBER,
                text_decoration="none",
                font_weight="600",
                font_size=["1.1rem", "1.18rem", "1.25rem"],
            ),
            spacing="4",
            width="100%",
            align_items="start",
        ),
    )


