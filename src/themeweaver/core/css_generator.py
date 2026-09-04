"""Generate Spyder help default.css, appeal.css, and pydoc.css from theme palettes."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Type, Union

from themeweaver.core.colorsystem import _resolve_color_reference

_logger = logging.getLogger(__name__)

# CSS custom property -> palette attribute (hex, or editor (color, bold, italic)).
# A string applies to both variants. A mapping must include both "dark" and "light".
# Example: "--header-text-color": {"dark": "COLOR_TEXT_1", "light": "COLOR_BACKGROUND_1"}
# Theme ``css_overrides`` may also use color-class refs (e.g. ``Primary.B30``).
CssColorSpec = Union[str, Mapping[str, str]]

# Shared palette mappings used by both default and appeal CSS.
_LINK_COLOR_SPEC: CssColorSpec = {"dark": "COLOR_ACCENT_3", "light": "COLOR_ACCENT_4"}
_HOVER_COLOR_SPEC: CssColorSpec = {"dark": "COLOR_ACCENT_4", "light": "COLOR_ACCENT_3"}
_SCROLLBAR_COLORS: Dict[str, CssColorSpec] = {
    "--scrollbar-thumb": "COLOR_DISABLED",
    "--scrollbar-thumb-hover": "SPECIAL_TABS_SELECTED",
}

# Arrow PNG filenames in theme rc/. default.css and pydoc.css use relative urls
# next to rc/; appeal.css embeds the files as data URIs (WebView has no theme path).
_ARROW_FILES: Dict[str, str] = {
    "--img-arrow-down": "arrow_down.png",
    "--img-arrow-down-disabled": "arrow_down_disabled.png",
    "--img-arrow-up": "arrow_up.png",
    "--img-arrow-up-disabled": "arrow_up_disabled.png",
    "--img-arrow-left": "arrow_left.png",
    "--img-arrow-left-disabled": "arrow_left_disabled.png",
    "--img-arrow-right": "arrow_right.png",
    "--img-arrow-right-disabled": "arrow_right_disabled.png",
}
_ARROW_IMAGES: Dict[str, str] = {
    css_var: f"url(rc/{filename})" for css_var, filename in _ARROW_FILES.items()
}

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
    "--link-color": _LINK_COLOR_SPEC,
    "--hover-color": _HOVER_COLOR_SPEC,
    "--danger-color": "COLOR_ERROR_2",
    "--warning-bg": "COLOR_WARN_2",
    "--warning-border": "COLOR_WARN_1",
    "--argspec-highlight": "EDITOR_SYMBOL",
    "--border-color": "COLOR_BACKGROUND_5",
    "--border-subtle": "COLOR_BACKGROUND_4",
    "--border-light": "COLOR_BACKGROUND_2",
    "--img-shadow-color": "COLOR_BACKGROUND_4",
    **_SCROLLBAR_COLORS,
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

# Appeal CSS custom property -> palette attribute (hex only).
# Theme ``appeal_overrides`` may also use color-class refs (e.g. ``Primary.B30``).
APPEAL_COLOR_MAP: Dict[str, CssColorSpec] = {
    "--background": "COLOR_BACKGROUND_1",
    "--foreground": "COLOR_TEXT_1",
    "--link-color": _LINK_COLOR_SPEC,
    "--hover-color": _HOVER_COLOR_SPEC,
    "--heart": {"light": "Error.B90", "dark": "COLOR_ACCENT_4"},
    "--highlight": {"light": "Error.B70", "dark": "COLOR_ACCENT_3"},
    "--hand": {"light": "Warning.B120", "dark": "Secondary.B110"},
    "--border-primary": "COLOR_BACKGROUND_5",
    "--border-secondary": "COLOR_BACKGROUND_4",
    "--code-bg": "COLOR_BACKGROUND_3",
    **_SCROLLBAR_COLORS,
}

# Non-palette static values for default CSS (aliases, literals, images). Shared by dark and light.
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
    **_ARROW_IMAGES,
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
    "--syn-type": "var(--syn-keyword)",
    "--syn-constant": "var(--syn-keyword)",
    "--syn-keyword-namespace": "var(--syn-keyword)",
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

# Fallback relative urls for appeal CSS when rc/ is not supplied (build without export).
APPEAL_STATIC: Dict[str, str] = dict(_ARROW_IMAGES)

# Pydoc CSS custom property -> palette attribute. Theme ``pydoc_overrides`` may
# also use color-class refs (e.g. ``Primary.B30``).
PYDOC_COLOR_MAP: Dict[str, CssColorSpec] = {
    "--background-color": "COLOR_BACKGROUND_1",
    "--surface-color": "COLOR_BACKGROUND_3",
    "--text-color": "COLOR_TEXT_1",
    "--heading-color": "COLOR_TEXT_3",
    "--header-bg-color": {"dark": "COLOR_ACCENT_1", "light": "SPECIAL_TABS_SELECTED"},
    "--header-text-color": {"dark": "COLOR_TEXT_1", "light": "COLOR_BACKGROUND_1"},
    "--link-color": _LINK_COLOR_SPEC,
    "--hover-color": _HOVER_COLOR_SPEC,
    "--danger-color": "COLOR_ERROR_2",
    "--border-color": "COLOR_BACKGROUND_5",
    "--muted-color": "COLOR_TEXT_4",
    "--syn-string": "EDITOR_STRING",
    **_SCROLLBAR_COLORS,
}

# Non-palette static values for pydoc CSS. Shared by dark and light.
PYDOC_STATIC: Dict[str, str] = {
    "--search-bg": "var(--surface-color)",
    "--search-border": "var(--border-color)",
    "--search-text": "var(--text-color)",
    "--search-submit-bg": "var(--header-bg-color)",
    "--search-submit-text": "var(--header-text-color)",
    "--border-radius": "4px",
    "--page-margin": "25px",
    **_ARROW_IMAGES,
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
        list(_ARROW_IMAGES),
    ),
    (
        "Syntax (Pygments)",
        [
            "--syn-highlight-bg",
            "--syn-fg",
            "--syn-comment",
            "--syn-comment-special-bg",
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

# Emission order for the generated pydoc :root block.
_PYDOC_ROOT_SECTIONS: List[Tuple[str, List[str]]] = [
    (
        "Main colors",
        [
            "--background-color",
            "--surface-color",
            "--text-color",
            "--header-text-color",
            "--heading-color",
            "--header-bg-color",
            "--link-color",
            "--hover-color",
            "--danger-color",
            "--border-color",
            "--muted-color",
            "--syn-string",
            "--scrollbar-thumb",
            "--scrollbar-thumb-hover",
            "--search-bg",
            "--search-border",
            "--search-text",
            "--search-submit-bg",
            "--search-submit-text",
            "--border-radius",
            "--page-margin",
        ],
    ),
    (
        "Images (filenames match theme rc/)",
        list(_ARROW_IMAGES),
    ),
]

_RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources" / "css"


def resolve_palette_key(spec: CssColorSpec, variant: str) -> str:
    """Return the color source key for a help CSS color spec and variant.

    The key is either a palette attribute (``COLOR_TEXT_1``) or a color-class
    reference (``Primary.B30``).
    """
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


def _validate_color_spec(css_var: str, spec: Any) -> CssColorSpec:
    """Validate and normalize a CSS color override or default spec."""
    if isinstance(spec, str):
        if not spec:
            raise ValueError(f"CSS color mapping for {css_var!r} is empty")
        return spec
    if isinstance(spec, Mapping):
        extra = set(spec) - {"dark", "light"}
        if extra:
            raise ValueError(
                f"CSS color mapping for {css_var!r} has unknown variant keys: "
                f"{sorted(extra)}"
            )
        missing = {"dark", "light"} - set(spec)
        if missing:
            raise ValueError(
                f"CSS color mapping for {css_var!r} is missing {sorted(missing)}"
            )
        dark = spec["dark"]
        light = spec["light"]
        if not isinstance(dark, str) or not dark:
            raise ValueError(
                f"CSS color mapping for {css_var!r} dark value must be a non-empty string"
            )
        if not isinstance(light, str) or not light:
            raise ValueError(
                f"CSS color mapping for {css_var!r} light value must be a non-empty string"
            )
        return {"dark": dark, "light": light}
    raise ValueError(
        f"CSS color mapping for {css_var!r} must be a string or "
        f"{{dark, light}} mapping, got {type(spec).__name__}"
    )


def merge_color_map(
    base_map: Mapping[str, CssColorSpec],
    overrides: Optional[Mapping[str, Any]] = None,
    *,
    map_name: str,
) -> Dict[str, CssColorSpec]:
    """Merge sparse theme overrides onto a base CSS color map.

    Unknown CSS variable keys raise ``ValueError``. Each override replaces the
    whole default spec for that key (no partial dark/light merge).
    """
    merged: Dict[str, CssColorSpec] = dict(base_map)
    if not overrides:
        return merged

    unknown = set(overrides) - set(base_map)
    if unknown:
        raise ValueError(
            f"Unknown override keys (not in {map_name}): {sorted(unknown)}"
        )

    for css_var, spec in overrides.items():
        merged[css_var] = _validate_color_spec(css_var, spec)
    return merged


def merge_css_color_map(
    overrides: Optional[Mapping[str, Any]] = None,
) -> Dict[str, CssColorSpec]:
    """Merge sparse theme overrides onto ``CSS_COLOR_MAP``."""
    return merge_color_map(CSS_COLOR_MAP, overrides, map_name="CSS_COLOR_MAP")


def merge_appeal_color_map(
    overrides: Optional[Mapping[str, Any]] = None,
) -> Dict[str, CssColorSpec]:
    """Merge sparse theme overrides onto ``APPEAL_COLOR_MAP``."""
    return merge_color_map(APPEAL_COLOR_MAP, overrides, map_name="APPEAL_COLOR_MAP")


def merge_pydoc_color_map(
    overrides: Optional[Mapping[str, Any]] = None,
) -> Dict[str, CssColorSpec]:
    """Merge sparse theme overrides onto ``PYDOC_COLOR_MAP``."""
    return merge_color_map(PYDOC_COLOR_MAP, overrides, map_name="PYDOC_COLOR_MAP")


def arrow_image_data_uris(rc_dir: Path) -> Dict[str, str]:
    """Return arrow CSS custom properties as PNG data URIs from ``rc_dir``."""
    values: Dict[str, str] = {}
    for css_var, filename in _ARROW_FILES.items():
        path = rc_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Arrow image for {css_var} not found: {path}")
        encoded = base64.standard_b64encode(path.read_bytes()).decode("ascii")
        values[css_var] = f'url("data:image/png;base64,{encoded}")'
    return values


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


def resolve_css_color_value(
    palette_class: Type[Any],
    key: str,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
) -> str:
    """Resolve a CSS color source to a hex string.

    ``key`` is a palette attribute (``COLOR_TEXT_1``) or a color-class reference
    (``Primary.B30``). Class refs require ``color_classes``.
    """
    if "." in key:
        if not color_classes:
            raise ValueError(
                f"Color-class reference {key!r} requires color_classes to resolve"
            )
        value = _resolve_color_reference(key, dict(color_classes))
        if not isinstance(value, str) or not value.startswith("#"):
            raise ValueError(
                f"Color-class reference {key!r} did not resolve to a hex color: {value!r}"
            )
        return value
    return palette_hex(palette_class, key)


def resolve_color_map_values(
    palette_class: Type[Any],
    variant: str,
    color_map: Mapping[str, CssColorSpec],
    *,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
    static: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """Resolve CSS custom properties from a color map (and optional static values)."""
    values: Dict[str, str] = dict(static) if static else {}
    for css_var, spec in color_map.items():
        source_key = resolve_palette_key(spec, variant)
        values[css_var] = resolve_css_color_value(
            palette_class, source_key, color_classes
        )
    return values


def resolve_root_values(
    palette_class: Type[Any],
    variant: str,
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
) -> Dict[str, str]:
    """Resolve all ``:root`` custom properties for a palette and variant."""
    mapping = color_map if color_map is not None else CSS_COLOR_MAP
    return resolve_color_map_values(
        palette_class,
        variant,
        mapping,
        color_classes=color_classes,
        static=CSS_STATIC,
    )


def format_root(
    values: Dict[str, str],
    *,
    sections: Optional[List[Tuple[str, List[str]]]] = None,
) -> str:
    """Format resolved values as a ``:root { ... }`` CSS block."""
    section_list = _ROOT_SECTIONS if sections is None else sections
    lines = [
        "/* Spyder CSS */",
        "/* Generated by ThemeWeaver from the theme palette. */",
        "",
        ":root {",
    ]
    for comment, names in section_list:
        if comment:
            lines.append("")
            lines.append(f"    /* --- {comment} --- */")
        for name in names:
            lines.append(f"    {name}: {values[name]};")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def build_root(
    palette_class: Type[Any],
    variant: str,
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
) -> str:
    """Build the ``:root`` block from palette-mapped and static values."""
    return format_root(
        resolve_root_values(
            palette_class,
            variant,
            color_map=color_map,
            color_classes=color_classes,
        )
    )


def _read_css_resource(filename: str, missing: str) -> str:
    """Read a CSS template from the resources directory."""
    path = _RESOURCES_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"{missing} not found: {path}")
    return path.read_text(encoding="utf-8")


def _append_scrollbar(rules: str) -> str:
    """Append the shared scrollbar template to a rules stylesheet."""
    scrollbar = _read_css_resource("scrollbar.css", "CSS scrollbar template")
    rules = rules.rstrip()
    scrollbar = scrollbar.lstrip()
    if scrollbar and not scrollbar.endswith("\n"):
        scrollbar += "\n"
    if not rules:
        return scrollbar
    return f"{rules}\n\n{scrollbar}"


def load_rules() -> str:
    """Load the shared CSS rules (no ``:root``) from the resources directory."""
    return _append_scrollbar(_read_css_resource("rules.css", "CSS rules template"))


def load_pydoc_rules() -> str:
    """Load pydoc CSS rules (no ``:root``) from the resources directory."""
    return _append_scrollbar(
        _read_css_resource("pydoc_rules.css", "Pydoc CSS rules template")
    )


def _require_css_variant(variant: str) -> None:
    if variant not in ("dark", "light"):
        raise ValueError(f"Unsupported CSS variant: {variant!r}")


def _write_css_file(variant_dir: Path, filename: str, content: str) -> Path:
    """Write CSS content into a variant export directory."""
    variant_dir.mkdir(parents=True, exist_ok=True)
    out_path = variant_dir / filename
    out_path.write_text(content, encoding="utf-8")
    _logger.info("📄 Wrote CSS: %s", out_path)
    return out_path


def _combine_root_and_rules(root: str, rules: str) -> str:
    """Join a ``:root`` block and a rules stylesheet."""
    root = root.rstrip()
    rules = rules.lstrip()
    if not root.endswith("\n"):
        root += "\n"
    if rules and not rules.endswith("\n"):
        rules += "\n"
    return f"{root}\n{rules}"


def build_default_css(
    variant: str,
    palette_class: Type[Any],
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
) -> str:
    """Build the full ``default.css`` content for a theme variant."""
    _require_css_variant(variant)
    return _combine_root_and_rules(
        build_root(
            palette_class,
            variant,
            color_map=color_map,
            color_classes=color_classes,
        ),
        load_rules(),
    )


def write_default_css(
    variant_dir: Path,
    variant: str,
    palette_class: Type[Any],
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
) -> Path:
    """Write ``default.css`` into a variant export directory.

    Returns:
        Path to the written file.
    """
    return _write_css_file(
        variant_dir,
        "default.css",
        build_default_css(
            variant,
            palette_class,
            color_map=color_map,
            color_classes=color_classes,
        ),
    )


def resolve_pydoc_values(
    palette_class: Type[Any],
    variant: str,
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
) -> Dict[str, str]:
    """Resolve pydoc CSS custom properties for a palette and variant."""
    mapping = color_map if color_map is not None else PYDOC_COLOR_MAP
    return resolve_color_map_values(
        palette_class,
        variant,
        mapping,
        color_classes=color_classes,
        static=PYDOC_STATIC,
    )


def build_pydoc_root(
    palette_class: Type[Any],
    variant: str,
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
) -> str:
    """Build the pydoc ``:root`` block from palette-mapped and static values."""
    return format_root(
        resolve_pydoc_values(
            palette_class,
            variant,
            color_map=color_map,
            color_classes=color_classes,
        ),
        sections=_PYDOC_ROOT_SECTIONS,
    )


def build_pydoc_css(
    variant: str,
    palette_class: Type[Any],
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
) -> str:
    """Build the full ``pydoc.css`` content for a theme variant."""
    _require_css_variant(variant)
    return _combine_root_and_rules(
        build_pydoc_root(
            palette_class,
            variant,
            color_map=color_map,
            color_classes=color_classes,
        ),
        load_pydoc_rules(),
    )


def write_pydoc_css(
    variant_dir: Path,
    variant: str,
    palette_class: Type[Any],
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
) -> Path:
    """Write ``pydoc.css`` into a variant export directory.

    Returns:
        Path to the written file.
    """
    return _write_css_file(
        variant_dir,
        "pydoc.css",
        build_pydoc_css(
            variant,
            palette_class,
            color_map=color_map,
            color_classes=color_classes,
        ),
    )


def resolve_appeal_values(
    palette_class: Type[Any],
    variant: str,
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
    rc_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """Resolve appeal CSS custom properties for a palette and variant.

    If ``rc_dir`` is given, arrow image vars are PNG data URIs from that
    directory. Otherwise relative ``url(rc/...)`` values are used.
    """
    mapping = color_map if color_map is not None else APPEAL_COLOR_MAP
    static = arrow_image_data_uris(rc_dir) if rc_dir is not None else APPEAL_STATIC
    return resolve_color_map_values(
        palette_class,
        variant,
        mapping,
        color_classes=color_classes,
        static=static,
    )


def format_appeal(values: Dict[str, str], variant: str) -> str:
    """Format resolved appeal values as a ``[data-mode] { ... }`` CSS block."""
    lines = [
        "/* Spyder CSS */",
        "/* Generated by ThemeWeaver from the theme palette. */",
        "",
        f'[data-mode="{variant}"] {{',
    ]
    for name in list(APPEAL_COLOR_MAP) + list(APPEAL_STATIC):
        lines.append(f"  {name}: {values[name]};")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def build_appeal_css(
    variant: str,
    palette_class: Type[Any],
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
    rc_dir: Optional[Path] = None,
) -> str:
    """Build the ``appeal.css`` content for a theme variant.

    Pass ``rc_dir`` to embed arrow PNGs as data URIs.
    """
    _require_css_variant(variant)
    return format_appeal(
        resolve_appeal_values(
            palette_class,
            variant,
            color_map=color_map,
            color_classes=color_classes,
            rc_dir=rc_dir,
        ),
        variant,
    )


def write_appeal_css(
    variant_dir: Path,
    variant: str,
    palette_class: Type[Any],
    *,
    color_map: Optional[Mapping[str, CssColorSpec]] = None,
    color_classes: Optional[Mapping[str, Type[Any]]] = None,
) -> Path:
    """Write ``appeal.css`` into a variant export directory.

    Arrow images are read from ``variant_dir/rc`` and embedded as data URIs.

    Returns:
        Path to the written file.
    """
    return _write_css_file(
        variant_dir,
        "appeal.css",
        build_appeal_css(
            variant,
            palette_class,
            color_map=color_map,
            color_classes=color_classes,
            rc_dir=variant_dir / "rc",
        ),
    )
