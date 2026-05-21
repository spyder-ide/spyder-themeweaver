"""
Theme export command.
"""

import logging
from pathlib import Path
from typing import Any

from themeweaver.cli.error_handling import operation_context
from themeweaver.core.theme_exporter import ThemeExporter

_logger = logging.getLogger(__name__)


def parse_theme_names(theme_args: list[str]) -> list[str]:
    """Expand theme CLI arguments into a list of theme names."""
    names: list[str] = []
    for arg in theme_args:
        for part in arg.split(","):
            name = part.strip()
            if name:
                names.append(name)
    return names


def cmd_export(args: Any) -> None:
    """Export theme(s) to build directory."""

    # Determine build directory
    build_dir = Path(args.output) if args.output else None

    # Determine themes directory
    themes_dir = (
        Path(args.theme_dir) if hasattr(args, "theme_dir") and args.theme_dir else None
    )

    # Create exporter with custom directories
    exporter = ThemeExporter(build_dir=build_dir, themes_dir=themes_dir)
    raw_compile_for = getattr(args, "compile_for", None)
    compile_for = raw_compile_for if isinstance(raw_compile_for, str) else "qtpy"
    raw_generate_palette_images = getattr(args, "generate_palette_images", None)
    generate_palette_images = (
        raw_generate_palette_images
        if isinstance(raw_generate_palette_images, bool)
        else False
    )

    export_options = {}
    if compile_for != "qtpy":
        export_options["compile_for"] = compile_for
    if generate_palette_images:
        export_options["generate_palette_images"] = generate_palette_images

    if args.all:
        _logger.info("🎨 Exporting all themes...")
        with operation_context("Theme export"):
            exported = exporter.export_all_themes(**export_options)

            _logger.info("✅ Successfully exported %d themes:", len(exported))
            for theme_name, variants in exported.items():
                _logger.info("  • %s: %s", theme_name, ", ".join(variants.keys()))

    else:
        theme_names = parse_theme_names(args.theme)
        variants = args.variants.split(",") if args.variants else None

        with operation_context("Theme export"):
            for theme_name in theme_names:
                exported = exporter.export_theme(
                    theme_name,
                    variants,
                    **export_options,
                )

                _logger.info("✅ Successfully exported theme '%s':", theme_name)
                for variant, path in exported.items():
                    _logger.info("  • %s: %s", variant, path)
