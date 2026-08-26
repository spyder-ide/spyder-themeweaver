# ThemeWeaver

ThemeWeaver is a Python tool to generate and export themes for the Spyder IDE with QDarkStyle integration. It builds consistent dark/light variants, exports Qt assets, and can package themes for Spyder.

## Project setup

This project uses [Pixi](https://pixi.sh/) for dependencies and tasks. Run tasks with `pixi run`; definitions live in `pyproject.toml`.

### Prerequisites

- [Pixi](https://pixi.sh/)
- Python 3.12+ (provided by the pixi environment)
- A supported Pixi platform: Linux x86_64, Windows x86_64, or macOS (Intel or Apple Silicon); see `tool.pixi.workspace.platforms` in `pyproject.toml`

### Installation

```bash
pixi install
pixi run python --version
```

## Quick start

Run the commands below from the **repository root** (where `pyproject.toml` and the `themes/` directory live) so default paths resolve correctly. Use `--theme-dir` if you run the CLI from another working directory.

```bash
# List themes in themes/
pixi run list-themes

# Export into build/ — one theme (dark + light), one variant only, or every theme
pixi run export spyder
pixi run export-light spyder
pixi run export-dark spyder
pixi run export-all

# Validate YAML theme config
pixi run validate solarized

# Validate contrast against bundled Spyder UI rules (dark/light)
pixi run validate-contrast zenburn
pixi run validate-contrast-all

# Preview (needs themes in build/ — export first)
pixi run export-all
pixi run preview

# Package for Spyder (needs themes in build/ — run export or export-all first; does not export)
pixi run package
pixi run package -- --themes dracula,solarized --output ./dist

# Export + package + twine check + editable install (local Spyder use)
pixi run deploy-local inkpot          # export one theme, then package all of build/
pixi run deploy-local-all             # export every theme, then package and install
```

Export tasks (`export`, `export-light`, `export-dark`, `export-all`) all call the `export` CLI and write under `build/`. The `package` task runs `python-package --run-build`: it copies themes from `build/` into a generated project under `dist/<package_name>/`, then runs `python -m build` to produce a wheel and sdist. It never runs export for you. `deploy-local <name>` exports that theme, then runs `package`, `package-check`, and `pip install -e dist/spyder_themes` (packaging still includes every theme already under `build/`). `deploy-local-all` does the same after `export-all`.

**Layout for PyPI artifacts:** Theme sources live under `dist/<package_name>/` (for example `dist/spyder_themes/pyproject.toml`, `README.md`, `LICENSE`, and the import package). By default, `python -m build` writes outputs into `dist/<package_name>/dist/` (for example `dist/spyder_themes/dist/*.whl` and `*.tar.gz`). If you pass `--build-outdir`, artifacts go to that directory instead. Run `twine check` and `twine upload` against the actual build output path.

The **Spyder theme bundle** has its own release version in `[tool.themeweaver.spyder-package].version` in `pyproject.toml`. It is independent of the `themeweaver` tool version. ThemeWeaver itself is not published to PyPI; only the generated Spyder package is intended for upload.

Theme generation (colors or YAML) is documented under [Theme generation](#theme-generation).

## CLI reference

Use `pixi run cli …` for flags not covered by a task, or `pixi run cli <command> --help`.

### Theme management

The `list-themes` Pixi task runs the CLI `list` subcommand (`pixi run cli list`).

```bash
pixi run list-themes
pixi run theme-info solarized
pixi run validate solarized
```

### Theme export

Exports theme assets under `build/` using QDarkStyle tooling.

```bash
# Pixi shortcuts
pixi run export spyder
pixi run export-dark spyder
pixi run export-light spyder
pixi run export-all

# Direct CLI (for additional flags)
pixi run cli export --theme spyder --variants dark,light
pixi run cli export --all --compile-for qtpy
pixi run cli export --theme spyder --generate-palette-images
```

Export flags include:

- `--theme` or `--all` (required, mutually exclusive)
- `--variants` (`dark`, `light`, or both)
- `--theme-dir` (source theme directory)
- `-o` / `--output` (build destination)
- `--compile-for` (QDarkStyle `_rc` target; default: `qtpy`)
- `--generate-palette-images` (emit `palette.svg` and `palette.png`; default: off)

Theme ids that contain shell metacharacters (for example `notepad++`) must be quoted when passed on the shell: `pixi run export 'notepad++'`.

Export also writes Spyder help `default.css` and `appeal.css` for each variant. Themes may override individual CSS color mappings in `mappings.yaml`; see [Help CSS overrides](#help-css-overrides) and [Appeal CSS overrides](#appeal-css-overrides).

### Dev sync

`dev-sync` exports one or more themes and copies them into an editable `spyder_themes` tree (default `dist/spyder_themes/spyder_themes`) for a fast install-free edit loop. Prefer this while iterating; use `deploy-local` / `deploy-local-all` when you want a full package build and `pip install -e`.

```bash
pixi run dev-sync inkpot
pixi run cli dev-sync --theme inkpot,dracula
pixi run cli dev-sync --theme inkpot --skip-export   # sync from build/ only
```

### Help CSS overrides

Optional `css_overrides` in a theme’s `mappings.yaml` replace entries from the built-in help CSS color map. Omit the section to keep defaults. Keys are CSS custom properties (for example `--hover-color`). Values are palette attributes (`COLOR_ACCENT_2`), color-class refs (`Primary.B30`), or a `{dark, light}` map (both keys required). Unknown CSS keys are rejected.

```yaml
css_overrides:
  --hover-color: COLOR_ACCENT_2
  --border-color:
    dark: Primary.B60
    light: Primary.B100
```

### Appeal CSS overrides

Optional `appeal_overrides` in a theme’s `mappings.yaml` replace entries from the built-in appeal CSS color map used for `appeal.css`. Omit the section to keep defaults. Keys are appeal CSS custom properties (for example `--link`). Values follow the same rules as `css_overrides`. Unknown keys are rejected.

```yaml
appeal_overrides:
  --link: COLOR_ACCENT_2
  --border-primary:
    dark: Primary.B60
    light: Primary.B100
```

### Contrast validation

Checks resolved theme colors against rule sets in `src/themeweaver/contrast/` (`rules_dark.yaml`, `rules_light.yaml`). Override with `--rules-dir` if you maintain a fork of the rules.

```bash
pixi run validate-contrast zenburn
pixi run validate-contrast zenburn --variant dark
pixi run validate-contrast zenburn --verbose
pixi run validate-contrast-all
```

Same options apply when using the CLI directly: `pixi run cli validate-contrast --help`.

### Spyder Python package (`python-package`)

Creates a single installable Python package from exported themes under `build/`. Export themes before packaging. With `--run-build` (used by the `package` Pixi task), the CLI also runs `python -m build` on the generated project so wheel and sdist appear under `dist/<package_name>/dist/`.

```bash
pixi run package
pixi run package -- --themes catppuccin-mocha,dracula --output ./dist
pixi run cli python-package --package-name my_spyder_themes --output ./dist --run-build
pixi run cli python-package --run-build --build-outdir /path/to/out   # optional custom output for build artifacts
```

Flags include `--themes` (comma-separated), `--package-name`, `-o` / `--output`, `--with-pyproject`, `--validate`, `--run-build`, and `--build-outdir`.

#### PyPI: check and upload

After `pixi run package` (with default package name `spyder_themes`):

```bash
pixi run package-check   # run after `package`; fails if dist/spyder_themes/dist/ has no artifacts yet
# optional: pip install dist/spyder_themes/dist/spyder_themes-*.whl in a clean environment

pixi run publish-testpypi   # TestPyPI — create an API token and configure ~/.pypirc or TWINE_* env vars
pixi run publish-pypi       # PyPI — same; use account tokens from https://pypi.org
```

Run `twine check` before every upload; fix any reported issues. See the [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/) tutorial for TestPyPI vs production and token scopes.

These tasks target `dist/spyder_themes/dist/*` (the default package name). If you package with `--package-name <name>`, run `twine check` / `twine upload` against `dist/<name>/dist/*` (or your `--build-outdir` path).

Optional `[project.urls]` for the generated package can be set via `homepage` and `repository` under `[tool.themeweaver.spyder-package]` in this repo’s `pyproject.toml`.

Archive packaging (ZIP / tar.gz / folder) for loose theme folders is implemented in `ThemePackager` in the Python API only; there is no CLI subcommand for it.

### Local deploy

```bash
pixi run deploy-local inkpot      # export inkpot → package all of build/ → twine check → pip install -e
pixi run deploy-local-all         # export-all → package → twine check → pip install -e
```

`deploy-local` does not limit packaging to the named theme; `package` still includes every exported theme present under `build/`.

### Theme generation

The `generate` command writes a new theme directory under `themes/<name>/` in the current working directory (or under `--output-dir`). It produces three files: `theme.yaml` (metadata), `colorsystem.yaml` (palette definitions), and `mappings.yaml` (semantic UI and syntax references). Those sources are what `export` reads; generation does not write to `build/`.

#### Six seed colors

The six inputs are not the entire UI palette. They seed the generator: each value anchors a family of derived colors (primary/secondary UI, state colors, group gradients, etc.) that fill `colorsystem.yaml` and drive `mappings.yaml`.

| Position | Role |
| -------- | ---- |
| 1 | Primary |
| 2 | Secondary |
| 3 | Error |
| 4 | Success |
| 5 | Warning |
| 6 | Group (starting point for group/syntax-related ramps) |

#### Hex format

- **CLI (`--colors`, `--syntax-colors-dark`, `--syntax-colors-light`):** each color must be `#` followed by exactly six hexadecimal digits (`#RRGGBB`). Shorthand `#RGB` is rejected during CLI validation.
- **YAML (`colors`, `syntax-colors`):** each string must be `#` followed by exactly six hexadecimal digits (`#RRGGBB`). Shorthand `#RGB` is rejected.

#### From the CLI

```bash
pixi run generate my_theme \
  --colors "#1e1e2e" "#b4befe" "#f38ba8" "#a6e3a1" "#fab387" "#eba0ac" \
  --display-name "My Custom Theme" \
  --description "Generated from base colors" \
  --author "Your Name" \
  --tags "custom,dark"
```

Example with syntax seed and editor formatting:

```bash
pixi run generate my_theme \
  --colors "#1e1e2e" "#b4befe" "#f38ba8" "#a6e3a1" "#fab387" "#eba0ac" \
  --syntax-colors-dark "#89b4fa" \
  --syntax-colors-light "#456492" \
  --syntax-format "keyword:bold,comment:italic,string:none"
```

| Flag | Purpose |
| ---- | ------- |
| `--variants dark light` | Emit only the listed variants (default: both). Syntax palettes for a variant are only built if that variant is included. |
| `--overwrite` | Replace an existing `themes/<name>/` directory. |
| `--output-dir <path>` | Parent directory for themes (default: `./themes`). Afterward, pass `--theme-dir` to `export` if you did not use the default. |
| `--simple-names` | Use simple internal color names instead of creative names in generated data. |
| `--syntax-format` | See [Syntax format](#syntax-format) below. |
| `--syntax-colors-dark` / `--syntax-colors-light` | See [Syntax colors](#syntax-colors) below. |
| `--validate-contrast` / `--no-validate-contrast` | After generation, run contrast checks against bundled rules (default: on). Failures are logged; generation still completes. |

#### Syntax colors

Syntax highlighting lives in dedicated palettes in `colorsystem.yaml` (names like `…SyntaxDark` / `…SyntaxLight`, or `AutoSyntaxDark` / `AutoSyntaxLight` when derived automatically). `mappings.yaml` points editor roles at slots `Syntax.B10`…`Syntax.B170` (dark) and `SyntaxLight.B10`…`SyntaxLight.B170` (light).

**Default (no `--syntax-colors-*` / no `syntax-colors` in YAML)**

If you do not pass any syntax colors for either variant, the tool builds **AutoSyntaxDark** and **AutoSyntaxLight** from the generated **GroupDark** and **GroupLight** palettes so syntax stays coherent with the group colors.

**One seed per variant**

Pass **exactly one** hex color for `--syntax-colors-dark` and/or `--syntax-colors-light`, or in YAML a list of length 1 under `syntax-colors.dark` / `syntax-colors.light`. The generator runs the same syntax palette algorithm as `pixi run cli palette --method syntax --from-color <hex>`: it produces **17** colors (`B10`…`B170`) distributed in LCH space from that seed (golden-ratio hue steps, bounded lightness/chroma ranges).

**Full palette (17 colors)**

Pass **exactly 17** space-separated hex values on the CLI, or a YAML list of length 17. They are assigned **in order** to `B10` through `B170` with no further adjustment—the i-th color (1-based) becomes `B(i*10)`.

| Index (1-based) | Slot | Semantic role in `mappings` (dark uses `Syntax.*`, light uses `SyntaxLight.*`) |
| --------------- | ---- | -------------------------------------------------------------------------------- |
| 1 | B10 | `EDITOR_CURRENTLINE` |
| 2 | B20 | `EDITOR_CURRENTCELL` |
| 3 | B30 | `EDITOR_OCCURRENCE` |
| 4 | B40 | `EDITOR_CTRLCLICK` |
| 5 | B50 | `EDITOR_SIDEAREAS` |
| 6 | B60 | `EDITOR_MATCHED_P` (matched parentheses) |
| 7 | B70 | `EDITOR_UNMATCHED_P` (unmatched parentheses) |
| 8 | B80 | `EDITOR_NORMAL` |
| 9 | B90 | `EDITOR_KEYWORD` |
| 10 | B100 | `EDITOR_MAGIC` |
| 11 | B110 | `EDITOR_BUILTIN` |
| 12 | B120 | `EDITOR_DEFINITION` |
| 13 | B130 | `EDITOR_COMMENT` |
| 14 | B140 | `EDITOR_STRING` |
| 15 | B150 | `EDITOR_NUMBER` |
| 16 | B160 | `EDITOR_INSTANCE` |
| 17 | B170 | `EDITOR_SYMBOL` (operators, brackets, punctuation) |

Editor **background** for the dark/light templates uses **Primary.B10**, not the syntax palette. A concrete hand-tuned 17-color layout with comments per slot is in `themes/catppuccin-mocha/colorsystem.yaml` under `CatppuccinMochaSyntaxDark` / `CatppuccinMochaSyntaxLight`.

**Mixing dark, light, and variants**

- You may set only dark, only light, or both. Counts are validated per variant: each side must be **1** or **17** colors, never another length.
- If you request **both** variants but supply syntax colors for **only one** side, the missing side gets a **fallback** palette generated from a neutral gray seed (`DefaultSyntaxDark` / `DefaultSyntaxLight`), not the auto-from-group path. To avoid that, either omit all explicit syntax colors (auto-from-group), or supply seeds/lists for both variants you care about.
- If you pass **only** `--syntax-colors-light` (no dark), the generator reuses the light syntax palette name for **both** `Syntax` and `SyntaxLight` class mappings; the symmetric case applies when only dark is set.
- If `--variants` is only `dark` or only `light`, syntax entries for the other variant are not added to the colorsystem.

**Discovering 17 colors**

To print a generated syntax ramp as hex values you can paste into YAML or the CLI, use:

```bash
pixi run cli palette --method syntax --from-color "#89b4fa" --output-format list
```

Adjust `--output-format` if you prefer another shape (`pixi run cli palette --help`).

#### Syntax format

`--syntax-format` sets bold and italic for editor syntax roles. It is a comma-separated list of `element:style` pairs. **Elements** (lowercase): `normal`, `keyword`, `magic`, `builtin`, `definition`, `comment`, `string`, `number`, `instance`, `symbol`. **Styles**: `none`, `bold`, `italic`, `both` (bold and italic). Whitespace around tokens is trimmed. Unknown element names or malformed segments (missing `:`) are skipped without error.

Defaults when an element is omitted match the historical Spyder-style template: for example `keyword` and `magic` are bold, `comment` and `instance` are italic, others are plain. Each specified element **overrides** that default for bold/italic only; later pairs in the string override earlier ones for the same element.

In YAML, `syntax-format` is a **map** from element name to style string; it is converted internally to the same comma-separated form. Map key order is not semantically significant.

The exporter stores mappings as `[color, bold, italic]` lists for the editor entries that support formatting.

#### From a YAML definition file

```bash
pixi run generate my_theme --from-yaml theme-definition.yaml
```

The file must have **exactly one** top-level key: the theme id inside the YAML. The **directory name** is always the `generate` argument (`my_theme` above), not that key. If the YAML id and CLI name differ, the CLI name is used and a warning is printed.

YAML fields (under that single top-level theme key):

| Field | Required | Notes |
| ----- | -------- | ----- |
| `colors` | Yes | Six hex strings, same order as the seed table above. |
| `overwrite` | No | Boolean; same as `--overwrite`. |
| `variants` | No | List such as `[dark, light]`; default both. |
| `display-name`, `description`, `author` | No | Metadata for `theme.yaml`. |
| `tags` | No | YAML list of strings (or omit). |
| `syntax-format` | No | Map of element → `none` / `bold` / `italic` / `both` (same elements as CLI). |
| `syntax-colors` | No | Optional map with `dark` and/or `light` keys; each value is a YAML list of **1** or **17** hex strings (see [Syntax colors](#syntax-colors)). |

If `syntax-colors` is omitted entirely, syntax colors are derived from the group palettes (auto syntax). If `variants` is omitted, both dark and light are generated.

**Example `theme-definition.yaml`**

The top-level key is the theme id stored in the YAML; the CLI still chooses the folder name (`my_theme` here).

```yaml
my_theme:
  colors:
    - "#1e1e2e"
    - "#b4befe"
    - "#f38ba8"
    - "#a6e3a1"
    - "#fab387"
    - "#eba0ac"
  display-name: "My Custom Theme"
  description: "Generated from a definition file"
  author: "Your Name"
  tags:
    - custom
    - dark
  variants:
    - dark
    - light
  overwrite: false
  # Optional: per-variant syntax seeds (1 hex each) — same effect as --syntax-colors-dark/light
  syntax-colors:
    dark:
      - "#89b4fa"
    light:
      - "#456492"
  # Optional: editor bold/italic — same meaning as --syntax-format
  syntax-format:
    keyword: bold
    comment: italic
    string: none
```

#### After generation

Run `pixi run validate <name>` on the new tree if you want structural checks only, or `pixi run validate-contrast <name>` for Spyder rule checks. To produce QSS under `build/`, run `pixi run export <name>` (and add `--theme-dir` if you used `--output-dir`).

For a hand-maintained reference layout, see `themes/catppuccin-mocha/` (`colorsystem.yaml`, `mappings.yaml`, `theme.yaml`).

### Color utilities

These commands print palettes to stdout (and optional logging). They do not modify `themes/` unless you copy values yourself. Use `pixi run cli <command> --help` for the full flag list.

#### `palette`

Builds **GroupDark** and **GroupLight** sets (or a single **Syntax** palette) as named steps `B10`, `B20`, … for groups, or `B10`…`B170` for syntax (17 colors, including the slot used for `EDITOR_SYMBOL`). Default `--num-colors` is 12 for group methods; `--method syntax` uses the full syntax size.

| `--method` | Behavior |
| ---------- | -------- |
| `perceptual` (default) | Spaced hues for dark and light “group” palettes; optional `--start-hue` (0–360). If you omit `--start-hue`, defaults are around 37° (dark) and 53° (light). |
| `optimal` | Colors tuned for distinguishability; `--start-hue` optional. |
| `uniform` | Hue steps of about 30° around the wheel. |
| `syntax` | 17-color syntax palette (B10–B170) from a seed; **requires** `--from-color`. |

**`--from-color` precedence:** If you pass `--from-color` and the method is **not** `syntax`, the implementation uses a golden-ratio-based expansion from that seed for GroupDark/GroupLight; the chosen `perceptual` / `optimal` / `uniform` method is **not** used in that branch. For `syntax`, `--from-color` is required.

| Other flags | Purpose |
| ----------- | ------- |
| `--output-format` | `list` (human-readable), `json`, or `class` (Python-like class snippets for pasting). |
| `--no-analysis` | Skip the perceptual distance summary logging after the main output. |

```bash
pixi run palette --method optimal --num-colors 12
pixi run palette --method syntax --from-color "#FF5500"
pixi run palette --from-color "#3c3836" --num-colors 10 --output-format json
```

#### `gradient`

Produces **16** colors along black → base color → white. Default `--method` is `lch-lightness` (dedicated lightness ramp). Other methods reuse the same piecewise interpolation as `interpolate` (black→color, then color→white) to fill 16 steps.

| Flag | Purpose |
| ---- | ------- |
| `--output` | `list`, `json`, or `yaml`. |
| `--name` | Palette name in structured outputs. |
| `--simple-names` | Simpler auto-generated names where applicable. |
| `--analyze` | Print interpolation analysis. |
| `--validate` | Check gradient color uniqueness. |
| `--exponent` | Used when `--method exponential`. |

```bash
pixi run gradient "#DF8E1D"
pixi run gradient "#DF8E1D" --output yaml --name "MyPalette"
```

#### `interpolate`

Steps between two hex endpoints. Default `--method` is `linear`; default step count is **8** if you omit the third positional argument.

| `--method` values | Notes |
| ----------------- | ----- |
| `linear`, `cubic`, `exponential`, `sine`, `cosine`, `hermite`, `quintic` | Curve-shaped ramps in RGB space; `exponential` uses `--exponent` (default 2). |
| `hsv`, `lch` | Perceptual or hue-space paths. |

Pixi shortcuts fix the method:

```bash
pixi run interpolate "#002B36" "#EEE8D5" 16
pixi run interpolate-lch "#002B36" "#EEE8D5" 16
pixi run interpolate-hsv "#002B36" "#EEE8D5" 16
```

Shared flags with `gradient`: `--output` (`list` / `json` / `yaml`), `--name`, `--simple-names`, `--analyze`, `--validate`, `--exponent`.

## Development

```bash
pixi run lint
pixi run format
pixi run lint-fix
pixi run check   # runs lint (ruff check) only
pixi run test
pixi run test-cov
pixi run inspect-cov   # HTTP server for htmlcov; open http://127.0.0.1:8000
```

### Prek

```bash
pixi run prek-install
pixi run prek-run
pixi run prek-update
```

## Pixi tasks

| Task                    | Description                                                                                                                        |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `lint`                  | Ruff check                                                                                                                         |
| `format`                | Ruff format                                                                                                                        |
| `lint-fix`              | Ruff check with autofix                                                                                                            |
| `check`                 | Same as `lint`                                                                                                                     |
| `cli`                   | `python -m themeweaver.cli` (pass subcommands and flags)                                                                           |
| `export`                | Export one theme (`pixi run export <name>`)                                                                                        |
| `export-light`          | Export light variant only                                                                                                          |
| `export-dark`           | Export dark variant only                                                                                                           |
| `export-all`            | Export every theme into `build/`                                                                                                   |
| `dev-sync`              | Export theme(s) and sync into editable `spyder_themes` tree                                                                        |
| `package`               | `python-package --run-build`: layout under `dist/<name>/`, then wheel + sdist under `dist/<name>/dist/` (run `export` / `export-all` first; all built themes unless `--themes` after `--`) |
| `package-check`         | `twine check` on `dist/spyder_themes/dist/*` (default package name)                                                                 |
| `publish-testpypi`      | `twine upload` to TestPyPI (`dist/spyder_themes/dist/*`)                                                                            |
| `publish-pypi`          | `twine upload` to PyPI (`dist/spyder_themes/dist/*`)                                                                                |
| `deploy-local`          | Export one theme, then package all of `build/`, check, and `pip install -e dist/spyder_themes`                                       |
| `deploy-local-all`      | `export-all` → `package` → `package-check` → `pip install -e dist/spyder_themes`                                                    |
| `list-themes`           | List theme directories                                                                                                             |
| `theme-info`            | Show theme metadata                                                                                                                |
| `generate`              | Generate a theme from colors or YAML                                                                                               |
| `validate`              | Validate theme YAML                                                                                                                |
| `validate-contrast`     | Contrast rules for one theme                                                                                                       |
| `validate-contrast-all` | Contrast rules for all themes                                                                                                      |
| `interpolate`           | Color interpolation (`$START_COLOR`, `$END_COLOR`, `$STEPS`)                                                                       |
| `interpolate-lch`       | Interpolate with `--method lch`                                                                                                    |
| `interpolate-hsv`       | Interpolate with `--method hsv`                                                                                                    |
| `palette`               | Palette generation                                                                                                                 |
| `gradient`              | 16-color lightness gradient                                                                                                        |
| `preview`               | Qt preview app                                                                                                                     |
| `test`                  | Pytest                                                                                                                             |
| `test-cov`              | Pytest with coverage                                                                                                               |
| `inspect-cov`           | Serve HTML coverage report                                                                                                         |
| `prek-install`          | Install git hooks                                                                                                                  |
| `prek-run`              | Run hooks on all files                                                                                                             |
| `prek-update`           | Autoupdate hook revisions                                                                                                          |

## Dependencies

Managed in `pyproject.toml` (pixi): Python 3.12, [QDarkStyle](https://github.com/ColinDuquesnoy/QDarkStyleSheet) (git `develop` branch), PyYAML, colorspacious, qtsass, PyQt5 (conda `pyqt`; preview imports `PyQt5`), `qtpy`, `pyside6`, ruff, pytest, `prek`, PyPA `build` and `twine` (for the Spyder package wheel/sdist workflow), and related dev tools.

QDarkStyle tracks `develop` until a release exposes the APIs this project uses; the dependency pin will move to a published version when that is available.

## Project layout

```
themeweaver/
├── src/themeweaver/
│   ├── cli/           # CLI entrypoint and commands
│   ├── contrast/      # Contrast rules and validator
│   ├── core/          # Export, CSS/help generation, YAML loading
│   ├── color_utils/   # Palettes, interpolation, helpers
│   └── resources/     # Shared templates (e.g. help CSS rules)
├── themes/            # Theme sources (default cwd-relative)
├── scripts/           # Preview launcher and helpers
│   └── preview/       # Preview UI implementation
├── tests/
├── pyproject.toml
└── README.md
```

## Contributing

1. Fork the repository and create a branch.
2. Change the code; add tests where it helps.
3. Run `pixi run check` and `pixi run test`.
4. Open a pull request.

## License

This project is licensed under the MIT License; see [LICENSE](./LICENSE).
