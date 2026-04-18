"""
metrics.py — Convert raw pose angles into a shot score + feedback labels.

Scoring logic:
- Each metric has an ideal range
- Deductions scale with how far outside the range the measurement is
- Final score is 0-100
- Returns top 2 issues by severity for the coaching output
"""

from cv_engine.database import IDEAL_RANGES, FEEDBACK_LABELS


def _range_deduction(value: float, lo: float, hi: float, max_deduction: float) -> tuple[float, str]:
    """
    Returns (deduction_points, direction) where direction is 'low' or 'high' or 'ok'.
    Deduction scales linearly: 0 at boundary, max_deduction at 2x the gap.
    """
    if lo <= value <= hi:
        return 0.0, "ok"
    elif value < lo:
        gap = lo - value
        span = (hi - lo) / 2 + 1e-8
        deduction = min(max_deduction, (gap / span) * max_deduction)
        return round(deduction, 1), "low"
    else:
        gap = value - hi
        span = (hi - lo) / 2 + 1e-8
        deduction = min(max_deduction, (gap / span) * max_deduction)
        return round(deduction, 1), "high"


# Max deduction per metric (sums to 100 if everything is worst case)
MAX_DEDUCTIONS = {
    "elbow_angle_deg":     22,
    "knee_bend_deg":       18,
    "release_angle_deg":   15,
    "torso_lean_deg":      12,
    "shoulder_tilt_deg":   10,
    "follow_through_deg":  13,
    "release_height_norm": 10,
}


def compute_score_and_issues(angles: dict) -> tuple[int, list[dict]]:
    """
    Returns:
        score: int 0-100
        issues: list of dicts sorted by severity (worst first)
                each: {metric, deduction, direction, label}
    """
    total_deduction = 0.0
    issues = []

    for metric, (lo, hi) in IDEAL_RANGES.items():
        value = angles.get(metric, 0.0)
        max_d = MAX_DEDUCTIONS.get(metric, 10)
        deduction, direction = _range_deduction(value, lo, hi, max_d)

        if deduction > 0:
            label = FEEDBACK_LABELS.get(metric, {}).get(direction, f"{metric} out of range")
            issues.append({
                "metric":    metric,
                "value":     round(value, 1),
                "ideal":     f"{lo}–{hi}",
                "deduction": deduction,
                "direction": direction,
                "label":     label,
            })
        total_deduction += deduction

    score = max(0, min(100, round(100 - total_deduction)))
    issues.sort(key=lambda x: x["deduction"], reverse=True)
    return score, issues
