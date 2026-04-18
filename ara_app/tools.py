from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict
from urllib import request

from shared.schema import ShotAnalysisResult, normalize_analysis_result


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "workspace" / "outputs"


def _write_mock_artifact(path: Path) -> None:
    """Create a tiny placeholder PNG so outbound attachments always work in stub mode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # 1x1 transparent PNG
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
        "ASsJTYQAAAAASUVORK5CYII="
    )
    path.write_bytes(base64.b64decode(png_b64))


def _stub_analysis(image_path: str) -> ShotAnalysisResult:
    artifact = OUTPUT_DIR / "mock_release_frame.png"
    _write_mock_artifact(artifact)

    return normalize_analysis_result(
        {
            "score": 82,
            "summary": "Your elbow flares outward before release.",
            "biggest_fix": "Keep your elbow under the ball through lift-off.",
            "drill": "One-hand form shooting from 5 feet, 3 sets of 10.",
            "artifact_path": str(artifact),
            "metrics": {
                "elbow_flare_deg": 14.2,
                "release_angle_deg": 48.8,
                "landing_drift_px": 21.0,
            },
            "error": False,
            "message": "",
            "image_path": image_path,
        }
    )


def _http_analysis(image_path: str, endpoint: str) -> ShotAnalysisResult:
    payload = json.dumps({"image_path": image_path}).encode("utf-8")
    req = request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")

    data: Dict[str, Any] = json.loads(body)
    return normalize_analysis_result(data)


def analyze_shot(image_path: str) -> ShotAnalysisResult:
    """Adapter layer for Person 2's image engine.

    Accepts a single image file or directory of images.
    
    Priority:
    1) SHOT_ANALYZER_URL: call remote HTTP analyzer
    2) USE_STUB_DATA=1: use deterministic local stub
    3) Default: call local cv_engine.pipeline analyzer
    """
    endpoint = os.getenv("SHOT_ANALYZER_URL", "").strip()
    if endpoint:
        return _http_analysis(image_path=image_path, endpoint=endpoint)

    if os.getenv("USE_STUB_DATA", "").strip() == "1":
        return _stub_analysis(image_path=image_path)

    # Lazy import keeps HTTP/stub mode usable even if CV deps are not installed.
    try:
        from pathlib import Path
        path = Path(image_path)
        
        if path.is_dir():
            from cv_engine.pipeline import analyze_shot_from_directory as cv_analyze_shot
            result = cv_analyze_shot(image_path=image_path)
        else:
            from cv_engine.pipeline import analyze_shot_from_image as cv_analyze_shot
            result = cv_analyze_shot(image_path=image_path)
        
        return normalize_analysis_result(result)
    except Exception as exc:
        if os.getenv("FALLBACK_TO_STUB_ON_CV_ERROR", "1").strip() == "1":
            return _stub_analysis(image_path=image_path)

        return normalize_analysis_result(
            {
                "error": True,
                "message": f"CV pipeline unavailable: {exc}",
            }
        )
