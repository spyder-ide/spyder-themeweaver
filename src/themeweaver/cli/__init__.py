"""
Command-line interface for ThemeWeaver.

This module provides CLI commands for generating, exporting, and managing themes.
"""

import argparse
import logging
import sys
from importlib.metadata import PackageNotFoundError, version

from themeweaver.cli.commands import (
    cmd_export,
    cmd_generate,
    cmd_gradient,
    cmd_info,
    cmd_interpolate,
    cmd_list,
    cmd_palette,
    cmd_python_package,
    cmd_validate,
    cmd_validate_contrast,
)
from themeweaver.cli.utils import setup_logging
from themeweaver.core.syntax_schema import (
    syntax_format_elements,
    syntax_palette_slot_count,
)

_logger = logging.getLogger(__name__)

try:
    _CLI_VERSION = version("themeweaver")
except PackageNotFoundError:
    _CLI_VERSION = "0.0.0"


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="themeweaver",
        description="ThemeWeaver - Generate and export Spyder themes",
    )

    # Add version argument
    parser.add_argument(
        "--version",
        action="version",
        version=f"ThemeWeaver {_CLI_VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List all available themes")
    list_parser.add_argument(
        "--theme-dir",
        help="Source directory where themes are stored (input). If not provided, uses themes/ directory in current working directory.",
    )
    list_parser.set_defaults(func=cmd_list)

    # Info command
    info_parser = subparsers.add_parser("info", help="Show detailed theme information")
    info_parser.add_argument("theme", help="Theme name to show info for")
    info_parser.add_argument(
        "--theme-dir",
        help="Source directory where themes are stored (input). If not provided, uses themes/ directory in current working directory.",
    )
    info_parser.set_defaults(func=cmd_info)

    # Export command
    export_parser = subparsers.add_parser(
        "export", help="Export theme(s) to build directory"
    )
    export_group = export_parser.add_mutually_exclusive_group(required=True)
    export_group.add_argument("--theme", help="Theme name to export")
    export_group.add_argument("--all", action="store_true", help="Export all themes")

    export_parser.add_argument(
        "--variants",
        help="Comma-separated list of variants to export (e.g., 'dark,light')",
    )
    export_parser.add_argument(
        "--theme-dir",
        help="Source directory where themes are stored (input). If not provided, uses themes/ directory in current working directory.",
    )
    export_parser.add_argument(
        "--output",
        "-o",
        help="Output directory where exported themes will be saved (destination). Default: build/ (at workspace root)",
    )
    export_parser.add_argument(
        "--compile-for",
        default="qtpy",
        choices=[
            "pyqt5",
            "pyqt6",
            "pyside2",
            "pyside6",
            "qtpy",
            "pyqtgraph",
            "qt",
            "qt5",
            "all",
        ],
        help="Qt binding target for generated _rc modules (default: qtpy)",
    )
    export_parser.add_argument(
        "--generate-palette-images",
        action="store_true",
        default=False,
        help="Generate palette.svg and palette.png preview files (default: False)",
    )
    export_parser.set_defaults(func=cmd_export)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate theme configuration"
    )
    validate_parser.add_argument("theme", help="Theme name to validate")
    validate_parser.add_argument(
        "--theme-dir",
        help="Source directory where themes are stored (input). If not provided, uses themes/ directory in current working directory.",
    )
    validate_parser.set_defaults(func=cmd_validate)

    # Validate contrast command
    contrast_parser = subparsers.add_parser(
        "validate-contrast",
        help="Validate theme color contrast against Spyder UI rules",
    )
    theme_group = contrast_parser.add_mutually_exclusive_group(required=True)
    theme_group.add_argument("theme", nargs="?", help="Theme name to validate")
    theme_group.add_argument(
        "--all",
        action="store_true",
        help="Validate all themes in the theme directory",
    )
    contrast_parser.add_argument(
        "--variant",
        choices=["dark", "light", "both"],
        default="both",
        help="Variant(s) to validate (default: both)",
    )
    contrast_parser.add_argument(
        "--theme-dir",
        help="Directory where themes are stored",
    )
    contrast_parser.add_argument(
        "--rules-dir",
        help="Directory containing rules YAML files (default: package contrast/)",
    )
    contrast_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show all rules including passed ones",
    )
    contrast_parser.set_defaults(func=cmd_validate_contrast)

    syntax_palette_size = syntax_palette_slot_count()
    syntax_elements = ", ".join(syntax_format_elements())

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a new theme from individual colors or YAML definition",
    )
    generate_parser.add_argument("name", help="Theme name (used for directory name)")

    # Input options - either colors or yaml file
    input_group = generate_parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--colors",
        nargs=6,
        metavar=("PRIMARY", "SECONDARY", "ERROR", "SUCCESS", "WARNING", "GROUP"),
        help="Generate theme from single colors for each palette (6 hex colors required in this order: Primary, Secondary, Error, Success, Warning, Group)",
    )
    input_group.add_argument(
        "--from-yaml",
        metavar="YAML_FILE",
        help="Generate theme from a YAML definition file",
    )

    generate_parser.add_argument(
        "--syntax-colors-dark",
        nargs="+",
        metavar="COLOR",
        help=(
            "Syntax highlighting colors for dark variant. Provide 1 color "
            f"(seeded auto-generation) or {syntax_palette_size} colors "
            "(full palette incl. symbol)."
        ),
    )

    generate_parser.add_argument(
        "--syntax-colors-light",
        nargs="+",
        metavar="COLOR",
        help=(
            "Syntax highlighting colors for light variant. Provide 1 color "
            f"(seeded auto-generation) or {syntax_palette_size} colors "
            "(full palette incl. symbol)."
        ),
    )

    generate_parser.add_argument(
        "--syntax-format",
        metavar="FORMAT",
        help=(
            "Syntax formatting specifications. Format: "
            "'element:bold,element:italic' "
            "(e.g., 'keyword:bold,comment:italic,instance:italic'). "
            f"Available elements: {syntax_elements}."
        ),
    )

    generate_parser.add_argument(
        "--variants",
        nargs="+",
        choices=["dark", "light"],
        metavar="VARIANT",
        help="Theme variants to generate. Choose from 'dark', 'light', or both. Default: both variants.",
    )

    # Theme metadata options
    generate_parser.add_argument("--display-name", help="Human-readable theme name")
    generate_parser.add_argument("--description", help="Theme description")
    generate_parser.add_argument(
        "--author", default="ThemeWeaver", help="Theme author (default: ThemeWeaver)"
    )
    generate_parser.add_argument("--tags", help="Comma-separated list of tags")

    # Options
    generate_parser.add_argument(
        "--validate-contrast",
        action="store_true",
        default=True,
        help="Run contrast validation after generation (default: True)",
    )
    generate_parser.add_argument(
        "--no-validate-contrast",
        dest="validate_contrast",
        action="store_false",
        help="Skip contrast validation after generation",
    )
    generate_parser.add_argument(
        "--simple-names",
        action="store_true",
        help="Use simple color names instead of creative names",
    )
    generate_parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing theme if it exists"
    )
    generate_parser.add_argument(
        "--output-dir",
        help="Output directory where the generated theme will be saved (destination). Default: themes/ directory in current working directory",
    )

    generate_parser.set_defaults(func=cmd_generate)

    # Interpolate command
    interpolate_parser = subparsers.add_parser(
        "interpolate", help="Interpolate between two colors using various methods"
    )
    interpolate_parser.add_argument(
        "start_color", help="Starting hex color (e.g., #FF0000)"
    )
    interpolate_parser.add_argument(
        "end_color", help="Ending hex color (e.g., #0000FF)"
    )
    interpolate_parser.add_argument(
        "steps",
        type=int,
        default=8,
        nargs="?",
        help="Number of interpolation steps (default: 8)",
    )
    interpolate_parser.add_argument(
        "--method",
        choices=[
            "linear",
            "cubic",
            "exponential",
            "sine",
            "cosine",
            "hermite",
            "quintic",
            "hsv",
            "lch",
        ],
        default="linear",
        help="Interpolation method (default: linear)",
    )
    interpolate_parser.add_argument(
        "--exponent",
        type=float,
        default=2,
        help="Exponent for exponential interpolation (default: 2)",
    )
    interpolate_parser.add_argument(
        "--output",
        choices=["list", "json", "yaml"],
        default="list",
        help="Output format (default: list)",
    )
    interpolate_parser.add_argument("--name", help="Name for the generated palette")
    interpolate_parser.add_argument(
        "--simple-names", action="store_true", help="Use simple color names"
    )
    interpolate_parser.add_argument(
        "--analyze", action="store_true", help="Show perceptual analysis"
    )
    interpolate_parser.add_argument(
        "--validate", action="store_true", help="Validate gradient uniqueness"
    )
    interpolate_parser.set_defaults(func=cmd_interpolate)

    # Gradient command
    gradient_parser = subparsers.add_parser(
        "gradient",
        help="Generate a 16-color lightness gradient from a single color",
    )
    gradient_parser.add_argument("color", help="Base hex color (e.g., #FF0000)")
    gradient_parser.add_argument(
        "--method",
        choices=[
            "lch-lightness",
            "linear",
            "cubic",
            "exponential",
            "sine",
            "cosine",
            "hermite",
            "quintic",
            "hsv",
            "lch",
        ],
        default="lch-lightness",
        help="Interpolation method (default: lch-lightness)",
    )
    gradient_parser.add_argument(
        "--exponent",
        type=float,
        default=2,
        help="Exponent for exponential interpolation (default: 2)",
    )
    gradient_parser.add_argument(
        "--output",
        choices=["list", "json", "yaml"],
        default="list",
        help="Output format (default: list)",
    )
    gradient_parser.add_argument("--name", help="Name for the generated palette")
    gradient_parser.add_argument(
        "--simple-names", action="store_true", help="Use simple color names"
    )
    gradient_parser.add_argument(
        "--analyze", action="store_true", help="Show perceptual analysis"
    )
    gradient_parser.add_argument(
        "--validate", action="store_true", help="Validate gradient uniqueness"
    )
    gradient_parser.set_defaults(func=cmd_gradient)

    # Palette command
    palette_parser = subparsers.add_parser("palette", help="Generate color palettes")
    palette_parser.add_argument(
        "--method",
        choices=["perceptual", "optimal", "uniform", "syntax"],
        default="perceptual",
        help="Generation method: perceptual (Delta E), optimal (max distinguishability), uniform (30° steps), syntax (syntax highlighting optimized) (default: perceptual)",
    )
    palette_parser.add_argument(
        "--from-color",
        help="Generate palette variations from a specific color (uses golden ratio method)",
    )
    palette_parser.add_argument(
        "--start-hue",
        type=int,
        help="Starting hue for generation (0-360) (used with optimal and uniform methods)",
    )
    palette_parser.add_argument(
        "--num-colors",
        type=int,
        default=12,
        help="Number of colors in palettes (default: 12)",
    )

    palette_parser.add_argument(
        "--output-format",
        choices=["class", "json", "list"],
        default="list",
        help="Output format (default: list)",
    )
    palette_parser.add_argument(
        "--no-analysis",
        action="store_true",
        help="Skip chromatic distance analysis output",
    )
    palette_parser.set_defaults(func=cmd_palette)

    # Package as Spyder-compatible package
    parser_python_package = subparsers.add_parser(
        "python-package",
        help="Export themes as single Spyder-compatible Python package",
    )
    parser_python_package.add_argument(
        "--themes", help="Comma-separated theme names (default: all)"
    )
    parser_python_package.add_argument(
        "--package-name",
        default="spyder_themes",
        help="Name of Python package (default: spyder_themes)",
    )
    parser_python_package.add_argument(
        "--output", "-o", help="Output directory (default: workspace/dist)"
    )
    parser_python_package.add_argument(
        "--with-pyproject",
        action="store_true",
        default=True,
        help="Generate pyproject.toml (default: True)",
    )
    parser_python_package.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Validate themes before packaging (default: True)",
    )
    parser_python_package.add_argument(
        "--run-build",
        action="store_true",
        help="After creating the package tree, run python -m build (wheel + sdist)",
    )
    parser_python_package.add_argument(
        "--build-outdir",
        metavar="DIR",
        help="Pass --outdir to build (default: <package_dir>/dist)",
    )
    parser_python_package.set_defaults(func=cmd_python_package)

    return parser


def main():
    """Main CLI entry point."""
    # Set up logging for CLI output
    setup_logging()

    parser = create_parser()

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return

    # Run the specified command
    try:
        args.func(args)
    except KeyboardInterrupt:
        _logger.warning("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        _logger.error("❌ Unexpected error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
