# Ara/Linq Bridge Mapping

This is the step-3 wiring spec for connecting an incoming iMessage/Linq event to the AraShot webhook.

## Goal

When a user texts a jump-shot video, the bridge should:

1. Download the attached video to a local absolute file path.
2. POST the message to the AraShot webhook.
3. Read the webhook response.
4. Send the returned text and attachments back to the same message thread.

## Inbound event to webhook payload

Map your bridge event into this JSON body:

```json
{
  "sender": "Carl",
  "text": "shot check",
  "attachments": ["C:/abs/path/to/downloaded_video.mp4"]
}
```

### Field mapping

- `sender`: display name or phone label from the incoming iMessage thread.
- `text`: the user’s message text, or an empty string if they only sent media.
- `attachments`: absolute local file paths for downloaded media.

### Important rules

- Always download the attachment before calling the webhook.
- Do not pass iMessage attachment IDs, cloud URLs, or temporary handles.
- Use an absolute path the machine running Ara can read.
- If there are multiple attachments, include every file path in the array.

## Webhook endpoint

Send the POST request to:

```text
https://environment-hughes-starting-labs.trycloudflare.com/incoming
```

During local development, you can use:

```text
http://127.0.0.1:8765/incoming
```

## Webhook response to iMessage reply

The webhook returns:

```json
{
  "recipient": "Carl",
  "text": "AraShot score: 82/100...",
  "attachments": ["C:/abs/path/to/release_frame.png"]
}
```

### Reply mapping

- `recipient`: use this to select the iMessage thread to reply to.
- `text`: send this as the main reply message.
- `attachments`: attach each file path if it exists on disk.

## Suggested Ara/Linq flow

1. Trigger on incoming iMessage with a media attachment.
2. Download the media to a known local folder, for example `C:/Ara/inbox/latest_shot.mp4`.
3. Build the webhook payload using the mappings above.
4. POST to the webhook.
5. Parse the JSON response.
6. Send `text` back to the same thread.
7. Attach the first file in `attachments` if present.

## Fallback behavior

If no video is attached:

1. Do not call the webhook.
2. Send a short prompt back to the user asking for a shot video.

Recommended prompt:

```text
Please send a jump-shot video attachment so I can analyze your form.
```

## Demo checklist

- Local webhook running
- Public tunnel running
- Bridge downloads video to a local path
- Bridge POSTs payload to `/incoming`
- Response text returns to the same iMessage thread
- Optional artifact attachment is sent if provided
