"""
ThemeWeaver - Generate and export Spyder themes.

This package provides utilities for creating, managing, and exporting
Spyder-compatible themes with QDarkStyle integration.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("themeweaver")
except PackageNotFoundError:
    # Package not installed, fallback to version in pyproject.toml
    __version__ = "0.1.0"

__author__ = "Andres Conrado Montoya Acosta (@conradolandia)"

from themeweaver.core.palette import ThemePalettes, create_palettes
from themeweaver.core.spyder_package_exporter import SpyderPackageExporter
from themeweaver.core.theme_exporter import ThemeExporter
from themeweaver.core.theme_packager import ThemePackager
from themeweaver.core.yaml_loader import (
    load_color_mappings_from_yaml,
    load_colors_from_yaml,
    load_css_overrides_from_yaml,
    load_semantic_mappings_from_yaml,
    load_theme_metadata_from_yaml,
)

# Core functionality exports


__all__ = [
    # Core classes
    "ThemePalettes",
    "ThemeExporter",
    "ThemePackager",
    "SpyderPackageExporter",
    # Main functions
    "create_palettes",
    # YAML loaders
    "load_theme_metadata_from_yaml",
    "load_colors_from_yaml",
    "load_color_mappings_from_yaml",
    "load_css_overrides_from_yaml",
    "load_semantic_mappings_from_yaml",
    # Version info
    "__version__",
    "__author__",
]
