from __future__ import annotations

from shared.schema import ShotAnalysisResult


def format_metrics(metrics: dict[str, float]) -> str:
    if not metrics:
        return ""
    pieces = []
    for key, value in metrics.items():
        label = key.replace("_", " ")
        pieces.append(f"- {label}: {value:.1f}")
    return "\n".join(pieces)


def format_coaching_reply(result: ShotAnalysisResult) -> str:
    if result["error"]:
        msg = result["message"] or "I could not analyze this clip. Please send a full-body side-view shot."
        return f"AraShot update:\n{msg}"

    score = max(0, min(100, int(result["score"])))
    metrics_block = format_metrics(result["metrics"])

    lines = [
        f"AraShot score: {score}/100",
        f"Top issue: {result['summary']}",
        f"Main fix: {result['biggest_fix']}",
        f"Drill: {result['drill']}",
    ]

    if metrics_block:
        lines.append("Metrics:")
        lines.append(metrics_block)

    return "\n".join(lines)
