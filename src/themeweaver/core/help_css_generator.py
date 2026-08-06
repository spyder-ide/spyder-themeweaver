"""Generate Spyder help default.css from theme palettes."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, Type, Union

_logger = logging.getLogger(__name__)

HEADER_TEXT_COLOR = "#FFFFFF"

HELP_CSS_COLOR_MAP: Dict[str, str] = {
    "--background-color": "COLOR_BACKGROUND_1",
    "--surface-color": "COLOR_BACKGROUND_3",
    "--surface-alt": "COLOR_BACKGROUND_2",
    "--code-bg": "COLOR_BACKGROUND_5",
    "--note-bg": "COLOR_HIGHLIGHT_1",
    "--text-color": "COLOR_TEXT_2",
    "--heading-color": "COLOR_ACCENT_5",
    "--highlight-text-color": "COLOR_TEXT_2",
    "--loading-text-color": "COLOR_TEXT_2",
    "--metadata-text-color": "COLOR_TEXT_2",
    "--header-bg-color-start": "COLOR_ACCENT_5",
    "--header-bg-color-mid": "COLOR_ACCENT_4",
    "--header-bg-color-end": "COLOR_ACCENT_3",
    "--link-color": "COLOR_ACCENT_5",
    "--hover-color": "COLOR_ACCENT_4",
    "--danger-color": "COLOR_ERROR_2",
    "--warning-bg": "COLOR_WARN_2",
    "--warning-border": "COLOR_WARN_1",
    "--argspec-highlight": "COLOR_ERROR_1",
    "--border-color": "COLOR_BACKGROUND_4",
    "--border-subtle": "COLOR_BACKGROUND_2",
    "--border-light": "COLOR_BACKGROUND_1",
    "--img-shadow-color": "COLOR_BACKGROUND_4",
    "--scrollbar-thumb": "COLOR_DISABLED",
    "--scrollbar-thumb-hover": "SPECIAL_TABS_SELECTED",
    "--syn-highlight-bg": "EDITOR_CURRENTCELL",
    "--syn-fg": "EDITOR_NORMAL",
    "--syn-comment": "EDITOR_COMMENT",
    "--syn-comment-special-bg": "EDITOR_CURRENTLINE",
    "--syn-error": "COLOR_ERROR_1",
    "--syn-error-bg": "COLOR_ERROR_5",
    "--syn-keyword": "EDITOR_KEYWORD",
    "--syn-operator": "EDITOR_SYMBOL",
    "--syn-inserted": "EDITOR_DEFINITION",
    "--syn-prompt": "EDITOR_BUILTIN",
    "--syn-number": "EDITOR_NUMBER",
    "--syn-string": "EDITOR_STRING",
}

# Match a CSS custom property whose value is a hex color (optional trailing comment).
_HEX_PROP_RE = re.compile(
    r"(?P<prefix>^\s*(?P<name>--[\w-]+)\s*:\s*)"
    r"(?P<hex>#[0-9A-Fa-f]{3,8})"
    r"(?P<suffix>\s*;.*)$",
    re.MULTILINE,
)

_RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources" / "help_css"


def _resources_dir() -> Path:
    """Return the directory containing help CSS templates."""
    return _RESOURCES_DIR


def palette_hex(palette_class: Type[Any], key: str) -> str:
    """Resolve a palette attribute to a hex color string.

    Editor syntax entries may be ``(color, bold, italic)``; only the color is used.
    """
    if not hasattr(palette_class, key):
        raise AttributeError(
            f"Palette {palette_class.__name__!r} has no attribute {key!r}"
        )
    value: Union[str, tuple, list] = getattr(palette_class, key)
    if isinstance(value, (tuple, list)) and value:
        value = value[0]
    if not isinstance(value, str) or not value.startswith("#"):
        raise ValueError(f"Palette attribute {key!r} is not a hex color: {value!r}")
    return value


def resolve_root(template_text: str, palette_class: Type[Any]) -> str:
    """Fill mapped hex properties in a ``:root`` template from the palette."""

    def _replace(match: re.Match[str]) -> str:
        name = match.group("name")
        if name == "--header-text-color":
            return f"{match.group('prefix')}{HEADER_TEXT_COLOR}{match.group('suffix')}"
        palette_key = HELP_CSS_COLOR_MAP.get(name)
        if palette_key is None:
            return match.group(0)
        hex_value = palette_hex(palette_class, palette_key)
        return f"{match.group('prefix')}{hex_value}{match.group('suffix')}"

    return _HEX_PROP_RE.sub(_replace, template_text)


def load_root_template(variant: str) -> str:
    """Load the packaged ``:root`` template for ``dark`` or ``light``."""
    if variant not in ("dark", "light"):
        raise ValueError(f"Unsupported help CSS variant: {variant!r}")
    path = _resources_dir() / f"root_{variant}.css"
    if not path.is_file():
        raise FileNotFoundError(f"Help CSS root template not found: {path}")
    return path.read_text(encoding="utf-8")


def load_rules() -> str:
    """Load the shared help CSS rules (no ``:root``)."""
    path = _resources_dir() / "rules.css"
    if not path.is_file():
        raise FileNotFoundError(f"Help CSS rules template not found: {path}")
    return path.read_text(encoding="utf-8")


def build_default_css(variant: str, palette_class: Type[Any]) -> str:
    """Build the full ``default.css`` content for a theme variant."""
    root = resolve_root(load_root_template(variant), palette_class).rstrip()
    rules = load_rules().lstrip()
    if not root.endswith("\n"):
        root += "\n"
    if rules and not rules.endswith("\n"):
        rules += "\n"
    return f"{root}\n{rules}"


def write_default_css(
    variant_dir: Path, variant: str, palette_class: Type[Any]
) -> Path:
    """Write ``default.css`` into a variant export directory.

    Returns:
        Path to the written file.
    """
    variant_dir.mkdir(parents=True, exist_ok=True)
    out_path = variant_dir / "default.css"
    content = build_default_css(variant, palette_class)
    out_path.write_text(content, encoding="utf-8")
    _logger.info("📄 Wrote help CSS: %s", out_path)
    return out_path
