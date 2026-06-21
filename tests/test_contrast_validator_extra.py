"""Additional branch coverage for contrast validator internals."""

from unittest.mock import patch

from themeweaver.contrast.validator import _sort_rules_by_dependency, validate_theme


def test_sort_rules_by_dependency_places_references_first() -> None:
    rules = {
        "R2": {"greater_than": "R1"},
        "R1": {"min_ratio": 3},
        "R3": {"greater_than": "R2"},
    }
    order = _sort_rules_by_dependency(rules)
    assert order.index("R1") < order.index("R2") < order.index("R3")


def test_validate_theme_missing_fg_or_bg_adds_failure() -> None:
    with (
        patch(
            "themeweaver.contrast.validator.load_rules",
            return_value={"R1": {"fg": "FG", "bg": "BG"}},
        ),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch(
            "themeweaver.contrast.validator.get_color_for_rule",
            side_effect=[None, "#000000"],
        ),
    ):
        result = validate_theme("t", "dark")
    assert result.failed_count == 1
    assert "Missing color" in result.results[0].message


def test_validate_theme_line_bg_missing_branch() -> None:
    rule = {"fg": "FG", "bg": "BG", "line_bg": "LBG", "fg_lbg_min": 3, "fg_bg_min": 4}
    with (
        patch("themeweaver.contrast.validator.load_rules", return_value={"R1": rule}),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch(
            "themeweaver.contrast.validator.get_color_for_rule",
            side_effect=["#111111", "#222222", None],
        ),
    ):
        result = validate_theme("t", "dark")
    assert result.failed_count == 1
    assert result.results[0].message == "Missing line_bg"


def test_validate_theme_standard_rule_with_opacity_suggestion() -> None:
    rule = {"fg": "FG", "bg": "BG", "fg_opacity": 0.75, "min_ratio": 7}
    with (
        patch("themeweaver.contrast.validator.load_rules", return_value={"R1": rule}),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch(
            "themeweaver.contrast.validator.get_color_for_rule",
            side_effect=["#111111", "#222222"],
        ),
        patch("themeweaver.contrast.validator.blend_alpha", return_value="#333333"),
        patch("themeweaver.contrast.validator.contrast_ratio", return_value=2.0),
    ):
        result = validate_theme("t", "dark", include_suggestions=True)
    assert result.failed_count == 1
    assert "opacity" in (result.results[0].suggestion or "")


def test_validate_theme_greater_than_dependency_failure() -> None:
    rules = {
        "A": {"fg": "FG", "bg": "BG", "min_ratio": 3},
        "B": {"fg": "FG", "bg": "BG", "greater_than": "A"},
    }
    with (
        patch("themeweaver.contrast.validator.load_rules", return_value=rules),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch(
            "themeweaver.contrast.validator.get_color_for_rule",
            side_effect=["#111111", "#222222", "#111111", "#222222"],
        ),
        patch(
            "themeweaver.contrast.validator.contrast_ratio",
            side_effect=[5.0, 4.0],
        ),
    ):
        result = validate_theme("t", "dark", include_suggestions=False)
    r_by_id = {r.rule_id: r for r in result.results}
    assert r_by_id["A"].passed is True
    assert r_by_id["B"].passed is False
    assert "greater_than" in rules["B"]


def test_validate_theme_greater_than_hex_suggestion() -> None:
    rules = {
        "A": {"fg": "FG", "bg": "BG", "min_ratio": 3},
        "B": {"fg": "FG", "bg": "BG", "greater_than": "A"},
    }

    def _get(_colors, _rule, role):
        return {"fg": "#111111", "bg": "#222222"}[role]

    with (
        patch("themeweaver.contrast.validator.load_rules", return_value=rules),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch("themeweaver.contrast.validator.get_color_for_rule", side_effect=_get),
        patch(
            "themeweaver.contrast.validator.contrast_ratio",
            side_effect=[5.0, 4.0],
        ),
        patch(
            "themeweaver.contrast.validator.adjust_for_contrast",
            return_value="#CCCCCC",
        ),
    ):
        result = validate_theme("t", "dark", include_suggestions=True)

    r_by_id = {r.rule_id: r for r in result.results}
    assert r_by_id["B"].passed is False
    assert "Try FG: #CCCCCC" in (r_by_id["B"].suggestion or "")
    assert "exceed A contrast (5.0)" in (r_by_id["B"].suggestion or "")


def test_validate_theme_greater_than_fallback_suggestion() -> None:
    rules = {
        "A": {"fg": "FG", "bg": "BG", "min_ratio": 3},
        "B": {"fg": "FG", "bg": "BG", "greater_than": "A", "tolerance": 0.2},
    }

    def _get(_colors, _rule, role):
        return {"fg": "#111111", "bg": "#222222"}[role]

    with (
        patch("themeweaver.contrast.validator.load_rules", return_value=rules),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch("themeweaver.contrast.validator.get_color_for_rule", side_effect=_get),
        patch(
            "themeweaver.contrast.validator.contrast_ratio",
            side_effect=[5.0, 4.0],
        ),
        patch(
            "themeweaver.contrast.validator.adjust_for_contrast",
            return_value="#111111",
        ),
    ):
        result = validate_theme("t", "dark", include_suggestions=True)

    r_by_id = {r.rule_id: r for r in result.results}
    assert "Adjust FG or BG to increase contrast" in (r_by_id["B"].suggestion or "")
    assert "need ratio > 4.8 vs A (5.0)" in (r_by_id["B"].suggestion or "")


def test_validate_theme_min_ratio_suggestion_takes_priority_over_greater_than() -> None:
    rules = {
        "A": {"fg": "FG", "bg": "BG", "min_ratio": 3},
        "B": {
            "fg": "FG",
            "bg": "BG",
            "min_ratio": 7,
            "greater_than": "A",
        },
    }

    def _get(_colors, _rule, role):
        return {"fg": "#111111", "bg": "#222222"}[role]

    with (
        patch("themeweaver.contrast.validator.load_rules", return_value=rules),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch("themeweaver.contrast.validator.get_color_for_rule", side_effect=_get),
        patch(
            "themeweaver.contrast.validator.contrast_ratio",
            side_effect=[5.0, 4.0],
        ),
        patch(
            "themeweaver.contrast.validator.adjust_for_contrast",
            return_value="#DDDDDD",
        ) as mock_adjust,
    ):
        result = validate_theme("t", "dark", include_suggestions=True)

    r_by_id = {r.rule_id: r for r in result.results}
    assert r_by_id["B"].passed is False
    assert "to meet ratio 7" in (r_by_id["B"].suggestion or "")
    mock_adjust.assert_called_once_with("#111111", "#222222", 7)


def test_validate_theme_skips_none_rule_entry() -> None:
    with (
        patch(
            "themeweaver.contrast.validator.load_rules",
            return_value={"R0": None, "R1": {"fg": "FG", "bg": "BG", "min_ratio": 1}},
        ),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch(
            "themeweaver.contrast.validator.get_color_for_rule",
            side_effect=["#111111", "#222222"],
        ),
        patch("themeweaver.contrast.validator.contrast_ratio", return_value=4.0),
    ):
        result = validate_theme("t", "dark")
    assert len(result.results) == 1
    assert result.results[0].rule_id == "R1"


def test_validate_theme_line_bg_failed_fg_bg_suggestion() -> None:
    rule = {
        "fg": "FG",
        "bg": "BG",
        "line_bg": "LBG",
        "fg_lbg_min": 1,
        "lbg_bg_min": 1,
        "fg_bg_min": 9,
    }

    def _get(_colors, _rule, role):
        return {"fg": "#111111", "bg": "#222222", "line_bg": "#333333"}[role]

    with (
        patch("themeweaver.contrast.validator.load_rules", return_value={"R1": rule}),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch("themeweaver.contrast.validator.get_color_for_rule", side_effect=_get),
        patch(
            "themeweaver.contrast.validator.contrast_ratio",
            side_effect=[5.0, 5.0, 2.0],  # fg_lbg, lbg_bg, fg_bg
        ),
        patch(
            "themeweaver.contrast.validator.adjust_for_contrast", return_value="#AAAAAA"
        ),
    ):
        result = validate_theme("t", "dark", include_suggestions=True)

    assert result.failed_count == 1
    assert "Try FG:" in (result.results[0].suggestion or "")


def test_validate_theme_line_bg_failed_fg_lbg_suggestion() -> None:
    rule = {
        "fg": "FG",
        "bg": "BG",
        "line_bg": "LBG",
        "fg_lbg_min": 5,
        "lbg_bg_min": 1,
        "fg_bg_min": 1,
    }

    def _get(_colors, _rule, role):
        return {"fg": "#111111", "bg": "#222222", "line_bg": "#333333"}[role]

    with (
        patch("themeweaver.contrast.validator.load_rules", return_value={"R1": rule}),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch("themeweaver.contrast.validator.get_color_for_rule", side_effect=_get),
        patch(
            "themeweaver.contrast.validator.contrast_ratio",
            side_effect=[2.0, 5.0, 5.0],  # fail fg_lbg only
        ),
        patch(
            "themeweaver.contrast.validator.adjust_for_contrast", return_value="#BBBBBB"
        ),
    ):
        result = validate_theme("t", "dark", include_suggestions=True)

    assert result.failed_count == 1
    assert "vs LBG" in (result.results[0].suggestion or "")


def test_validate_theme_line_bg_failed_lbg_bg_fallback_suggestion() -> None:
    rule = {
        "fg": "FG",
        "bg": "BG",
        "line_bg": "LBG",
        "fg_lbg_min": 1,
        "lbg_bg_min": 6,
        "fg_bg_min": 1,
    }

    def _get(_colors, _rule, role):
        return {"fg": "#111111", "bg": "#222222", "line_bg": "#333333"}[role]

    with (
        patch("themeweaver.contrast.validator.load_rules", return_value={"R1": rule}),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch("themeweaver.contrast.validator.get_color_for_rule", side_effect=_get),
        patch(
            "themeweaver.contrast.validator.contrast_ratio",
            side_effect=[5.0, 2.0, 5.0],  # fail lbg_bg only
        ),
        patch(
            "themeweaver.contrast.validator.adjust_for_contrast",
            return_value="#333333",  # same as original -> fallback message path
        ),
    ):
        result = validate_theme("t", "dark", include_suggestions=True)

    assert result.failed_count == 1
    assert "Adjust LBG or BG to increase contrast" in (
        result.results[0].suggestion or ""
    )


def test_validate_theme_standard_max_ratio_failure() -> None:
    rule = {"fg": "FG", "bg": "BG", "max_ratio": 3}
    with (
        patch("themeweaver.contrast.validator.load_rules", return_value={"R1": rule}),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch(
            "themeweaver.contrast.validator.get_color_for_rule",
            side_effect=["#111111", "#222222"],
        ),
        patch("themeweaver.contrast.validator.contrast_ratio", return_value=5.0),
    ):
        result = validate_theme("t", "dark", include_suggestions=False)
    assert result.failed_count == 1
    assert "> 3.0" in result.results[0].message


def test_validate_theme_standard_max_ratio_suggestion() -> None:
    rule = {"fg": "FG", "bg": "BG", "max_ratio": 3}
    with (
        patch("themeweaver.contrast.validator.load_rules", return_value={"R1": rule}),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch(
            "themeweaver.contrast.validator.get_color_for_rule",
            side_effect=["#111111", "#222222"],
        ),
        patch("themeweaver.contrast.validator.contrast_ratio", return_value=5.0),
    ):
        result = validate_theme("t", "dark", include_suggestions=True)
    assert result.failed_count == 1
    assert "reduce contrast" in (result.results[0].suggestion or "")


def test_validate_theme_standard_min_ratio_fallback_suggestion() -> None:
    rule = {"fg": "FG", "bg": "BG", "min_ratio": 7}

    def _get(_colors, _rule, role):
        return {"fg": "#111111", "bg": "#222222"}[role]

    with (
        patch("themeweaver.contrast.validator.load_rules", return_value={"R1": rule}),
        patch("themeweaver.contrast.validator.resolve_theme_colors", return_value={}),
        patch("themeweaver.contrast.validator.get_color_for_rule", side_effect=_get),
        patch(
            "themeweaver.contrast.validator.contrast_ratio",
            return_value=2.0,
        ),
        patch(
            "themeweaver.contrast.validator.adjust_for_contrast",
            return_value="#111111",  # same color => fallback message
        ),
    ):
        result = validate_theme("t", "dark", include_suggestions=True)

    assert result.failed_count == 1
    assert "Adjust FG or BG to increase contrast" in (
        result.results[0].suggestion or ""
    )
