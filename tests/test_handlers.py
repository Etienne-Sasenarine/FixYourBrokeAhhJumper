from __future__ import annotations

from pathlib import Path

from ara_app.handlers import process_incoming_message
from shared.schema import IncomingMessage


def test_no_video_attachment_returns_prompt() -> None:
    incoming = IncomingMessage(sender="Ara User", text="hey", attachments=[])
    out = process_incoming_message(incoming)

    assert out.recipient == "Ara User"
    assert "Please send a jump-shot video" in out.text
    assert out.attachments == []


def test_process_video_attachment_roundtrip(tmp_path: Path) -> None:
    src = tmp_path / "clip.mp4"
    src.write_bytes(b"fake video")

    incoming = IncomingMessage(sender="Ara User", text="check shot", attachments=[str(src)])
    out = process_incoming_message(incoming)

    assert out.recipient == "Ara User"
    assert "AraShot score:" in out.text
    assert len(out.attachments) <= 1
