"""
Pre-computed NBA player shooting form database.
Vectors are sourced from biomechanics research and coaching literature
on each player's documented shot mechanics.

These are REFERENCE vectors — angles representing each player's ideal
shot at their release point, averaged across their known mechanics.

No video processing needed at demo time. This ships pre-built.
"""

NBA_PLAYERS = [
    {
        "name": "Stephen Curry",
        "team": "GSW",
        "height_in": 75,
        "weight_lb": 185,
        "position": "PG",
        "style": "Quick trigger, high arc, minimal gather — pure rhythm shooter",
        "pose_vector": {
            "elbow_angle_deg": 91.0,
            "knee_bend_deg": 118.0,
            "release_angle_deg": 58.0,
            "torso_lean_deg": 4.0,
            "shoulder_tilt_deg": 2.5,
            "follow_through_deg": 72.0,
            "release_height_norm": 0.88,
        },
    },
    {
        "name": "Klay Thompson",
        "team": "GSW",
        "height_in": 79,
        "weight_lb": 215,
        "position": "SG",
        "style": "Textbook catch-and-shoot, perfect elbow tuck, minimal movement",
        "pose_vector": {
            "elbow_angle_deg": 88.0,
            "knee_bend_deg": 122.0,
            "release_angle_deg": 55.0,
            "torso_lean_deg": 3.5,
            "shoulder_tilt_deg": 1.8,
            "follow_through_deg": 75.0,
            "release_height_norm": 0.85,
        },
    },
    {
        "name": "Jayson Tatum",
        "team": "BOS",
        "height_in": 80,
        "weight_lb": 210,
        "position": "SF",
        "style": "High release, smooth off-balance, long gather — wing scorer",
        "pose_vector": {
            "elbow_angle_deg": 95.0,
            "knee_bend_deg": 115.0,
            "release_angle_deg": 52.0,
            "torso_lean_deg": 8.0,
            "shoulder_tilt_deg": 4.0,
            "follow_through_deg": 68.0,
            "release_height_norm": 0.92,
        },
    },
    {
        "name": "Damian Lillard",
        "team": "MIL",
        "height_in": 74,
        "weight_lb": 195,
        "position": "PG",
        "style": "Explosive leg drive, low gather, deep range — off-dribble specialist",
        "pose_vector": {
            "elbow_angle_deg": 93.0,
            "knee_bend_deg": 128.0,
            "release_angle_deg": 54.0,
            "torso_lean_deg": 6.0,
            "shoulder_tilt_deg": 3.0,
            "follow_through_deg": 70.0,
            "release_height_norm": 0.82,
        },
    },
    {
        "name": "Kevin Durant",
        "team": "PHX",
        "height_in": 83,
        "weight_lb": 240,
        "position": "SF",
        "style": "Unguardable high release, minimal knee bend, pure extension",
        "pose_vector": {
            "elbow_angle_deg": 98.0,
            "knee_bend_deg": 108.0,
            "release_angle_deg": 50.0,
            "torso_lean_deg": 2.0,
            "shoulder_tilt_deg": 2.0,
            "follow_through_deg": 78.0,
            "release_height_norm": 0.95,
        },
    },
    {
        "name": "Devin Booker",
        "team": "PHX",
        "height_in": 78,
        "weight_lb": 206,
        "position": "SG",
        "style": "Strong base, consistent mid-range, reliable footwork",
        "pose_vector": {
            "elbow_angle_deg": 90.0,
            "knee_bend_deg": 120.0,
            "release_angle_deg": 53.0,
            "torso_lean_deg": 5.0,
            "shoulder_tilt_deg": 2.8,
            "follow_through_deg": 71.0,
            "release_height_norm": 0.84,
        },
    },
    {
        "name": "Donovan Mitchell",
        "team": "CLE",
        "height_in": 74,
        "weight_lb": 215,
        "position": "SG",
        "style": "Athletic off-dribble, strong torso rotation, mid-range craftsman",
        "pose_vector": {
            "elbow_angle_deg": 97.0,
            "knee_bend_deg": 125.0,
            "release_angle_deg": 51.0,
            "torso_lean_deg": 9.0,
            "shoulder_tilt_deg": 5.5,
            "follow_through_deg": 65.0,
            "release_height_norm": 0.80,
        },
    },
    {
        "name": "LaMelo Ball",
        "team": "CHA",
        "height_in": 79,
        "weight_lb": 180,
        "position": "PG",
        "style": "Unorthodox early release, high arc, creative footwork",
        "pose_vector": {
            "elbow_angle_deg": 105.0,
            "knee_bend_deg": 112.0,
            "release_angle_deg": 60.0,
            "torso_lean_deg": 7.0,
            "shoulder_tilt_deg": 6.0,
            "follow_through_deg": 62.0,
            "release_height_norm": 0.86,
        },
    },
]

# Feature keys used for KNN — order matters, must match pose.py output
FEATURE_KEYS = [
    "elbow_angle_deg",
    "knee_bend_deg",
    "release_angle_deg",
    "torso_lean_deg",
    "shoulder_tilt_deg",
    "follow_through_deg",
    "release_height_norm",
]

# How much each feature counts in matching
# Elbow and knee are most diagnostic for shot quality
FEATURE_WEIGHTS = [
    0.28,  # elbow_angle_deg
    0.20,  # knee_bend_deg
    0.18,  # release_angle_deg
    0.12,  # torso_lean_deg
    0.10,  # shoulder_tilt_deg
    0.08,  # follow_through_deg
    0.04,  # release_height_norm
]

# Ideal ranges for scoring (min, max) — outside = deductions
IDEAL_RANGES = {
    "elbow_angle_deg":     (85,  100),
    "knee_bend_deg":       (110, 130),
    "release_angle_deg":   (45,   60),
    "torso_lean_deg":      (0,    10),
    "shoulder_tilt_deg":   (0,     5),
    "follow_through_deg":  (60,   80),
    "release_height_norm": (0.78,  1.0),
}

# Feedback labels when a metric is outside range
FEEDBACK_LABELS = {
    "elbow_angle_deg": {
        "low":  "elbow too tucked — widen slightly for power",
        "high": "elbow flaring out — keep it under the ball",
    },
    "knee_bend_deg": {
        "low":  "not enough knee bend — load your legs for more power",
        "high": "over-bending knees — trust your base, don't squat",
    },
    "release_angle_deg": {
        "low":  "flat release — aim for a higher arc",
        "high": "too much arc — straighten your trajectory",
    },
    "torso_lean_deg": {
        "high": "leaning too far forward — stay tall through the shot",
    },
    "shoulder_tilt_deg": {
        "high": "shoulders uneven — level them for consistency",
    },
    "follow_through_deg": {
        "low":  "cutting the follow-through short — hold the finish",
        "high": "over-rotating wrist — stay controlled",
    },
    "release_height_norm": {
        "low":  "releasing too low — get the ball higher before letting go",
    },
}
