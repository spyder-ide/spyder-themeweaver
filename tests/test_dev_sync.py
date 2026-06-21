"""Tests for dev-sync CLI command."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from themeweaver.cli.commands.dev_sync import (
    _theme_registered,
    cmd_dev_sync,
    sync_theme_to_package,
)


def _write_minimal_theme(theme_dir: Path) -> None:
    theme_dir.mkdir(parents=True, exist_ok=True)
    (theme_dir / "__init__.py").write_text("# theme\n", encoding="utf-8")
    (theme_dir / "colorsystem.py").write_text("# colors\n", encoding="utf-8")
    (theme_dir / "palette.py").write_text("# palette\n", encoding="utf-8")
    (theme_dir / "dark").mkdir()
    (theme_dir / "dark" / "darkstyle.qss").write_text("/* qss */", encoding="utf-8")


def _write_package_init(package_root: Path, themes: list[str]) -> None:
    package_root.mkdir(parents=True, exist_ok=True)
    themes_repr = ", ".join(repr(name) for name in themes)
    (package_root / "__init__.py").write_text(
        f"THEMES = [{themes_repr}]\n",
        encoding="utf-8",
    )


class TestThemeRegistered:
    def test_returns_true_when_theme_listed(self, tmp_path: Path) -> None:
        package_root = tmp_path / "spyder_themes"
        _write_package_init(package_root, ["miami-nights", "dracula"])
        assert _theme_registered(package_root, "miami-nights") is True

    def test_returns_false_when_theme_missing(self, tmp_path: Path) -> None:
        package_root = tmp_path / "spyder_themes"
        _write_package_init(package_root, ["dracula"])
        assert _theme_registered(package_root, "miami-nights") is False

    def test_returns_false_without_init(self, tmp_path: Path) -> None:
        package_root = tmp_path / "spyder_themes"
        package_root.mkdir()
        assert _theme_registered(package_root, "miami-nights") is False


class TestSyncThemeToPackage:
    def test_copies_theme_tree(self, tmp_path: Path) -> None:
        build_dir = tmp_path / "build"
        package_root = tmp_path / "dist" / "spyder_themes" / "spyder_themes"
        _write_minimal_theme(build_dir / "miami-nights")
        (build_dir / "miami-nights" / "palette.png").write_bytes(b"png")

        dst = sync_theme_to_package(build_dir, package_root, "miami-nights")

        assert dst == package_root / "miami-nights"
        assert (dst / "palette.py").exists()
        assert (dst / "dark" / "darkstyle.qss").exists()
        assert not (dst / "palette.png").exists()

    def test_replaces_existing_destination(self, tmp_path: Path) -> None:
        build_dir = tmp_path / "build"
        package_root = tmp_path / "package"
        _write_minimal_theme(build_dir / "miami-nights")
        _write_minimal_theme(package_root / "miami-nights")
        (package_root / "miami-nights" / "stale.txt").write_text(
            "old", encoding="utf-8"
        )

        sync_theme_to_package(build_dir, package_root, "miami-nights")

        assert not (package_root / "miami-nights" / "stale.txt").exists()
        assert (package_root / "miami-nights" / "palette.py").exists()

    def test_raises_when_build_theme_missing(self, tmp_path: Path) -> None:
        build_dir = tmp_path / "build"
        package_root = tmp_path / "package"
        package_root.mkdir()

        with pytest.raises(FileNotFoundError, match="not found"):
            sync_theme_to_package(build_dir, package_root, "miami-nights")


class TestCmdDevSync:
    def test_exports_and_syncs(self, tmp_path: Path) -> None:
        package_root = tmp_path / "dist" / "spyder_themes" / "spyder_themes"
        _write_package_init(package_root, ["miami-nights"])

        args = SimpleNamespace(
            theme=["miami-nights"],
            theme_dir=None,
            build_dir=str(tmp_path / "build"),
            package_dir=str(package_root),
            skip_export=False,
            compile_for="qtpy",
            generate_palette_images=False,
        )

        with patch(
            "themeweaver.cli.commands.dev_sync.ThemeExporter"
        ) as mock_exporter_class:
            mock_exporter = Mock()
            mock_exporter_class.return_value = mock_exporter
            with patch(
                "themeweaver.cli.commands.dev_sync.sync_theme_to_package",
                return_value=package_root / "miami-nights",
            ) as mock_sync:
                cmd_dev_sync(args)

        mock_exporter.export_theme.assert_called_once_with("miami-nights")
        mock_sync.assert_called_once_with(
            Path(args.build_dir),
            package_root,
            "miami-nights",
        )

    def test_skip_export_only_syncs(self, tmp_path: Path) -> None:
        package_root = tmp_path / "package"
        _write_package_init(package_root, ["miami-nights"])

        args = SimpleNamespace(
            theme=["miami-nights"],
            theme_dir=None,
            build_dir=str(tmp_path / "build"),
            package_dir=str(package_root),
            skip_export=True,
            compile_for="qtpy",
            generate_palette_images=False,
        )

        with patch(
            "themeweaver.cli.commands.dev_sync.ThemeExporter"
        ) as mock_exporter_class:
            with patch(
                "themeweaver.cli.commands.dev_sync.sync_theme_to_package",
                return_value=package_root / "miami-nights",
            ):
                cmd_dev_sync(args)

        mock_exporter_class.return_value.export_theme.assert_not_called()

    def test_exits_when_package_tree_missing(self, tmp_path: Path) -> None:
        args = SimpleNamespace(
            theme=["miami-nights"],
            theme_dir=None,
            build_dir=str(tmp_path / "build"),
            package_dir=str(tmp_path / "missing"),
            skip_export=True,
            compile_for="qtpy",
            generate_palette_images=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd_dev_sync(args)
        assert exc_info.value.code == 1
