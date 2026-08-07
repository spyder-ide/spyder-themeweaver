#!/usr/bin/env python3
"""
Integration tests for the ThemeWeaver exporter.

This module tests the complete export pipeline without requiring CLI setup.
"""

import random
from pathlib import Path
from typing import Any

import pytest

from themeweaver.core.theme_exporter import ThemeExporter


@pytest.fixture
def fresh_exporter(tmp_path: Path) -> ThemeExporter:
    """Isolated exporter with an empty build directory (per test)."""
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    return ThemeExporter(build_dir=build_dir)


@pytest.fixture(scope="class")
def spyder_full_export(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[ThemeExporter, Path, dict[str, Any]]:
    """One full spyder export shared by structure tests (saves ~1 export per class)."""
    build_dir = tmp_path_factory.mktemp("build_spyder_shared")
    exporter = ThemeExporter(build_dir=build_dir)
    result = exporter.export_theme("spyder")
    return exporter, build_dir, result


class TestThemeExporterSpyderExport:
    """Assertions against a single shared full export of ``spyder``."""

    def test_spyder_theme_export(
        self,
        spyder_full_export: tuple[ThemeExporter, Path, dict[str, Any]],
    ) -> None:
        """Test complete export of spyder theme."""
        _exporter, _build_dir, result = spyder_full_export

        assert isinstance(result, dict)
        assert len(result) > 0

        expected_variants = ["dark", "light"]
        for variant in expected_variants:
            assert variant in result
            assert isinstance(result[variant], Path)
            assert result[variant].exists()

    def test_exported_files_structure(
        self,
        spyder_full_export: tuple[ThemeExporter, Path, dict[str, Any]],
    ) -> None:
        """Test that exported files have expected structure."""
        exporter, build_dir, _result = spyder_full_export

        spyder_dir = build_dir / "spyder"
        assert spyder_dir.exists()

        expected_files = ["colorsystem.py", "palette.py", "__init__.py", "theme.yaml"]
        for file_name in expected_files:
            file_path = spyder_dir / file_name
            assert file_path.exists()
            assert file_path.stat().st_size > 0

        init_text = (spyder_dir / "__init__.py").read_text(encoding="utf-8")
        assert "from .palette import SpyderPaletteDark, SpyderPaletteLight" in init_text
        assert 'THEME_ID = "spyder"' in init_text
        assert "Theme:" not in init_text
        assert "Author:" not in init_text

        source_yaml = (exporter.themes_dir / "spyder" / "theme.yaml").read_text(
            encoding="utf-8"
        )
        exported_yaml = (spyder_dir / "theme.yaml").read_text(encoding="utf-8")
        assert exported_yaml == source_yaml

        for variant in ["dark", "light"]:
            variant_dir = spyder_dir / variant
            assert variant_dir.exists()
            qss_file = variant_dir / f"{variant}style.qss"
            assert qss_file.exists()
            assert (variant_dir / "default.css").exists()


class TestThemeExporter:
    """Integration tests using a fresh build directory per test."""

    def test_exporter_initialization(
        self, fresh_exporter: ThemeExporter, tmp_path: Path
    ) -> None:
        """Test that exporter initializes correctly."""
        assert fresh_exporter.build_dir == tmp_path / "build"
        assert fresh_exporter.themes_dir.exists()
        assert fresh_exporter.themes_dir.name == "themes"

    def test_theme_discovery(self, fresh_exporter: ThemeExporter) -> None:
        """Test that exporter can discover available themes."""
        themes = list(fresh_exporter.themes_dir.iterdir())
        available_themes = [
            t.name for t in themes if t.is_dir() and not t.name.startswith(".")
        ]

        assert len(available_themes) > 0
        assert "spyder" in available_themes

    def test_theme_not_found_error(self, fresh_exporter: ThemeExporter) -> None:
        """Test that exporter raises appropriate error for non-existent theme."""
        with pytest.raises(FileNotFoundError):
            fresh_exporter.export_theme("nonexistent_theme")

    def test_export_specific_variants(self, fresh_exporter: ThemeExporter) -> None:
        """Test exporting specific variants only."""
        result = fresh_exporter.export_theme("spyder", variants=["dark"])

        assert "dark" in result
        assert "light" not in result

        spyder_dir = fresh_exporter.build_dir / "spyder"
        assert (spyder_dir / "dark").exists()

    def test_export_representative_themes(self, fresh_exporter: ThemeExporter) -> None:
        """Export a small sample: spyder plus one other theme (fast integration check)."""
        themes_dir = fresh_exporter.themes_dir
        available = sorted(
            d.name
            for d in themes_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )
        assert "spyder" in available
        others = [t for t in available if t != "spyder"]
        assert others, "need at least one theme besides spyder"
        second = random.Random(42).choice(others)
        to_export = ["spyder", second]

        result: dict[str, dict[str, Path]] = {}
        for name in to_export:
            result[name] = fresh_exporter.export_theme(name)

        assert set(result.keys()) == set(to_export)
        for theme_name, variants in result.items():
            assert isinstance(variants, dict)
            assert len(variants) > 0
            for _v, path in variants.items():
                assert isinstance(path, Path)
                assert path.exists()

    def test_theme_not_found_error_with_detailed_message(
        self, fresh_exporter: ThemeExporter
    ) -> None:
        """Test that an appropriate error message is provided for a non-existent theme."""
        with pytest.raises(FileNotFoundError) as exc_info:
            fresh_exporter.export_theme("nonexistent_theme")
        assert "nonexistent_theme" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_export_with_empty_variants_list(
        self, fresh_exporter: ThemeExporter
    ) -> None:
        """Test exporting with empty variants list."""
        with pytest.raises(ValueError, match="No variants to export"):
            fresh_exporter.export_theme("spyder", variants=[])

    def test_export_with_invalid_variant(self, fresh_exporter: ThemeExporter) -> None:
        """Test exporting with invalid variant name."""
        with pytest.raises(ValueError, match="Variant 'invalid_variant' not supported"):
            fresh_exporter.export_theme("spyder", variants=["dark", "invalid_variant"])

    def test_export_all_themes_stops_on_first_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """export_all_themes must not swallow per-theme errors."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        exporter = ThemeExporter(build_dir=build_dir)

        calls: list[str] = []

        def fake_export_theme(theme_name: str, *args: Any, **kwargs: Any) -> dict:
            calls.append(theme_name)
            if theme_name == "inkpot":
                raise AttributeError(
                    "Palette 'DarkPalette' has no attribute 'COLOR_ERROR_5'"
                )
            return {"dark": build_dir / theme_name / "dark"}

        monkeypatch.setattr(exporter, "export_theme", fake_export_theme)

        # Deterministic discovery order via sorted names in export_all_themes
        with pytest.raises(
            RuntimeError, match="Failed to export theme 'inkpot'"
        ) as exc:
            exporter.export_all_themes()

        assert isinstance(exc.value.__cause__, AttributeError)
        assert "inkpot" in calls
        # Themes after inkpot alphabetically must not have been attempted
        assert "miami-nights" not in calls
        assert "spyder" not in calls
        assert "zenburn" not in calls
