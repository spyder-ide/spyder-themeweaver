"""Tests for CSS default.css generation."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from themeweaver.core.colorsystem import get_color_classes_for_theme
from themeweaver.core.css_generator import (
    CSS_COLOR_MAP,
    CSS_STATIC,
    build_default_css,
    build_root,
    merge_css_color_map,
    palette_hex,
    resolve_css_color_value,
    resolve_palette_key,
    write_default_css,
)
from themeweaver.core.palette import create_palettes
from themeweaver.core.theme_exporter import ThemeExporter
from themeweaver.core.yaml_loader import load_css_overrides_from_yaml


def _css_var_value(css: str, name: str) -> str:
    match = re.search(
        rf"^\s*{re.escape(name)}\s*:\s*([^;]+);",
        css,
        re.MULTILINE,
    )
    assert match is not None, f"CSS variable {name} not found"
    return match.group(1).strip()


class TestPaletteHex:
    def test_plain_hex(self) -> None:
        class Pal:
            COLOR_TEXT_2 = "#C0C4C8"

        assert palette_hex(Pal, "COLOR_TEXT_2") == "#C0C4C8"

    def test_editor_tuple(self) -> None:
        class Pal:
            EDITOR_KEYWORD = ("#c670e0", False, False)

        assert palette_hex(Pal, "EDITOR_KEYWORD") == "#c670e0"

    def test_missing_attr(self) -> None:
        class Pal:
            pass

        with pytest.raises(AttributeError):
            palette_hex(Pal, "COLOR_TEXT_2")


class TestResolveCssColorValue:
    def test_palette_attribute(self) -> None:
        class Pal:
            COLOR_ACCENT_2 = "#aabbcc"

        assert resolve_css_color_value(Pal, "COLOR_ACCENT_2") == "#aabbcc"

    def test_color_class_ref(self) -> None:
        class Primary:
            B30 = "#112233"

        class Pal:
            pass

        assert (
            resolve_css_color_value(Pal, "Primary.B30", {"Primary": Primary})
            == "#112233"
        )

    def test_color_class_ref_requires_classes(self) -> None:
        class Pal:
            pass

        with pytest.raises(ValueError, match="requires color_classes"):
            resolve_css_color_value(Pal, "Primary.B30")


class TestResolvePaletteKey:
    def test_string_applies_to_both_variants(self) -> None:
        assert resolve_palette_key("COLOR_TEXT_1", "dark") == "COLOR_TEXT_1"
        assert resolve_palette_key("COLOR_TEXT_1", "light") == "COLOR_TEXT_1"

    def test_mapping_picks_variant(self) -> None:
        spec = {"dark": "COLOR_TEXT_1", "light": "COLOR_BACKGROUND_1"}
        assert resolve_palette_key(spec, "dark") == "COLOR_TEXT_1"
        assert resolve_palette_key(spec, "light") == "COLOR_BACKGROUND_1"

    def test_mapping_missing_variant(self) -> None:
        with pytest.raises(KeyError, match="missing 'light'"):
            resolve_palette_key({"dark": "COLOR_TEXT_1"}, "light")

    def test_mapping_unknown_key(self) -> None:
        with pytest.raises(ValueError, match="unknown variant keys"):
            resolve_palette_key(
                {"dark": "COLOR_TEXT_1", "light": "COLOR_TEXT_1", "sepia": "X"},
                "dark",
            )


class TestMergeCssColorMap:
    def test_no_overrides_returns_defaults(self) -> None:
        merged = merge_css_color_map(None)
        assert merged == CSS_COLOR_MAP
        assert merged is not CSS_COLOR_MAP

    def test_sparse_override_replaces_spec(self) -> None:
        merged = merge_css_color_map({"--hover-color": "COLOR_ACCENT_2"})
        assert merged["--hover-color"] == "COLOR_ACCENT_2"
        assert merged["--text-color"] == CSS_COLOR_MAP["--text-color"]

    def test_variant_override(self) -> None:
        merged = merge_css_color_map(
            {
                "--border-color": {
                    "dark": "Primary.B60",
                    "light": "Primary.B100",
                }
            }
        )
        assert merged["--border-color"] == {
            "dark": "Primary.B60",
            "light": "Primary.B100",
        }

    def test_unknown_key_rejected(self) -> None:
        with pytest.raises(ValueError, match="Unknown CSS override keys"):
            merge_css_color_map({"--not-a-real-var": "COLOR_TEXT_1"})

    def test_partial_variant_mapping_rejected(self) -> None:
        with pytest.raises(ValueError, match="missing"):
            merge_css_color_map({"--border-color": {"dark": "COLOR_BACKGROUND_5"}})


class TestBuildRoot:
    def test_mapped_vars_match_palette(self) -> None:
        palettes = create_palettes("spyder")
        for variant, palette in (("dark", palettes.dark), ("light", palettes.light)):
            root = build_root(palette, variant)
            for css_var, spec in CSS_COLOR_MAP.items():
                palette_key = resolve_palette_key(spec, variant)
                expected = palette_hex(palette, palette_key)
                assert _css_var_value(root, css_var) == expected, (
                    f"{variant} {css_var} should be {expected}"
                )

    def test_variant_specific_mapping(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setitem(
            CSS_COLOR_MAP,
            "--header-text-color",
            {"dark": "COLOR_TEXT_1", "light": "COLOR_BACKGROUND_1"},
        )
        palettes = create_palettes("spyder")
        dark_root = build_root(palettes.dark, "dark")
        light_root = build_root(palettes.light, "light")
        assert _css_var_value(dark_root, "--header-text-color") == palette_hex(
            palettes.dark, "COLOR_TEXT_1"
        )
        assert _css_var_value(light_root, "--header-text-color") == palette_hex(
            palettes.light, "COLOR_BACKGROUND_1"
        )

    def test_static_aliases_and_images(self) -> None:
        palettes = create_palettes("spyder")
        root = build_root(palettes.dark, "dark")
        assert _css_var_value(root, "--note-border") == CSS_STATIC["--note-border"]
        assert (
            _css_var_value(root, "--syn-string-alt") == CSS_STATIC["--syn-string-alt"]
        )
        assert (
            _css_var_value(root, "--img-arrow-down") == CSS_STATIC["--img-arrow-down"]
        )

    def test_overrides_apply_palette_and_class_refs(self) -> None:
        palettes = create_palettes("brutalism")
        color_classes = get_color_classes_for_theme("brutalism")
        color_map = merge_css_color_map(
            {
                "--hover-color": "COLOR_ACCENT_2",
                "--border-color": {
                    "dark": "Primary.B60",
                    "light": "Primary.B100",
                },
            }
        )
        dark_root = build_root(
            palettes.dark,
            "dark",
            color_map=color_map,
            color_classes=color_classes,
        )
        assert _css_var_value(dark_root, "--hover-color") == palette_hex(
            palettes.dark, "COLOR_ACCENT_2"
        )
        assert (
            _css_var_value(dark_root, "--border-color") == color_classes["Primary"].B60
        )
        assert _css_var_value(dark_root, "--text-color") == palette_hex(
            palettes.dark, "COLOR_TEXT_1"
        )


class TestBuildAndWrite:
    def test_build_includes_rules(self) -> None:
        palettes = create_palettes("spyder")
        css = build_default_css("dark", palettes.dark)
        assert ":root {" in css
        assert "body {" in css
        assert "div.title h1" in css

    def test_invalid_variant(self) -> None:
        palettes = create_palettes("spyder")
        with pytest.raises(ValueError, match="Unsupported CSS variant"):
            build_default_css("sepia", palettes.dark)

    def test_write_default_css(self, tmp_path: Path) -> None:
        palettes = create_palettes("spyder")
        variant_dir = tmp_path / "dark"
        out = write_default_css(variant_dir, "dark", palettes.dark)
        assert out == variant_dir / "default.css"
        assert out.is_file()
        assert "url(rc/arrow_down.png)" in out.read_text(encoding="utf-8")


class TestLoadCssOverrides:
    def test_missing_section_is_empty(self) -> None:
        assert load_css_overrides_from_yaml("spyder") == {}

    def test_brutalism_sparse_overrides(self) -> None:
        overrides = load_css_overrides_from_yaml("brutalism")
        assert overrides["--hover-color"] == "COLOR_ACCENT_2"
        assert overrides["--border-color"] == {
            "dark": "Primary.B60",
            "light": "Primary.B100",
        }


class TestExportIntegration:
    def test_spyder_export_writes_default_css(self, tmp_path: Path) -> None:
        exporter = ThemeExporter(build_dir=tmp_path / "build")
        result = exporter.export_theme("spyder")
        for variant, variant_dir in result.items():
            css_path = variant_dir / "default.css"
            assert css_path.is_file()
            text = css_path.read_text(encoding="utf-8")
            palette = create_palettes("spyder").get_palette(variant)
            assert palette is not None
            for css_var, spec in CSS_COLOR_MAP.items():
                palette_key = resolve_palette_key(spec, variant)
                assert _css_var_value(text, css_var) == palette_hex(
                    palette, palette_key
                )
            assert "url(rc/arrow_down.png)" in text
            assert "body {" in text

    def test_non_spyder_theme_uses_its_palette(self, tmp_path: Path) -> None:
        exporter = ThemeExporter(build_dir=tmp_path / "build")
        theme_name = "brutalism"
        result = exporter.export_theme(theme_name, variants=["dark"])
        css_path = result["dark"] / "default.css"
        assert css_path.is_file()
        text = css_path.read_text(encoding="utf-8")
        palette = create_palettes(theme_name).dark
        color_classes = get_color_classes_for_theme(theme_name)
        color_map = merge_css_color_map(load_css_overrides_from_yaml(theme_name))
        spyder_palette = create_palettes("spyder").dark
        differed = False
        for css_var, spec in color_map.items():
            source_key = resolve_palette_key(spec, "dark")
            theme_hex = resolve_css_color_value(palette, source_key, color_classes)
            assert _css_var_value(text, css_var) == theme_hex
            default_key = resolve_palette_key(CSS_COLOR_MAP[css_var], "dark")
            if theme_hex != palette_hex(spyder_palette, default_key):
                differed = True
        assert differed, "expected brutalism palette to differ from spyder"
        assert _css_var_value(text, "--hover-color") == palette_hex(
            palette, "COLOR_ACCENT_2"
        )
        assert _css_var_value(text, "--border-color") == color_classes["Primary"].B60
