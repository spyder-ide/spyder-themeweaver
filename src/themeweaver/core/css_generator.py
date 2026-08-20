"""Generate Spyder help default.css from theme palettes."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple, Type, Union

_logger = logging.getLogger(__name__)

# CSS custom property -> palette attribute (hex, or editor (color, bold, italic)).
# A string applies to both variants. A mapping must include both "dark" and "light".
# Example: "--header-text-color": {"dark": "COLOR_TEXT_1", "light": "COLOR_BACKGROUND_1"}
CssColorSpec = Union[str, Mapping[str, str]]
CSS_COLOR_MAP: Dict[str, CssColorSpec] = {
    "--background-color": "COLOR_BACKGROUND_1",
    "--surface-color": "COLOR_BACKGROUND_3",
    "--surface-alt": "COLOR_BACKGROUND_4",
    "--code-bg": "COLOR_BACKGROUND_2",
    "--note-bg": {"dark": "COLOR_HIGHLIGHT_1", "light": "COLOR_ACCENT_1"},
    "--text-color": "COLOR_TEXT_1",
    "--heading-color": "COLOR_TEXT_3",
    "--highlight-text-color": "COLOR_TEXT_1",
    "--loading-text-color": "COLOR_TEXT_1",
    "--metadata-text-color": "COLOR_TEXT_1",
    "--header-bg-color": {"dark": "COLOR_ACCENT_1", "light": "SPECIAL_TABS_SELECTED"},
    "--header-text-color": {"dark": "COLOR_TEXT_1", "light": "COLOR_BACKGROUND_1"},
    "--link-color": "COLOR_ACCENT_5",
    "--hover-color": "COLOR_ACCENT_3",
    "--danger-color": "COLOR_ERROR_2",
    "--warning-bg": "COLOR_WARN_2",
    "--warning-border": "COLOR_WARN_1",
    "--argspec-highlight": "EDITOR_SYMBOL",
    "--border-color": "COLOR_BACKGROUND_5",
    "--border-subtle": "COLOR_BACKGROUND_4",
    "--border-light": "COLOR_BACKGROUND_2",
    "--img-shadow-color": "COLOR_BACKGROUND_4",
    "--scrollbar-thumb": "COLOR_DISABLED",
    "--scrollbar-thumb-hover": "SPECIAL_TABS_SELECTED",
    "--syn-highlight-bg": "EDITOR_CURRENTCELL",
    "--syn-fg": "EDITOR_NORMAL",
    "--syn-builtin": "EDITOR_BUILTIN",
    "--syn-comment": "EDITOR_COMMENT",
    "--syn-comment-special-bg": "EDITOR_CURRENTLINE",
    "--syn-error": "COLOR_ERROR_1",
    "--syn-error-bg": "COLOR_ERROR_5",
    "--syn-keyword": "EDITOR_KEYWORD",
    "--syn-operator": "EDITOR_SYMBOL",
    "--syn-inserted": "EDITOR_DEFINITION",
    "--syn-prompt": "EDITOR_STRING",
    "--syn-number": "EDITOR_NUMBER",
    "--syn-string": "EDITOR_STRING",
}

# Non-palette :root values (aliases, literals, images). Shared by dark and light.
CSS_STATIC: Dict[str, str] = {
    "--note-border": "var(--border-light)",
    "--note-text": "var(--text-color)",
    "--loading-bg": "var(--surface-color)",
    "--loading-box-shadow": "none",
    "--field-list-th-color": "var(--text-color)",
    "--metadata-box-shadow": "none",
    "--table-th-color": "var(--text-color)",
    "--panel-title-color": "var(--header-text-color)",
    "--doc-warning-bg": "var(--warning-bg)",
    "--doc-warning-border": "var(--warning-border)",
    "--doc-warning-text": "var(--header-text-color)",
    "--collapse-expand-color": "var(--link-color)",
    "--panel-accent": "var(--header-bg-color)",
    "--panel-usage-heading-border": "var(--background-color)",
    "--border-radius": "4px",
    "--border-radius-lg": "6px",
    "--box-shadow": "0 1px 1px rgba(0, 0, 0, 0.05)",
    "--img-box-shadow": "0px 2px 6px var(--img-shadow-color)",
    "--page-margin": "0px 25px 15px 25px",
    "--font-title": "'Trebuchet MS', sans-serif",
    "--font-heading": "'Helvetica', sans-serif",
    "--img-arrow-down": "url(rc/arrow_down.png)",
    "--img-arrow-down-disabled": "url(rc/arrow_down_disabled.png)",
    "--img-arrow-up": "url(rc/arrow_up.png)",
    "--img-arrow-up-disabled": "url(rc/arrow_up_disabled.png)",
    "--img-arrow-left": "url(rc/arrow_left.png)",
    "--img-arrow-left-disabled": "url(rc/arrow_left_disabled.png)",
    "--img-arrow-right": "url(rc/arrow_right.png)",
    "--img-arrow-right-disabled": "url(rc/arrow_right_disabled.png)",
    "--syn-string-alt": "var(--syn-prompt)",
    "--syn-comment-multiline": "var(--syn-comment)",
    "--syn-preproc": "var(--syn-comment)",
    "--syn-subheading": "var(--syn-comment)",
    "--syn-error-border": "var(--syn-error)",
    "--syn-heading": "var(--syn-fg)",
    "--syn-output": "var(--syn-fg)",
    "--syn-traceback": "var(--syn-fg)",
    "--syn-entity": "var(--syn-fg)",
    "--syn-label": "var(--syn-fg)",
    "--syn-variable": "var(--syn-fg)",
    "--syn-whitespace": "var(--syn-fg)",
    "--syn-builtin": "var(--syn-builtin)",
    "--syn-type": "var(--syn-keyword)",
    "--syn-constant": "var(--syn-keyword)",
    "--syn-keyword-namespace": "var(--syn-keyword)",
    "--syn-operator-word": "var(--syn-operator)",
    "--syn-deleted": "var(--syn-operator)",
    "--syn-tag": "var(--syn-operator)",
    "--syn-class": "var(--syn-inserted)",
    "--syn-decorator": "var(--syn-inserted)",
    "--syn-function": "var(--syn-inserted)",
    "--syn-attribute": "var(--syn-inserted)",
    "--syn-exception": "var(--syn-inserted)",
    "--syn-namespace": "var(--syn-fg)",
    "--syn-string-escape": "var(--syn-number)",
    "--syn-string-interpol": "var(--syn-string-alt)",
    "--syn-string-other": "var(--syn-string-alt)",
    "--syn-string-regex": "var(--syn-string-alt)",
    "--syn-string-symbol": "var(--syn-string-alt)",
}

# Emission order and optional section comments for the generated :root block.
_ROOT_SECTIONS: List[Tuple[str, List[str]]] = [
    (
        "Main colors",
        [
            "--background-color",
            "--surface-color",
            "--surface-alt",
            "--code-bg",
            "--note-bg",
            "--note-border",
            "--note-text",
            "--loading-bg",
            "--loading-box-shadow",
            "--text-color",
            "--header-text-color",
            "--heading-color",
            "--highlight-text-color",
            "--loading-text-color",
            "--field-list-th-color",
            "--metadata-text-color",
            "--metadata-box-shadow",
            "--table-th-color",
            "--panel-title-color",
            "--header-bg-color",
            "--link-color",
            "--hover-color",
            "--danger-color",
            "--warning-bg",
            "--warning-border",
            "--doc-warning-bg",
            "--doc-warning-border",
            "--doc-warning-text",
            "--argspec-highlight",
            "--collapse-expand-color",
            "--panel-accent",
            "--panel-usage-heading-border",
            "--border-color",
            "--border-subtle",
            "--border-light",
            "--img-shadow-color",
            "--scrollbar-thumb",
            "--scrollbar-thumb-hover",
            "--border-radius",
            "--border-radius-lg",
            "--box-shadow",
            "--img-box-shadow",
            "--page-margin",
            "--font-title",
            "--font-heading",
        ],
    ),
    (
        "Images (filenames match theme rc/)",
        [
            "--img-arrow-down",
            "--img-arrow-down-disabled",
            "--img-arrow-up",
            "--img-arrow-up-disabled",
            "--img-arrow-left",
            "--img-arrow-left-disabled",
            "--img-arrow-right",
            "--img-arrow-right-disabled",
        ],
    ),
    (
        "Syntax (Pygments)",
        [
            "--syn-highlight-bg",
            "--syn-fg",
            "--syn-comment",
            "--syn-comment-special-bg",
            "--syn-builtin",
            "--syn-error",
            "--syn-error-bg",
            "--syn-keyword",
            "--syn-operator",
            "--syn-inserted",
            "--syn-prompt",
            "--syn-number",
            "--syn-string",
            "--syn-string-alt",
            "--syn-comment-multiline",
            "--syn-preproc",
            "--syn-subheading",
            "--syn-error-border",
            "--syn-heading",
            "--syn-output",
            "--syn-traceback",
            "--syn-entity",
            "--syn-label",
            "--syn-variable",
            "--syn-whitespace",
            "--syn-builtin",
            "--syn-type",
            "--syn-constant",
            "--syn-keyword-namespace",
            "--syn-operator-word",
            "--syn-deleted",
            "--syn-tag",
            "--syn-class",
            "--syn-decorator",
            "--syn-function",
            "--syn-attribute",
            "--syn-exception",
            "--syn-namespace",
            "--syn-string-escape",
            "--syn-string-interpol",
            "--syn-string-other",
            "--syn-string-regex",
            "--syn-string-symbol",
        ],
    ),
]

_RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources" / "css"


def resolve_palette_key(spec: CssColorSpec, variant: str) -> str:
    """Return the palette attribute name for a help CSS color spec and variant."""
    if isinstance(spec, str):
        return spec
    extra = set(spec) - {"dark", "light"}
    if extra:
        raise ValueError(
            f"Help CSS color mapping has unknown variant keys: {sorted(extra)}"
        )
    try:
        return spec[variant]
    except KeyError as exc:
        raise KeyError(
            f"Help CSS color mapping is missing {variant!r} (have {sorted(spec)})"
        ) from exc


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


def resolve_root_values(palette_class: Type[Any], variant: str) -> Dict[str, str]:
    """Resolve all ``:root`` custom properties for a palette and variant."""
    values: Dict[str, str] = dict(CSS_STATIC)
    for css_var, spec in CSS_COLOR_MAP.items():
        palette_key = resolve_palette_key(spec, variant)
        values[css_var] = palette_hex(palette_class, palette_key)
    return values


def format_root(values: Dict[str, str]) -> str:
    """Format resolved values as a ``:root { ... }`` CSS block."""
    lines = [
        "/* Spyder CSS */",
        "/* Generated by ThemeWeaver from the theme palette. */",
        "",
        ":root {",
    ]
    for comment, names in _ROOT_SECTIONS:
        if comment:
            lines.append("")
            lines.append(f"    /* --- {comment} --- */")
        for name in names:
            lines.append(f"    {name}: {values[name]};")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def build_root(palette_class: Type[Any], variant: str) -> str:
    """Build the ``:root`` block from palette-mapped and static values."""
    return format_root(resolve_root_values(palette_class, variant))


def load_rules() -> str:
    """Load the shared help CSS rules (no ``:root``)."""
    path = _RESOURCES_DIR / "rules.css"
    if not path.is_file():
        raise FileNotFoundError(f"CSS rules template not found: {path}")
    return path.read_text(encoding="utf-8")


def build_default_css(variant: str, palette_class: Type[Any]) -> str:
    """Build the full ``default.css`` content for a theme variant."""
    if variant not in ("dark", "light"):
        raise ValueError(f"Unsupported CSS variant: {variant!r}")
    root = build_root(palette_class, variant).rstrip()
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
    _logger.info("📄 Wrote CSS: %s", out_path)
    return out_path
