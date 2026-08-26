"""
Centralized YAML loading utilities for ThemeWeaver.

This module provides unified functions for loading theme configuration files,
eliminating duplication across different modules.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


def load_yaml_file(
    file_path: Path, section: Optional[str] = None
) -> Union[Dict[str, Any], List[Any], str, int, float, bool, None]:
    """
    Load and parse a YAML file with optional section extraction.

    Args:
        file_path: Path to the YAML file
        section: Optional section name to extract from the loaded data

    Returns:
        Parsed YAML data or the specified section

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the YAML file contains invalid syntax
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if section and isinstance(data, dict):
            return data.get(section, {})
        return data

    except FileNotFoundError:
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file {file_path}: {e}")


def load_colors_from_yaml(
    theme_name: str = "solarized", themes_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load color definitions from colorsystem.yaml file for a specific theme.

    Args:
        theme_name: Name of the theme to load. Defaults to "solarized".
        themes_dir: Directory where themes are stored. If None, uses default.

    Returns:
        Color definitions loaded from the YAML file.

    Raises:
        FileNotFoundError: If the theme directory or colorsystem.yaml file doesn't exist.
        ValueError: If the YAML file contains invalid syntax.
    """
    if themes_dir is None:
        themes_dir = Path.cwd() / "themes"

    yaml_file = themes_dir / theme_name / "colorsystem.yaml"
    return load_yaml_file(yaml_file)


def load_color_mappings_from_yaml(
    theme_name: str = "solarized", themes_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Load color class mappings from mappings.yaml file for a specific theme.

    Args:
        theme_name: Name of the theme to load. Defaults to "solarized".
        themes_dir: Directory where themes are stored. If None, uses default.

    Returns:
        Color class mappings loaded from the YAML file.

    Raises:
        FileNotFoundError: If the theme directory or mappings.yaml file doesn't exist.
        ValueError: If the YAML file contains invalid syntax.
    """
    if themes_dir is None:
        themes_dir = Path.cwd() / "themes"

    mappings_file = themes_dir / theme_name / "mappings.yaml"
    return load_yaml_file(mappings_file, "color_classes")


def load_semantic_mappings_from_yaml(
    theme_name: str = "solarized", themes_dir: Optional[Path] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Load semantic UI mappings from mappings.yaml file for a specific theme.

    Args:
        theme_name: Name of the theme to load. Defaults to "solarized".
        themes_dir: Directory where themes are stored. If None, uses default.

    Returns:
        Semantic mappings for dark and light variants.

    Raises:
        FileNotFoundError: If the theme directory or mappings.yaml file doesn't exist.
        ValueError: If the YAML file contains invalid syntax.
    """
    if themes_dir is None:
        themes_dir = Path.cwd() / "themes"

    mappings_file = themes_dir / theme_name / "mappings.yaml"
    semantic_mappings = load_yaml_file(mappings_file, "semantic_mappings")

    # Convert lists to tuples for syntax colors with formatting specifications
    for variant in semantic_mappings:
        for key, value in semantic_mappings[variant].items():
            # Check if it's a list with 3 elements (color, bold, italic)
            if isinstance(value, list) and len(value) == 3:
                # Convert list to tuple
                semantic_mappings[variant][key] = tuple(value)

    return semantic_mappings


def load_css_overrides_from_yaml(
    theme_name: str = "solarized", themes_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load sparse help-CSS color overrides from mappings.yaml for a theme.

    Keys are CSS custom property names (e.g. ``--hover-color``). Values are
    palette attribute names, color-class refs (``Primary.B30``), or a mapping
    with both ``dark`` and ``light`` variants. Missing section yields ``{}``.

    Args:
        theme_name: Name of the theme to load. Defaults to "solarized".
        themes_dir: Directory where themes are stored. If None, uses default.

    Returns:
        CSS override mapping, or empty dict if the section is absent.

    Raises:
        FileNotFoundError: If the theme directory or mappings.yaml file doesn't exist.
        ValueError: If the YAML file contains invalid syntax.
    """
    if themes_dir is None:
        themes_dir = Path.cwd() / "themes"

    mappings_file = themes_dir / theme_name / "mappings.yaml"
    overrides = load_yaml_file(mappings_file, "css_overrides")
    if overrides is None:
        return {}
    if not isinstance(overrides, dict):
        raise ValueError(
            f"css_overrides in {mappings_file} must be a mapping, got {type(overrides).__name__}"
        )
    return overrides


def load_appeal_overrides_from_yaml(
    theme_name: str = "solarized", themes_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load sparse appeal-CSS color overrides from mappings.yaml for a theme.

    Keys are CSS custom property names (e.g. ``--action``). Values are palette
    attribute names, color-class refs (``Primary.B30``), or a mapping with both
    ``dark`` and ``light`` variants. Missing section yields ``{}``.

    Args:
        theme_name: Name of the theme to load. Defaults to "solarized".
        themes_dir: Directory where themes are stored. If None, uses default.

    Returns:
        Appeal override mapping, or empty dict if the section is absent.

    Raises:
        FileNotFoundError: If the theme directory or mappings.yaml file doesn't exist.
        ValueError: If the YAML file contains invalid syntax.
    """
    if themes_dir is None:
        themes_dir = Path.cwd() / "themes"

    mappings_file = themes_dir / theme_name / "mappings.yaml"
    overrides = load_yaml_file(mappings_file, "appeal_overrides")
    if overrides is None:
        return {}
    if not isinstance(overrides, dict):
        raise ValueError(
            f"appeal_overrides in {mappings_file} must be a mapping, got {type(overrides).__name__}"
        )
    return overrides


def load_theme_metadata_from_yaml(
    theme_name: str = "solarized", themes_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load theme metadata from theme.yaml file for a specific theme.

    Args:
        theme_name: Name of the theme to load. Defaults to "solarized".
        themes_dir: Directory where themes are stored. If None, uses default.

    Returns:
        Theme metadata loaded from the YAML file.

    Raises:
        FileNotFoundError: If the theme directory or theme.yaml file doesn't exist.
        ValueError: If the YAML file contains invalid syntax.
    """
    if themes_dir is None:
        themes_dir = Path.cwd() / "themes"

    yaml_file = themes_dir / theme_name / "theme.yaml"
    return load_yaml_file(yaml_file)
