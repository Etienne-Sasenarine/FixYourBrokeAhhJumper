from ara_app.formatter import format_coaching_reply


def test_format_coaching_reply_success() -> None:
    result = {
        "score": 78,
        "summary": "Elbow drifts outside your shooting line.",
        "biggest_fix": "Keep elbow under the ball.",
        "drill": "One-hand form shooting, 30 reps.",
        "artifact_path": "",
        "metrics": {"release_angle_deg": 50.1},
        "error": False,
        "message": "",
    }

    text = format_coaching_reply(result)
    assert "AraShot score: 78/100" in text
    assert "Top issue:" in text
    assert "Metrics:" in text


def test_format_coaching_reply_error() -> None:
    result = {
        "score": 0,
        "summary": "",
        "biggest_fix": "",
        "drill": "",
        "artifact_path": "",
        "metrics": {},
        "error": True,
        "message": "Shooter not fully visible.",
    }

    text = format_coaching_reply(result)
    assert "AraShot update:" in text
    assert "Shooter not fully visible." in text
