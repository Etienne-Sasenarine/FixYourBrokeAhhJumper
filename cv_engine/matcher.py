"""
matcher.py — KNN similarity matching against the NBA player database.

Given a user's measured shot angles + their height/weight,
returns the top-K most similar NBA players with per-angle deltas.

No sklearn needed — pure numpy KNN with weighted cosine similarity.
"""

import numpy as np
from cv_engine.database import NBA_PLAYERS, FEATURE_KEYS, FEATURE_WEIGHTS


def _to_vector(angle_dict: dict) -> np.ndarray:
    return np.array([float(angle_dict.get(k, 0.0)) for k in FEATURE_KEYS])


def _normalize(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    return v / (norm + 1e-8)


def _height_score(user_height_in: int, player_height_in: int) -> float:
    """
    1.0 = exact height match
    0.0 = 8+ inch difference
    Linear decay between 0 and 8 inches.
    """
    diff = abs(user_height_in - player_height_in)
    return max(0.0, 1.0 - diff / 8.0)


def _weighted_cosine(user_vec: np.ndarray, player_vec: np.ndarray) -> float:
    """Cosine similarity with per-feature weighting."""
    w = np.array(FEATURE_WEIGHTS)
    u = user_vec * w
    p = player_vec * w
    return float(np.dot(_normalize(u), _normalize(p)))


def match_player(
    user_angles: dict,
    user_height_in: int,
    user_weight_lb: int,
    top_k: int = 3,
) -> list[dict]:
    """
    Find the top-K NBA players whose shooting mechanics best match the user.

    Args:
        user_angles: dict with same keys as FEATURE_KEYS
        user_height_in: user height in inches (e.g. 72 for 6'0")
        user_weight_lb: user weight in lbs
        top_k: number of matches to return

    Returns:
        List of match dicts sorted by similarity descending.
        Each dict has: player_name, team, similarity_pct, angle_deltas, style
    """
    user_vec = _to_vector(user_angles)
    results = []

    for player in NBA_PLAYERS:
        player_vec = _to_vector(player["pose_vector"])

        # Pose similarity (80% of score)
        pose_sim = _weighted_cosine(user_vec, player_vec)

        # Height similarity (20% of score)
        h_sim = _height_score(user_height_in, player["height_in"])

        final_score = (pose_sim * 0.80) + (h_sim * 0.20)

        # Per-angle deltas: positive = user is higher than player
        deltas = {
            k: round(float(user_angles.get(k, 0) - player["pose_vector"].get(k, 0)), 1)
            for k in FEATURE_KEYS
        }

        results.append({
            "player_name":      player["name"],
            "team":             player["team"],
            "height_in":        player["height_in"],
            "weight_lb":        player["weight_lb"],
            "position":         player["position"],
            "style":            player["style"],
            "similarity_pct":   round(final_score * 100, 1),
            "angle_deltas":     deltas,
            "player_angles":    player["pose_vector"],
        })

    results.sort(key=lambda x: x["similarity_pct"], reverse=True)
    return results[:top_k]
