"""Targeted tests for remaining executable branches."""

from __future__ import annotations

import importlib
from contextlib import nullcontext
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest


def test_package_version_fallback() -> None:
    import themeweaver

    with patch(
        "importlib.metadata.version", side_effect=PackageNotFoundError("themeweaver")
    ):
        reloaded = importlib.reload(themeweaver)
        assert reloaded.__version__ == "0.1.0"
    importlib.reload(themeweaver)


def test_duplicate_gradient_details() -> None:
    from themeweaver.color_utils.interpolation_methods import (
        validate_gradient_uniqueness,
    )

    valid, details = validate_gradient_uniqueness(["#000000", "#FFFFFF", "#000000"])
    assert valid is False
    assert details["indices"] == [(0, 2)]


def test_dev_sync_helper_and_error_branches(tmp_path: Path) -> None:
    from themeweaver.cli.commands import dev_sync

    assert dev_sync._workspace_root().name == "themeweaver"
    assert dev_sync._default_package_root().parts[-2:] == (
        "spyder_themes",
        "spyder_themes",
    )

    package_root = tmp_path / "package"
    package_root.mkdir()
    (package_root / "__init__.py").write_text(
        "OTHER = ['x']\nTHEMES = ('not', 'a', 'list')\n", encoding="utf-8"
    )
    assert dev_sync._theme_registered(package_root, "x") is False

    source = tmp_path / "build" / "broken"
    source.mkdir(parents=True)
    with pytest.raises(ValueError, match="missing required files"):
        dev_sync.sync_theme_to_package(tmp_path / "build", package_root, "broken")


def test_dev_sync_nondefault_export_options_and_warning(tmp_path: Path) -> None:
    from themeweaver.cli.commands import dev_sync

    package_root = tmp_path / "package"
    package_root.mkdir()
    (package_root / "__init__.py").write_text("THEMES = []\n", encoding="utf-8")
    args = SimpleNamespace(
        theme=["sample"],
        theme_dir=str(tmp_path / "themes"),
        build_dir=str(tmp_path / "build"),
        package_dir=str(package_root),
        skip_export=False,
        compile_for="pyqt6",
        generate_palette_images=True,
    )
    exporter = Mock()
    with (
        patch.object(dev_sync, "ThemeExporter", return_value=exporter),
        patch.object(dev_sync, "operation_context", return_value=nullcontext()),
        patch.object(
            dev_sync,
            "sync_theme_to_package",
            return_value=package_root / "sample",
        ),
        patch.object(dev_sync._logger, "warning") as warning,
    ):
        dev_sync.cmd_dev_sync(args)

    exporter.export_theme.assert_called_once_with(
        "sample", compile_for="pyqt6", generate_palette_images=True
    )
    warning.assert_called_once()


def test_theme_utils_custom_variants_and_mapping_shapes(tmp_path: Path) -> None:
    from themeweaver.core import theme_utils

    metadata = theme_utils.generate_theme_metadata(
        "sample", None, None, "author", None, variants=["dark"]
    )
    assert metadata["variants"] == {"dark": True}
    assert metadata["tags"] == ["dark"]

    template = {
        "nested": {
            "primary": "Primary.B10",
            "secondary": "Secondary.B20",
            "literal": "Literal",
            "primary_format": ["Primary.B30", True, False],
            "secondary_format": ["Secondary.B40", False, True],
            "short_list": ["unchanged"],
            "numeric": 42,
        }
    }
    colors = {
        "_palette_names": {"primary": "One", "secondary": "Two"},
    }
    with patch.object(theme_utils, "get_mappings_template", return_value=template):
        mappings = theme_utils.generate_mappings(colors)
    nested = mappings["semantic_mappings"]["nested"]
    assert nested["primary"] == "One.B10"
    assert nested["secondary"] == "Two.B20"
    assert nested["primary_format"][0] == "One.B30"
    assert nested["secondary_format"][0] == "Two.B40"
    assert nested["short_list"] == ["unchanged"]
    assert nested["numeric"] == 42

    output = tmp_path / "lists.yaml"
    theme_utils.write_yaml_file(output, {"short": [1, 2], "long": list(range(7))})
    text = output.read_text(encoding="utf-8")
    assert "short: [1, 2]" in text
    assert "long:" in text


def test_colorsystem_remaining_reference_errors_and_dict() -> None:
    from themeweaver.core.colorsystem import _resolve_color_reference

    class Primary:
        B10 = "#123456"

    classes = {"Primary": Primary}
    assert _resolve_color_reference(
        {"color": "Primary.B10", "bold": True}, classes
    ) == ("#123456", True, False)
    with pytest.raises(ValueError, match="Invalid color dict"):
        _resolve_color_reference({"bold": True}, classes)
    with pytest.raises(ValueError, match="Invalid color reference"):
        _resolve_color_reference(object(), classes)


def test_colorsystem_missing_mapped_palette() -> None:
    from themeweaver.core import colorsystem

    with (
        patch.object(colorsystem, "load_colors_from_yaml", return_value={}),
        patch.object(
            colorsystem,
            "load_color_mappings_from_yaml",
            return_value={"Primary": "Missing"},
        ),
        pytest.raises(ValueError, match="Palette 'Missing' not found"),
    ):
        colorsystem.get_color_classes_for_theme("sample")


def test_syntax_schema_custom_format_and_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from themeweaver.core import syntax_schema

    formatted = syntax_schema._default_formatted_value(
        "keyword", {"keyword": {"italic": True}}, "Syntax.B10"
    )
    assert formatted == ["Syntax.B10", False, True]

    monkeypatch.setattr(
        syntax_schema,
        "EDITOR_MAPPING_SPECS",
        (syntax_schema.EditorMappingSpec("BROKEN", "syntax_plain"),),
    )
    with pytest.raises(ValueError, match="Missing slot_index"):
        syntax_schema.build_editor_syntax_mappings("dark")

    monkeypatch.setattr(
        syntax_schema,
        "EDITOR_MAPPING_SPECS",
        (syntax_schema.EditorMappingSpec("BROKEN", "syntax_plain", slot_index=999),),
    )
    with pytest.raises(ValueError, match="Slot index out of range"):
        syntax_schema.build_editor_syntax_mappings("dark")

    monkeypatch.setattr(
        syntax_schema,
        "EDITOR_MAPPING_SPECS",
        (syntax_schema.EditorMappingSpec("BROKEN", "syntax_formatted", slot_index=0),),
    )
    with pytest.raises(ValueError, match="Missing format_element"):
        syntax_schema.build_editor_syntax_mappings("dark")


def test_palette_container_and_creation_errors() -> None:
    from themeweaver.core import palette

    assert palette.ThemePalettes().get_palette("other") is None

    common = (
        patch.object(palette, "get_color_classes_for_theme", return_value={}),
        patch.object(palette, "create_palette_class", return_value=type("P", (), {})),
    )
    with (
        patch.object(palette, "load_theme_metadata_from_yaml", return_value={}),
        pytest.raises(ValueError, match="No variants specified"),
    ):
        palette.create_palettes("sample")

    with (
        patch.object(
            palette,
            "load_theme_metadata_from_yaml",
            return_value={"variants": {"dark": True}},
        ),
        patch.object(palette, "load_semantic_mappings_from_yaml", return_value={}),
        patch.object(palette, "get_color_classes_for_theme", return_value={}),
        pytest.raises(ValueError, match="no dark semantic mappings"),
    ):
        palette.create_palettes("sample")

    with (
        patch.object(
            palette,
            "load_theme_metadata_from_yaml",
            return_value={"variants": {"light": True}},
        ),
        patch.object(palette, "load_semantic_mappings_from_yaml", return_value={}),
        patch.object(palette, "get_color_classes_for_theme", return_value={}),
        pytest.raises(ValueError, match="no light semantic mappings"),
    ):
        palette.create_palettes("sample")

    with (
        patch.object(
            palette,
            "load_theme_metadata_from_yaml",
            return_value={"variants": {"dark": False, "light": False}},
        ),
        patch.object(palette, "load_semantic_mappings_from_yaml", return_value={}),
        common[0],
        common[1],
        pytest.raises(ValueError, match="no enabled variants"),
    ):
        palette.create_palettes("sample")


def test_yaml_loader_errors_and_css_override_validation(tmp_path: Path) -> None:
    from themeweaver.core import yaml_loader

    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError, match="YAML file not found"):
        yaml_loader.load_yaml_file(missing)

    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("value: [\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Error parsing YAML"):
        yaml_loader.load_yaml_file(invalid)

    with patch.object(yaml_loader, "load_yaml_file", return_value=None):
        assert (
            yaml_loader.load_css_overrides_from_yaml("sample", themes_dir=tmp_path)
            == {}
        )
        assert (
            yaml_loader.load_appeal_overrides_from_yaml("sample", themes_dir=tmp_path)
            == {}
        )
        assert (
            yaml_loader.load_pydoc_overrides_from_yaml("sample", themes_dir=tmp_path)
            == {}
        )
    with (
        patch.object(yaml_loader, "load_yaml_file", return_value=[]),
        pytest.raises(ValueError, match="must be a mapping"),
    ):
        yaml_loader.load_css_overrides_from_yaml("sample", themes_dir=tmp_path)
    with (
        patch.object(yaml_loader, "load_yaml_file", return_value=[]),
        pytest.raises(ValueError, match="must be a mapping"),
    ):
        yaml_loader.load_appeal_overrides_from_yaml("sample", themes_dir=tmp_path)
    with (
        patch.object(yaml_loader, "load_yaml_file", return_value=[]),
        pytest.raises(ValueError, match="must be a mapping"),
    ):
        yaml_loader.load_pydoc_overrides_from_yaml("sample", themes_dir=tmp_path)


def test_rules_loader_remaining_branches(tmp_path: Path) -> None:
    from themeweaver.contrast.rules_loader import _expand_rules, load_rules

    assert _expand_rules({"literal": 3}) == {"literal": 3}
    with pytest.raises(FileNotFoundError, match="Rules file not found"):
        load_rules("dark", tmp_path)
    (tmp_path / "rules_dark.yaml").write_text("", encoding="utf-8")
    assert load_rules("dark", tmp_path) == {}


def test_color_resolver_remaining_branches() -> None:
    from themeweaver.contrast import color_resolver

    palettes = Mock()
    palettes.get_palette.return_value = None
    with (
        patch.object(color_resolver, "create_palettes", return_value=palettes),
        pytest.raises(ValueError, match="does not support variant"),
    ):
        color_resolver.resolve_theme_colors("sample", "dark")

    colors = {"A": "#000000", "B": "#FFFFFF"}
    assert color_resolver.get_color_for_rule(colors, {}, "unknown") is None
    assert color_resolver.get_color_for_rule(colors, {}, "fg") is None
    assert (
        color_resolver.get_color_for_rule(
            colors,
            {"bg": ["A", "MISSING"], "bg_blend": 0.5},
            "bg",
        )
        is None
    )
    with patch.object(color_resolver, "blend_alpha", return_value="#808080"):
        assert (
            color_resolver.get_color_for_rule(
                colors,
                {"bg": ["A", "B"], "bg_blend": 0.5},
                "bg",
            )
            == "#808080"
        )


def test_theme_generator_variants_and_legacy_data(tmp_path: Path) -> None:
    from themeweaver.core import theme_generator

    generator = theme_generator.ThemeGenerator(tmp_path)
    legacy = {"variants": ["dark"], "Primary": {"B10": "#000000"}}
    with (
        patch.object(
            theme_generator, "generate_mappings", return_value={"map": 1}
        ) as gen,
        patch.object(theme_generator, "write_yaml_file", return_value="written"),
    ):
        files = generator.generate_theme_from_data("sample", legacy)
    gen.assert_called_once_with(legacy)
    assert set(files) == {"theme.yaml", "colorsystem.yaml", "mappings.yaml"}


def test_spyder_init_generation_for_single_variants(tmp_path: Path) -> None:
    from themeweaver.core import spyder_generator

    generator = spyder_generator.SpyderFileGenerator()
    for has_dark, expected in [
        (True, "SpyderPaletteDark"),
        (False, "SpyderPaletteLight"),
    ]:
        palettes = SimpleNamespace(has_dark=has_dark, has_light=not has_dark)
        with patch.object(spyder_generator, "create_palettes", return_value=palettes):
            generator.generate_theme_init_file(
                "sample", {}, tmp_path, themes_dir=tmp_path
            )
        assert expected in (tmp_path / "__init__.py").read_text(encoding="utf-8")


def test_theme_exporter_skip_variant_and_successful_export_all(tmp_path: Path) -> None:
    from themeweaver.core import theme_exporter

    themes_dir = tmp_path / "themes"
    (themes_dir / "sample").mkdir(parents=True)
    exporter = object.__new__(theme_exporter.ThemeExporter)
    exporter.themes_dir = themes_dir
    exporter.build_dir = tmp_path / "build"
    exporter.asset_exporter = Mock()
    exporter.spyder_generator = Mock()
    palettes = Mock()
    palettes.get_palette.return_value = None
    with (
        patch.object(
            theme_exporter,
            "load_theme_metadata_from_yaml",
            return_value={"variants": {"dark": True}},
        ),
        patch.object(theme_exporter, "create_palettes", return_value=palettes),
        patch.object(theme_exporter, "load_css_overrides_from_yaml", return_value={}),
        patch.object(
            theme_exporter, "load_appeal_overrides_from_yaml", return_value={}
        ),
        patch.object(theme_exporter, "load_pydoc_overrides_from_yaml", return_value={}),
        patch.object(theme_exporter, "merge_css_color_map", return_value={}),
        patch.object(theme_exporter, "merge_appeal_color_map", return_value={}),
        patch.object(theme_exporter, "merge_pydoc_color_map", return_value={}),
        patch.object(theme_exporter, "get_color_classes_for_theme", return_value={}),
    ):
        assert exporter.export_theme("sample") == {}

    with patch.object(exporter, "export_theme", return_value={"dark": tmp_path}):
        assert exporter.export_all_themes() == {"sample": {"dark": tmp_path}}


def test_palette_generator_remaining_paths() -> None:
    from themeweaver.color_utils import palette_generators

    with (
        patch.object(palette_generators, "is_lch_in_gamut", return_value=True),
        patch.object(palette_generators, "lch_to_hex", return_value="#123456"),
    ):
        _, light = palette_generators._generate_group_palettes("#654321", 50, 30, 10, 1)
    assert light["B10"] == "#123456"
    assert palette_generators._find_dominant_hues([42.0]) == [42.0]

    analysis = {"avg_lightness": 50, "avg_chroma": 40, "dominant_hues": []}
    with (
        patch.object(palette_generators, "is_lch_in_gamut", return_value=True),
        patch.object(palette_generators, "lch_to_hex", return_value="#123456"),
    ):
        generated = palette_generators._generate_syntax_from_analysis(analysis, "dark")
    assert len(generated) == palette_generators.SYNTAX_PALETTE_SIZE


def test_mappings_template_custom_and_unknown_formats() -> None:
    from themeweaver.color_utils.mappings_template import _get_syntax_format

    assert _get_syntax_format("keyword", {"keyword": {"bold": True}}, "Syntax.B10") == [
        "Syntax.B10",
        True,
        False,
    ]
    assert _get_syntax_format("unknown", None, "Syntax.B20") == [
        "Syntax.B20",
        False,
        False,
    ]


def test_yaml_theme_loader_full_light_syntax_palette() -> None:
    from themeweaver.core.syntax_schema import syntax_palette_slot_count
    from themeweaver.core.yaml_theme_loader import parse_theme_definition

    syntax = ["#123456"] * syntax_palette_slot_count()
    result = parse_theme_definition(
        {
            "name": "sample",
            "colors": ["#111111"] * 6,
            "syntax-colors": {"light": syntax},
        }
    )
    assert result["syntax_colors_light"] == syntax


def test_spyder_package_exporter_missing_license(tmp_path: Path) -> None:
    from themeweaver.core.spyder_package_exporter import SpyderPackageExporter

    exporter = SpyderPackageExporter(
        build_dir=tmp_path / "build", output_dir=tmp_path / "dist"
    )
    exporter.workspace_root = tmp_path / "workspace"
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    exporter._copy_license(package_dir)
    assert not (package_dir / "LICENSE").exists()


def test_theme_export_command_nondefault_options() -> None:
    from themeweaver.cli.commands import theme_export

    args = SimpleNamespace(
        output=None,
        theme_dir=None,
        compile_for="pyqt6",
        generate_palette_images=True,
        all=True,
        theme=None,
        variants=None,
    )
    exporter = Mock()
    exporter.export_all_themes.return_value = {}
    with (
        patch.object(theme_export, "ThemeExporter", return_value=exporter),
        patch.object(theme_export, "operation_context", return_value=nullcontext()),
    ):
        theme_export.cmd_export(args)
    exporter.export_all_themes.assert_called_once_with(
        compile_for="pyqt6", generate_palette_images=True
    )


def test_color_interpolation_nonquiet_path() -> None:
    from themeweaver.cli.commands import color_interpolation

    args = SimpleNamespace(
        output=None,
        start_color="#000000",
        end_color="#FFFFFF",
        steps=2,
        method="linear",
        exponent=2,
        analyze=False,
        validate=False,
    )
    with (
        patch.object(
            color_interpolation,
            "interpolate_colors",
            return_value=["#000000", "#FFFFFF"],
        ) as interpolate,
        patch.object(
            color_interpolation, "operation_context", return_value=nullcontext()
        ),
    ):
        color_interpolation.cmd_interpolate(args)
    interpolate.assert_called_once()


def test_python_build_failure_uses_return_code() -> None:
    from themeweaver.cli.commands import theme_package

    with (
        patch.object(theme_package.subprocess, "run", return_value=Mock(returncode=7)),
        pytest.raises(SystemExit) as error,
    ):
        theme_package._run_python_build(Path("/tmp/package"), None)
    assert error.value.code == 7


def test_color_analysis_short_input() -> None:
    from themeweaver.color_utils.color_analysis import analyze_chromatic_distances

    assert analyze_chromatic_distances(["#000000"]) is None


def test_interpolation_analysis_expected_lch_spacing(
    capsys: pytest.CaptureFixture,
) -> None:
    from themeweaver.color_utils import interpolation_analysis

    info = {"hsv_degrees": (0.0, 0.0, 0.0), "lch": None}
    with (
        patch.object(interpolation_analysis, "get_color_info", return_value=info),
        patch.object(
            interpolation_analysis, "calculate_delta_e", side_effect=[1.0, 9.0]
        ),
    ):
        interpolation_analysis.analyze_interpolation(
            ["#000000", "#777777", "#FFFFFF"], "lch"
        )
    assert "Expected for LCH method" in capsys.readouterr().out


def test_cli_theme_info_url_branch() -> None:
    from themeweaver.cli import utils

    metadata = {"url": "https://example.invalid", "tags": ["one"]}
    palettes = SimpleNamespace(supported_variants=["dark"])
    with (
        patch.object(utils, "load_theme_metadata_from_yaml", return_value=metadata),
        patch.object(utils, "create_palettes", return_value=palettes),
        patch.object(utils._logger, "info") as info,
    ):
        utils.show_theme_info("sample")
    assert any("URL:" in call.args[0] for call in info.call_args_list)


class _ExpandingSliceList(list[str]):
    """Sequence whose slices expose the defensive trim branch."""

    def __getitem__(self, index):  # type: ignore[no-untyped-def, override]
        if isinstance(index, slice):
            return ["#111111"] * 12
        return super().__getitem__(index)


def test_color_gradient_defensive_trim_with_custom_sequence() -> None:
    from themeweaver.cli.commands import color_gradient

    values = _ExpandingSliceList(["#000000", "#FFFFFF"])
    with patch.object(color_gradient, "interpolate_colors", return_value=values):
        colors = color_gradient._generate_gradient_with_method("#123456", "linear")
    assert len(colors) == 16


def test_validator_line_background_specific_suggestion() -> None:
    from themeweaver.contrast import validator

    rule = {
        "fg": "FG",
        "bg": "BG",
        "line_bg": "LBG",
        "fg_lbg_min": 1,
        "lbg_bg_min": 6,
        "fg_bg_min": 1,
    }

    def get_color(_colors, _rule, role):
        return {"fg": "#111111", "bg": "#222222", "line_bg": "#333333"}[role]

    with (
        patch.object(validator, "load_rules", return_value={"R1": rule}),
        patch.object(validator, "resolve_theme_colors", return_value={}),
        patch.object(validator, "get_color_for_rule", side_effect=get_color),
        patch.object(validator, "contrast_ratio", side_effect=[5.0, 2.0, 5.0]),
        patch.object(validator, "adjust_for_contrast", return_value="#AAAAAA"),
    ):
        result = validator.validate_theme("sample", "dark")
    assert "Try LBG: #AAAAAA" in (result.results[0].suggestion or "")
