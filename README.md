# FixYourBrokeAhhJumper

AraShot MVP split for a 2-person hackathon team.

## Person 1 scope (implemented)

This repo now includes Person 1's orchestration layer:
- message intake
- attachment handling
- saved clip path (`workspace/inbox/latest_shot.mp4`)
- analyzer tool call
- response formatting
- artifact attach-back

## Project structure

```
ara_app/
	app.py
	handlers.py
	formatter.py
	tools.py
cv_engine/
	README.md
shared/
	schema.py
workspace/
	inbox/
	outputs/
```

## How to run Person 1 demo

1. Use Python 3.10+.
2. Place any sample video on disk (for example: `C:\temp\shot.mp4`).
3. Run:

```bash
python -m ara_app.app --video C:\temp\shot.mp4 --sender "Ara Demo User"
```

You should see:
- an outbound coaching text
- one attachment path (mock annotated frame)

## Webhook mode for bridge integration

Start the webhook service:

```bash
python -m ara_app.webhook
```

Health check:

```bash
curl http://127.0.0.1:8765/health
```

Incoming message contract (`POST /incoming`):

```json
{
	"sender": "Ara Demo User",
	"text": "shot check",
	"attachments": ["C:/temp/shot.mp4"]
}
```

Example PowerShell call:

```powershell
$body = @{
	sender = "Ara Demo User"
	text = "shot check"
	attachments = @("C:/temp/shot.mp4")
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8765/incoming" -ContentType "application/json" -Body $body
```

The response payload is your outbound message structure:
- recipient
- text
- attachments

## Step 3: Bridge the phone to the webhook

Use the bridge adapter when Ara or Linq downloads the iMessage attachment to a local path.

Full field-by-field mapping spec: [docs/ara_linq_mapping.md](docs/ara_linq_mapping.md)

Example:

```bash
python -m ara_app.bridge --endpoint https://environment-hughes-starting-labs.trycloudflare.com/incoming --sender "Carl" --text "shot check" --attachment "C:\temp\shot.mp4"
```

What this does:
- builds the exact JSON payload the webhook expects
- posts the downloaded video path to the public tunnel
- prints the returned coaching response

Use this same shape inside Ara/Linq:

```json
{
	"sender": "Carl",
	"text": "shot check",
	"attachments": ["C:/temp/shot.mp4"]
}
```

If you are wiring Ara/Linq directly, the bridge steps are:
- detect incoming iMessage with video attachment
- save the attachment to a local absolute path
- call the webhook with sender, text, and attachments
- forward the returned `text` and `attachments` back to the iMessage thread

## Analyzer integration modes

### Mode A: real Person 2 engine (default local)
No environment variable is needed. Person 1 now calls `cv_engine.pipeline.analyze_shot()` directly.

### Mode B: real Person 2 engine (HTTP)
Set:

```bash
set SHOT_ANALYZER_URL=http://localhost:8001/analyze
```

Then run the same Person 1 command. The app will POST:

```json
{
	"video_path": ".../workspace/inbox/latest_shot.mp4"
}
```

### Mode C: deterministic stub (for fast UI testing)
Set:

```bash
set USE_STUB_DATA=1
```

## Shared output contract

Person 2 must return JSON matching `shared/schema.py`:

```json
{
	"score": 78,
	"summary": "Your elbow flares outward before release.",
	"biggest_fix": "Keep your elbow under the ball.",
	"drill": "One-hand form shooting from 5 feet.",
	"artifact_path": "workspace/outputs/release_frame.png",
	"metrics": {
		"release_angle_deg": 49.2,
		"elbow_angle_deg": 151.0,
		"landing_drift_px": 28
	},
	"error": false,
	"message": ""
}
```

Failure example:

```json
{
	"score": 0,
	"summary": "",
	"biggest_fix": "",
	"drill": "",
	"artifact_path": "",
	"metrics": {},
	"error": true,
	"message": "Shooter not fully visible. Please record from the side with full body in frame."
}
```

## Files you own as Person 1

- `ara_app/handlers.py`: receive message, validate video attachment, save clip, call analyzer, return response
- `ara_app/tools.py`: adapter to stub or external analyzer service
- `ara_app/formatter.py`: concise coaching message format
- `ara_app/app.py`: local CLI demo entrypoint
- `ara_app/webhook.py`: HTTP endpoint for incoming bridge messages
- `ara_app/bridge.py`: CLI bridge adapter that posts to the webhook
- `shared/schema.py`: handshake schema and normalizer

## Tests

Run tests with:

```bash
python -m pytest
```
