"""
pose.py — MediaPipe pose extraction and angle computation.

Responsibilities:
- Load video, sample frames efficiently
- Run MediaPipe Pose on each frame
- Smooth landmarks over time
- Compute joint angles at each frame
- Detect shot phase (setup → dip → rise → release → follow-through)
- Return per-frame angle timeseries + release-frame metrics
"""

import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass
from typing import Optional

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

PoseLandmark = mp_pose.PoseLandmark


# ── Data structures ────────────────────────────────────────────────────────

@dataclass
class FrameAngles:
    frame_idx: int
    timestamp_ms: float
    elbow_angle: float
    knee_angle: float
    hip_angle: float
    shoulder_tilt: float
    wrist_height: float      # normalized 0-1 (0=bottom of frame)
    wrist_x: float           # normalized, for drift tracking
    ankle_x: float           # normalized, for drift tracking
    torso_lean: float
    wrist_angle: float       # proxy for follow-through
    visible: bool = True


@dataclass
class PoseResult:
    frames: list[FrameAngles]
    release_frame_idx: int
    release_angles: FrameAngles
    takeoff_wrist_x: float   # for landing drift calc
    fps: float
    total_frames: int
    annotated_frame: Optional[np.ndarray] = None  # BGR image at release


# ── Geometry helpers ───────────────────────────────────────────────────────

def _pt(lm, idx) -> np.ndarray:
    l = lm[idx]
    return np.array([l.x, l.y])

def _angle(a, b, c) -> float:
    """Angle at joint b, given points a-b-c. Returns degrees 0-180."""
    ab = a - b
    cb = c - b
    cos = np.dot(ab, cb) / (np.linalg.norm(ab) * np.linalg.norm(cb) + 1e-8)
    return float(np.degrees(np.arccos(np.clip(cos, -1, 1))))

def _visibility_ok(lm, indices: list[int], threshold: float = 0.5) -> bool:
    return all(lm[i].visibility > threshold for i in indices)


# ── Core extraction ────────────────────────────────────────────────────────

def extract_frames(video_path: str, max_frames: int = 60) -> tuple[list, float, int]:
    """
    Sample up to max_frames evenly from the video.
    Returns (frames_bgr, fps, total_frame_count).
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    sample_count = min(max_frames, total)
    indices = np.linspace(0, total - 1, sample_count, dtype=int)

    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if ret:
            frames.append((int(idx), frame))

    cap.release()
    return frames, fps, total


def extract_frames_from_image(image_path: str) -> tuple[list, float, int]:
    """
    Load a single image file. Returns (frames_bgr, fps=1.0, total_frame_count=1).
    Treats the image as a single frame.
    """
    frame = cv2.imread(image_path)
    if frame is None:
        return [], 1.0, 0
    
    return [(0, frame)], 1.0, 1


def extract_frames_from_directory(directory: str, max_frames: int = 60) -> tuple[list, float, int]:
    """
    Load all image files from a directory in alphanumeric order.
    Returns (frames_bgr, fps=1.0, total_frame_count).
    Treats images as a sequence of frames.
    """
    from pathlib import Path
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.mp4', '.avi'}
    image_files = sorted([
        f for f in Path(directory).iterdir() 
        if f.suffix.lower() in image_extensions
    ])
    
    if not image_files:
        return [], 1.0, 0
    
    # Sample evenly if more than max_frames
    sample_indices = np.linspace(0, len(image_files) - 1, min(max_frames, len(image_files)), dtype=int)
    
    frames = []
    for idx in sample_indices:
        frame = cv2.imread(str(image_files[idx]))
        if frame is not None:
            frames.append((idx, frame))
    
    return frames, 1.0, len(image_files)


def _process_frame(frame_bgr: np.ndarray, pose, frame_idx: int, fps: float) -> Optional[FrameAngles]:
    """Run MediaPipe on one frame and return angles, or None if pose not detected."""
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if not results.pose_landmarks:
        return None

    lm = results.pose_landmarks.landmark

    # Key landmark indices
    R_SHOULDER = PoseLandmark.RIGHT_SHOULDER
    L_SHOULDER = PoseLandmark.LEFT_SHOULDER
    R_ELBOW    = PoseLandmark.RIGHT_ELBOW
    R_WRIST    = PoseLandmark.RIGHT_WRIST
    R_HIP      = PoseLandmark.RIGHT_HIP
    R_KNEE     = PoseLandmark.RIGHT_KNEE
    R_ANKLE    = PoseLandmark.RIGHT_ANKLE
    L_HIP      = PoseLandmark.LEFT_HIP

    # Check critical landmarks are visible
    critical = [R_SHOULDER, R_ELBOW, R_WRIST, R_HIP, R_KNEE, R_ANKLE]
    if not _visibility_ok(lm, critical, 0.4):
        return None

    rs  = _pt(lm, R_SHOULDER)
    ls  = _pt(lm, L_SHOULDER)
    re  = _pt(lm, R_ELBOW)
    rw  = _pt(lm, R_WRIST)
    rh  = _pt(lm, R_HIP)
    lh  = _pt(lm, L_HIP)
    rk  = _pt(lm, R_KNEE)
    ra  = _pt(lm, R_ANKLE)

    elbow_angle    = _angle(rs, re, rw)
    knee_angle     = _angle(rh, rk, ra)
    hip_angle      = _angle(rs, rh, rk)
    shoulder_tilt  = float(abs(lm[L_SHOULDER].y - lm[R_SHOULDER].y) * 100)

    # Torso lean: angle of shoulder-hip line from vertical
    hip_mid = (rh + lh) / 2
    sh_mid  = (rs + ls) / 2
    torso_vec = sh_mid - hip_mid
    torso_lean = float(abs(np.degrees(np.arctan2(torso_vec[0], -torso_vec[1]))))

    # Wrist angle (elbow-wrist-fingertip proxy using wrist direction)
    wrist_angle = float(abs(rw[1] - re[1]) * 180)  # simplified proxy

    return FrameAngles(
        frame_idx=frame_idx,
        timestamp_ms=(frame_idx / fps) * 1000,
        elbow_angle=round(elbow_angle, 1),
        knee_angle=round(knee_angle, 1),
        hip_angle=round(hip_angle, 1),
        shoulder_tilt=round(shoulder_tilt, 2),
        wrist_height=round(1.0 - float(lm[R_WRIST].y), 3),  # invert: 1=top
        wrist_x=round(float(lm[R_WRIST].x), 3),
        ankle_x=round(float(lm[R_ANKLE].x), 3),
        torso_lean=round(torso_lean, 1),
        wrist_angle=round(wrist_angle, 1),
        visible=True,
    )


def run_pose_extraction(frames_indexed: list, fps: float, debug: bool = False) -> list[FrameAngles]:
    """Run MediaPipe across all sampled frames."""
    results = []
    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,          # 1 = good balance on CPU
        smooth_landmarks=False,
        min_detection_confidence=0.45,
        min_tracking_confidence=0.45,
    ) as pose:
        for (idx, frame) in frames_indexed:
            fa = _process_frame(frame, pose, idx, fps)
            if fa:
                results.append(fa)
            if debug:
                debug_frame = frame.copy()
                rgb = cv2.cvtColor(debug_frame, cv2.COLOR_BGR2RGB)
                mp_results = pose.process(rgb)
                
                if mp_results.pose_landmarks:
                    mp_drawing.draw_landmarks(
                        debug_frame, 
                        mp_results.pose_landmarks, 
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 150), thickness=2, circle_radius=3),
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2)
                    )
                
                # Resize window if the video is massive (e.g., 4K phone video)
                h, w = debug_frame.shape[:2]
                if h > 800:
                    scale = 800 / h
                    debug_frame = cv2.resize(debug_frame, (int(w * scale), 800))

                cv2.imshow("MediaPipe Vision Stream", debug_frame)
                cv2.waitKey(30) # Delay in ms to simulate video playback speed

    if debug:
        cv2.destroyAllWindows()

    return results


# ── Shot phase detection ───────────────────────────────────────────────────

def detect_release_frame(frame_angles: list[FrameAngles]) -> int:
    """
    Identify the release frame index within frame_angles list.

    Heuristic:
    - Release = frame where wrist is highest AND elbow is most extended
      (largest elbow angle after the dip phase)
    - We look for the peak wrist height after a dip-then-rise pattern
    """
    if not frame_angles:
        return 0

    wrist_heights = np.array([f.wrist_height for f in frame_angles])
    elbow_angles  = np.array([f.elbow_angle  for f in frame_angles])

    # Smooth to remove noise
    if len(wrist_heights) > 5:
        kernel = np.ones(3) / 3
        wrist_heights_smooth = np.convolve(wrist_heights, kernel, mode='same')
    else:
        wrist_heights_smooth = wrist_heights

    # Score = wrist height (normalized) + elbow extension contribution
    elbow_norm = (elbow_angles - elbow_angles.min()) / (elbow_angles.ptp() + 1e-8)
    score = wrist_heights_smooth * 0.7 + elbow_norm * 0.3

    # Only look in the top 60% of the video (ignore follow-through decay)
    cutoff = int(len(score) * 0.85)
    release_local = int(np.argmax(score[:cutoff]))
    return release_local


def compute_release_angle(frame_angles: list[FrameAngles], release_idx: int) -> float:
    """
    Estimate ball release angle from wrist trajectory slope around release.
    Uses wrist height change over the frames around release.
    """
    n = len(frame_angles)
    lo = max(0, release_idx - 2)
    hi = min(n - 1, release_idx + 2)

    if hi <= lo:
        return 50.0  # fallback

    dy = frame_angles[hi].wrist_height - frame_angles[lo].wrist_height
    dx = frame_angles[hi].wrist_x      - frame_angles[lo].wrist_x + 1e-8

    angle = float(np.degrees(np.arctan2(abs(dy), abs(dx))))
    return round(min(80.0, max(20.0, angle)), 1)


def compute_landing_drift(frame_angles: list[FrameAngles], release_idx: int) -> float:
    """
    Pixel-space drift: how far does the shooter's ankle move horizontally
    from takeoff (lowest knee angle) to landing (after peak).
    Returned in normalized units * 100 for readability.
    """
    if len(frame_angles) < 4:
        return 0.0

    # Takeoff = frame with most knee bend before release
    pre = frame_angles[:release_idx + 1]
    if not pre:
        return 0.0
    takeoff_idx = int(np.argmin([f.knee_angle for f in pre]))
    takeoff_x = pre[takeoff_idx].ankle_x

    # Landing = frame with lowest wrist height after release
    post = frame_angles[release_idx:]
    if not post:
        return 0.0
    landing_x = post[-1].ankle_x

    return round(abs(landing_x - takeoff_x) * 100, 1)


# ── Annotation ────────────────────────────────────────────────────────────

def annotate_release_frame(frame_bgr: np.ndarray, release_fa: FrameAngles) -> np.ndarray:
    """
    Draw pose overlay + angle readouts on the release frame.
    Returns annotated BGR image.
    """
    img = frame_bgr.copy()
    h, w = img.shape[:2]

    # Re-run pose on this specific frame to get landmarks for drawing
    with mp_pose.Pose(static_image_mode=True, model_complexity=1,
                      min_detection_confidence=0.4) as pose:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                img,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(
                    color=(0, 255, 150), thickness=2, circle_radius=4),
                connection_drawing_spec=mp_drawing.DrawingSpec(
                    color=(255, 255, 255), thickness=2),
            )

    # Overlay angle readouts
    metrics = [
        (f"Elbow: {release_fa.elbow_angle:.0f}deg", (0, 255, 150)),
        (f"Knee:  {release_fa.knee_angle:.0f}deg",  (0, 200, 255)),
        (f"Lean:  {release_fa.torso_lean:.0f}deg",  (255, 200, 0)),
    ]
    for i, (text, color) in enumerate(metrics):
        cv2.putText(img, text, (12, 32 + i * 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 4)
        cv2.putText(img, text, (12, 32 + i * 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

    # Release label
    cv2.putText(img, "RELEASE FRAME", (w - 220, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 4)
    cv2.putText(img, "RELEASE FRAME", (w - 220, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 100, 50), 2)

    return img


# ── Main entry ────────────────────────────────────────────────────────────

def run_pose_pipeline(video_path: str, max_frames: int = 60, debug: bool = False) -> Optional[PoseResult]:
    """
    Full pipeline: video → PoseResult with release frame angles + annotated image.
    Returns None if pose cannot be reliably detected.
    """
    frames_indexed, fps, total = extract_frames(video_path, max_frames)

    if not frames_indexed:
        return None

    frame_angles = run_pose_extraction(frames_indexed, fps, debug=debug)

    # Need at least 5 good frames
    if len(frame_angles) < 5:
        return None

    release_idx = detect_release_frame(frame_angles)
    release_fa  = frame_angles[release_idx]

    # Annotate the actual source frame at that index
    source_frame = frames_indexed[
        min(release_idx, len(frames_indexed) - 1)
    ][1]
    annotated = annotate_release_frame(source_frame, release_fa)

    # Takeoff wrist x = wrist position at deepest knee bend
    pre = frame_angles[:release_idx + 1]
    takeoff_idx = int(np.argmin([f.knee_angle for f in pre])) if pre else 0
    takeoff_wrist_x = frame_angles[takeoff_idx].wrist_x

    return PoseResult(
        frames=frame_angles,
        release_frame_idx=release_idx,
        release_angles=release_fa,
        takeoff_wrist_x=takeoff_wrist_x,
        fps=fps,
        total_frames=total,
        annotated_frame=annotated,
    )
