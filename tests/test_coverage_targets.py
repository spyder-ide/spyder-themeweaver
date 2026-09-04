"""Targeted branch coverage for palette, generation, export, packaging, and CSS."""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import yaml

from themeweaver.cli.commands import theme_generation
from themeweaver.color_utils import palette_loaders
from themeweaver.core import css_generator, qdarkstyle_exporter
from themeweaver.core.qdarkstyle_exporter import QDarkStyleAssetExporter
from themeweaver.core.theme_packager import ThemePackager


def test_load_color_groups_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        palette_loaders.load_color_groups_from_file(tmp_path / "missing.py")


def test_palette_loader_records_unexpected_python_error(tmp_path: Path) -> None:
    palette_file = tmp_path / "palette.yaml"
    palette_file.write_text("Primary:\n  B10: '#123456'\n", encoding="utf-8")

    with patch.object(
        palette_loaders,
        "load_color_groups_from_file",
        side_effect=RuntimeError("broken import"),
    ):
        assert palette_loaders.load_palette_from_file(palette_file)["colors"] == {
            "B10": "#123456"
        }


def test_palette_loader_yaml_expected_format(tmp_path: Path) -> None:
    palette_file = tmp_path / "palette.yaml"
    palette_file.write_text("ignored", encoding="utf-8")
    expected = {"name": "Named", "colors": {"red": "#ff0000"}}

    with (
        patch.object(palette_loaders, "load_color_groups_from_file", return_value={}),
        patch.object(palette_loaders.yaml, "safe_load", return_value=expected),
        patch.object(
            palette_loaders, "_extract_color_group_from_yaml", return_value=(None, None)
        ),
    ):
        assert palette_loaders.load_palette_from_file(palette_file) is expected


@pytest.mark.parametrize(
    "yaml_error",
    [yaml.YAMLError("invalid yaml"), RuntimeError("unexpected yaml failure")],
)
def test_palette_loader_yaml_errors_fall_back_to_json(
    tmp_path: Path, yaml_error: Exception
) -> None:
    palette_file = tmp_path / "palette.json"
    palette_file.write_text("{}", encoding="utf-8")

    with (
        patch.object(palette_loaders, "load_color_groups_from_file", return_value={}),
        patch.object(palette_loaders.yaml, "safe_load", side_effect=yaml_error),
        patch.object(
            palette_loaders.json,
            "load",
            return_value={"colors": {"red": "#ff0000"}},
        ),
    ):
        assert palette_loaders.load_palette_from_file(palette_file)["colors"][
            "red"
        ] == ("#ff0000")


@pytest.mark.parametrize(
    ("json_data", "expected_name"),
    [
        ({"colors": {"red": "#ff0000"}}, None),
        ({"red": "#ff0000"}, "Palette from palette.json"),
    ],
)
def test_palette_loader_json_dictionary_formats(
    tmp_path: Path, json_data: dict[str, object], expected_name: str | None
) -> None:
    palette_file = tmp_path / "palette.json"
    palette_file.write_text("{}", encoding="utf-8")

    with (
        patch.object(palette_loaders, "load_color_groups_from_file", return_value={}),
        patch.object(palette_loaders.yaml, "safe_load", return_value=[]),
        patch.object(palette_loaders.json, "load", return_value=json_data),
    ):
        result = palette_loaders.load_palette_from_file(palette_file)

    if expected_name is None:
        assert result is json_data
    else:
        assert result == {"name": expected_name, "colors": json_data}


def test_palette_loader_file_read_error(tmp_path: Path) -> None:
    palette_file = tmp_path / "palette.json"
    palette_file.write_text("{}", encoding="utf-8")

    with (
        patch.object(palette_loaders, "load_color_groups_from_file", return_value={}),
        patch("builtins.open", side_effect=OSError("unreadable")),
        pytest.raises(ValueError, match="File reading: OSError"),
    ):
        palette_loaders.load_palette_from_file(palette_file)


def test_palette_loader_unexpected_json_error(tmp_path: Path) -> None:
    palette_file = tmp_path / "palette.json"
    palette_file.write_text("{}", encoding="utf-8")

    with (
        patch.object(palette_loaders, "load_color_groups_from_file", return_value={}),
        patch.object(palette_loaders.yaml, "safe_load", return_value=[]),
        patch.object(
            palette_loaders.json, "load", side_effect=RuntimeError("bad decoder")
        ),
        pytest.raises(ValueError, match="JSON: Unexpected error: RuntimeError"),
    ):
        palette_loaders.load_palette_from_file(palette_file)


def test_get_available_color_groups_missing_file(tmp_path: Path) -> None:
    assert palette_loaders.get_available_color_groups(tmp_path / "missing.yaml") == []


def _yaml_args(path: Path, **overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "from_yaml": str(path),
        "name": "test-theme",
        "output_dir": None,
        "overwrite": False,
        "validate_contrast": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (FileNotFoundError("gone"), "YAML file not found"),
        (yaml.YAMLError("broken"), "YAML parsing error"),
        (RuntimeError("boom"), "Unexpected error parsing YAML file"),
    ],
)
def test_generate_from_yaml_maps_loader_errors(
    tmp_path: Path, error: Exception, message: str
) -> None:
    yaml_file = tmp_path / "theme.yaml"
    yaml_file.write_text("name: test", encoding="utf-8")

    with (
        patch.object(theme_generation, "operation_context", return_value=nullcontext()),
        patch.object(theme_generation, "load_theme_from_yaml", side_effect=error),
        pytest.raises(ValueError, match=message),
    ):
        theme_generation._generate_from_yaml(_yaml_args(yaml_file), Mock())


def test_generate_from_yaml_default_hint_and_contrast(tmp_path: Path) -> None:
    yaml_file = tmp_path / "theme.yaml"
    yaml_file.write_text("name: test", encoding="utf-8")
    parsed = {
        "name": "test-theme",
        "colors": ["#111111", "#222222", "#333333", "#444444", "#555555", "#666666"],
        "variants": ["dark"],
    }
    generator = Mock()
    generator.themes_dir = tmp_path / "themes"
    generator.theme_exists.return_value = False
    generator.generate_theme_from_data.return_value = {}

    with (
        patch.object(theme_generation, "operation_context", return_value=nullcontext()),
        patch.object(theme_generation, "load_theme_from_yaml", return_value={}),
        patch.object(theme_generation, "parse_theme_definition", return_value=parsed),
        patch.object(
            theme_generation, "validate_input_colors", return_value=(True, "")
        ),
        patch.object(theme_generation, "generate_theme_from_colors", return_value={}),
        patch.object(theme_generation, "_run_contrast_validation") as contrast,
    ):
        theme_generation._generate_from_yaml(_yaml_args(yaml_file), generator)

    contrast.assert_called_once_with("test-theme", ["dark"], generator.themes_dir)


def _color_args(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "name": "test-theme",
        "colors": ["#111111", "#222222", "#333333", "#444444", "#555555", "#666666"],
        "syntax_colors_dark": None,
        "syntax_colors_light": None,
        "display_name": None,
        "description": None,
        "author": "ThemeWeaver",
        "tags": None,
        "overwrite": False,
        "output_dir": None,
        "validate_contrast": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _generation_patches() -> tuple[object, ...]:
    return (
        patch.object(theme_generation, "operation_context", return_value=nullcontext()),
        patch.object(theme_generation, "syntax_palette_slot_count", return_value=3),
        patch.object(
            theme_generation, "validate_input_colors", return_value=(True, "")
        ),
        patch.object(theme_generation, "generate_theme_from_colors", return_value={}),
    )


def test_generate_from_colors_rejects_invalid_dark_syntax_count(tmp_path: Path) -> None:
    generator = Mock(themes_dir=tmp_path)
    generator.theme_exists.return_value = False
    patches = _generation_patches()
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        pytest.raises(ValueError, match="Syntax colors dark"),
    ):
        theme_generation._generate_from_colors(
            _color_args(syntax_colors_dark=["#111111", "#222222"]), generator
        )


def test_generate_from_colors_rejects_invalid_light_syntax_count(
    tmp_path: Path,
) -> None:
    generator = Mock(themes_dir=tmp_path)
    generator.theme_exists.return_value = False
    patches = _generation_patches()
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        pytest.raises(ValueError, match="Syntax colors light"),
    ):
        theme_generation._generate_from_colors(
            _color_args(syntax_colors_light=["#111111", "#222222"]), generator
        )


@pytest.mark.parametrize(
    "syntax_colors_light",
    [["#abcdef"], ["#111111", "#222222", "#333333"]],
)
def test_generate_from_colors_light_syntax_and_explicit_variants(
    tmp_path: Path, syntax_colors_light: list[str]
) -> None:
    generator = Mock()
    generator.themes_dir = tmp_path
    generator.theme_exists.return_value = False
    generator.generate_theme_from_data.return_value = {}
    validate = Mock(return_value=(True, ""))

    with (
        patch.object(theme_generation, "operation_context", return_value=nullcontext()),
        patch.object(theme_generation, "syntax_palette_slot_count", return_value=3),
        patch.object(theme_generation, "validate_input_colors", validate),
        patch.object(
            theme_generation, "generate_theme_from_colors", return_value={}
        ) as generate,
        patch.object(theme_generation, "_run_contrast_validation"),
    ):
        theme_generation._generate_from_colors(
            _color_args(
                syntax_colors_light=syntax_colors_light,
                variants=["light"],
                output_dir=str(tmp_path),
            ),
            generator,
        )

    assert validate.call_count == 2
    assert validate.call_args_list[1].kwargs["syntax_colors"] == (
        syntax_colors_light[0] if len(syntax_colors_light) == 1 else syntax_colors_light
    )
    assert generate.call_args.kwargs["variants"] == ["light"]


def test_qdarkstyle_unavailable_raises_import_error() -> None:
    with (
        patch.object(qdarkstyle_exporter, "QDS_AVAILABLE", False),
        patch.object(qdarkstyle_exporter, "QDS_IMPORT_ERROR", "not installed"),
        pytest.raises(ImportError, match="not installed"),
    ):
        QDarkStyleAssetExporter()


def test_qdarkstyle_export_adds_palette_image_arguments(tmp_path: Path) -> None:
    exporter = object.__new__(QDarkStyleAssetExporter)

    class Palette:
        COLOR = "#123456"

    result = Mock(returncode=0, stdout="", stderr="")
    with patch.object(
        qdarkstyle_exporter.subprocess, "run", return_value=result
    ) as run:
        output = exporter.export_assets(
            Palette,
            tmp_path,
            "dark",
            cleanup_intermediate=False,
            generate_palette_images=True,
        )

    command = run.call_args.args[0]
    assert command[command.index("--palette-images") + 1] == "True"
    assert command[command.index("--palette-images-path") + 1] == str(tmp_path)
    assert output == tmp_path / "dark"


def test_qdarkstyle_export_reports_subprocess_failure(tmp_path: Path) -> None:
    exporter = object.__new__(QDarkStyleAssetExporter)

    class Palette:
        COLOR = "#123456"

    result = Mock(returncode=2, stdout="", stderr="failed")
    with (
        patch.object(qdarkstyle_exporter.subprocess, "run", return_value=result),
        pytest.raises(RuntimeError, match="return code 2"),
    ):
        exporter.export_assets(Palette, tmp_path, "dark")


def test_qdarkstyle_cleanup_removes_stale_resource_and_handles_empty(
    tmp_path: Path,
) -> None:
    exporter = object.__new__(QDarkStyleAssetExporter)
    variant_dir = tmp_path / "dark"
    variant_dir.mkdir()
    stale = variant_dir / "pyqt5_darkstyle_rc.py"
    stale.write_text("stale", encoding="utf-8")

    exporter._cleanup_intermediate_files(
        tmp_path, variant_dir, "qtpy", generate_palette_images=True
    )
    assert not stale.exists()

    exporter._cleanup_intermediate_files(
        tmp_path, variant_dir, "qtpy", generate_palette_images=True
    )


def test_package_all_themes_without_build_directory(tmp_path: Path) -> None:
    packager = ThemePackager(tmp_path / "packages")
    packager.build_dir = tmp_path / "missing-build"
    assert packager.package_all_themes() == {}


def test_package_all_themes_continues_after_failure(tmp_path: Path) -> None:
    packager = ThemePackager(tmp_path / "packages")
    packager.build_dir = tmp_path / "build"
    (packager.build_dir / "good").mkdir(parents=True)
    (packager.build_dir / "bad").mkdir()

    def package(name: str, format: str) -> Path:
        if name == "bad":
            raise RuntimeError("cannot package")
        return tmp_path / f"{name}.{format}"

    with patch.object(packager, "package_theme", side_effect=package):
        assert packager.package_all_themes() == {"good": tmp_path / "good.zip"}


@pytest.mark.parametrize("destination_is_directory", [True, False])
def test_copy_theme_files_replaces_existing_destination(
    tmp_path: Path, destination_is_directory: bool
) -> None:
    packager = ThemePackager(tmp_path / "packages")
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "assets").mkdir(parents=True)
    (source / "assets" / "new.txt").write_text("new", encoding="utf-8")
    destination.mkdir()
    existing = destination / "assets"
    if destination_is_directory:
        existing.mkdir()
        (existing / "old.txt").write_text("old", encoding="utf-8")
    else:
        existing.write_text("old", encoding="utf-8")

    packager._copy_theme_files("theme", source, destination)
    assert (existing / "new.txt").read_text(encoding="utf-8") == "new"


def test_readme_includes_url_and_tags(tmp_path: Path) -> None:
    packager = ThemePackager(tmp_path / "packages")
    content = packager._generate_readme_content(
        "theme",
        {"url": "https://example.invalid", "tags": ["dark", "accessible"]},
    )
    assert "- **URL**: https://example.invalid" in content
    assert "- **Tags**: dark, accessible" in content


@pytest.mark.parametrize(
    ("spec", "message"),
    [
        ("", "is empty"),
        ({"dark": "A", "light": "B", "sepia": "C"}, "unknown variant keys"),
        ({"dark": "", "light": "B"}, "dark value"),
        ({"dark": "A", "light": ""}, "light value"),
        (42, "must be a string"),
    ],
)
def test_css_color_spec_validation_errors(spec: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        css_generator._validate_color_spec("--text-color", spec)


def test_palette_hex_rejects_non_hex_value() -> None:
    class Palette:
        COLOR = "red"

    with pytest.raises(ValueError, match="not a hex color"):
        css_generator.palette_hex(Palette, "COLOR")


def test_color_class_reference_rejects_non_hex_result() -> None:
    with (
        patch.object(css_generator, "_resolve_color_reference", return_value="red"),
        pytest.raises(ValueError, match="did not resolve to a hex color"),
    ):
        css_generator.resolve_css_color_value(
            object, "Primary.B10", {"Primary": object}
        )


def test_load_rules_missing_template(tmp_path: Path) -> None:
    with (
        patch.object(css_generator, "_RESOURCES_DIR", tmp_path),
        pytest.raises(FileNotFoundError, match="CSS rules template not found"),
    ):
        css_generator.load_rules()


def test_load_rules_missing_scrollbar_template(tmp_path: Path) -> None:
    (tmp_path / "rules.css").write_text("body {}\n", encoding="utf-8")
    with (
        patch.object(css_generator, "_RESOURCES_DIR", tmp_path),
        pytest.raises(FileNotFoundError, match="CSS scrollbar template not found"),
    ):
        css_generator.load_rules()


def test_load_pydoc_rules_missing_template(tmp_path: Path) -> None:
    with (
        patch.object(css_generator, "_RESOURCES_DIR", tmp_path),
        pytest.raises(FileNotFoundError, match="Pydoc CSS rules template not found"),
    ):
        css_generator.load_pydoc_rules()


def test_append_scrollbar_empty_rules_and_missing_newline() -> None:
    with patch.object(
        css_generator, "_read_css_resource", return_value="::-webkit-scrollbar {}"
    ):
        assert css_generator._append_scrollbar("") == "::-webkit-scrollbar {}\n"
        assert css_generator._append_scrollbar("body {}") == (
            "body {}\n\n::-webkit-scrollbar {}\n"
        )


def test_append_scrollbar_empty_scrollbar() -> None:
    with patch.object(css_generator, "_read_css_resource", return_value=""):
        assert css_generator._append_scrollbar("body {}") == "body {}\n\n"


def test_build_default_css_adds_rules_trailing_newline() -> None:
    with (
        patch.object(css_generator, "build_root", return_value=":root {}\n"),
        patch.object(css_generator, "load_rules", return_value="body {}"),
    ):
        assert css_generator.build_default_css("dark", object).endswith("body {}\n")


def test_build_pydoc_css_adds_rules_trailing_newline() -> None:
    with (
        patch.object(css_generator, "build_pydoc_root", return_value=":root {}\n"),
        patch.object(css_generator, "load_pydoc_rules", return_value="body {}"),
    ):
        assert css_generator.build_pydoc_css("dark", object).endswith("body {}\n")
