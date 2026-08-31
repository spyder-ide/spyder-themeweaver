"""Tests for CSS default.css generation."""

from __future__ import annotations

import base64
import re
from pathlib import Path

import pytest

from themeweaver.core.colorsystem import get_color_classes_for_theme
from themeweaver.core.css_generator import (
    _ARROW_FILES,
    APPEAL_COLOR_MAP,
    APPEAL_STATIC,
    CSS_COLOR_MAP,
    CSS_STATIC,
    arrow_image_data_uris,
    build_appeal_css,
    build_default_css,
    build_root,
    merge_appeal_color_map,
    merge_css_color_map,
    palette_hex,
    resolve_css_color_value,
    resolve_palette_key,
    write_appeal_css,
    write_default_css,
)
from themeweaver.core.palette import create_palettes
from themeweaver.core.theme_exporter import ThemeExporter
from themeweaver.core.yaml_loader import (
    load_appeal_overrides_from_yaml,
    load_css_overrides_from_yaml,
)

_STUB_PNG = b"\x89PNG\r\nstub"


def _write_stub_arrow_pngs(rc_dir: Path, content: bytes = _STUB_PNG) -> None:
    rc_dir.mkdir(parents=True, exist_ok=True)
    for filename in _ARROW_FILES.values():
        (rc_dir / filename).write_bytes(content)


def _css_var_value(css: str, name: str) -> str:
    match = re.search(
        rf"^\s*{re.escape(name)}\s*:\s*(.+);\s*$",
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
        with pytest.raises(ValueError, match="Unknown override keys"):
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
        palettes = create_palettes("spyder")
        color_classes = get_color_classes_for_theme("spyder")
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


class TestMergeAppealColorMap:
    def test_no_overrides_returns_defaults(self) -> None:
        merged = merge_appeal_color_map(None)
        assert merged == APPEAL_COLOR_MAP
        assert merged is not APPEAL_COLOR_MAP

    def test_sparse_override_replaces_spec(self) -> None:
        merged = merge_appeal_color_map({"--link": "COLOR_ACCENT_2"})
        assert merged["--link"] == "COLOR_ACCENT_2"
        assert merged["--foreground"] == APPEAL_COLOR_MAP["--foreground"]

    def test_variant_override(self) -> None:
        merged = merge_appeal_color_map(
            {
                "--border-primary": {
                    "dark": "Primary.B60",
                    "light": "Primary.B100",
                }
            }
        )
        assert merged["--border-primary"] == {
            "dark": "Primary.B60",
            "light": "Primary.B100",
        }

    def test_unknown_key_rejected(self) -> None:
        with pytest.raises(ValueError, match="Unknown override keys"):
            merge_appeal_color_map({"--not-a-real-var": "COLOR_TEXT_1"})

    def test_partial_variant_mapping_rejected(self) -> None:
        with pytest.raises(ValueError, match="missing"):
            merge_appeal_color_map({"--link": {"dark": "COLOR_ACCENT_1"}})


class TestArrowImageDataUris:
    def test_encodes_png_bytes(self, tmp_path: Path) -> None:
        rc_dir = tmp_path / "rc"
        _write_stub_arrow_pngs(rc_dir)
        uris = arrow_image_data_uris(rc_dir)
        assert list(uris) == list(_ARROW_FILES)
        encoded = uris["--img-arrow-down"]
        assert encoded.startswith('url("data:image/png;base64,')
        payload = encoded.removeprefix('url("data:image/png;base64,').removesuffix('")')
        assert base64.standard_b64decode(payload) == _STUB_PNG

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="arrow_down.png"):
            arrow_image_data_uris(tmp_path)


class TestBuildAppeal:
    def test_mapped_vars_match_palette(self) -> None:
        palettes = create_palettes("spyder")
        color_classes = get_color_classes_for_theme("spyder")
        for variant, palette in (("dark", palettes.dark), ("light", palettes.light)):
            css = build_appeal_css(variant, palette, color_classes=color_classes)
            assert f'[data-mode="{variant}"] {{' in css
            for css_var, spec in APPEAL_COLOR_MAP.items():
                source_key = resolve_palette_key(spec, variant)
                expected = resolve_css_color_value(palette, source_key, color_classes)
                assert _css_var_value(css, css_var) == expected, (
                    f"{variant} {css_var} should be {expected}"
                )
            for css_var, value in APPEAL_STATIC.items():
                assert _css_var_value(css, css_var) == value

    def test_invalid_variant(self) -> None:
        palettes = create_palettes("spyder")
        with pytest.raises(ValueError, match="Unsupported CSS variant"):
            build_appeal_css("sepia", palettes.dark)

    def test_write_appeal_css_embeds_arrow_data_uris(self, tmp_path: Path) -> None:
        palettes = create_palettes("spyder")
        color_classes = get_color_classes_for_theme("spyder")
        variant_dir = tmp_path / "dark"
        rc_dir = variant_dir / "rc"
        _write_stub_arrow_pngs(rc_dir)
        out = write_appeal_css(
            variant_dir,
            "dark",
            palettes.dark,
            color_classes=color_classes,
        )
        assert out == variant_dir / "appeal.css"
        text = out.read_text(encoding="utf-8")
        assert '[data-mode="dark"]' in text
        assert "url(rc/" not in text
        expected = arrow_image_data_uris(rc_dir)
        for css_var, value in expected.items():
            assert _css_var_value(text, css_var) == value

    def test_write_appeal_css_requires_rc_pngs(self, tmp_path: Path) -> None:
        palettes = create_palettes("spyder")
        with pytest.raises(FileNotFoundError, match="arrow_down.png"):
            write_appeal_css(tmp_path / "dark", "dark", palettes.dark)

    def test_build_appeal_css_embeds_from_rc_dir(self, tmp_path: Path) -> None:
        palettes = create_palettes("spyder")
        color_classes = get_color_classes_for_theme("spyder")
        rc_dir = tmp_path / "rc"
        _write_stub_arrow_pngs(rc_dir)
        css = build_appeal_css(
            "dark",
            palettes.dark,
            color_classes=color_classes,
            rc_dir=rc_dir,
        )
        expected = arrow_image_data_uris(rc_dir)
        assert _css_var_value(css, "--img-arrow-down") == expected["--img-arrow-down"]
        assert "url(rc/" not in css

    def test_overrides_apply_palette_and_class_refs(self) -> None:
        palettes = create_palettes("spyder")
        color_classes = get_color_classes_for_theme("spyder")
        color_map = merge_appeal_color_map(
            {
                "--link": "COLOR_ACCENT_2",
                "--border-primary": {
                    "dark": "Primary.B60",
                    "light": "Primary.B100",
                },
            }
        )
        dark_css = build_appeal_css(
            "dark",
            palettes.dark,
            color_map=color_map,
            color_classes=color_classes,
        )
        assert _css_var_value(dark_css, "--link") == palette_hex(
            palettes.dark, "COLOR_ACCENT_2"
        )
        assert (
            _css_var_value(dark_css, "--border-primary") == color_classes["Primary"].B60
        )
        assert _css_var_value(dark_css, "--foreground") == palette_hex(
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

    def test_sparse_overrides_from_yaml(self, tmp_path: Path) -> None:
        theme_dir = tmp_path / "fixture-theme"
        theme_dir.mkdir()
        (theme_dir / "mappings.yaml").write_text(
            "\n".join(
                [
                    "css_overrides:",
                    "  --hover-color: COLOR_ACCENT_2",
                    "  --border-color:",
                    "    dark: Primary.B60",
                    "    light: Primary.B100",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        overrides = load_css_overrides_from_yaml("fixture-theme", themes_dir=tmp_path)
        assert overrides["--hover-color"] == "COLOR_ACCENT_2"
        assert overrides["--border-color"] == {
            "dark": "Primary.B60",
            "light": "Primary.B100",
        }


class TestLoadAppealOverrides:
    def test_missing_section_is_empty(self) -> None:
        assert load_appeal_overrides_from_yaml("spyder") == {}

    def test_sparse_overrides_from_yaml(self, tmp_path: Path) -> None:
        theme_dir = tmp_path / "fixture-theme"
        theme_dir.mkdir()
        (theme_dir / "mappings.yaml").write_text(
            "\n".join(
                [
                    "appeal_overrides:",
                    "  --link: COLOR_ACCENT_2",
                    "  --border-primary:",
                    "    dark: Primary.B60",
                    "    light: Primary.B100",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        overrides = load_appeal_overrides_from_yaml(
            "fixture-theme", themes_dir=tmp_path
        )
        assert overrides["--link"] == "COLOR_ACCENT_2"
        assert overrides["--border-primary"] == {
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

            appeal_path = variant_dir / "appeal.css"
            assert appeal_path.is_file()
            appeal_text = appeal_path.read_text(encoding="utf-8")
            assert f'[data-mode="{variant}"]' in appeal_text
            color_classes = get_color_classes_for_theme("spyder")
            for css_var, spec in APPEAL_COLOR_MAP.items():
                source_key = resolve_palette_key(spec, variant)
                assert _css_var_value(appeal_text, css_var) == resolve_css_color_value(
                    palette, source_key, color_classes
                )
            expected_arrows = arrow_image_data_uris(variant_dir / "rc")
            for css_var, value in expected_arrows.items():
                assert _css_var_value(appeal_text, css_var) == value
            assert "url(rc/" not in appeal_text

    def test_non_spyder_theme_uses_its_palette(self, tmp_path: Path) -> None:
        exporter = ThemeExporter(build_dir=tmp_path / "build")
        # Any non-spyder theme; do not assert theme-specific css_overrides.
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
        assert differed, f"expected {theme_name} palette to differ from spyder"

    def test_appeal_overrides_from_yaml(self, tmp_path: Path) -> None:
        theme_dir = tmp_path / "themes" / "fixture-theme"
        theme_dir.mkdir(parents=True)
        (theme_dir / "theme.yaml").write_text(
            "\n".join(
                [
                    "name: fixture-theme",
                    "variants:",
                    "  dark: true",
                    "  light: true",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (theme_dir / "colorsystem.yaml").write_text(
            (Path.cwd() / "themes" / "spyder" / "colorsystem.yaml").read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
        (theme_dir / "mappings.yaml").write_text(
            (Path.cwd() / "themes" / "spyder" / "mappings.yaml").read_text(
                encoding="utf-8"
            )
            + "\nappeal_overrides:\n  --link: COLOR_ACCENT_2\n",
            encoding="utf-8",
        )
        exporter = ThemeExporter(
            build_dir=tmp_path / "build", themes_dir=tmp_path / "themes"
        )
        result = exporter.export_theme("fixture-theme", variants=["dark"])
        appeal_text = (result["dark"] / "appeal.css").read_text(encoding="utf-8")
        palette = create_palettes("fixture-theme", themes_dir=tmp_path / "themes").dark
        assert _css_var_value(appeal_text, "--link") == palette_hex(
            palette, "COLOR_ACCENT_2"
        )
