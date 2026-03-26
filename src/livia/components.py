"""Reusable UI components for the Livia website."""

from typing import Literal

import reflex as rx
import yaml

from livia.constants import (
    ACCENT_MAP,
    AMBER,
    AMBER_DIM,
    BUBBLE_ITEMS,
    BubbleItem,
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


class InstagramSidebarState(rx.State):
    is_open: bool = True

    def toggle(self) -> None:
        self.is_open = not self.is_open


class GithubSidebarState(rx.State):
    is_open: bool = True

    def toggle(self) -> None:
        self.is_open = not self.is_open


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
    is_active = rx.State.router.page.path == link.href
    return rx.link(
        rx.hstack(
            rx.cond(
                bool(link.icon),
                rx.icon(tag=link.icon or "link", size=16),
                rx.fragment(),
            ),
            rx.text(link.label),
            spacing="2",
            align="center",
        ),
        href=link.href,
        is_external=link.external,
        color=rx.cond(is_active, TEXT_LIGHT, TEXT_MUTED),
        font_weight=rx.cond(is_active, "700", "500"),
        font_size=["1.05rem", "1.15rem", "1.25rem"],
        text_decoration="none",
        _hover={"color": TEXT_LIGHT},
        transition="color 0.2s ease",
    )


def bottom_nav() -> rx.Component:
    """Floating bottom navigation dock."""
    return rx.box(
        rx.hstack(
            *(_nav_link(link) for link in NAV_LINKS),
            spacing="6",
            wrap="wrap",
            justify="center",
            align="center",
        ),
        position="fixed",
        bottom=["0.6rem", "0.85rem", "1rem"],
        left="50%",
        transform="translateX(-50%)",
        z_index="50",
        width=["calc(100% - 1.5rem)", "calc(100% - 2rem)", "auto"],
        backdrop_filter="blur(24px)",
        background="rgba(18, 15, 12, 0.72)",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="999px",
        box_shadow=SHADOW,
        padding_x=["1.2rem", "1.6rem", "2.4rem"],
        padding_y=["0.7rem", "0.8rem", "0.9rem"],
    )


# ---------------------------------------------------------------------------
# Sidebars
# ---------------------------------------------------------------------------

def instagram_sidebar() -> rx.Component:
    """Collapsible Instagram sidebar fixed to the right edge of the viewport."""
    return rx.box(
        rx.box(
            rx.text(
                "@paral_design",
                font_size="0.72rem",
                font_weight="700",
                letter_spacing="0.14em",
                text_transform="uppercase",
                color=AMBER,
                white_space="nowrap",
                style={"writing_mode": "vertical-rl", "text_orientation": "mixed"},
            ),
            on_click=InstagramSidebarState.toggle,
            cursor="pointer",
            position="absolute",
            top="50%",
            right="100%",
            transform="translateY(-50%)",
            background=PANEL_BG,
            backdrop_filter="blur(20px)",
            border=f"1px solid {PANEL_BORDER}",
            border_radius="0.6rem 0 0 0.6rem",
            padding_x="0.4rem",
            padding_y="0.8rem",
            z_index="52",
        ),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "@paral_design",
                        text_transform="uppercase",
                        letter_spacing="0.14em",
                        font_size="0.72rem",
                        color=AMBER,
                        font_weight="700",
                    ),
                    rx.box(
                        rx.text("✕", color=TEXT_MUTED, font_size="1.1rem", cursor="pointer"),
                        on_click=InstagramSidebarState.toggle,
                    ),
                    justify="between",
                    width="100%",
                    align="center",
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
                    font_size="0.9rem",
                ),
                spacing="3",
                width="100%",
            ),
            padding="1rem",
            width="100%",
            overflow_y="auto",
        ),
        position="fixed",
        top="50%",
        right="0",
        transform=rx.cond(
            InstagramSidebarState.is_open,
            "translateY(-50%)",
            "translateY(-50%) translateX(100%)",
        ),
        width=["85vw", "340px", "360px"],
        max_height="85vh",
        overflow="visible",
        background=PANEL_BG,
        backdrop_filter="blur(20px)",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="1.2rem 0 0 1.2rem",
        box_shadow=SHADOW,
        z_index="51",
        transition="transform 0.3s ease",
    )


def github_sidebar() -> rx.Component:
    """Collapsible GitHub & Tech sidebar fixed to the left edge of the viewport."""
    return rx.box(
        rx.box(
            rx.text(
                "GITHUB / TECH",
                font_size="0.72rem",
                font_weight="700",
                letter_spacing="0.14em",
                text_transform="uppercase",
                color=GREEN,
                white_space="nowrap",
            ),
            on_click=GithubSidebarState.toggle,
            cursor="pointer",
            position="absolute",
            top="50%",
            right="-3.3rem",
            transform="translateY(-50%) rotate(90deg)",
            transform_origin="top center",
            background=PANEL_BG,
            backdrop_filter="blur(20px)",
            border=f"1px solid {PANEL_BORDER}",
            border_radius="0.6rem 0.6rem 0 0",
            padding_x="0.8rem",
            padding_y="0.4rem",
            z_index="100",
            height="auto",
        ),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.text("✕", color=TEXT_MUTED, font_size="1.1rem", cursor="pointer"),
                        on_click=GithubSidebarState.toggle,
                    ),
                    rx.text(
                        "GITHUB & TECH",
                        text_transform="uppercase",
                        letter_spacing="0.14em",
                        font_size="0.72rem",
                        color=GREEN,
                        font_weight="700",
                    ),
                    justify="between",
                    width="100%",
                    align="center",
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
            ),
            padding="1rem",
            width="100%",
            max_height="80vh",
            overflow_y="auto",
        ),
        position="fixed",
        top="50%",
        left="0",
        transform=rx.cond(
            GithubSidebarState.is_open,
            "translateY(-50%)",
            "translateY(-50%) translateX(-100%)",
        ),
        width=["85vw", "340px", "360px"],
        max_height="85vh",
        overflow="visible",
        background=PANEL_BG,
        backdrop_filter="blur(20px)",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="0 1.2rem 1.2rem 0",
        box_shadow=SHADOW,
        z_index="100",
        transition="transform 0.3s ease",
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
        "font_size": ["1.2rem", "1.4rem", "1.6rem"],
        "font_weight": "600",
        "color": TEXT_MUTED,
        "cursor": "pointer",
        "white_space": "normal",
        "word_break": "break-word",
        "text_align": sidebar_side,
        "width": "100%",
        "_selected": {
            "color": accent,
        },
    }
    desktop_sidebar = rx.tabs.list(
        *(rx.tabs.trigger(tab.label, value=tab.value, style=tab_trigger_style) for tab in tabs),
        display=["none", "none", "flex"],
        flex_direction="column",
        align_items="flex-start" if sidebar_side == "left" else "flex-end",
        justify_content="flex-start",
        gap="0.5rem",
        min_width="14rem",
        width="auto",
        flex_shrink="0",
        position="sticky",
        top="1.5rem",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="1rem",
        background="rgba(18, 15, 12, 0.78)",
        backdrop_filter="blur(16px)",
        padding="1rem",
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


# ---------------------------------------------------------------------------
# Bubbles (home page)
# ---------------------------------------------------------------------------

BUBBLE_EFFECT_JS = """
useEffect(() => {
  function computeArcRadius() {
    var vw = window.innerWidth * 0.48;
    var vh = window.innerHeight * 0.44;
    return Math.min(vw, vh);
  }

  function positionBubbles() {
    var radius = computeArcRadius();
    var bubbles = document.querySelectorAll(".bubble[data-angle]");
    bubbles.forEach(function (el) {
      var angleDeg = parseFloat(el.getAttribute("data-angle"));
      var rad = (angleDeg * Math.PI) / 180;
      var ox = Math.cos(rad) * radius;
      var oy = Math.sin(rad) * radius;
      el.style.setProperty("--offset-x", ox + "px");
      el.style.setProperty("--offset-y", oy + "px");
    });
  }

  var shiverTimers = [];

  function scheduleShiver(bubble) {
    var delay = 3000 + Math.random() * 5000;
    var timerId = setTimeout(function () {
      bubble.classList.add("shiver");
      var removeId = setTimeout(function () {
        bubble.classList.remove("shiver");
      }, 400);
      shiverTimers.push(removeId);
      scheduleShiver(bubble);
    }, delay);
    shiverTimers.push(timerId);
  }

  positionBubbles();

  var bubbles = document.querySelectorAll(".bubble[data-angle]");
  bubbles.forEach(function (bubble) {
    var floatDur = 4 + Math.random() * 3;
    var floatDelay = Math.random() * -6;
    var floatAmp = 6 + Math.random() * 6;
    bubble.style.setProperty("--float-dur", floatDur + "s");
    bubble.style.setProperty("--float-delay", floatDelay + "s");
    bubble.style.setProperty("--float-amp", floatAmp + "px");
    scheduleShiver(bubble);
  });

  window.addEventListener("resize", positionBubbles);

  return function () {
    window.removeEventListener("resize", positionBubbles);
    shiverTimers.forEach(function (id) { clearTimeout(id); });
  };
}, [])
"""


class BubbleHooks(rx.Fragment):
    """Invisible component that injects the bubble positioning and animation hooks."""

    def add_hooks(self) -> list[str]:
        return [BUBBLE_EFFECT_JS]


def _bubble_component(item: BubbleItem) -> rx.Component:
    """Build a native Reflex component for a single floating bubble."""
    label = rx.el.span(item.icon_label, class_name="bubble-label")
    tooltip = rx.el.span(item.tooltip, class_name="bubble-tooltip")
    attrs: dict[str, str] = {
        "data-angle": str(item.angle),
        "data-accent": item.accent,
    }
    if item.external:
        attrs["target"] = "_blank"
        attrs["rel"] = "noopener noreferrer"
    return rx.el.a(
        label,
        tooltip,
        href=item.href,
        class_name="bubble",
        custom_attrs=attrs,
    )


def bubble_overlay() -> rx.Component:
    """Floating navigation bubbles arranged in an arc around viewport center."""
    return rx.fragment(
        rx.box(
            rx.box(
                *(_bubble_component(b) for b in BUBBLE_ITEMS),
                class_name="bubble-origin",
            ),
            class_name="bubble-container",
        ),
        BubbleHooks.create(),
    )
