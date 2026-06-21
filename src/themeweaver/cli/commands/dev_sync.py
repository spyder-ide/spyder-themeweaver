"""
Dev sync command: export a theme and copy it into an editable spyder_themes tree.
"""

from __future__ import annotations

import ast
import logging
import shutil
from pathlib import Path
from typing import Any

from themeweaver.cli.commands.theme_export import parse_theme_names
from themeweaver.cli.error_handling import handle_validation_error, operation_context
from themeweaver.core.theme_exporter import ThemeExporter

_logger = logging.getLogger(__name__)

_SYNC_IGNORE = shutil.ignore_patterns("palette.png", "palette.svg")


def _workspace_root() -> Path:
    return Path(__file__).parent.parent.parent.parent.parent


def _default_package_root() -> Path:
    return _workspace_root() / "dist" / "spyder_themes" / "spyder_themes"


def _theme_registered(package_root: Path, theme_name: str) -> bool:
    """Return True if ``theme_name`` appears in the package ``THEMES`` list."""
    init_path = package_root / "__init__.py"
    if not init_path.exists():
        return False

    tree = ast.parse(init_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "THEMES":
                if isinstance(node.value, ast.List):
                    names = [
                        elt.value
                        for elt in node.value.elts
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    ]
                    return theme_name in names
    return False


def sync_theme_to_package(
    build_dir: Path,
    package_root: Path,
    theme_name: str,
) -> Path:
    """Copy one exported theme from ``build_dir`` into the editable package tree."""
    src = build_dir / theme_name
    if not src.is_dir():
        raise FileNotFoundError(
            f"Exported theme '{theme_name}' not found in {build_dir}. "
            "Run export or dev-sync without --skip-export first."
        )

    required = ["__init__.py", "colorsystem.py", "palette.py"]
    missing = [name for name in required if not (src / name).exists()]
    if missing:
        raise ValueError(
            f"Theme '{theme_name}' in {build_dir} is missing required files: "
            f"{', '.join(missing)}"
        )

    package_root.mkdir(parents=True, exist_ok=True)
    dst = package_root / theme_name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=_SYNC_IGNORE)
    return dst


def cmd_dev_sync(args: Any) -> None:
    """Export theme(s) and sync them into an editable spyder_themes install tree."""
    build_dir = (
        Path(args.build_dir)
        if getattr(args, "build_dir", None)
        else _workspace_root() / "build"
    )
    package_root = (
        Path(args.package_dir)
        if getattr(args, "package_dir", None)
        else _default_package_root()
    )
    themes_dir = Path(args.theme_dir) if getattr(args, "theme_dir", None) else None
    theme_names = parse_theme_names(args.theme)
    skip_export = getattr(args, "skip_export", False)

    if not package_root.is_dir() or not (package_root / "__init__.py").exists():
        handle_validation_error(
            "Editable package tree not found at "
            f"{package_root}. Run once:\n"
            "  pixi run export-all\n"
            "  pixi run cli python-package\n"
            "  pip install -e dist/spyder_themes   # in spyder-dev env"
        )

    exporter = ThemeExporter(build_dir=build_dir, themes_dir=themes_dir)
    export_options = {}
    compile_for = getattr(args, "compile_for", "qtpy")
    if compile_for != "qtpy":
        export_options["compile_for"] = compile_for
    if getattr(args, "generate_palette_images", False):
        export_options["generate_palette_images"] = True

    synced: list[Path] = []
    with operation_context("Dev sync"):
        for theme_name in theme_names:
            if not skip_export:
                exporter.export_theme(theme_name, **export_options)

            if not _theme_registered(package_root, theme_name):
                _logger.warning(
                    "Theme '%s' is not listed in %s THEMES; Spyder will not "
                    "show it until you run a full python-package once.",
                    theme_name,
                    package_root / "__init__.py",
                )

            dst = sync_theme_to_package(build_dir, package_root, theme_name)
            synced.append(dst)
            _logger.info("✅ Synced '%s' to %s", theme_name, dst)

    _logger.info(
        "✅ Dev sync complete for %d theme(s). Restart Spyder to pick up changes.",
        len(synced),
    )
