"""Tests for SpyderPackageExporter."""

from pathlib import Path

from themeweaver.core.spyder_package_exporter import SpyderPackageExporter


def _minimal_exported_theme(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "__init__.py").write_text("# theme\n", encoding="utf-8")
    (path / "colorsystem.py").write_text("X = 1\n", encoding="utf-8")
    (path / "palette.py").write_text("Y = 2\n", encoding="utf-8")
    (path / "dark").mkdir()
    (path / "dark" / "stub.qss").write_text("/* */\n", encoding="utf-8")


class TestSpyderPackageExporter:
    def test_discover_themes_filters_incomplete(self, tmp_path: Path) -> None:
        build = tmp_path / "build"
        build.mkdir()
        good = build / "good"
        _minimal_exported_theme(good)
        bad = build / "bad"
        bad.mkdir()
        (bad / "colorsystem.py").write_text("x", encoding="utf-8")
        # missing palette.py

        exp = SpyderPackageExporter(build_dir=build, output_dir=tmp_path / "dist")
        assert exp._discover_themes() == ["good"]

    def test_validate_theme_missing_file(self, tmp_path: Path) -> None:
        t = tmp_path / "t"
        t.mkdir()
        (t / "__init__.py").write_text("", encoding="utf-8")
        (t / "colorsystem.py").write_text("", encoding="utf-8")
        # no palette.py
        exp = SpyderPackageExporter(build_dir=tmp_path / "b", output_dir=tmp_path / "d")
        assert exp._validate_theme(t) is False

    def test_validate_theme_no_variant_dirs(self, tmp_path: Path) -> None:
        t = tmp_path / "t"
        t.mkdir()
        for name in ("__init__.py", "colorsystem.py", "palette.py"):
            (t / name).write_text("", encoding="utf-8")
        exp = SpyderPackageExporter(build_dir=tmp_path / "b", output_dir=tmp_path / "d")
        assert exp._validate_theme(t) is False

    def test_create_package_skips_invalid_when_validate(self, tmp_path: Path) -> None:
        build = tmp_path / "build"
        out = tmp_path / "dist"
        bad = build / "broken"
        bad.mkdir(parents=True)
        (bad / "__init__.py").write_text("", encoding="utf-8")

        exp = SpyderPackageExporter(
            build_dir=build, output_dir=out, package_name="pkg_one"
        )
        pkg = exp.create_package(theme_names=["broken"], validate=True)
        inner = pkg / "pkg_one"
        assert inner.exists()
        assert not (inner / "broken").exists()

    def test_create_package_with_pyproject_and_metadata(self, tmp_path: Path) -> None:
        build = tmp_path / "build"
        _minimal_exported_theme(build / "alpha")
        out = tmp_path / "dist"
        meta = {
            "version": "2.0.0",
            "display_name": "DN",
            "description": "DD",
            "author": "AA",
            "license": "MIT",
            "requires-python": ">=3.10",
        }
        exp = SpyderPackageExporter(
            build_dir=build, output_dir=out, package_name="my_themes"
        )
        pkg = exp.create_package(
            theme_names=["alpha"], metadata=meta, with_pyproject=True, validate=True
        )
        init_py = pkg / "my_themes" / "__init__.py"
        assert init_py.read_text(encoding="utf-8").count("2.0.0") >= 1
        assert "DN" in init_py.read_text(encoding="utf-8")
        pp = pkg / "pyproject.toml"
        assert pp.exists()
        text = pp.read_text(encoding="utf-8")
        assert 'name = "my_themes"' in text
        assert "2.0.0" in text
        assert 'readme = "README.md"' in text
        assert 'license-files = ["LICENSE"]' in text
        assert '"**/*.yaml"' in text
        readme = (pkg / "README.md").read_text(encoding="utf-8")
        assert "## Included themes" in readme
        assert "- `alpha`" in readme
        assert "https://github.com/conradolandia/spyder-themeweaver" in readme
        assert (pkg / "LICENSE").is_file()

    def test_create_package_pyproject_includes_urls_when_set(
        self, tmp_path: Path
    ) -> None:
        build = tmp_path / "build"
        _minimal_exported_theme(build / "alpha")
        out = tmp_path / "dist"
        meta = {
            "version": "1.0.0",
            "display_name": "DN",
            "description": "DD",
            "author": "AA",
            "license": "MIT",
            "requires-python": ">=3.10",
            "homepage": "https://example.org/themes",
            "repository": "https://github.com/org/repo",
        }
        exp = SpyderPackageExporter(
            build_dir=build, output_dir=out, package_name="url_pkg"
        )
        pkg = exp.create_package(
            theme_names=["alpha"], metadata=meta, with_pyproject=True, validate=True
        )
        text = (pkg / "pyproject.toml").read_text(encoding="utf-8")
        assert "[project.urls]" in text
        assert "https://example.org/themes" in text
        assert "https://github.com/org/repo" in text
        assert "Operating System :: OS Independent" not in text
        readme = (pkg / "README.md").read_text(encoding="utf-8")
        assert "https://github.com/org/repo" in readme

    def test_create_package_pyproject_uses_custom_classifiers(
        self, tmp_path: Path
    ) -> None:
        build = tmp_path / "build"
        _minimal_exported_theme(build / "alpha")
        out = tmp_path / "dist"
        meta = {
            "version": "1.0.0",
            "display_name": "DN",
            "description": "DD",
            "author": "AA",
            "license": "MIT",
            "requires-python": ">=3.10",
            "classifiers": [
                "Programming Language :: Python :: 3.12",
                "Operating System :: OS Independent",
            ],
        }
        exp = SpyderPackageExporter(
            build_dir=build, output_dir=out, package_name="class_pkg"
        )
        pkg = exp.create_package(
            theme_names=["alpha"], metadata=meta, with_pyproject=True, validate=True
        )
        text = (pkg / "pyproject.toml").read_text(encoding="utf-8")
        assert "Programming Language :: Python :: 3.12" in text
        assert "Operating System :: OS Independent" in text
        assert "Development Status :: 4 - Beta" not in text

    def test_create_package_readme_source_uses_homepage_when_repository_missing(
        self, tmp_path: Path
    ) -> None:
        build = tmp_path / "build"
        _minimal_exported_theme(build / "alpha")
        out = tmp_path / "dist"
        meta = {
            "version": "1.0.0",
            "display_name": "DN",
            "description": "DD",
            "author": "AA",
            "license": "MIT",
            "requires-python": ">=3.10",
            "homepage": "https://example.org/themes",
        }
        exp = SpyderPackageExporter(
            build_dir=build, output_dir=out, package_name="url_pkg"
        )
        pkg = exp.create_package(
            theme_names=["alpha"], metadata=meta, with_pyproject=True, validate=True
        )
        readme = (pkg / "README.md").read_text(encoding="utf-8")
        assert "https://example.org/themes" in readme

    def test_create_package_without_pyproject(self, tmp_path: Path) -> None:
        build = tmp_path / "build"
        _minimal_exported_theme(build / "beta")
        out = tmp_path / "dist"
        exp = SpyderPackageExporter(build_dir=build, output_dir=out, package_name="p2")
        pkg = exp.create_package(
            theme_names=["beta"], with_pyproject=False, validate=True
        )
        assert not (pkg / "pyproject.toml").exists()
        assert (pkg / "p2" / "beta" / "palette.py").exists()

    def test_create_package_overwrites_existing(self, tmp_path: Path) -> None:
        build = tmp_path / "build"
        _minimal_exported_theme(build / "gamma")
        out = tmp_path / "dist"
        exp = SpyderPackageExporter(build_dir=build, output_dir=out, package_name="p3")
        pkg = exp.create_package(theme_names=["gamma"], validate=True)
        marker = pkg / "p3" / "OLD.txt"
        marker.write_text("old", encoding="utf-8")
        exp.create_package(theme_names=["gamma"], validate=True)
        assert not marker.exists()
        assert (pkg / "p3" / "gamma" / "palette.py").exists()

    def test_create_package_discover_all(self, tmp_path: Path) -> None:
        build = tmp_path / "build"
        _minimal_exported_theme(build / "z_theme")
        _minimal_exported_theme(build / "a_theme")
        out = tmp_path / "dist"
        exp = SpyderPackageExporter(build_dir=build, output_dir=out, package_name="p4")
        pkg = exp.create_package(theme_names=None, validate=True, with_pyproject=False)
        inner = pkg / "p4"
        names = {p.name for p in inner.iterdir() if p.is_dir()}
        assert names == {"a_theme", "z_theme"}
