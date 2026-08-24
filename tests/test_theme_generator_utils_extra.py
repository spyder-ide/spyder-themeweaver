"""Additional branch coverage for theme_generator_utils."""

from unittest.mock import patch

import pytest

from themeweaver.color_utils import theme_generator_utils as tgu


def _fake_palette(prefix: str) -> dict[str, str]:
    base = sum(ord(c) for c in prefix) % 120 + 80
    return {
        f"B{i * 10}": f"#{(base + i) % 256:02X}{(base + i * 2) % 256:02X}{(base + i * 3) % 256:02X}"
        for i in range(1, 18)
    }


def test_get_palette_names_fallback_for_empty_normalized_name() -> None:
    colors = ["#111111", "#222222", "#333333", "#444444", "#555555", "#666666"]
    color_names = {c: "name" for c in colors}

    with (
        patch(
            "themeweaver.color_utils.theme_generator_utils.normalize_color_name_to_safe_ascii",
            return_value="",
        ),
        patch(
            "themeweaver.color_utils.theme_generator_utils.generate_random_adjective",
            return_value="Calm",
        ),
    ):
        names = tgu.get_palette_names(colors, color_names)

    assert names["primary"] == "CalmColor111111"
    assert names["group_base"] == "CalmColor666666"


def test_get_palette_names_fallback_for_missing_api_name() -> None:
    colors = ["#111111", "#222222", "#333333", "#444444", "#555555", "#666666"]

    with patch.object(tgu, "generate_random_adjective", return_value="Calm"):
        names = tgu.get_palette_names(colors, {})

    assert names["primary"] == "Calm111111"
    assert names["group_base"] == "Calm666666"


def test_build_colorsystem_defaults_syntax_dark_only_variant() -> None:
    palettes = {
        "primary": [f"#A{i:02X}" for i in range(16)],
        "secondary": [f"#B{i:02X}" for i in range(16)],
        "error": [f"#C{i:02X}" for i in range(16)],
        "success": [f"#D{i:02X}" for i in range(16)],
        "warning": [f"#E{i:02X}" for i in range(16)],
    }
    names = {
        "primary": "P",
        "secondary": "S",
        "error": "E",
        "success": "U",
        "warning": "W",
        "group_base": "Group",
    }

    with patch(
        "themeweaver.color_utils.theme_generator_utils.generate_palettes_from_color"
    ) as mock_gen:
        mock_gen.side_effect = [
            (_fake_palette("D"), _fake_palette("L")),  # group
            _fake_palette("SD"),  # default dark syntax fallback
        ]
        colorsystem = tgu.build_colorsystem(
            palettes=palettes,
            names=names,
            group_initial_color="#123456",
            syntax_colors_dark=None,
            syntax_colors_light=None,
            variants=["dark"],
        )

    assert "AutoSyntaxDark" in colorsystem
    assert "AutoSyntaxLight" not in colorsystem
    assert "Logos" in colorsystem


def test_build_colorsystem_provided_light_syntax_list() -> None:
    palettes = {
        "primary": [f"#A{i:02X}" for i in range(16)],
        "secondary": [f"#B{i:02X}" for i in range(16)],
        "error": [f"#C{i:02X}" for i in range(16)],
        "success": [f"#D{i:02X}" for i in range(16)],
        "warning": [f"#E{i:02X}" for i in range(16)],
    }
    names = {
        "primary": "P",
        "secondary": "S",
        "error": "E",
        "success": "U",
        "warning": "W",
        "group_base": "Group",
        "syntax_light": "MySyntaxLight",
    }

    with (
        patch(
            "themeweaver.color_utils.theme_generator_utils.generate_palettes_from_color"
        ) as mock_gen,
        patch(
            "themeweaver.color_utils.theme_generator_utils.generate_syntax_palette_from_colors",
            return_value=_fake_palette("LS"),
        ),
    ):
        mock_gen.side_effect = [
            (_fake_palette("D"), _fake_palette("L")),  # group
            _fake_palette("DD"),  # default dark syntax fallback
        ]
        colorsystem = tgu.build_colorsystem(
            palettes=palettes,
            names=names,
            group_initial_color="#123456",
            syntax_colors_dark=None,
            syntax_colors_light=["#111111"] * 17,
            variants=["dark", "light"],
        )

    assert "DefaultSyntaxDark" in colorsystem
    assert "MySyntaxLight" in colorsystem


def test_build_colorsystem_default_variants_and_custom_logos() -> None:
    palettes = {
        key: [f"#{i:06X}" for i in range(16)]
        for key in ("primary", "secondary", "error", "success", "warning")
    }
    names = {
        "primary": "P",
        "secondary": "S",
        "error": "E",
        "success": "U",
        "warning": "W",
        "group_base": "Group",
    }
    logos = {"B10": "#123456"}

    with (
        patch.object(
            tgu,
            "generate_palettes_from_color",
            return_value=(_fake_palette("D"), _fake_palette("L")),
        ),
        patch.object(
            tgu,
            "generate_syntax_from_group_colors",
            return_value=(_fake_palette("SD"), _fake_palette("SL")),
        ),
    ):
        colorsystem = tgu.build_colorsystem(
            palettes, names, "#123456", logos=logos, variants=None
        )

    assert "AutoSyntaxDark" in colorsystem
    assert "AutoSyntaxLight" in colorsystem
    assert colorsystem["Logos"] is logos


def test_build_colorsystem_with_dark_list_and_light_seed() -> None:
    palettes = {
        key: [f"#{i:06X}" for i in range(16)]
        for key in ("primary", "secondary", "error", "success", "warning")
    }
    names = {
        "primary": "P",
        "secondary": "S",
        "error": "E",
        "success": "U",
        "warning": "W",
        "group_base": "Group",
        "syntax_dark": "DarkSyntax",
        "syntax_light": "LightSyntax",
    }

    with (
        patch.object(tgu, "generate_palettes_from_color") as generate,
        patch.object(
            tgu,
            "generate_syntax_palette_from_colors",
            return_value=_fake_palette("SD"),
        ),
    ):
        generate.side_effect = [
            (_fake_palette("D"), _fake_palette("L")),
            _fake_palette("SL"),
        ]
        colorsystem = tgu.build_colorsystem(
            palettes,
            names,
            "#123456",
            syntax_colors_dark=["#111111"] * 17,
            syntax_colors_light="#222222",
        )

    assert "DarkSyntax" in colorsystem
    assert "LightSyntax" in colorsystem


def test_build_colorsystem_with_dark_seed_and_default_light() -> None:
    palettes = {
        key: [f"#{i:06X}" for i in range(16)]
        for key in ("primary", "secondary", "error", "success", "warning")
    }
    names = {
        "primary": "P",
        "secondary": "S",
        "error": "E",
        "success": "U",
        "warning": "W",
        "group_base": "Group",
    }

    with patch.object(tgu, "generate_palettes_from_color") as generate:
        generate.side_effect = [
            (_fake_palette("D"), _fake_palette("L")),
            _fake_palette("SD"),
            _fake_palette("SL"),
        ]
        colorsystem = tgu.build_colorsystem(
            palettes,
            names,
            "#123456",
            syntax_colors_dark="#111111",
            syntax_colors_light=None,
        )

    assert "DefaultSyntaxDark" in colorsystem
    assert "DefaultSyntaxLight" in colorsystem


def test_parse_syntax_format_invalid_tokens_ignored() -> None:
    fmt = "keyword:bold,unknown:bold,comment:both,broken,instance:none"
    parsed = tgu.parse_syntax_format(fmt)
    assert parsed["keyword"]["bold"] is True
    assert parsed["comment"]["bold"] is True and parsed["comment"]["italic"] is True
    assert parsed["instance"]["bold"] is False and parsed["instance"]["italic"] is False


def test_validate_input_colors_with_invalid_syntax_entry() -> None:
    ok, msg = tgu.validate_input_colors(
        "#1A72BB",
        "#FF5500",
        "#E11C1C",
        "#00AA55",
        "#FF9900",
        "#8844EE",
        syntax_colors=["#777777", "#GGGGGG"],
    )
    assert ok is False
    assert "syntax_2" in msg


@pytest.mark.parametrize(
    ("syntax_dark", "syntax_light", "expected_dark", "expected_light"),
    [
        (["#111111"], None, "PSyntaxDark", "PSyntaxDark"),
        (None, "#222222", "PSyntaxLight", "PSyntaxLight"),
        ("#111111", "#222222", "PSyntaxDark", "PSyntaxLight"),
        (None, ["#222222"], "PSyntaxLight", "PSyntaxLight"),
    ],
)
def test_generate_theme_variant_syntax_paths(
    syntax_dark, syntax_light, expected_dark, expected_light
) -> None:
    names = {
        "primary": "P",
        "secondary": "S",
        "error": "E",
        "success": "U",
        "warning": "W",
        "group_base": "G",
    }

    with (
        patch.object(tgu, "generate_main_palettes", return_value={}),
        patch.object(tgu, "get_color_names_from_api", return_value={}),
        patch.object(tgu, "get_palette_names", return_value=names.copy()),
        patch.object(tgu, "build_colorsystem", return_value={}),
        patch.object(tgu, "parse_syntax_format", return_value={}),
        patch.object(tgu, "create_mappings", return_value={}) as create,
    ):
        result = tgu.generate_theme_from_colors(
            "#100000",
            "#200000",
            "#300000",
            "#400000",
            "#500000",
            "#600000",
            syntax_colors_dark=syntax_dark,
            syntax_colors_light=syntax_light,
            variants=["dark"],
        )

    assert result["variants"] == ["dark"]
    assert create.call_args.args[1:3] == (expected_dark, expected_light)


def test_validate_input_colors_with_syntax_seed() -> None:
    with (
        patch.object(tgu, "hex_to_rgb", return_value=(128, 128, 128)),
        patch.object(tgu, "rgb_to_lch", return_value=(50, 20, 30)),
    ):
        valid, message = tgu.validate_input_colors(
            "#111111",
            "#222222",
            "#333333",
            "#444444",
            "#555555",
            "#666666",
            syntax_colors="#777777",
        )

    assert valid is True
    assert message == ""
