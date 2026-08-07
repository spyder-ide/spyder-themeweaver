"""
Main theme exporter module for ThemeWeaver.

This module orchestrates the complete theme export process by coordinating:
- QDarkStyle asset generation (qdarkstyle_exporter.py)
- Spyder Python file generation (spyder_generator.py)
- Theme validation and metadata handling
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from themeweaver.core.colorsystem import load_theme_metadata_from_yaml
from themeweaver.core.help_css_generator import write_default_css
from themeweaver.core.palette import create_palettes
from themeweaver.core.qdarkstyle_exporter import QDarkStyleAssetExporter
from themeweaver.core.spyder_generator import SpyderFileGenerator

_logger = logging.getLogger(__name__)


class ThemeExporter:
    """Exports ThemeWeaver themes to complete Spyder-compatible packages."""

    def __init__(
        self, build_dir: Optional[Path] = None, themes_dir: Optional[Path] = None
    ) -> None:
        """Initialize the exporter.

        Args:
            build_dir: Directory to export themes to. Defaults to workspace 'build' directory.
            themes_dir: Directory where themes are stored. Defaults to package 'themes' directory.
        """
        # Get workspace root
        self.workspace_root = Path(__file__).parent.parent.parent.parent
        self.build_dir = build_dir or self.workspace_root / "build"
        self.themes_dir = themes_dir or Path.cwd() / "themes"

        # Initialize component exporters
        self.asset_exporter = QDarkStyleAssetExporter()
        self.spyder_generator = SpyderFileGenerator()

    def export_theme(
        self,
        theme_name: str,
        variants: Optional[List[str]] = None,
        cleanup_intermediate: bool = True,
        compile_for: str = "qtpy",
        generate_palette_images: bool = False,
    ) -> Dict[str, Path]:
        """Export a complete theme package with assets and Python files.

        Args:
            theme_name: Name of the theme to export
            variants: List of variants to export ('dark', 'light'). If None, exports all supported variants.
            cleanup_intermediate: Whether to remove intermediate files (SASS, redundant palette.py)
            compile_for: Qt binding target for compiled resource modules
            generate_palette_images: Whether to generate palette.svg and palette.png preview files

        Returns:
            Dict mapping variant names to their export directories

        Raises:
            FileNotFoundError: If theme doesn't exist
            ValueError: If theme has invalid configuration
        """
        _logger.info("🎨 Exporting theme: %s", theme_name)

        # Validate theme exists
        theme_dir = self.themes_dir / theme_name
        if not theme_dir.exists():
            raise FileNotFoundError(
                f"Theme '{theme_name}' not found in {self.themes_dir}"
            )

        # Load theme metadata
        theme_metadata = load_theme_metadata_from_yaml(
            theme_name, themes_dir=self.themes_dir
        )
        supported_variants = theme_metadata.get("variants", {})

        # Determine which variants to export
        if variants is None:
            variants = [v for v, enabled in supported_variants.items() if enabled]
        else:
            # Validate requested variants are supported
            for variant in variants:
                if not supported_variants.get(variant, False):
                    raise ValueError(
                        f"Variant '{variant}' not supported by theme '{theme_name}'"
                    )

        if not variants:
            raise ValueError(f"No variants to export for theme '{theme_name}'")

        _logger.info("📋 Exporting variants: %s", ", ".join(variants))

        # Create theme export directory
        export_dir = self.build_dir / theme_name
        export_dir.mkdir(parents=True, exist_ok=True)

        # Load theme palettes
        palettes = create_palettes(theme_name, themes_dir=self.themes_dir)

        exported_paths: Dict[str, Path] = {}

        # Export each variant
        for variant in variants:
            _logger.info("📋 Processing %s variant...", variant)

            palette_class = palettes.get_palette(variant)
            if palette_class is None:
                _logger.warning("⚠️  Skipping %s variant (not supported)", variant)
                continue

            # Export QDarkStyle assets for this variant
            variant_dir = self.asset_exporter.export_assets(
                palette_class,
                export_dir,
                variant,
                cleanup_intermediate,
                compile_for=compile_for,
                generate_palette_images=generate_palette_images,
            )
            write_default_css(variant_dir, variant, palette_class)
            exported_paths[variant] = variant_dir

        # Generate Spyder-compatible Python files
        self.spyder_generator.generate_files(
            theme_name, theme_metadata, export_dir, themes_dir=self.themes_dir
        )
        self._copy_theme_metadata(theme_name, export_dir)

        _logger.info("✅ Theme '%s' exported to: %s", theme_name, export_dir)
        return exported_paths

    def _copy_theme_metadata(self, theme_name: str, export_dir: Path) -> None:
        """Copy theme metadata YAML into the exported theme directory."""
        source = self.themes_dir / theme_name / "theme.yaml"
        destination = export_dir / "theme.yaml"
        if source.is_file():
            shutil.copy2(source, destination)
            _logger.info("📄 Copied metadata: %s", destination.name)

    def export_all_themes(
        self,
        cleanup_intermediate: bool = True,
        compile_for: str = "qtpy",
        generate_palette_images: bool = False,
    ) -> Dict[str, Dict[str, Path]]:
        """Export all available themes.

        Stops on the first theme that fails to export.

        Args:
            cleanup_intermediate: Whether to remove intermediate files (SASS, redundant palette.py)
            compile_for: Qt binding target for compiled resource modules
            generate_palette_images: Whether to generate palette.svg and palette.png preview files

        Returns:
            Dict mapping theme names to their variant export paths

        Raises:
            Exception: Re-raises the first export failure, with the theme name in the message.
        """
        exported_themes: Dict[str, Dict[str, Path]] = {}

        theme_dirs = sorted(
            (
                d
                for d in self.themes_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ),
            key=lambda p: p.name,
        )

        for theme_dir in theme_dirs:
            theme_name = theme_dir.name
            try:
                exported_themes[theme_name] = self.export_theme(
                    theme_name,
                    cleanup_intermediate=cleanup_intermediate,
                    compile_for=compile_for,
                    generate_palette_images=generate_palette_images,
                )
            except Exception as e:
                raise RuntimeError(f"Failed to export theme '{theme_name}': {e}") from e

        return exported_themes
