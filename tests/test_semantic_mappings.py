#!/usr/bin/env python3
"""
Tests for semantic mappings and palette creation in themeweaver.

Tests the semantic mappings functionality including:
- Loading semantic mappings from YAML
- Creating palette classes dynamically
- Error handling for invalid mappings
- Integration with color classes

Run with: `python -m pytest tests/test_semantic_mappings.py -v`
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from themeweaver.core.colorsystem import (
    create_palette_class,
    get_color_classes_for_theme,
    load_semantic_mappings_from_yaml,
)


class TestSemanticMappings:
    """Test cases for semantic mappings functionality."""

    def test_load_semantic_mappings_success(self) -> None:
        """Test loading semantic mappings from YAML."""
        semantic_mappings = load_semantic_mappings_from_yaml()

        # Check that we have both dark and light mappings
        assert "dark" in semantic_mappings
        assert "light" in semantic_mappings

        # Check some key mappings exist
        dark_mappings = semantic_mappings["dark"]
        light_mappings = semantic_mappings["light"]

        assert "COLOR_BACKGROUND_1" in dark_mappings
        assert "COLOR_TEXT_1" in dark_mappings
        assert "COLOR_ACCENT_1" in dark_mappings

        assert "COLOR_BACKGROUND_1" in light_mappings
        assert "COLOR_TEXT_1" in light_mappings
        assert "COLOR_ACCENT_1" in light_mappings

    def test_load_semantic_mappings_with_theme_name(self) -> None:
        """Test loading semantic mappings with explicit theme name."""
        semantic_mappings = load_semantic_mappings_from_yaml("solarized")

        assert "dark" in semantic_mappings
        assert "light" in semantic_mappings

        # Verify some expected mappings
        dark_mappings = semantic_mappings["dark"]
        assert dark_mappings["COLOR_BACKGROUND_1"] == "Primary.B10"
        assert dark_mappings["COLOR_TEXT_1"] == "Primary.B130"
        assert dark_mappings["COLOR_ACCENT_1"] == "Secondary.B10"

        light_mappings = semantic_mappings["light"]
        assert light_mappings["COLOR_BACKGROUND_1"] == "Primary.B140"
        assert light_mappings["COLOR_TEXT_1"] == "Primary.B20"
        assert light_mappings["COLOR_ACCENT_1"] == "Secondary.B80"

    def test_load_semantic_mappings_nonexistent_theme(self) -> None:
        """Test loading semantic mappings for non-existent theme."""
        with pytest.raises(FileNotFoundError):
            load_semantic_mappings_from_yaml("nonexistent")

    def test_create_palette_class_dark(self) -> None:
        """Test creating a dark palette class dynamically."""
        from qdarkstyle.palette import Palette  # type: ignore

        # Get actual color classes
        color_classes = get_color_classes_for_theme("solarized")
        Primary = color_classes["Primary"]
        Secondary = color_classes["Secondary"]

        # Mock semantic mappings
        semantic_mappings = {
            "COLOR_BACKGROUND_1": "Primary.B10",
            "COLOR_TEXT_1": "Primary.B130",
            "COLOR_ACCENT_1": "Secondary.B10",
        }

        # Create palette class
        DarkPalette = create_palette_class(
            "dark", semantic_mappings, color_classes, Palette
        )

        # Verify class properties
        assert DarkPalette.ID == "dark"
        assert DarkPalette.COLOR_BACKGROUND_1 == Primary.B10
        assert DarkPalette.COLOR_TEXT_1 == Primary.B130
        assert DarkPalette.COLOR_ACCENT_1 == Secondary.B10

        # Verify it's a proper subclass
        assert issubclass(DarkPalette, Palette)

    def test_create_palette_class_light(self) -> None:
        """Test creating a light palette class dynamically."""
        from qdarkstyle.palette import Palette  # type: ignore

        # Get actual color classes
        color_classes = get_color_classes_for_theme("solarized")
        Primary = color_classes["Primary"]
        Secondary = color_classes["Secondary"]

        # Mock semantic mappings
        semantic_mappings = {
            "COLOR_BACKGROUND_1": "Primary.B140",
            "COLOR_TEXT_1": "Primary.B20",
            "COLOR_ACCENT_1": "Secondary.B80",
        }

        # Create palette class
        LightPalette = create_palette_class(
            "light", semantic_mappings, color_classes, Palette
        )

        # Verify class properties
        assert LightPalette.ID == "light"
        assert LightPalette.COLOR_BACKGROUND_1 == Primary.B140
        assert LightPalette.COLOR_TEXT_1 == Primary.B20
        assert LightPalette.COLOR_ACCENT_1 == Secondary.B80

        # Verify it's a proper subclass
        assert issubclass(LightPalette, Palette)

    def test_create_palette_class_with_numeric_values(self) -> None:
        """Test creating palette class with numeric values like OPACITY_TOOLTIP."""
        from qdarkstyle.palette import Palette  # type: ignore

        # Get actual color classes
        color_classes = get_color_classes_for_theme("solarized")
        Primary = color_classes["Primary"]

        # Mock semantic mappings including numeric value
        semantic_mappings = {
            "COLOR_BACKGROUND_1": "Primary.B10",
            "OPACITY_TOOLTIP": 230,
        }

        # Create palette class
        DarkPalette = create_palette_class(
            "dark", semantic_mappings, color_classes, Palette
        )

        # Verify both color and numeric properties
        assert DarkPalette.COLOR_BACKGROUND_1 == Primary.B10
        assert DarkPalette.OPACITY_TOOLTIP == 230

    def test_create_palette_class_invalid_color_reference(self) -> None:
        """Test creating palette class with invalid color reference."""
        from qdarkstyle.palette import Palette  # type: ignore

        # Get actual color classes
        color_classes = get_color_classes_for_theme("solarized")
        _Primary = color_classes["Primary"]

        # Mock semantic mappings with invalid reference
        semantic_mappings = {
            "COLOR_BACKGROUND_1": "NonExistent.B10",
        }

        # Should raise ValueError for invalid reference
        with pytest.raises(ValueError, match="Color class 'NonExistent' not found"):
            create_palette_class("dark", semantic_mappings, color_classes, Palette)

    def test_create_palette_class_invalid_attribute(self) -> None:
        """Test creating palette class with invalid attribute reference."""
        from qdarkstyle.palette import Palette  # type: ignore

        # Get actual color classes
        color_classes = get_color_classes_for_theme("solarized")
        _Primary = color_classes["Primary"]

        # Mock semantic mappings with invalid attribute
        semantic_mappings = {
            "COLOR_BACKGROUND_1": "Primary.B999",
        }

        # Should raise ValueError for invalid attribute
        with pytest.raises(ValueError, match="Attribute 'B999' not found"):
            create_palette_class("dark", semantic_mappings, color_classes, Palette)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
