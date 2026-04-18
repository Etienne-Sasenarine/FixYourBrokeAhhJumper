from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, TypedDict


class ShotAnalysisResult(TypedDict):
    score: int
    summary: str
    biggest_fix: str
    drill: str
    artifact_path: str
    metrics: Dict[str, float]
    error: bool
    message: str


@dataclass(frozen=True)
class IncomingMessage:
    sender: str
    text: str
    attachments: list[str]


@dataclass(frozen=True)
class OutgoingMessage:
    recipient: str
    text: str
    attachments: list[str]


def normalize_analysis_result(raw: Dict[str, Any]) -> ShotAnalysisResult:
    """Normalize analyzer output so Person 1 can trust one stable shape."""
    defaults: ShotAnalysisResult = {
        "score": 0,
        "summary": "",
        "biggest_fix": "",
        "drill": "",
        "artifact_path": "",
        "metrics": {},
        "error": False,
        "message": "",
    }

    merged = {**defaults, **(raw or {})}

    artifact = str(merged.get("artifact_path", "") or "")
    if artifact:
        merged["artifact_path"] = str(Path(artifact))

    metrics = merged.get("metrics")
    if not isinstance(metrics, dict):
        merged["metrics"] = {}

    merged["score"] = int(merged.get("score", 0) or 0)
    merged["error"] = bool(merged.get("error", False))

    return merged  # type: ignore[return-value]
