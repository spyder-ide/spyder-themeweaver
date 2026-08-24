"""Tests for color name normalization and API parsing."""

import builtins
import importlib
import json
from unittest.mock import MagicMock, patch

from themeweaver.color_utils import color_names
from themeweaver.color_utils.color_names import normalize_color_name_to_safe_ascii


def test_normalize_apostrophe_and_spaces() -> None:
    assert normalize_color_name_to_safe_ascii("Guns N' Roses") == "GunsNRoses"
    assert normalize_color_name_to_safe_ascii("Red") == "Red"


def test_normalize_curly_apostrophe() -> None:
    # U+2019 RIGHT SINGLE QUOTATION MARK
    assert normalize_color_name_to_safe_ascii("Guns N\u2019 Roses") == "GunsNRoses"


def test_normalize_accented_latin() -> None:
    assert normalize_color_name_to_safe_ascii("Café Noir") == "CafeNoir"


def test_normalize_empty_or_whitespace() -> None:
    assert normalize_color_name_to_safe_ascii("") == ""
    assert normalize_color_name_to_safe_ascii("   ") == ""


def test_normalize_non_latin_only() -> None:
    assert normalize_color_name_to_safe_ascii("日本") == ""


def test_normalize_mixed_and_digits() -> None:
    assert normalize_color_name_to_safe_ascii("Level 42 Gray") == "Level42Gray"


def test_http_user_agent_handles_version_lookup_failure() -> None:
    with patch("importlib.metadata.version", side_effect=RuntimeError):
        assert color_names._http_user_agent().startswith("Themeweaver/0 ")


def test_randomname_import_error_sets_unavailable() -> None:
    original_import = builtins.__import__

    def reject_randomname(name, *args, **kwargs):
        if name == "randomname":
            raise ImportError
        return original_import(name, *args, **kwargs)

    try:
        with patch("builtins.__import__", side_effect=reject_randomname):
            importlib.reload(color_names)
        assert color_names.RANDOMNAME_AVAILABLE is False
    finally:
        importlib.reload(color_names)


def test_get_color_names_from_api_empty_and_invalid_inputs() -> None:
    assert color_names.get_color_names_from_api([]) == {}
    assert color_names.get_color_names_from_api(["bad"]) == {}


def test_get_color_names_from_api_parses_response_shapes() -> None:
    payload = {
        "colors": [
            {"requestedHex": "abcdef", "name": "Café Noir"},
            {"hex": "#123456", "name": "日本"},
            {"requestedHex": "#654321", "name": ""},
        ]
    }
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(payload).encode()

    with patch("urllib.request.urlopen", return_value=response):
        result = color_names.get_color_names_from_api(
            ["#ABCDEF", "#123456"], quiet=True
        )

    assert result == {
        "#ABCDEF": "CafeNoir",
        "#123456": "Color123456",
    }


def test_get_color_names_from_api_handles_request_failure() -> None:
    with patch("urllib.request.urlopen", side_effect=OSError("offline")):
        assert color_names.get_color_names_from_api(["#ABCDEF"]) == {}


def test_get_color_name_normalizes_input() -> None:
    with patch.object(
        color_names,
        "get_color_names_from_api",
        return_value={"#ABCDEF": "Example"},
    ) as get_names:
        assert color_names.get_color_name("abcdef", quiet=True) == "Example"
    get_names.assert_called_once_with(["#ABCDEF"], quiet=True)


def test_generate_random_adjective_fallbacks_and_success() -> None:
    with patch.object(color_names, "RANDOMNAME_AVAILABLE", False):
        assert color_names.generate_random_adjective() == "Creative"

    with (
        patch.object(color_names, "RANDOMNAME_AVAILABLE", True),
        patch("random.choice", return_value="speed"),
        patch.object(color_names.randomname, "generate", return_value="rapid"),
    ):
        assert color_names.generate_random_adjective() == "Rapid"

    with (
        patch.object(color_names, "RANDOMNAME_AVAILABLE", True),
        patch("random.choice", side_effect=RuntimeError),
    ):
        assert color_names.generate_random_adjective() == "Creative"


def test_get_palette_name_from_color_variants() -> None:
    with (
        patch.object(color_names, "get_color_name", return_value="Café Noir"),
        patch.object(color_names, "generate_random_adjective", return_value="Calm"),
    ):
        assert color_names.get_palette_name_from_color("#123456") == "CalmCafeNoir"
        assert (
            color_names.get_palette_name_from_color("#123456", creative=False)
            == "CafeNoir"
        )

    with (
        patch.object(color_names, "get_color_name", return_value="日本"),
        patch.object(color_names, "generate_random_adjective", return_value="Calm"),
    ):
        assert color_names.get_palette_name_from_color("#123456") == "CalmColor123456"

    with (
        patch.object(color_names, "get_color_name", return_value=None),
        patch.object(color_names, "generate_random_adjective", return_value="Calm"),
    ):
        assert color_names.get_palette_name_from_color("#123456") == "Calm123456"
        assert (
            color_names.get_palette_name_from_color("#123456", creative=False)
            == "123456"
        )
