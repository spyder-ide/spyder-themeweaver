"""
Theme packaging command.

This module handles packaging of exported themes into compressed archives
with proper metadata inclusion for distribution.
"""

import logging
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Optional

from themeweaver.cli.error_handling import operation_context
from themeweaver.core.spyder_package_exporter import SpyderPackageExporter

_logger = logging.getLogger(__name__)


def _read_package_metadata_from_pyproject(workspace_root: Path) -> dict[str, Any]:
    """Read package metadata from pyproject.toml.

    Args:
        workspace_root: Root directory of the workspace

    Returns:
        Dictionary with package metadata, using defaults if not found
    """
    pyproject_path = workspace_root / "pyproject.toml"
    defaults = {
        "version": "0.1.0",
        "display_name": "Spyder Themes",
        "description": "Collection of themes for Spyder IDE",
        "author": "ThemeWeaver",
        "license": "MIT",
        "requires-python": ">=3.9",
        "homepage": "",
        "repository": "",
        "classifiers": [
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: User Interfaces",
            "Programming Language :: Python :: 3",
        ],
    }

    if not pyproject_path.exists():
        _logger.warning("pyproject.toml not found, using default metadata")
        return defaults

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        package_config = (
            data.get("tool", {}).get("themeweaver", {}).get("spyder-package", {})
        )
        # Merge with defaults to ensure all keys are present
        return {**defaults, **package_config}
    except Exception as e:
        _logger.warning("Failed to read package metadata from pyproject.toml: %s", e)
        return defaults


def _run_python_build(
    package_dir: Path,
    build_outdir: Optional[Path],
    *,
    verbose: bool = False,
) -> None:
    """Run ``python -m build`` on the generated project directory."""
    cmd: list[str] = [
        sys.executable,
        "-m",
        "build",
        "--verbose" if verbose else "--quiet",
        str(package_dir),
    ]
    if build_outdir is not None:
        cmd.extend(["--outdir", str(build_outdir)])
    _logger.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def cmd_python_package(args: Any) -> None:
    """Export themes as a single Spyder-compatible Python package."""
    verbose = getattr(args, "verbose", False)
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse theme names if provided
    theme_names = None
    if hasattr(args, "themes") and args.themes:
        theme_names = [t.strip() for t in args.themes.split(",")]

    # Create exporter
    exporter = SpyderPackageExporter(
        build_dir=Path(args.build_dir)
        if hasattr(args, "build_dir") and args.build_dir
        else None,
        output_dir=Path(args.output) if args.output else None,
        package_name=args.package_name
        if hasattr(args, "package_name")
        else "spyder_themes",
    )

    # Read package metadata from pyproject.toml
    metadata = _read_package_metadata_from_pyproject(exporter.workspace_root)

    with operation_context("Package creation"):
        package_dir = exporter.create_package(
            theme_names=theme_names,
            metadata=metadata,
            with_pyproject=getattr(args, "with_pyproject", True),
            validate=getattr(args, "validate", True),
        )

    if getattr(args, "run_build", False):
        build_outdir = (
            Path(args.build_outdir).resolve()
            if getattr(args, "build_outdir", None)
            else None
        )
        with operation_context("Building wheel and sdist"):
            _run_python_build(package_dir, build_outdir, verbose=verbose)
