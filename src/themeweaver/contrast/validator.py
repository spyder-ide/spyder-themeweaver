"""Contrast validation engine."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from themeweaver.color_utils import (
    adjust_for_contrast,
    blend_alpha,
    contrast_ratio,
)
from themeweaver.contrast.color_resolver import get_color_for_rule, resolve_theme_colors
from themeweaver.contrast.rules_loader import load_rules


@dataclass
class RuleResult:
    """Result of validating a single contrast rule."""

    rule_id: str
    passed: bool
    actual_ratio: Optional[float] = None
    message: str = ""
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of contrast validation for a theme variant."""

    variant: str
    results: List[RuleResult] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0

    @property
    def all_passed(self) -> bool:
        return self.failed_count == 0


# Round contrast ratios to 1 decimal before comparison to avoid float precision issues
_CONTRAST_PRECISION = 1


def _round_ratio(ratio: float) -> float:
    return round(ratio, _CONTRAST_PRECISION)


def _suggest_fg_contrast_increase(
    *,
    fg_name: str,
    bg_name: str,
    orig_fg: str,
    bg_hex: str,
    target_ratio: float,
    ratio: float,
    success_reason: str,
    fallback_detail: str,
) -> str:
    """Build a hex or fallback suggestion to raise fg vs bg contrast."""
    suggestion_hex = adjust_for_contrast(orig_fg, bg_hex, target_ratio)
    if suggestion_hex and suggestion_hex.upper() != orig_fg.upper():
        return f"Try {fg_name}: {suggestion_hex} (was {orig_fg}) {success_reason}"
    return (
        f"Adjust {fg_name} or {bg_name} to increase contrast "
        f"({fallback_detail}, current ratio {ratio:.1f})"
    )


def _sort_rules_by_dependency(rules: Dict[str, Any]) -> List[str]:
    """Sort rule IDs so that referenced rules (greater_than) come first."""
    order: List[str] = []
    seen: set = set()

    def visit(rid: str) -> None:
        if rid in seen:
            return
        seen.add(rid)
        rule = rules.get(rid)
        if rule and "greater_than" in rule:
            ref = rule["greater_than"]
            if ref in rules:
                visit(ref)
        order.append(rid)

    for rid in rules:
        visit(rid)
    return order


def validate_theme(
    theme_name: str,
    variant: str,
    themes_dir: Optional[Path] = None,
    rules_dir: Optional[Path] = None,
    include_suggestions: bool = True,
) -> ValidationResult:
    """
    Validate a theme's contrast against Spyder UI rules.

    Args:
        theme_name: Theme name
        variant: "dark" or "light"
        themes_dir: Themes directory
        rules_dir: Rules YAML directory
        include_suggestions: Whether to compute adjust_for_contrast suggestions for failures

    Returns:
        ValidationResult with per-rule pass/fail and optional suggestions
    """
    rules = load_rules(variant, rules_dir)
    default_tolerance = float(rules.pop("_default_tolerance", 0))
    colors = resolve_theme_colors(theme_name, variant, themes_dir)

    ratio_cache: Dict[str, float] = {}
    results: List[RuleResult] = []
    rule_order = _sort_rules_by_dependency(rules)

    for rule_id in rule_order:
        rule = rules.get(rule_id)
        if not rule:
            continue

        fg_hex = get_color_for_rule(colors, rule, "fg")
        bg_hex = get_color_for_rule(colors, rule, "bg")

        if not fg_hex or not bg_hex:
            results.append(
                RuleResult(
                    rule_id=rule_id,
                    passed=False,
                    message=f"Missing color: fg={fg_hex is None}, bg={bg_hex is None}",
                )
            )
            continue

        # PE22: fg has 75% opacity
        if rule.get("fg_opacity"):
            alpha = rule["fg_opacity"]
            fg_hex = blend_alpha(bg_hex, fg_hex, alpha)

        # PE5A-C: check fg/lbg, lbg/bg, fg/bg
        if "line_bg" in rule and "fg_lbg_min" in rule:
            line_bg_hex = get_color_for_rule(colors, rule, "line_bg")
            if not line_bg_hex:
                results.append(
                    RuleResult(rule_id=rule_id, passed=False, message="Missing line_bg")
                )
                continue

            fg_lbg = _round_ratio(contrast_ratio(fg_hex, line_bg_hex))
            lbg_bg = _round_ratio(contrast_ratio(line_bg_hex, bg_hex))
            fg_bg = _round_ratio(contrast_ratio(fg_hex, bg_hex))

            fg_name = rule.get("fg", "fg")
            line_bg_name = rule.get("line_bg", "line_bg")
            bg_name = rule.get("bg", "bg")

            tol = float(rule.get("tolerance", default_tolerance))
            passed = True
            msg_parts = []
            min_fg_lbg = float(rule.get("fg_lbg_min", 0))
            min_lbg_bg = float(rule.get("lbg_bg_min", 0))
            min_fg_bg = float(rule.get("fg_bg_min", 0))
            if fg_lbg < min_fg_lbg - tol:
                passed = False
                msg_parts.append(
                    f"{fg_name} vs {line_bg_name}: ratio {fg_lbg:.1f} < {min_fg_lbg}"
                )
            if lbg_bg < min_lbg_bg - tol:
                passed = False
                msg_parts.append(
                    f"{line_bg_name} vs {bg_name}: ratio {lbg_bg:.1f} < {min_lbg_bg}"
                )
            if fg_bg < min_fg_bg - tol:
                passed = False
                msg_parts.append(
                    f"{fg_name} vs {bg_name}: ratio {fg_bg:.1f} < {min_fg_bg}"
                )

            ratio_cache[rule_id] = fg_bg
            suggestion = None
            if not passed and include_suggestions:
                failed_fg_lbg = fg_lbg < min_fg_lbg - tol
                failed_lbg_bg = lbg_bg < min_lbg_bg - tol
                failed_fg_bg = fg_bg < min_fg_bg - tol

                if failed_fg_bg:
                    orig_fg = get_color_for_rule(colors, rule, "fg")
                    if orig_fg:
                        min_r = float(rule.get("fg_bg_min", 9))
                        suggestion_hex = adjust_for_contrast(orig_fg, bg_hex, min_r)
                        if suggestion_hex and suggestion_hex.upper() != orig_fg.upper():
                            suggestion = f"Try {fg_name}: {suggestion_hex} (was {orig_fg}) to meet ratio {min_r}"
                elif failed_fg_lbg:
                    orig_fg = get_color_for_rule(colors, rule, "fg")
                    if orig_fg:
                        min_r = float(rule.get("fg_lbg_min", 0))
                        suggestion_hex = adjust_for_contrast(
                            orig_fg, line_bg_hex, min_r
                        )
                        if suggestion_hex and suggestion_hex.upper() != orig_fg.upper():
                            suggestion = f"Try {fg_name}: {suggestion_hex} (was {orig_fg}) to meet ratio {min_r} vs {line_bg_name}"
                elif failed_lbg_bg:
                    orig_lbg = get_color_for_rule(colors, rule, "line_bg")
                    if orig_lbg:
                        min_r = float(rule.get("lbg_bg_min", 0))
                        suggestion_hex = adjust_for_contrast(orig_lbg, bg_hex, min_r)
                        if (
                            suggestion_hex
                            and suggestion_hex.upper() != orig_lbg.upper()
                        ):
                            suggestion = f"Try {line_bg_name}: {suggestion_hex} (was {orig_lbg}) to meet ratio {min_r} vs {bg_name}"
                    if not suggestion:
                        suggestion = (
                            f"Adjust {line_bg_name} or {bg_name} to increase contrast "
                            f"(ratio {lbg_bg:.1f} < {min_lbg_bg})"
                        )

            results.append(
                RuleResult(
                    rule_id=rule_id,
                    passed=passed,
                    actual_ratio=fg_bg,
                    message="; ".join(msg_parts) if msg_parts else "OK",
                    suggestion=suggestion,
                )
            )
            continue

        # Standard contrast check
        ratio = _round_ratio(contrast_ratio(fg_hex, bg_hex))
        ratio_cache[rule_id] = ratio

        fg_name = rule.get("fg", "fg")
        bg_name = rule.get("bg", "bg")

        passed = True
        msg_parts = []
        failed_min = False
        failed_max = False
        failed_greater_than = False
        ref_rule_id: Optional[str] = None
        ref_rounded: Optional[float] = None

        tol = float(rule.get("tolerance", default_tolerance))
        min_ratio = float(rule["min_ratio"]) if "min_ratio" in rule else None
        max_ratio = float(rule["max_ratio"]) if "max_ratio" in rule else None
        if min_ratio is not None and ratio < min_ratio - tol:
            passed = False
            failed_min = True
            msg_parts.append(f"{fg_name} vs {bg_name}: ratio {ratio:.1f} < {min_ratio}")

        if max_ratio is not None and ratio > max_ratio + tol:
            passed = False
            failed_max = True
            msg_parts.append(f"{fg_name} vs {bg_name}: ratio {ratio:.1f} > {max_ratio}")

        if "greater_than" in rule:
            ref_ratio = ratio_cache.get(rule["greater_than"])
            if ref_ratio is not None:
                ref_rounded = _round_ratio(ref_ratio)
                if ratio < ref_rounded - tol:
                    passed = False
                    failed_greater_than = True
                    ref_rule_id = rule["greater_than"]
                    msg_parts.append(
                        f"{fg_name} vs {bg_name}: ratio {ratio:.1f} <= {rule['greater_than']} ({ref_rounded:.1f})"
                    )

        suggestion = None
        if not passed and include_suggestions:
            if failed_min:
                if "fg_opacity" in rule:
                    alpha = rule["fg_opacity"]
                    suggestion = (
                        f"Adjust {fg_name} (base color at {alpha:.0%} opacity) or opacity "
                        f"to meet ratio {min_ratio} (blended ratio {ratio:.1f})"
                    )
                else:
                    orig_fg = get_color_for_rule(colors, rule, "fg")
                    if orig_fg:
                        min_r = rule["min_ratio"]
                        suggestion = _suggest_fg_contrast_increase(
                            fg_name=fg_name,
                            bg_name=bg_name,
                            orig_fg=orig_fg,
                            bg_hex=bg_hex,
                            target_ratio=min_r,
                            ratio=ratio,
                            success_reason=f"to meet ratio {min_r}",
                            fallback_detail=f"ratio {ratio:.1f} < {min_ratio}",
                        )
            elif (
                failed_greater_than
                and ref_rule_id is not None
                and ref_rounded is not None
            ):
                orig_fg = get_color_for_rule(colors, rule, "fg")
                if orig_fg:
                    target_ratio = ref_rounded - tol
                    suggestion = _suggest_fg_contrast_increase(
                        fg_name=fg_name,
                        bg_name=bg_name,
                        orig_fg=orig_fg,
                        bg_hex=bg_hex,
                        target_ratio=target_ratio,
                        ratio=ratio,
                        success_reason=(
                            f"to exceed {ref_rule_id} contrast ({ref_rounded:.1f})"
                        ),
                        fallback_detail=(
                            f"need ratio > {target_ratio:.1f} vs {ref_rule_id} "
                            f"({ref_rounded:.1f})"
                        ),
                    )
            elif failed_max and max_ratio is not None:
                suggestion = (
                    f"Adjust {fg_name} or {bg_name} to reduce contrast "
                    f"(ratio {ratio:.1f} > {max_ratio})"
                )

        results.append(
            RuleResult(
                rule_id=rule_id,
                passed=passed,
                actual_ratio=ratio,
                message="; ".join(msg_parts) if msg_parts else "OK",
                suggestion=suggestion,
            )
        )

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count

    return ValidationResult(
        variant=variant,
        results=results,
        passed_count=passed_count,
        failed_count=failed_count,
    )
