from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from ara_app.formatter import format_coaching_reply
from ara_app.tools import analyze_shot
from shared.schema import IncomingMessage, OutgoingMessage, ShotAnalysisResult


ROOT = Path(__file__).resolve().parents[1]
INBOX_DIR = ROOT / "workspace" / "inbox"
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi"}


def _first_video_attachment(attachments: list[str]) -> str | None:
    for item in attachments:
        if Path(item).suffix.lower() in VIDEO_EXTS:
            return item
    return None


def _store_latest_clip(source_path: str) -> Path:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    source = Path(source_path)
    target = INBOX_DIR / "latest_shot.mp4"
    shutil.copy2(source, target)
    return target


def process_incoming_message(
    message: IncomingMessage,
    analyzer: Callable[[str], ShotAnalysisResult] = analyze_shot,
) -> OutgoingMessage:
    video = _first_video_attachment(message.attachments)
    if not video:
        return OutgoingMessage(
            recipient=message.sender,
            text="Please send a jump-shot video attachment so I can analyze your form.",
            attachments=[],
        )

    saved_video = _store_latest_clip(video)
    result = analyzer(str(saved_video))
    reply = format_coaching_reply(result)

    outbound_attachments: list[str] = []
    artifact = result.get("artifact_path", "")
    if artifact and Path(artifact).exists():
        outbound_attachments.append(artifact)

    return OutgoingMessage(
        recipient=message.sender,
        text=reply,
        attachments=outbound_attachments,
    )
