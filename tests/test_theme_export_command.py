"""
Tests for theme export CLI command.
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from themeweaver.cli.commands.theme_export import cmd_export, parse_theme_names


class TestParseThemeNames:
    """Test theme name parsing for export."""

    def test_single_name(self) -> None:
        assert parse_theme_names(["dracula"]) == ["dracula"]

    def test_space_separated(self) -> None:
        assert parse_theme_names(["gruvbox", "inkpot", "idle"]) == [
            "gruvbox",
            "inkpot",
            "idle",
        ]

    def test_comma_separated(self) -> None:
        assert parse_theme_names(["gruvbox,inkpot,idle"]) == [
            "gruvbox",
            "inkpot",
            "idle",
        ]

    def test_mixed_with_whitespace(self) -> None:
        assert parse_theme_names(["gruvbox, inkpot", "idle"]) == [
            "gruvbox",
            "inkpot",
            "idle",
        ]


class TestThemeExportCommand:
    """Test theme export command functionality."""

    def test_cmd_export_single_theme(self) -> None:
        """Test exporting a single theme."""
        args = Mock()
        args.all = False
        args.theme = ["dracula"]
        args.variants = "dark,light"
        args.output = None
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_theme.return_value = {
                    "dark": "/path/to/dracula-dark.qss",
                    "light": "/path/to/dracula-light.qss",
                }

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    mock_exporter_class.assert_called_once_with(
                        build_dir=None, themes_dir=None
                    )
                    mock_exporter.export_theme.assert_called_once_with(
                        "dracula", ["dark", "light"]
                    )
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__

    def test_cmd_export_single_theme_no_variants(self) -> None:
        """Test exporting a single theme without specifying variants."""
        args = Mock()
        args.all = False
        args.theme = ["solarized"]
        args.variants = None
        args.output = None
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_theme.return_value = {
                    "dark": "/path/to/solarized-dark.qss",
                    "light": "/path/to/solarized-light.qss",
                }

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    mock_exporter_class.assert_called_once_with(
                        build_dir=None, themes_dir=None
                    )
                    mock_exporter.export_theme.assert_called_once_with(
                        "solarized", None
                    )
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__

    def test_cmd_export_single_theme_with_output_dir(self) -> None:
        """Test exporting a single theme with custom output directory."""
        args = Mock()
        args.all = False
        args.theme = ["gruvbox"]
        args.variants = "dark"
        args.output = "/custom/output"
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_theme.return_value = {
                    "dark": "/custom/output/gruvbox-dark.qss"
                }

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    mock_exporter_class.assert_called_once_with(
                        build_dir=Path("/custom/output"), themes_dir=None
                    )
                    mock_exporter.export_theme.assert_called_once_with(
                        "gruvbox", ["dark"]
                    )
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__

    def test_cmd_export_all_themes(self) -> None:
        """Test exporting all themes."""
        args = Mock()
        args.all = True
        args.theme = None
        args.variants = None
        args.output = None
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_all_themes.return_value = {
                    "dracula": {
                        "dark": "/path/to/dracula-dark.qss",
                        "light": "/path/to/dracula-light.qss",
                    },
                    "solarized": {
                        "dark": "/path/to/solarized-dark.qss",
                        "light": "/path/to/solarized-light.qss",
                    },
                    "gruvbox": {"dark": "/path/to/gruvbox-dark.qss"},
                }

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    mock_exporter_class.assert_called_once_with(
                        build_dir=None, themes_dir=None
                    )
                    mock_exporter.export_all_themes.assert_called_once()
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__

    def test_cmd_export_all_themes_with_output_dir(self) -> None:
        """Test exporting all themes with custom output directory."""
        args = Mock()
        args.all = True
        args.theme = None
        args.variants = None
        args.output = "/custom/build"
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_all_themes.return_value = {
                    "dracula": {"dark": "/custom/build/dracula-dark.qss"},
                    "solarized": {"light": "/custom/build/solarized-light.qss"},
                }

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    mock_exporter_class.assert_called_once_with(
                        build_dir=Path("/custom/build"), themes_dir=None
                    )
                    mock_exporter.export_all_themes.assert_called_once()
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__

    def test_cmd_export_single_theme_single_variant(self) -> None:
        """Test exporting a single theme with single variant."""
        args = Mock()
        args.all = False
        args.theme = ["monokai"]
        args.variants = "dark"
        args.output = None
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_theme.return_value = {
                    "dark": "/path/to/monokai-dark.qss"
                }

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    mock_exporter_class.assert_called_once_with(
                        build_dir=None, themes_dir=None
                    )
                    mock_exporter.export_theme.assert_called_once_with(
                        "monokai", ["dark"]
                    )
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__

    def test_cmd_export_single_theme_multiple_variants(self) -> None:
        """Test exporting a single theme with multiple variants."""
        args = Mock()
        args.all = False
        args.theme = ["catppuccin-mocha"]
        args.variants = "dark,light,auto"
        args.output = None
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_theme.return_value = {
                    "dark": "/path/to/catppuccin-mocha-dark.qss",
                    "light": "/path/to/catppuccin-mocha-light.qss",
                    "auto": "/path/to/catppuccin-mocha-auto.qss",
                }

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    mock_exporter_class.assert_called_once_with(
                        build_dir=None, themes_dir=None
                    )
                    mock_exporter.export_theme.assert_called_once_with(
                        "catppuccin-mocha", ["dark", "light", "auto"]
                    )
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__

    def test_cmd_export_all_themes_empty_result(self) -> None:
        """Test exporting all themes with empty result."""
        args = Mock()
        args.all = True
        args.theme = None
        args.variants = None
        args.output = None
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_all_themes.return_value = {}

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    mock_exporter_class.assert_called_once_with(
                        build_dir=None, themes_dir=None
                    )
                    mock_exporter.export_all_themes.assert_called_once()
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__

    def test_cmd_export_single_theme_empty_result(self) -> None:
        """Test exporting a single theme with empty result."""
        args = Mock()
        args.all = False
        args.theme = ["nonexistent"]
        args.variants = None
        args.output = None
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_theme.return_value = {}

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    mock_exporter_class.assert_called_once_with(
                        build_dir=None, themes_dir=None
                    )
                    mock_exporter.export_theme.assert_called_once_with(
                        "nonexistent", None
                    )
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__

    def test_cmd_export_multiple_themes(self) -> None:
        """Test exporting multiple themes in one invocation."""
        args = Mock()
        args.all = False
        args.theme = ["gruvbox", "inkpot", "idle"]
        args.variants = None
        args.output = None
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_theme.return_value = {"dark": "/path/to/dark"}

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    assert mock_exporter.export_theme.call_count == 3
                    mock_exporter.export_theme.assert_any_call("gruvbox", None)
                    mock_exporter.export_theme.assert_any_call("inkpot", None)
                    mock_exporter.export_theme.assert_any_call("idle", None)
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__

    def test_cmd_export_comma_separated_themes(self) -> None:
        """Test exporting themes passed as a comma-separated list."""
        args = Mock()
        args.all = False
        args.theme = ["gruvbox,inkpot"]
        args.variants = "dark"
        args.output = None
        args.theme_dir = None

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            with patch(
                "themeweaver.cli.commands.theme_export.ThemeExporter"
            ) as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter_class.return_value = mock_exporter
                mock_exporter.export_theme.return_value = {"dark": "/path/to/dark.qss"}

                with patch(
                    "themeweaver.cli.commands.theme_export._logger"
                ) as mock_logger:
                    cmd_export(args)

                    assert mock_exporter.export_theme.call_count == 2
                    mock_exporter.export_theme.assert_any_call("gruvbox", ["dark"])
                    mock_exporter.export_theme.assert_any_call("inkpot", ["dark"])
                    mock_logger.info.assert_called()
        finally:
            sys.stdout = sys.__stdout__
