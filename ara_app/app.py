from __future__ import annotations

import argparse
from pathlib import Path

from ara_app.handlers import process_incoming_message
from shared.schema import IncomingMessage


def run_demo(image_path: str, sender: str) -> None:
    msg = IncomingMessage(sender=sender, text="shot check", attachments=[image_path])

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
    parser.add_argument("--image", required=True, help="Path to a local shot image file (JPG/PNG) or directory of images")
    parser.add_argument("--sender", default="Ara Demo User", help="Simulated iMessage sender")
    args = parser.parse_args()

    image = Path(args.image)
    if not image.exists():
        raise FileNotFoundError(f"Image/directory not found: {image}")

    run_demo(image_path=str(image), sender=args.sender)


if __name__ == "__main__":
    main()
