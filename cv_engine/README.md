# CV Engine Placeholder

Person 2 owns this folder.

Contract expected by Person 1:
- Input: `video_path` (local file path)
- Output: JSON object with fields in `shared/schema.py` (`ShotAnalysisResult`)

The Person 1 app can call either:
- stub analyzer (default), or
- HTTP analyzer when `SHOT_ANALYZER_URL` is set.
