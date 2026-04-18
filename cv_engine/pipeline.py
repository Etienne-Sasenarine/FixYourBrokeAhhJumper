"""
pipeline.py — The single entry point for Person 1.

Person 1 calls ONE function:

    from cv_engine.pipeline import analyze_shot

    result = analyze_shot(
        video_path="workspace/inbox/latest_shot.mp4",
        user_height_in=72,
        user_weight_lb=180,
    )

Returns a dict matching cv_engine/schema.py ShotResult.

Person 1 never imports anything else from cv_engine.
"""

import os
import sys
import cv2
import numpy as np

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cv_engine.pose    import run_pose_pipeline, compute_release_angle, compute_landing_drift
from cv_engine.matcher import match_player
from cv_engine.metrics import compute_score_and_issues
from cv_engine.database import FEATURE_KEYS
from cv_engine.schema   import ShotResult, ShotMetrics, err_not_visible, err_no_shot_detected


# Drill library — keyed by metric name
DRILLS = {
    "elbow_angle_deg": (
        "Wall drill: stand 6 inches from a wall with your shooting side facing it. "
        "Shoot without hitting the wall — forces your elbow in. 50 reps before every session."
    ),
    "knee_bend_deg": (
        "Squat-to-shoot: from a standing position, drop into a quarter squat, then explode "
        "into your shot. Builds the habit of loading your legs. 3 sets of 10."
    ),
    "release_angle_deg": (
        "Arch drill: shoot from 5 feet aiming to hit the top of the backboard square. "
        "Forces a higher arc. 20 reps, move back one step when you groove it."
    ),
    "torso_lean_deg": (
        "Chair drill: sit on a chair and shoot to a low hoop or target. "
        "Removes your legs, forces torso to stay tall. 15 reps."
    ),
    "shoulder_tilt_deg": (
        "Mirror drill: shoot in front of a mirror. Watch your shoulders — "
        "they should stay level through the entire motion. 20 reps with feedback."
    ),
    "follow_through_deg": (
        "Hold the finish: after every rep, hold your follow-through for 3 seconds. "
        "Coaches call this 'cookie jar' — reach in and hold. 20 reps."
    ),
    "release_height_norm": (
        "One-hand form shooting: shooting hand only, from 4 feet. "
        "Focus on pushing the ball up before out. 30 reps, both eyes open."
    ),
}


def _build_angles_dict(pose_result, release_angle: float, landing_drift: float) -> dict:
    """Convert PoseResult release frame into the angles dict used by matcher + metrics."""
    ra = pose_result.release_angles
    return {
        "elbow_angle_deg":     ra.elbow_angle,
        "knee_bend_deg":       ra.knee_angle,
        "release_angle_deg":   release_angle,
        "torso_lean_deg":      ra.torso_lean,
        "shoulder_tilt_deg":   ra.shoulder_tilt,
        "follow_through_deg":  min(90.0, ra.wrist_angle),
        "release_height_norm": ra.wrist_height,
        "landing_drift_px":    landing_drift,
    }


def _save_artifact(annotated_frame: np.ndarray, output_dir: str = "workspace/outputs") -> str:
    """Save annotated release frame as JPEG. Returns path."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "release_frame.jpg")
    cv2.imwrite(path, annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return path


def analyze_shot(
    video_path: str,
    user_height_in: int = 72,
    user_weight_lb: int = 185,
    output_dir: str = "workspace/outputs",
) -> dict:
    """
    Full jump shot analysis pipeline.

    Args:
        video_path:      path to the MP4 video file
        user_height_in:  user height in inches (default 6'0" = 72)
        user_weight_lb:  user weight in lbs
        output_dir:      where to save the annotated frame

    Returns:
        dict matching ShotResult schema (see cv_engine/schema.py)
    """

    # ── 1. Validate input ─────────────────────────────────────────────────
    if not os.path.exists(video_path):
        return ShotResult(
            error=True,
            message=f"Video file not found: {video_path}"
        ).to_dict()

    # ── 2. Pose extraction ────────────────────────────────────────────────
    pose_result = run_pose_pipeline(video_path, max_frames=60, debug=True)

    if pose_result is None:
        return err_not_visible()

    if len(pose_result.frames) < 5:
        return err_no_shot_detected()

    # ── 3. Compute derived metrics ─────────────────────────────────────────
    release_angle  = compute_release_angle(pose_result.frames, pose_result.release_frame_idx)
    landing_drift  = compute_landing_drift(pose_result.frames, pose_result.release_frame_idx)
    angles         = _build_angles_dict(pose_result, release_angle, landing_drift)

    # ── 4. Score + issues ─────────────────────────────────────────────────
    score, issues = compute_score_and_issues(angles)

    # ── 5. NBA matching ───────────────────────────────────────────────────
    matches = match_player(
        user_angles=angles,
        user_height_in=user_height_in,
        user_weight_lb=user_weight_lb,
        top_k=3,
    )
    top_match  = matches[0] if matches else None
    sec_match  = matches[1] if len(matches) > 1 else None

    # ── 6. Build feedback text ────────────────────────────────────────────
    top_issue   = issues[0] if issues else None
    sec_issue   = issues[1] if len(issues) > 1 else None

    summary = top_issue["label"] if top_issue else "Solid mechanics overall."
    biggest_fix = (
        f"Fix your {top_issue['metric'].replace('_', ' ').replace(' deg', '')}: "
        f"measured {top_issue['value']}° (ideal {top_issue['ideal']}°)."
        if top_issue else "Keep working on consistency."
    )
    drill = DRILLS.get(top_issue["metric"], "Form shooting from 5 feet, 20 reps.") if top_issue else ""

    # ── 7. Save annotated artifact ────────────────────────────────────────
    artifact_path = ""
    if pose_result.annotated_frame is not None:
        artifact_path = _save_artifact(pose_result.annotated_frame, output_dir)

    # ── 8. Build ShotMetrics ──────────────────────────────────────────────
    metrics = ShotMetrics(
        elbow_angle_deg      = angles["elbow_angle_deg"],
        knee_bend_deg        = angles["knee_bend_deg"],
        release_angle_deg    = angles["release_angle_deg"],
        torso_lean_deg       = angles["torso_lean_deg"],
        shoulder_tilt_deg    = angles["shoulder_tilt_deg"],
        follow_through_deg   = angles["follow_through_deg"],
        landing_drift_px     = landing_drift,
        release_height_norm  = angles["release_height_norm"],

        matched_player        = top_match["player_name"]    if top_match else "",
        matched_player_team   = top_match["team"]           if top_match else "",
        matched_player_style  = top_match["style"]          if top_match else "",
        match_similarity_pct  = top_match["similarity_pct"] if top_match else 0.0,
        second_match          = sec_match["player_name"]    if sec_match else "",
        second_match_pct      = sec_match["similarity_pct"] if sec_match else 0.0,
    )

    return ShotResult(
        score        = score,
        summary      = summary,
        biggest_fix  = biggest_fix,
        drill        = drill,
        artifact_path= artifact_path,
        metrics      = metrics,
        error        = False,
        message      = "",
    ).to_dict()


def analyze_shot_from_image(
    image_path: str,
    user_height_in: int = 72,
    user_weight_lb: int = 185,
    output_dir: str = "workspace/outputs",
) -> dict:
    """
    Analyze a single jump shot image (release frame).

    Args:
        image_path:      path to a single image file (JPG, PNG)
        user_height_in:  user height in inches (default 6'0" = 72)
        user_weight_lb:  user weight in lbs
        output_dir:      where to save the annotated frame

    Returns:
        dict matching ShotResult schema (see cv_engine/schema.py)
    """

    if not os.path.exists(image_path):
        return ShotResult(
            error=True,
            message=f"Image file not found: {image_path}"
        ).to_dict()

    # Load single image
    from cv_engine.pose import extract_frames_from_image, run_pose_extraction, detect_release_frame, annotate_release_frame
    
    frames_indexed, fps, total = extract_frames_from_image(image_path)
    
    if not frames_indexed:
        return ShotResult(
            error=True,
            message="Could not load image. Make sure it's a valid JPG or PNG."
        ).to_dict()

    # Extract pose from the image
    frame_angles = run_pose_extraction(frames_indexed, fps, debug=False)

    if not frame_angles:
        return err_not_visible()

    release_idx = 0  # Single image, so it's the release frame
    release_fa = frame_angles[0]

    # Compute derived metrics (simpler for single frame)
    angles = {
        "elbow_angle_deg": release_fa.elbow_angle,
        "knee_bend_deg": release_fa.knee_angle,
        "release_angle_deg": 50.0,  # Estimated from wrist position
        "torso_lean_deg": release_fa.torso_lean,
        "shoulder_tilt_deg": release_fa.shoulder_tilt,
        "follow_through_deg": release_fa.wrist_angle,
        "release_height_norm": release_fa.wrist_height,
        "landing_drift_px": 0.0,  # Not applicable for single frame
    }

    # Score + issues
    score, issues = compute_score_and_issues(angles)

    # NBA matching
    matches = match_player(
        user_angles=angles,
        user_height_in=user_height_in,
        user_weight_lb=user_weight_lb,
        top_k=3,
    )
    top_match = matches[0] if matches else None
    sec_match = matches[1] if len(matches) > 1 else None

    # Build feedback
    top_issue = issues[0] if issues else None
    summary = top_issue["label"] if top_issue else "Solid mechanics overall."
    biggest_fix = (
        f"Fix your {top_issue['metric'].replace('_', ' ').replace(' deg', '')}: "
        f"measured {top_issue['value']}° (ideal {top_issue['ideal']}°)."
        if top_issue else "Keep working on consistency."
    )
    drill = DRILLS.get(top_issue["metric"], "Form shooting from 5 feet, 20 reps.") if top_issue else ""

    # Save annotated artifact
    source_frame = frames_indexed[0][1]
    annotated = annotate_release_frame(source_frame, release_fa)
    artifact_path = _save_artifact(annotated, output_dir)

    # Build metrics
    metrics = ShotMetrics(
        elbow_angle_deg=angles["elbow_angle_deg"],
        knee_bend_deg=angles["knee_bend_deg"],
        release_angle_deg=angles["release_angle_deg"],
        torso_lean_deg=angles["torso_lean_deg"],
        shoulder_tilt_deg=angles["shoulder_tilt_deg"],
        follow_through_deg=angles["follow_through_deg"],
        landing_drift_px=angles["landing_drift_px"],
        release_height_norm=angles["release_height_norm"],
        matched_player=top_match["player_name"] if top_match else "",
        matched_player_team=top_match["team"] if top_match else "",
        matched_player_style=top_match["style"] if top_match else "",
        match_similarity_pct=top_match["similarity_pct"] if top_match else 0.0,
        second_match=sec_match["player_name"] if sec_match else "",
        second_match_pct=sec_match["similarity_pct"] if sec_match else 0.0,
    )

    return ShotResult(
        score=score,
        summary=summary,
        biggest_fix=biggest_fix,
        drill=drill,
        artifact_path=artifact_path,
        metrics=metrics,
        error=False,
        message="",
    ).to_dict()


def analyze_shot_from_directory(
    directory: str,
    user_height_in: int = 72,
    user_weight_lb: int = 185,
    output_dir: str = "workspace/outputs",
) -> dict:
    """
    Analyze a sequence of images from a directory (like video frames).

    Args:
        directory:       path to directory containing image files
        user_height_in:  user height in inches (default 6'0" = 72)
        user_weight_lb:  user weight in lbs
        output_dir:      where to save the annotated frame

    Returns:
        dict matching ShotResult schema (see cv_engine/schema.py)
    """

    if not os.path.isdir(directory):
        return ShotResult(
            error=True,
            message=f"Directory not found: {directory}"
        ).to_dict()

    # Load images from directory
    from cv_engine.pose import extract_frames_from_directory, run_pose_extraction, detect_release_frame, annotate_release_frame
    
    frames_indexed, fps, total = extract_frames_from_directory(directory, max_frames=60)

    if not frames_indexed:
        return ShotResult(
            error=True,
            message="No image files found in directory. Supported formats: JPG, PNG"
        ).to_dict()

    # Extract pose sequence
    frame_angles = run_pose_extraction(frames_indexed, fps, debug=False)

    if len(frame_angles) < 2:
        return err_not_visible()

    # Detect release frame from sequence
    release_idx = detect_release_frame(frame_angles)
    release_fa = frame_angles[release_idx]

    # Compute derived metrics
    from cv_engine.pose import compute_release_angle, compute_landing_drift
    
    release_angle = compute_release_angle(frame_angles, release_idx)
    landing_drift = compute_landing_drift(frame_angles, release_idx)
    angles = _build_angles_dict_simple(frame_angles[release_idx], release_angle, landing_drift)

    # Score + issues
    score, issues = compute_score_and_issues(angles)

    # NBA matching
    matches = match_player(
        user_angles=angles,
        user_height_in=user_height_in,
        user_weight_lb=user_weight_lb,
        top_k=3,
    )
    top_match = matches[0] if matches else None
    sec_match = matches[1] if len(matches) > 1 else None

    # Build feedback
    top_issue = issues[0] if issues else None
    summary = top_issue["label"] if top_issue else "Solid mechanics overall."
    biggest_fix = (
        f"Fix your {top_issue['metric'].replace('_', ' ').replace(' deg', '')}: "
        f"measured {top_issue['value']}° (ideal {top_issue['ideal']}°)."
        if top_issue else "Keep working on consistency."
    )
    drill = DRILLS.get(top_issue["metric"], "Form shooting from 5 feet, 20 reps.") if top_issue else ""

    # Save annotated artifact
    source_frame = frames_indexed[min(release_idx, len(frames_indexed) - 1)][1]
    annotated = annotate_release_frame(source_frame, release_fa)
    artifact_path = _save_artifact(annotated, output_dir)

    # Build metrics
    metrics = ShotMetrics(
        elbow_angle_deg=angles["elbow_angle_deg"],
        knee_bend_deg=angles["knee_bend_deg"],
        release_angle_deg=angles["release_angle_deg"],
        torso_lean_deg=angles["torso_lean_deg"],
        shoulder_tilt_deg=angles["shoulder_tilt_deg"],
        follow_through_deg=angles["follow_through_deg"],
        landing_drift_px=landing_drift,
        release_height_norm=angles["release_height_norm"],
        matched_player=top_match["player_name"] if top_match else "",
        matched_player_team=top_match["team"] if top_match else "",
        matched_player_style=top_match["style"] if top_match else "",
        match_similarity_pct=top_match["similarity_pct"] if top_match else 0.0,
        second_match=sec_match["player_name"] if sec_match else "",
        second_match_pct=sec_match["similarity_pct"] if sec_match else 0.0,
    )

    return ShotResult(
        score=score,
        summary=summary,
        biggest_fix=biggest_fix,
        drill=drill,
        artifact_path=artifact_path,
        metrics=metrics,
        error=False,
        message="",
    ).to_dict()


def _build_angles_dict_simple(release_fa, release_angle: float, landing_drift: float) -> dict:
    """Convert single FrameAngles into angles dict."""
    return {
        "elbow_angle_deg": release_fa.elbow_angle,
        "knee_bend_deg": release_fa.knee_angle,
        "release_angle_deg": release_angle,
        "torso_lean_deg": release_fa.torso_lean,
        "shoulder_tilt_deg": release_fa.shoulder_tilt,
        "follow_through_deg": min(90.0, release_fa.wrist_angle),
        "release_height_norm": release_fa.wrist_height,
        "landing_drift_px": landing_drift,
    }

    import json
    import argparse

    parser = argparse.ArgumentParser(description="Test the jump shot analyzer")
    parser.add_argument("video", help="Path to jump shot video")
    parser.add_argument("--height", type=int, default=72, help="Height in inches")
    parser.add_argument("--weight", type=int, default=185, help="Weight in lbs")
    args = parser.parse_args()

    print(f"Analyzing {args.video}...")
    result = analyze_shot(args.video, args.height, args.weight)
    print(json.dumps(result, indent=2))
