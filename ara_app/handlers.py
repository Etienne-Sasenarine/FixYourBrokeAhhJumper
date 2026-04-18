from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from ara_app.formatter import format_coaching_reply
from ara_app.tools import analyze_shot
from shared.schema import IncomingMessage, OutgoingMessage, ShotAnalysisResult


ROOT = Path(__file__).resolve().parents[1]
INBOX_DIR = ROOT / "workspace" / "inbox"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}


def _first_image_attachment(attachments: list[str]) -> str | None:
    for item in attachments:
        path = Path(item)
        if path.is_dir() or path.suffix.lower() in IMAGE_EXTS:
            return item
    return None


def _store_latest_image(source_path: str) -> Path:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    source = Path(source_path)
    
    if source.is_dir():
        # If source is a directory, copy all images to a subdirectory
        target_dir = INBOX_DIR / "latest_shot"
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(source, target_dir)
        return target_dir
    else:
        # If source is a single image, copy it
        target = INBOX_DIR / f"latest_shot{source.suffix}"
        shutil.copy2(source, target)
        return target


def process_incoming_message(
    message: IncomingMessage,
    analyzer: Callable[[str], ShotAnalysisResult] = analyze_shot,
) -> OutgoingMessage:
    image = _first_image_attachment(message.attachments)
    if not image:
        return OutgoingMessage(
            recipient=message.sender,
            text="Please send a jump-shot image (JPG/PNG) or a folder of images so I can analyze your form.",
            attachments=[],
        )

    saved_image = _store_latest_image(image)
    result = analyzer(str(saved_image))
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
