
# FixYourBrokeAhhJumper
## Winner of Most Technical @ Ara (YC P26) x Cornell Hackathon


Have you ever been at the gym with your homeboy and thought, “Wow, your jumper sucks”? Now introducing FixYourBrokeAhhJumper! Based on metrics from your favorite players like LeBron James, Stephen Curry, and Donovan Mitchell, we use computer vision and frame-by-frame analysis to suggest form adjustments and drills. You receive on-demand feedback right on the court—just as if you were texting a friend.

FixYourBrokeAhhJumper is a project for automated basketball shot analysis. It processes video clips, analyzes shooting form, and returns actionable coaching feedback. This project demonstrates modular orchestration, computer vision, and messaging integration.

## Features
- **Automated video intake and processing**
- **Computer vision shot analysis**
- **Actionable coaching feedback**
- **Webhook and CLI integration**
- **Modular, testable Python codebase**

## Project Structure

```
ara_app/         # Orchestration, CLI, webhook, formatting
cv_engine/       # Computer vision engine
shared/          # Shared schemas
workspace/       # Inbox and outputs
tests/           # Unit tests
```

## Getting Started

### Prerequisites
- Python 3.10+
- [Install requirements](requirements.txt):
  ```bash
  pip install -r requirements.txt
  ```

### Quick Demo
1. Place a sample video on disk (e.g., `C:\temp\shot.mp4`).
2. Run the CLI demo:
   ```bash
   python -m ara_app.app --video C:\temp\shot.mp4 --sender "Demo User"
   ```
3. Output: Coaching feedback and annotated frame path.

### Webhook Mode
Start the webhook service:
```bash
python -m ara_app.webhook
```
Health check:
```bash
curl http://127.0.0.1:8765/health
```

Send a message (PowerShell example):
```powershell
$body = @{ sender = "Demo User"; text = "shot check"; attachments = @("C:/temp/shot.mp4") } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8765/incoming" -ContentType "application/json" -Body $body
```

### Bridge Integration
Use the bridge to forward iMessage/video attachments:
```bash
python -m ara_app.bridge --endpoint <webhook_url> --sender "User" --text "shot check" --attachment "C:\temp\shot.mp4"
```
See [docs/ara_linq_mapping.md](docs/ara_linq_mapping.md) for mapping details.

## Analyzer Modes
- **Local CV Engine:** Calls `cv_engine.pipeline.analyze_shot()` directly.
- **HTTP Analyzer:** Set `SHOT_ANALYZER_URL` to use a remote analyzer.
- **Stub Mode:** Set `USE_STUB_DATA=1` for deterministic test data.

## Output Contract
The analyzer returns JSON matching `shared/schema.py`. Example:
```json
{
  "score": 78,
  "summary": "Your elbow flares outward before release.",
  "biggest_fix": "Keep your elbow under the ball.",
  "drill": "One-hand form shooting from 5 feet.",
  "artifact_path": "workspace/outputs/release_frame.png",
  "metrics": { "release_angle_deg": 49.2, "elbow_angle_deg": 151.0 },
  "error": false,
  "message": ""
}
```

## Testing
Run all tests:
```bash
python -m pytest
```

## Contributing
Pull requests and issues are welcome! Please open an issue to discuss major changes.

## License
MIT License. See LICENSE file for details.
