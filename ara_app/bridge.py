from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib import request


def build_payload(sender: str, text: str, attachments: list[str]) -> dict[str, Any]:
    return {
        "sender": sender,
        "text": text,
        "attachments": attachments,
    }


def post_incoming(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")

    return json.loads(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a phone/bridge message to AraShot webhook")
    parser.add_argument("--endpoint", required=True, help="Webhook endpoint, e.g. https://xxxx.trycloudflare.com/incoming")
    parser.add_argument("--sender", required=True, help="iMessage sender name or phone label")
    parser.add_argument("--text", default="shot check", help="Message text")
    parser.add_argument(
        "--attachment",
        action="append",
        default=[],
        help="Absolute path to a downloaded video attachment. Can be passed multiple times.",
    )
    args = parser.parse_args()

    attachments: list[str] = []
    for item in args.attachment:
        path = Path(item)
        if not path.exists():
            raise FileNotFoundError(f"Attachment not found: {path}")
        attachments.append(str(path))

    payload = build_payload(args.sender, args.text, attachments)
    response = post_incoming(args.endpoint, payload)
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()