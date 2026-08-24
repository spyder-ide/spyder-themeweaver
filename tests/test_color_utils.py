#!/usr/bin/env python3
"""
Test suite for themeweaver color utilities.

Run with: `python -m pytest tests/test_color_utils.py -v`
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestColorUtils:
    """Test core color utility functions."""

    def test_hex_rgb_conversion(self) -> None:
        """Test hex to RGB and RGB to hex conversion."""
        from themeweaver.color_utils import hex_to_rgb, rgb_to_hex

        # Test basic conversion
        rgb = hex_to_rgb("#ff0000")
        assert rgb == (255, 0, 0)

        # Test round trip
        hex_color = rgb_to_hex(rgb)
        assert hex_color.lower() == "#ff0000"

        # Test various formats
        assert hex_to_rgb("ff0000") == (255, 0, 0)  # Without #
        assert hex_to_rgb("#FF0000") == (255, 0, 0)  # Uppercase

    def test_hsv_conversion(self) -> None:
        """Test HSV color space conversion."""
        from themeweaver.color_utils import hsv_to_rgb, rgb_to_hsv

        # Test red color
        hsv = rgb_to_hsv((255, 0, 0))
        assert len(hsv) == 3
        assert hsv[1] > 0.9  # High saturation
        assert hsv[2] > 0.9  # High value

        # Test round trip
        rgb_back = hsv_to_rgb(hsv)
        assert all(
            abs(a - b) < 2 for a, b in zip(rgb_back, (255, 0, 0))
        )  # Allow small rounding errors

    def test_lch_conversion(self) -> None:
        """Test LCH color space conversion."""
        from themeweaver.color_utils import calculate_delta_e, lch_to_hex, rgb_to_lch

        # Test conversion
        lch = rgb_to_lch((255, 0, 0))
        assert len(lch) == 3
        assert lch[0] > 0  # Lightness should be positive

        # Test round trip
        hex_from_lch = lch_to_hex(*lch)
        assert hex_from_lch.startswith("#")

        # Test delta E calculation
        delta_e = calculate_delta_e("#ff0000", "#00ff00")
        assert isinstance(delta_e, (int, float))
        assert delta_e > 0

    def test_color_info(self) -> None:
        """Test color information retrieval."""
        from themeweaver.color_utils import get_color_info

        info = get_color_info("#ff0000")
        assert isinstance(info, dict)
        assert "hex" in info
        assert "rgb" in info
        assert info["hex"] == "#ff0000"
        assert info["rgb"] == (255, 0, 0)

    def test_relative_luminance(self) -> None:
        """Test WCAG relative luminance."""
        from themeweaver.color_utils import relative_luminance

        assert relative_luminance("#000000") == 0.0
        assert abs(relative_luminance("#FFFFFF") - 1.0) < 0.001
        assert 0 < relative_luminance("#808080") < 1

    def test_contrast_ratio(self) -> None:
        """Test WCAG contrast ratio."""
        from themeweaver.color_utils import contrast_ratio

        # Black on white = 21
        assert 20.9 < contrast_ratio("#000000", "#FFFFFF") < 21.1
        assert 20.9 < contrast_ratio("#FFFFFF", "#000000") < 21.1
        # Same color = 1
        assert abs(contrast_ratio("#FF0000", "#FF0000") - 1.0) < 0.01

    def test_blend_alpha(self) -> None:
        """Test alpha-over blending."""
        from themeweaver.color_utils import blend_alpha

        # 0% top = bottom
        assert blend_alpha("#000000", "#FFFFFF", 0) == "#000000"
        # 100% top = top
        assert blend_alpha("#000000", "#FFFFFF", 1) == "#FFFFFF"
        # 50% blend
        mid = blend_alpha("#000000", "#FFFFFF", 0.5)
        assert mid.startswith("#")
        assert mid != "#000000" and mid != "#FFFFFF"

    def test_adjust_for_contrast(self) -> None:
        """Test LCH-based contrast adjustment."""
        from themeweaver.color_utils import adjust_for_contrast, contrast_ratio

        # Gray on light gray - low contrast
        fg, bg = "#888888", "#CCCCCC"
        assert contrast_ratio(fg, bg) < 3
        adjusted = adjust_for_contrast(fg, bg, 3)
        assert adjusted is not None
        assert contrast_ratio(adjusted, bg) >= 2.99

    def test_invalid_hex_colors(self) -> None:
        """Reject malformed lengths and non-hexadecimal digits."""
        from themeweaver.color_utils import hex_to_rgb

        with pytest.raises(ValueError, match="6 characters"):
            hex_to_rgb("#123")
        with pytest.raises(ValueError, match="hex digits"):
            hex_to_rgb("#GGGGGG")

    def test_conversion_exception_fallbacks(self) -> None:
        """Use documented fallbacks when colorspacious rejects input."""
        from themeweaver.color_utils import color_utils

        with patch.object(
            color_utils.colorspacious, "cspace_convert", side_effect=ValueError
        ):
            assert color_utils.lch_to_hex(50, 20, 30) == "#808080"
            assert color_utils.rgb_to_lch((1, 2, 3)) == [50, 0, 0]
            assert color_utils.calculate_delta_e("#000000", "#FFFFFF") is None
            assert color_utils.is_lch_in_gamut(50, 20, 30) is False

        with patch.object(color_utils.colorspacious, "deltaE", side_effect=ValueError):
            assert color_utils.calculate_delta_e("#000000", "#FFFFFF") is None

    def test_color_info_lch_failure(self) -> None:
        """Return empty LCH fields when conversion raises."""
        from themeweaver.color_utils import color_utils

        with patch.object(color_utils, "rgb_to_lch", side_effect=TypeError):
            info = color_utils.get_color_info("#123456")

        assert info["lch"] is None
        assert info["lch_lightness"] is None

    def test_is_color_dark_luminance_fallback(self) -> None:
        """Use RGB luminance if LCH conversion raises."""
        from themeweaver.color_utils import color_utils

        with patch.object(color_utils, "rgb_to_lch", return_value=[20, 0, 0]):
            assert color_utils.is_color_dark("#123456")

        with patch.object(color_utils, "rgb_to_lch", side_effect=OverflowError):
            assert color_utils.is_color_dark("#000000")
            assert not color_utils.is_color_dark("#FFFFFF")

    def test_find_max_chroma_expands_initial_bound(self) -> None:
        """Expand the search bound when chroma 150 remains in gamut."""
        from themeweaver.color_utils import color_utils

        with patch.object(
            color_utils,
            "is_lch_in_gamut",
            side_effect=lambda lightness, chroma, hue: chroma < 200,
        ):
            result = color_utils.find_max_in_gamut_chroma(50, 30)

        assert 199 < result < 200

    def test_adjust_gamut_preserves_chroma_when_possible(self) -> None:
        """Select a nearby lightness that supports the requested chroma."""
        from themeweaver.color_utils import color_utils

        with patch.object(
            color_utils,
            "is_lch_in_gamut",
            side_effect=lambda lightness, chroma, hue: lightness == 51,
        ):
            assert color_utils.adjust_lch_to_gamut(50, 100, 30, preserve="chroma") == (
                51,
                100,
                30,
            )

    def test_empty_standard_deviation(self) -> None:
        """An empty sample has zero standard deviation."""
        from themeweaver.color_utils import calculate_std_dev

        assert calculate_std_dev([]) == 0

    def test_adjust_for_contrast_early_return_and_no_candidate(self) -> None:
        """Cover unchanged and unachievable contrast results."""
        from themeweaver.color_utils import color_utils

        assert color_utils.adjust_for_contrast("#000000", "#FFFFFF", 7) == "#000000"

        with patch.object(color_utils, "is_lch_in_gamut", return_value=False):
            assert color_utils.adjust_for_contrast("#888888", "#CCCCCC", 7) is None


class TestColorGeneration:
    """Test color generation functions."""

    def test_theme_optimized_colors(self) -> None:
        """Test theme-optimized color generation."""
        from themeweaver.color_utils import generate_theme_colors

        colors = generate_theme_colors(theme="dark", num_colors=5, start_hue=30)

        assert isinstance(colors, list)
        assert len(colors) == 5
        assert all(c.startswith("#") for c in colors)
        assert all(len(c) == 7 for c in colors)  # All should be 6-digit hex


class TestPaletteLoaders:
    """Test palette loading and validation."""

    def test_palette_validation(self) -> None:
        """Test palette data validation."""
        from themeweaver.color_utils import validate_palette_data

        # Valid palette
        valid_palette = {
            "name": "Test Palette",
            "colors": {"red": "#ff0000", "blue": "#0000ff"},
        }
        assert validate_palette_data(valid_palette) is True

        # Invalid palette (missing name) - should raise ValueError
        invalid_palette = {"colors": {"red": "#ff0000"}}
        try:
            validate_palette_data(invalid_palette)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected behavior

    def test_args_parsing(self) -> None:
        """Test parsing palette from command line arguments."""
        from themeweaver.color_utils import parse_palette_from_args

        args_palette = parse_palette_from_args(["red=#ff0000", "blue=#0000ff"])
        assert isinstance(args_palette, dict)
        assert "colors" in args_palette
        assert args_palette["colors"]["red"] == "#ff0000"
        assert args_palette["colors"]["blue"] == "#0000ff"


class TestCoreModules:
    """Test core themeweaver modules."""

    def test_colorsystem_import(self) -> None:
        """Test that colorsystem classes can be imported and have expected structure."""
        from themeweaver.core.colorsystem import get_color_classes_for_theme

        # Get color classes dynamically
        color_classes = get_color_classes_for_theme("solarized")
        Primary = color_classes["Primary"]
        Secondary = color_classes["Secondary"]
        Success = color_classes["Success"]
        Error = color_classes["Error"]
        Warning = color_classes["Warning"]

        # Test that classes have color attributes (expect them to start with #)
        color_classes_list = [Primary, Secondary, Success, Error, Warning]
        for color_class in color_classes_list:
            attrs = [
                attr
                for attr in dir(color_class)
                if not attr.startswith("_")
                and isinstance(getattr(color_class, attr), str)
            ]
            hex_attrs = [
                getattr(color_class, attr)
                for attr in attrs
                if getattr(color_class, attr).startswith("#")
            ]
            assert len(hex_attrs) > 0, (
                f"{color_class.__name__} should have hex color attributes"
            )

    def test_theme_palette_imports(self) -> None:
        """Test that theme and palette modules can be imported."""
        from themeweaver.core.palette import ThemePalettes, create_palettes

        # Test that we can create palettes
        palettes = create_palettes("solarized")
        assert palettes is not None
        assert isinstance(palettes, ThemePalettes)


class TestColorAnalysis:
    """Test color analysis functions."""

    def test_chromatic_distances(self) -> None:
        """Test chromatic distance analysis."""
        from themeweaver.color_utils import analyze_chromatic_distances

        test_colors = ["#ff0000", "#00ff00", "#0000ff"]
        distances = analyze_chromatic_distances(test_colors, "Test Group")
        # This function returns a list of distance dictionaries
        assert isinstance(distances, list)
        assert len(distances) == 2  # 3 colors -> 2 distance measurements
        assert all("delta_e" in d for d in distances)


if __name__ == "__main__":
    # Run tests with pytest
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)
