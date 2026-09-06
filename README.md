# Text to Speech

This command-line tool creates natural-sounding narration with Microsoft Edge neural voices. Use it transparently and follow the disclosure and synthetic-media rules of the platform where you publish.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Examples

Convert a sentence. For Urdu or Roman Urdu, the default voice is `ur-PK-AsadNeural`:

```bash
python tts.py --text "Hello how are you" --output welcome.mp3
```

Convert a text file and leave a disclosure sidecar:

```bash
python tts.py --file script.txt --voice ur-PK-AsadNeural --rate=-5% --pitch=+0Hz --output narration.mp3 --disclosure
```

For the best Urdu pronunciation, write the script in Urdu letters, for example:

```bash
python tts.py --text "السلام علیکم حسن بھائی، کیسے ہیں؟" --voice ur-PK-AsadNeural --output urdu.mp3
```

Roman Urdu does not have one standard spelling, so spellings such as `kesa han`, `kaise hain`, and `kesay hain` can be pronounced differently. Add commas and full stops to create natural pauses. Use `ur-PK-UzmaNeural` for a female voice.

See available voices:

```bash
python tts.py --list-voices
```

## Browser studio

Start the local frontend:

```bash
source .venv/bin/activate
python app.py
```

Then open <http://127.0.0.1:3000>. Select Urdu / Roman Urdu, English, or Hindi; choose a voice; write or import a script; adjust pace and pitch; and download the MP3 result.

### Use your own voice

The studio can create a custom voice from your own recording through ElevenLabs. This requires an ElevenLabs account and API key. Set it only in your terminal, never in frontend code:

```bash
export ELEVENLABS_API_KEY="your-api-key"
python app.py
```

In the studio, upload a clean recording of the consenting speaker, confirm ownership or permission, click **Create my voice**, select **My custom voice**, and generate the narration. Use a quiet recording with one speaker and clear Urdu/English speech. Do not upload another person’s voice without their explicit permission. Custom voice cloning is optional; the built-in neural voices still work without an API key.

Instant Voice Cloning is a paid ElevenLabs feature. If the app reports that the subscription does not include it, the API key is valid but the current plan cannot create a clone; upgrade the plan or keep using the built-in voices.

The web studio is local, but the selected neural voice service must be reachable to generate speech. It is designed for transparent synthetic narration and does not attempt to bypass AI-detection or platform labeling systems.

Naturalness usually improves when the script uses short paragraphs, punctuation, contractions, and explicit pauses. This tool does not attempt to bypass AI-detection or platform labeling systems.