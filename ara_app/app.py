from __future__ import annotations

import argparse
from pathlib import Path

from ara_app.handlers import process_incoming_message
from shared.schema import IncomingMessage


def run_demo(video_path: str, sender: str) -> None:
    msg = IncomingMessage(sender=sender, text="shot check", attachments=[video_path])

    print("AraShot: analyzing your shot...")
    response = process_incoming_message(msg)

    print("\n--- Outbound Message ---")
    print(f"To: {response.recipient}")
    print(response.text)

    if response.attachments:
        print("\nAttachments:")
        for item in response.attachments:
            print(f"- {item}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Person 1 orchestration demo for AraShot")
    parser.add_argument("--video", required=True, help="Path to a local shot video file")
    parser.add_argument("--sender", default="Ara Demo User", help="Simulated iMessage sender")
    args = parser.parse_args()

    video = Path(args.video)
    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")

    run_demo(video_path=str(video), sender=args.sender)


if __name__ == "__main__":
    main()
