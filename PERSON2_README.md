# Person 2 — CV Engine

## Your 2-hour build order

### Minute 0–10: Setup
```bash
pip install mediapipe opencv-python numpy
python -c "import mediapipe, cv2, numpy; print('OK')"
```

### Minute 10–20: Verify stub works for Person 1
Send Person 1 this:
```python
from cv_engine.stub import analyze_shot
print(analyze_shot("any_path.mp4"))
```
They're unblocked. You now work in parallel.

### Minute 20–60: Build pose.py
Test with any video:
```bash
python -c "
from cv_engine.pose import run_pose_pipeline
r = run_pose_pipeline('your_test_video.mp4')
print(r.release_angles if r else 'No pose detected')
"
```

### Minute 60–80: Build + test metrics.py
```bash
python -c "
from cv_engine.metrics import compute_score_and_issues
angles = {'elbow_angle_deg': 143, 'knee_bend_deg': 118, 'release_angle_deg': 48,
          'torso_lean_deg': 6, 'shoulder_tilt_deg': 3, 'follow_through_deg': 55,
          'release_height_norm': 0.81}
score, issues = compute_score_and_issues(angles)
print('Score:', score)
for i in issues[:3]: print(i)
"
```

### Minute 80–100: Test full pipeline end-to-end
```bash
python cv_engine/pipeline.py your_test_video.mp4 --height 72 --weight 185
```

### Minute 100–120: Integration + hardening
- Run on 2-3 different videos
- Test error cases (bad angle, no body visible)
- Save a good annotated frame for the demo
- Tell Person 1 to swap stub → pipeline import

## Interface you give Person 1

```python
from cv_engine.pipeline import analyze_shot

result = analyze_shot(
    video_path="workspace/inbox/latest_shot.mp4",
    user_height_in=72,    # 6'0" = 72 inches
    user_weight_lb=185,
)
```

Output schema — never change the top-level keys:
```json
{
  "score": 74,
  "summary": "Your elbow flares outward before release.",
  "biggest_fix": "Fix your elbow angle: measured 143.0° (ideal 85–100°).",
  "drill": "Wall drill: ...",
  "artifact_path": "workspace/outputs/release_frame.jpg",
  "metrics": { ... },
  "error": false,
  "message": ""
}
```

Error output:
```json
{
  "error": true,
  "message": "Shooter not fully visible. Please record from the side with your full body in frame."
}
```

## Tips for filming test videos
- Film from the side — not head-on, not behind
- Full body must be visible (head to feet)
- Good light, no motion blur
- 5–15 seconds is ideal
- iPhone slo-mo (240fps) works great
