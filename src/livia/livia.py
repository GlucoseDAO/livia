"""Livia Zaharia personal website built with Reflex."""

from dataclasses import dataclass
from pathlib import Path
import re

import reflex as rx

CONTENT_DIR = Path(__file__).parent.parent.parent / "content"

SERIF_FONT = '"Cormorant Garamond", Georgia, serif'
SANS_FONT = '"Manrope", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'

BACKGROUND = "#120f0c"
PANEL_BG = "rgba(18, 15, 12, 0.82)"
PANEL_BORDER = "rgba(255, 248, 238, 0.12)"
TEXT_LIGHT = "#f5f0e8"
TEXT_MUTED = "rgba(245, 240, 232, 0.7)"
GREEN = "#5ea882"
GREEN_DIM = "#2f5b46"
AMBER = "#d4943a"
AMBER_DIM = "#9a6527"
SHADOW = "0 12px 48px rgba(0, 0, 0, 0.35)"
GLUCOSEDAO_GITHUB_URL = "https://github.com/GlucoseDAO/"
GLUCOSEDAO_YOUTUBE_URL = "https://www.youtube.com/watch?v=6aTajGZCnEA"

MARKDOWN_COMPONENT_MAP = {
    "p": lambda text: rx.text(text, color=TEXT_LIGHT, line_height="1.8", font_size="0.95rem"),
    "a": lambda text, **props: rx.link(
        text,
        color=AMBER,
        text_decoration="none",
        font_weight="600",
        _hover={"color": TEXT_LIGHT},
        **props,
    ),
    "h1": lambda text: rx.heading(
        text,
        font_family=SERIF_FONT,
        color=TEXT_LIGHT,
        font_size=["1.6rem", "1.8rem", "2rem"],
    ),
    "h2": lambda text: rx.heading(
        text,
        font_family=SERIF_FONT,
        color=TEXT_LIGHT,
        font_size=["1.3rem", "1.45rem", "1.6rem"],
    ),
}

YOUTUBE_WATCH_RE = re.compile(r"^https?://(?:www\.)?youtube\.com/watch\?[^#\s]*v=([A-Za-z0-9_-]{11})[^#\s]*$")
YOUTUBE_SHORT_RE = re.compile(r"^https?://(?:www\.)?youtu\.be/([A-Za-z0-9_-]{11})[^#\s]*$")
MARKDOWN_LINK_RE = re.compile(r"^\[[^\]]+\]\((https?://[^)\s]+)\)$")


def load_content(name: str) -> str:
    return (CONTENT_DIR / f"{name}.md").read_text()


def extract_youtube_id(line: str) -> str | None:
    """Extract a YouTube video ID from a markdown line."""
    stripped = line.strip()
    if not stripped:
        return None

    candidate_url = stripped
    link_match = MARKDOWN_LINK_RE.fullmatch(stripped)
    if link_match:
        candidate_url = link_match.group(1)

    watch_match = YOUTUBE_WATCH_RE.fullmatch(candidate_url)
    if watch_match:
        return watch_match.group(1)

    short_match = YOUTUBE_SHORT_RE.fullmatch(candidate_url)
    if short_match:
        return short_match.group(1)

    return None


def youtube_embed(video_id: str) -> rx.Component:
    """Render a responsive YouTube iframe embed."""
    return rx.box(
        rx.el.iframe(
            src=f"https://www.youtube.com/embed/{video_id}",
            width="100%",
            height="420",
            frameborder="0",
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
            allowfullscreen="true",
            style={
                "border": "none",
                "border_radius": "0.8rem",
                "display": "block",
            },
        ),
        width="100%",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="0.9rem",
        overflow="hidden",
        background="#000",
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
        if video_id is None:
            markdown_buffer.append(line)
            continue
        flush_markdown_buffer()
        components.append(youtube_embed(video_id))

    flush_markdown_buffer()
    return rx.vstack(*components, spacing="4", width="100%", align_items="stretch")


@dataclass(frozen=True)
class LinkItem:
    label: str
    href: str
    external: bool = False
    icon: str | None = None


@dataclass(frozen=True)
class CardItem:
    title: str
    body: str
    href: str
    link_label: str
    accent: str
    external: bool = False


NAV_LINKS = (
    LinkItem("Home", "/"),
    LinkItem("About", "/about"),
    LinkItem("Art & Design", "/art-design"),
    LinkItem("GlucoseDAO", "/glucosedao"),
    LinkItem("GitHub", GLUCOSEDAO_GITHUB_URL, True, "github"),
    LinkItem("YouTube", GLUCOSEDAO_YOUTUBE_URL, True, "youtube"),
)

ABOUT_LINKS = (
    LinkItem("Instagram @paral_design", "https://www.instagram.com/paral_design/", True),
    LinkItem("LinkedIn", "https://ro.linkedin.com/in/livia-zaharia-4b1425a0", True),
    LinkItem("GlucoseDAO GitHub", "https://github.com/GlucoseDAO/", True),
    LinkItem("GlucoseDAO Hugging Face Spaces", "https://huggingface.co/spaces/GlucoseDao", True),
)

SELECTED_WORK = (
    CardItem(
        title="Biology Collection",
        body=(
            "Biology-inspired wearable forms developed through parametric thinking, "
            "porous geometries, and controlled variations that feel grown rather than drawn."
        ),
        href="https://www.instagram.com/paral_design/",
        link_label="View @paral_design",
        accent=AMBER,
        external=True,
    ),
    CardItem(
        title="Supernova Collection",
        body=(
            "A study in expansion, rhythm, and luminous structure translated into "
            "jewellery-scale computational forms."
        ),
        href="https://www.instagram.com/paral_design/",
        link_label="View @paral_design",
        accent=AMBER,
        external=True,
    ),
    CardItem(
        title="Paths. Memories. Guides.",
        body=(
            "Paths. Memories. Guides. explores how a path set by an event becomes memory, "
            "and memory becomes guide. The collection was developed through digital "
            "modelling and fabrication processes such as 3D printing, casting, and laser cutting."
        ),
        href="https://www.romanianjewelryweek.com/participants-2022/livia-zaharia",
        link_label="Romanian Jewelry Week 2022",
        accent=AMBER,
        external=True,
    ),
)


class InstagramSidebarState(rx.State):
    is_open: bool = True

    def toggle(self) -> None:
        self.is_open = not self.is_open


def bottom_nav() -> rx.Component:
    """Floating bottom navigation dock."""
    return rx.box(
        rx.hstack(
            *(
                rx.link(
                    rx.hstack(
                        rx.cond(
                            bool(link.icon),
                            rx.icon(tag=link.icon or "link", size=14),
                            rx.fragment(),
                        ),
                        rx.text(link.label),
                        spacing="2",
                        align="center",
                    ),
                    href=link.href,
                    is_external=link.external,
                    color=TEXT_MUTED,
                    font_weight="500",
                    font_size=["0.82rem", "0.88rem", "0.95rem"],
                    text_decoration="none",
                    _hover={"color": TEXT_LIGHT},
                )
                for link in NAV_LINKS
            ),
            spacing="5",
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
        padding_x=["1rem", "1.4rem", "2rem"],
        padding_y=["0.65rem", "0.7rem", "0.75rem"],
    )


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
    """Dimmed background for inner pages so panels are readable."""
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


def panel(*children: rx.Component) -> rx.Component:
    """Opaque readable content panel."""
    return rx.box(
        *children,
        background=PANEL_BG,
        backdrop_filter="blur(20px)",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="1.2rem",
        padding=["1.2rem", "1.4rem", "1.6rem"],
        box_shadow=SHADOW,
        width="100%",
    )


def markdown_panel(content_name: str) -> rx.Component:
    """Panel that renders markdown loaded from the content/ directory."""
    return panel(markdown_with_embeds(load_content(content_name)))


def feature_card(item: CardItem) -> rx.Component:
    """Project card with readable background."""
    return panel(
        rx.box(
            height="3px",
            width="4rem",
            border_radius="999px",
            background=f"linear-gradient(90deg, {item.accent}, transparent)",
            margin_bottom="0.8rem",
        ),
        rx.vstack(
            rx.heading(
                item.title,
                font_family=SERIF_FONT,
                font_size=["1.4rem", "1.55rem", "1.7rem"],
                color=TEXT_LIGHT,
            ),
            rx.text(item.body, color=TEXT_MUTED, line_height="1.7", font_size="0.95rem"),
            rx.link(
                item.link_label,
                href=item.href,
                is_external=item.external,
                color=item.accent,
                text_decoration="none",
                font_weight="600",
                font_size="0.9rem",
            ),
            align_items="start",
            spacing="3",
        ),
    )


def link_list(title: str, links: tuple[LinkItem, ...], accent: str) -> rx.Component:
    """Compact link list panel."""
    return panel(
        rx.text(
            title,
            text_transform="uppercase",
            letter_spacing="0.14em",
            font_size="0.72rem",
            color=accent,
            font_weight="700",
            margin_bottom="0.8rem",
        ),
        rx.vstack(
            *(
                rx.link(
                    link.label,
                    href=link.href,
                    is_external=link.external,
                    color=TEXT_LIGHT,
                    text_decoration="none",
                    font_size="0.95rem",
                    _hover={"color": accent},
                )
                for link in links
            ),
            align_items="start",
            spacing="3",
        ),
    )


def instagram_sidebar() -> rx.Component:
    """Collapsible Instagram sidebar fixed to the right edge of the viewport."""
    return rx.box(
        # Tab handle (always visible)
        rx.box(
            rx.text(
                "@paral_design",
                font_size="0.72rem",
                font_weight="700",
                letter_spacing="0.14em",
                text_transform="uppercase",
                color=AMBER,
                white_space="nowrap",
            ),
            on_click=InstagramSidebarState.toggle,
            cursor="pointer",
            position="absolute",
            top="50%",
            left="-2.2rem",
            transform="translateY(-50%) rotate(-90deg)",
            transform_origin="center center",
            background=PANEL_BG,
            backdrop_filter="blur(20px)",
            border=f"1px solid {PANEL_BORDER}",
            border_radius="0.6rem 0.6rem 0 0",
            padding_x="0.8rem",
            padding_y="0.4rem",
            z_index="52",
        ),
        # Sidebar content
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
                rx.el.iframe(
                    src="https://www.instagram.com/paral_design/embed",
                    width="100%",
                    height="390px",
                    frameborder="0",
                    scrolling="no",
                    style={
                        "border": "none",
                        "border_radius": "0.8rem",
                        "background": "#1a1714",
                    },
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
            display=rx.cond(InstagramSidebarState.is_open, "block", "none"),
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
        overflow_y="auto",
        background=PANEL_BG,
        backdrop_filter="blur(20px)",
        border=f"1px solid {PANEL_BORDER}",
        border_radius="1.2rem 0 0 1.2rem",
        box_shadow=SHADOW,
        z_index="51",
        transition="transform 0.3s ease",
    )


def page_content(*children: rx.Component) -> rx.Component:
    """Centered content wrapper for inner pages."""
    return rx.box(
        rx.vstack(
            *children,
            spacing="4",
            width="100%",
            max_width="42rem",
            align_items="stretch",
        ),
        position="relative",
        z_index="3",
        max_width="76rem",
        margin="0 auto",
        padding_x=["1rem", "1.5rem", "2.5rem"],
        padding_top=["1.5rem", "2rem", "3rem"],
        padding_bottom=["6rem", "6.5rem", "7rem"],
    )


def section_heading(title: str, accent: str) -> rx.Component:
    """Page section heading."""
    return rx.vstack(
        rx.heading(
            title,
            font_family=SERIF_FONT,
            color=TEXT_LIGHT,
            font_size=["2rem", "2.4rem", "2.8rem"],
            letter_spacing="0.03em",
        ),
        rx.box(
            height="3px",
            width="5rem",
            border_radius="999px",
            background=f"linear-gradient(90deg, {accent}, transparent)",
        ),
        align_items="start",
        spacing="2",
        width="100%",
    )


def home_page() -> rx.Component:
    """Homepage: fullscreen portrait + name overlay + bottom nav."""
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
        bottom_nav(),
        min_height="100vh",
        font_family=SANS_FONT,
    )


def about_page() -> rx.Component:
    return rx.box(
        fullscreen_bg_dimmed(),
        page_content(
            section_heading("About", GREEN),
            markdown_panel("about"),
            link_list("Links", ABOUT_LINKS, GREEN),
        ),
        bottom_nav(),
        min_height="100vh",
        font_family=SANS_FONT,
    )


def art_design_page() -> rx.Component:
    return rx.box(
        fullscreen_bg_dimmed(),
        page_content(
            section_heading("Art & Design", AMBER),
            markdown_panel("art_design"),
        ),
        instagram_sidebar(),
        bottom_nav(),
        min_height="100vh",
        font_family=SANS_FONT,
    )


def glucosedao_page() -> rx.Component:
    return rx.box(
        fullscreen_bg_dimmed(),
        page_content(
            section_heading("GlucoseDAO", GREEN),
            markdown_panel("glucosedao"),
            link_list(
                "Links",
                (
                    LinkItem("GitHub Organization", "https://github.com/GlucoseDAO/", True),
                    LinkItem("Hugging Face Spaces", "https://huggingface.co/spaces/GlucoseDao", True),
                ),
                GREEN,
            ),
        ),
        bottom_nav(),
        min_height="100vh",
        font_family=SANS_FONT,
    )


app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700&display=swap",
    ],
    style={
        "background": BACKGROUND,
        "color": TEXT_LIGHT,
        "font_family": SANS_FONT,
    },
)
app.add_page(home_page, route="/", title="Livia Zaharia")
app.add_page(about_page, route="/about", title="About | Livia Zaharia")
app.add_page(art_design_page, route="/art-design", title="Art & Design | Livia Zaharia")
app.add_page(glucosedao_page, route="/glucosedao", title="GlucoseDAO | Livia Zaharia")
