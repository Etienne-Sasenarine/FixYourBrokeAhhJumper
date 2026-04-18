from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ShotMetrics:
    elbow_angle_deg: float = 0.0
    knee_bend_deg: float = 0.0
    release_angle_deg: float = 0.0
    torso_lean_deg: float = 0.0
    shoulder_tilt_deg: float = 0.0
    follow_through_deg: float = 0.0
    landing_drift_px: float = 0.0
    release_height_norm: float = 0.0
    matched_player: str = ""
    matched_player_team: str = ""
    matched_player_style: str = ""
    match_similarity_pct: float = 0.0
    second_match: str = ""
    second_match_pct: float = 0.0


@dataclass
class ShotResult:
    score: int = 0
    summary: str = ""
    biggest_fix: str = ""
    drill: str = ""
    artifact_path: str = ""
    metrics: ShotMetrics = field(default_factory=ShotMetrics)
    error: bool = False
    message: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["metrics"] = asdict(self.metrics)
        return data


@dataclass(frozen=True)
class IncomingMessage:
    sender: str
    text: str
    attachments: List[str]


@dataclass(frozen=True)
class OutgoingMessage:
    recipient: str
    text: str
    attachments: List[str]


ShotAnalysisResult = Dict[str, Any]


def err_not_visible() -> ShotAnalysisResult:
    return ShotResult(
        error=True,
        message="Shooter not fully visible. Please record from the side with your full body in frame.",
    ).to_dict()


def err_no_shot_detected() -> ShotAnalysisResult:
    return ShotResult(
        error=True,
        message="Could not detect a jump shot in this clip. Make sure the video shows a full shooting motion.",
    ).to_dict()


def err_bad_angle() -> ShotAnalysisResult:
    return ShotResult(
        error=True,
        message="Camera angle looks head-on. Film from the side for best results.",
    ).to_dict()


def normalize_analysis_result(raw: Dict[str, Any]) -> ShotAnalysisResult:
    """Normalize analyzer output so Person 1 can trust one stable shape."""
    defaults: Dict[str, Any] = {
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

    return merged
