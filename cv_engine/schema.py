"""
Shared contract between ara_app (Person 1) and cv_engine (Person 2).
Neither side changes this file without agreement.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ShotMetrics:
    elbow_angle_deg: float = 0.0        # shooting elbow at release (target: 85-100)
    knee_bend_deg: float = 0.0          # knee angle at jump initiation (target: 110-130)
    release_angle_deg: float = 0.0      # wrist-to-ball trajectory angle (target: 45-60)
    torso_lean_deg: float = 0.0         # forward lean at release (target: <10)
    shoulder_tilt_deg: float = 0.0      # lateral shoulder level (target: <5)
    follow_through_deg: float = 0.0     # wrist snap angle post-release (target: >60)
    landing_drift_px: float = 0.0       # horizontal drift from takeoff to landing
    release_height_norm: float = 0.0    # normalized wrist height at release (0-1)

    # NBA match fields (filled by matcher)
    matched_player: str = ""
    matched_player_team: str = ""
    matched_player_style: str = ""
    match_similarity_pct: float = 0.0
    second_match: str = ""
    second_match_pct: float = 0.0


@dataclass
class ShotResult:
    # Core fields Person 1 uses directly
    score: int = 0                      # 0-100 overall shot score
    summary: str = ""                   # one sentence: what's the main issue
    biggest_fix: str = ""              # one sentence: top correction
    drill: str = ""                     # one sentence: drill to fix it
    artifact_path: str = ""            # path to annotated output frame/gif

    # Full metrics for Claude to use in diagnosis
    metrics: ShotMetrics = field(default_factory=ShotMetrics)

    # Error handling
    error: bool = False
    message: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["metrics"] = asdict(self.metrics)
        return d


# Canonical failure responses
def err_not_visible() -> dict:
    return ShotResult(
        error=True,
        message="Shooter not fully visible. Please record from the side with your full body in frame."
    ).to_dict()

def err_no_shot_detected() -> dict:
    return ShotResult(
        error=True,
        message="Could not detect a jump shot in this clip. Make sure the video shows a full shooting motion."
    ).to_dict()

def err_bad_angle() -> dict:
    return ShotResult(
        error=True,
        message="Camera angle looks head-on. Film from the side for best results."
    ).to_dict()
