"""
stub.py — Drop-in replacement for pipeline.analyze_shot during development.

Person 1: replace this import:

    from cv_engine.stub import analyze_shot      # while Person 2 builds

with this when ready:

    from cv_engine.pipeline import analyze_shot  # real CV

The output schema is identical.
"""


def analyze_shot(
    video_path: str,
    user_height_in: int = 72,
    user_weight_lb: int = 185,
    output_dir: str = "workspace/outputs",
) -> dict:
    """Stub: returns realistic fake data so Person 1 can wire the full Ara flow."""
    return {
        "score": 74,
        "summary": "Your elbow flares outward before release.",
        "biggest_fix": "Fix your elbow angle: measured 143.0° (ideal 85–100°).",
        "drill": (
            "Wall drill: stand 6 inches from a wall with your shooting side facing it. "
            "Shoot without hitting the wall — forces your elbow in. 50 reps before every session."
        ),
        "artifact_path": "workspace/outputs/mock_release_frame.jpg",
        "metrics": {
            "elbow_angle_deg":      143.0,
            "knee_bend_deg":        118.0,
            "release_angle_deg":     48.5,
            "torso_lean_deg":         6.2,
            "shoulder_tilt_deg":      3.1,
            "follow_through_deg":    55.0,
            "landing_drift_px":      22.4,
            "release_height_norm":    0.81,
            "matched_player":        "Klay Thompson",
            "matched_player_team":   "GSW",
            "matched_player_style":  "Textbook catch-and-shoot, perfect elbow tuck, minimal movement",
            "match_similarity_pct":  71.3,
            "second_match":          "Devin Booker",
            "second_match_pct":      68.1,
        },
        "error": False,
        "message": "",
    }
