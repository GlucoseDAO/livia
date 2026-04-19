"""Shared constants, paths, regexes, and data classes for the Livia website."""

from dataclasses import dataclass
from pathlib import Path
import re

import reflex as rx

CONTENT_DIR = Path(__file__).parent.parent.parent / "content"
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"

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

ACCENT_MAP: dict[str, str] = {"amber": AMBER, "green": GREEN}
ACCENT_DIM_MAP: dict[str, str] = {"amber": AMBER_DIM, "green": GREEN_DIM}

MARKDOWN_COMPONENT_MAP = {
    "p": lambda text: rx.text(
        text,
        color=TEXT_LIGHT,
        line_height="2",
        font_size=["1.15rem", "1.25rem", "1.35rem"],
        margin_top="0.8rem",
        margin_bottom="0.8rem",
    ),
    "a": lambda text, **props: rx.link(
        text,
        color=AMBER,
        text_decoration="none",
        font_weight="600",
        font_size="inherit",
        _hover={"color": TEXT_LIGHT},
        **props,
    ),
    "h1": lambda text: rx.heading(
        text,
        font_family=SERIF_FONT,
        color=TEXT_LIGHT,
        font_size=["2rem", "2.5rem", "3rem"],
        margin_top="2.5rem",
        margin_bottom="1rem",
    ),
    "h2": lambda text: rx.heading(
        text,
        font_family=SERIF_FONT,
        color=TEXT_LIGHT,
        font_size=["1.6rem", "2rem", "2.4rem"],
        margin_top="2rem",
        margin_bottom="0.8rem",
    ),
}

# Pieces page: single body size (no responsive type ramp) to avoid uneven blocks of text.
_PIECES_TEXT = "1.05rem"
PIECES_MARKDOWN_COMPONENT_MAP = {
    "p": lambda text: rx.text(
        text,
        color=TEXT_LIGHT,
        font_size=_PIECES_TEXT,
        line_height="1.65",
        word_break="break-word",
        overflow_wrap="anywhere",
        margin_top="0.55rem",
        margin_bottom="0.55rem",
    ),
    "a": lambda text, **props: rx.link(
        text,
        color=AMBER,
        text_decoration="none",
        font_weight="600",
        font_size=_PIECES_TEXT,
        word_break="break-all",
        _hover={"color": TEXT_LIGHT},
        **props,
    ),
    "h1": lambda text: rx.heading(
        text,
        font_family=SERIF_FONT,
        color=TEXT_LIGHT,
        font_size="1.35rem",
        line_height="1.35",
        margin_top="1.5rem",
        margin_bottom="0.6rem",
    ),
    "h2": lambda text: rx.heading(
        text,
        font_family=SERIF_FONT,
        color=TEXT_LIGHT,
        font_size="1.35rem",
        line_height="1.35",
        margin_top="2rem",
        margin_bottom="0.65rem",
    ),
    "h3": lambda text: rx.heading(
        text,
        font_family=SERIF_FONT,
        color=TEXT_LIGHT,
        font_size="1.2rem",
        line_height="1.35",
        margin_top="1.25rem",
        margin_bottom="0.5rem",
    ),
    "em": lambda text: rx.text(
        text,
        as_="em",
        color=TEXT_MUTED,
        font_size=_PIECES_TEXT,
        font_style="italic",
        line_height="1.65",
    ),
    "strong": lambda text: rx.text(
        text,
        as_="b",
        color=TEXT_LIGHT,
        font_size=_PIECES_TEXT,
        font_weight="600",
        line_height="1.65",
    ),
}

YOUTUBE_WATCH_RE = re.compile(r"^https?://(?:www\.)?youtube\.com/watch\?[^#\s]*v=([A-Za-z0-9_-]{11})[^#\s]*$")
YOUTUBE_SHORT_RE = re.compile(r"^https?://(?:www\.)?youtu\.be/([A-Za-z0-9_-]{11})[^#\s]*$")
MARKDOWN_LINK_RE = re.compile(r"^\[[^\]]+\]\((https?://[^)\s]+)\)$")
GALLERY_DIRECTIVE_RE = re.compile(r"^<!--\s*gallery:\s*(.+?)\s*-->$")
ARTIFACT_IMAGE_RE = re.compile(r"^<!--\s*artifact:\s*(.+?)\s*-->$")
SEQUENCE_DIRECTIVE_RE = re.compile(r"^<!--\s*sequence:\s*(.+?)\s*-->$")

_TAB_PREFIX_RE = re.compile(r"^(\d+)_(.+)$")
_REF_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*$", re.DOTALL)


@dataclass(frozen=True)
class LinkItem:
    label: str
    href: str
    external: bool = False
    icon: str | None = None
    accent: str | None = None
    tooltip: str | None = None


@dataclass(frozen=True)
class TabSpec:
    label: str
    value: str
    content: rx.Component
    href: str | None = None


NAV_LINKS = (
    LinkItem(
        "Home",
        "/",
        accent="neutral",
        tooltip="Portrait background and entry",
    ),
    LinkItem(
        "Biography",
        "/biography",
        accent="amber",
        tooltip="Designer, maker, founder",
    ),
    LinkItem(
        "Art & Design",
        "/art-design",
        accent="amber",
        tooltip="Parametric form and fabrication",
    ),
    LinkItem(
        "Pieces",
        "/pieces",
        accent="amber",
        tooltip="Works and objects",
    ),
    LinkItem(
        "Science & Tech",
        "/science-tech",
        accent="green",
        tooltip="Digital health and glucose dynamics",
    ),
)

BIOGRAPHY_LINK_GROUPS: tuple[tuple[str, tuple[LinkItem, ...]], ...] = (
    (
        "Science & Tech",
        (
            LinkItem("GlucoseDAO GitHub", "https://github.com/GlucoseDAO/", True),
            LinkItem("Sugar-Sugar Game", "https://sugar-sugar.glucosedao.org", True),
            LinkItem("GlucoseDAO Hugging Face Spaces", "https://huggingface.co/spaces/GlucoseDao", True),
            LinkItem("Longevity Genie", "https://longevity-genie.github.io", True),
            LinkItem("Longevity Genie GitHub", "https://github.com/longevity-genie", True),
            LinkItem("HEALES", "https://heales.org/", True),
        ),
    ),
    (
        "Art & Design",
        (
            LinkItem("Materialized Enhancements", "https://materialized-enhancements.longevity-genie.info/", True),
            LinkItem(
                "Romanian Jewelry Week 2025",
                "https://www.romanianjewelryweek.com/participants-2025/livia-zaharia",
                True,
            ),
        ),
    ),
    (
        "Social media & contacts",
        (
            LinkItem("Instagram @paral_design", "https://www.instagram.com/paral_design/", True),
            LinkItem("Facebook byLiviaZaharia", "https://www.facebook.com/byLiviaZaharia/", True),
            LinkItem("LinkedIn", "https://www.linkedin.com/in/livia-zaharia-4b1425a0", True),
        ),
    ),
)

