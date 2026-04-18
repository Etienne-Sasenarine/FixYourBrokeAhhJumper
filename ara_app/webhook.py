from __future__ import annotations

import json
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from ara_app.handlers import process_incoming_message
from shared.schema import IncomingMessage


class AraShotWebhookHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 (http handler naming)
        if self.path != "/incoming":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": True, "message": "Route not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)

        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": True, "message": "Invalid JSON payload"})
            return

        sender = str(payload.get("sender", "") or "")
        text = str(payload.get("text", "") or "")
        attachments_raw = payload.get("attachments", [])

        if not sender:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": True, "message": "Missing sender"})
            return

        attachments = []
        if isinstance(attachments_raw, list):
            attachments = [str(item) for item in attachments_raw if isinstance(item, str)]

        incoming = IncomingMessage(sender=sender, text=text, attachments=attachments)
        outgoing = process_incoming_message(incoming)

        self._send_json(HTTPStatus.OK, asdict(outgoing))

    def do_GET(self) -> None:  # noqa: N802 (http handler naming)
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": True, "message": "Route not found"})


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), AraShotWebhookHandler)
    print(f"AraShot webhook listening at http://{host}:{port}")
    print("POST /incoming and GET /health are available")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
