"""
Semantic mappings template for ThemeWeaver.

This module contains the template for semantic UI mappings used in theme generation.
The template uses generic palette names (Primary, Secondary, etc.) that get resolved
to actual palette names during theme generation.
"""

from typing import Dict, Optional

from themeweaver.core.syntax_schema import (
    build_editor_syntax_mappings,
    default_format_bold_italic,
)


def _get_syntax_format(
    element: str, syntax_format: Optional[Dict[str, Dict[str, bool]]], color: str
) -> list:
    """Get syntax formatting for a specific element.

    Args:
        element: Element name (normal, keyword, etc.)
        syntax_format: Optional syntax formatting specifications
        color: Color reference

    Returns:
        List with [color, bold, italic]
    """
    if syntax_format and element in syntax_format:
        format_spec = syntax_format[element]
        return [color, format_spec.get("bold", False), format_spec.get("italic", False)]

    # Default formatting
    defaults = default_format_bold_italic()
    if element in defaults:
        element_defaults = defaults[element]
        return [color, element_defaults["bold"], element_defaults["italic"]]

    return [color, False, False]


def get_mappings_template(syntax_format: Optional[Dict[str, Dict[str, bool]]] = None):
    """
    Returns the semantic mappings template for both dark and light variants.

    Args:
        syntax_format: Optional syntax formatting specifications

    Returns:
        dict: Template with semantic mappings using generic palette names
    """
    return {
        "dark": {
            # Background colors (aligned with hand-maintained themes e.g. inkpot)
            "COLOR_BACKGROUND_1": "Primary.B10",
            "COLOR_BACKGROUND_2": "Primary.B20",
            "COLOR_BACKGROUND_3": "Primary.B30",
            "COLOR_BACKGROUND_4": "Primary.B40",
            "COLOR_BACKGROUND_5": "Primary.B50",
            "COLOR_BACKGROUND_6": "Primary.B70",
            # Text colors
            "COLOR_TEXT_1": "Primary.B140",
            "COLOR_TEXT_2": "Primary.B130",
            "COLOR_TEXT_3": "Primary.B120",
            "COLOR_TEXT_4": "Primary.B110",
            # Accent colors
            "COLOR_ACCENT_1": "Secondary.B50",
            "COLOR_ACCENT_2": "Secondary.B60",
            "COLOR_ACCENT_3": "Secondary.B70",
            "COLOR_ACCENT_4": "Secondary.B80",
            "COLOR_ACCENT_5": "Secondary.B100",
            # Disabled elements
            "COLOR_DISABLED": "Primary.B70",
            # Success / error / warn (dialog feedback; 5 steps each)
            "COLOR_SUCCESS_1": "Success.B40",
            "COLOR_SUCCESS_2": "Success.B70",
            "COLOR_SUCCESS_3": "Success.B90",
            "COLOR_SUCCESS_4": "Success.B110",
            "COLOR_SUCCESS_5": "Success.B130",
            "COLOR_ERROR_1": "Error.B60",
            "COLOR_ERROR_2": "Error.B70",
            "COLOR_ERROR_3": "Error.B110",
            "COLOR_ERROR_4": "Error.B120",
            "COLOR_ERROR_5": "Error.B130",
            "COLOR_WARN_1": "Warning.B70",
            "COLOR_WARN_2": "Warning.B80",
            "COLOR_WARN_3": "Warning.B90",
            "COLOR_WARN_4": "Warning.B100",
            "COLOR_WARN_5": "Warning.B120",
            # Icon colors
            "ICON_1": "Primary.B140",
            "ICON_2": "Secondary.B100",
            "ICON_3": "Success.B100",
            "ICON_4": "Error.B90",
            "ICON_5": "Warning.B90",
            "ICON_6": "Primary.B30",
            "ICON_7": "GroupDark.B90",
            # Group colors
            "GROUP_1": "GroupDark.B10",
            "GROUP_2": "GroupDark.B20",
            "GROUP_3": "GroupDark.B30",
            "GROUP_4": "GroupDark.B40",
            "GROUP_5": "GroupDark.B50",
            "GROUP_6": "GroupDark.B60",
            "GROUP_7": "GroupDark.B70",
            "GROUP_8": "GroupDark.B80",
            "GROUP_9": "GroupDark.B90",
            "GROUP_10": "GroupDark.B100",
            "GROUP_11": "GroupDark.B110",
            "GROUP_12": "GroupDark.B120",
            # Highlight colors
            "COLOR_HIGHLIGHT_1": "Secondary.B10",
            "COLOR_HIGHLIGHT_2": "Secondary.B20",
            "COLOR_HIGHLIGHT_3": "Secondary.B30",
            "COLOR_HIGHLIGHT_4": "Secondary.B50",
            # Occurrence colors
            "COLOR_OCCURRENCE_1": "Primary.B10",
            "COLOR_OCCURRENCE_2": "Primary.B20",
            "COLOR_OCCURRENCE_3": "Primary.B30",
            "COLOR_OCCURRENCE_4": "Primary.B50",
            "COLOR_OCCURRENCE_5": "Primary.B80",
            **build_editor_syntax_mappings("dark", syntax_format, _get_syntax_format),
            # Logo colors
            "PYTHON_LOGO_UP": "Logos.B10",
            "PYTHON_LOGO_DOWN": "Logos.B20",
            "SPYDER_LOGO_BACKGROUND": "Logos.B30",
            "SPYDER_LOGO_WEB": "Logos.B40",
            "SPYDER_LOGO_SNAKE": "Logos.B50",
            # Special tabs
            "SPECIAL_TABS_SEPARATOR": "Primary.B70",
            "SPECIAL_TABS_SELECTED": "Secondary.B60",
            # For the heart used to ask for donations
            "COLOR_HEART": "Secondary.B80",
            # For editor tooltips
            "TIP_TITLE_COLOR": "Success.B80",
            "TIP_CHAR_HIGHLIGHT_COLOR": "Syntax.B170",
            # Tooltip opacity (numeric value, not a color reference)
            "OPACITY_TOOLTIP": 230,
        },
        "light": {
            # Background colors
            "COLOR_BACKGROUND_1": "Primary.B140",
            "COLOR_BACKGROUND_2": "Primary.B130",
            "COLOR_BACKGROUND_3": "Primary.B120",
            "COLOR_BACKGROUND_4": "Primary.B130",
            "COLOR_BACKGROUND_5": "Primary.B110",
            "COLOR_BACKGROUND_6": "Primary.B100",
            # Text colors
            "COLOR_TEXT_1": "Primary.B20",
            "COLOR_TEXT_2": "Primary.B30",
            "COLOR_TEXT_3": "Primary.B40",
            "COLOR_TEXT_4": "Primary.B50",
            # Accent colors
            "COLOR_ACCENT_1": "Secondary.B120",
            "COLOR_ACCENT_2": "Secondary.B110",
            "COLOR_ACCENT_3": "Secondary.B100",
            "COLOR_ACCENT_4": "Secondary.B90",
            "COLOR_ACCENT_5": "Secondary.B80",
            # Disabled elements
            "COLOR_DISABLED": "Primary.B80",
            # Success / error / warn (dialog feedback; 5 steps each)
            "COLOR_SUCCESS_1": "Success.B110",
            "COLOR_SUCCESS_2": "Success.B80",
            "COLOR_SUCCESS_3": "Success.B60",
            "COLOR_SUCCESS_4": "Success.B40",
            "COLOR_SUCCESS_5": "Success.B20",
            "COLOR_ERROR_1": "Error.B60",
            "COLOR_ERROR_2": "Error.B50",
            "COLOR_ERROR_3": "Error.B40",
            "COLOR_ERROR_4": "Error.B30",
            "COLOR_ERROR_5": "Error.B20",
            "COLOR_WARN_1": "Warning.B110",
            "COLOR_WARN_2": "Warning.B80",
            "COLOR_WARN_3": "Warning.B60",
            "COLOR_WARN_4": "Warning.B50",
            "COLOR_WARN_5": "Warning.B30",
            # Icon colors (no Tertiary palette in generated themes — use Secondary)
            "ICON_1": "Primary.B10",
            "ICON_2": "Secondary.B90",
            "ICON_3": "Success.B60",
            "ICON_4": "Error.B80",
            "ICON_5": "Warning.B80",
            "ICON_6": "Primary.B120",
            "ICON_7": "GroupLight.B90",
            # Group colors
            "GROUP_1": "GroupLight.B10",
            "GROUP_2": "GroupLight.B20",
            "GROUP_3": "GroupLight.B30",
            "GROUP_4": "GroupLight.B40",
            "GROUP_5": "GroupLight.B50",
            "GROUP_6": "GroupLight.B60",
            "GROUP_7": "GroupLight.B70",
            "GROUP_8": "GroupLight.B80",
            "GROUP_9": "GroupLight.B90",
            "GROUP_10": "GroupLight.B100",
            "GROUP_11": "GroupLight.B110",
            "GROUP_12": "GroupLight.B120",
            # Highlight colors
            "COLOR_HIGHLIGHT_1": "Secondary.B140",
            "COLOR_HIGHLIGHT_2": "Secondary.B130",
            "COLOR_HIGHLIGHT_3": "Secondary.B120",
            "COLOR_HIGHLIGHT_4": "Secondary.B100",
            # Occurrence colors
            "COLOR_OCCURRENCE_1": "Primary.B140",
            "COLOR_OCCURRENCE_2": "Primary.B130",
            "COLOR_OCCURRENCE_3": "Primary.B120",
            "COLOR_OCCURRENCE_4": "Primary.B100",
            "COLOR_OCCURRENCE_5": "Primary.B70",
            **build_editor_syntax_mappings("light", syntax_format, _get_syntax_format),
            # Logo colors
            "PYTHON_LOGO_UP": "Logos.B10",
            "PYTHON_LOGO_DOWN": "Logos.B20",
            "SPYDER_LOGO_BACKGROUND": "Logos.B30",
            "SPYDER_LOGO_WEB": "Logos.B40",
            "SPYDER_LOGO_SNAKE": "Logos.B50",
            # Special tabs
            "SPECIAL_TABS_SEPARATOR": "Primary.B80",
            "SPECIAL_TABS_SELECTED": "Secondary.B80",
            # For the heart used to ask for donations
            "COLOR_HEART": "Error.B70",
            # For editor tooltips
            "TIP_TITLE_COLOR": "Success.B30",
            "TIP_CHAR_HIGHLIGHT_COLOR": "SyntaxLight.B170",
            # Tooltip opacity (numeric value, not a color reference)
            "OPACITY_TOOLTIP": 230,
        },
    }
