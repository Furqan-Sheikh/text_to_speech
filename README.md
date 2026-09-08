# Text to Speech

This project provides two narration paths:

- The lightweight CLI and browser studio use Microsoft Edge neural voices.
- The local GPU studio uses open-source models for consent-based English and Urdu voice cloning without an ElevenLabs key.

Use generated audio transparently and follow the disclosure and synthetic-media rules of the platform where you publish.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, use:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
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

Then open <http://127.0.0.1:3000>. Select Urdu / Roman Urdu or English; choose a voice; write or import a script; adjust pace and pitch; and download the MP3 result.

## Local voice cloning

Local cloning requires an NVIDIA GPU with working CUDA. The current implementation uses Chatterbox for English, and the public `facebook/mms-tts-urd-script_arabic` model followed by Chatterbox voice conversion for Urdu. It does not train a new model from your two recordings; the recordings provide the speaker reference for pretrained models. Fine-tuning requires a much larger, carefully transcribed dataset.

Install the GPU dependencies:

```powershell
python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements-cloud.txt
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CUDA unavailable')"
```

The CUDA check must print `True`. The first local run downloads the Chatterbox and Urdu model weights from Hugging Face and can take several minutes.

Start the local browser studio:

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Open <http://127.0.0.1:3000>, upload one or more clean MP3, WAV, or MP4 recordings, confirm that you own the voice or have permission to use it, and click **Create my voice**. MP4/MOV uploads are converted to a normalized mono WAV locally and stored as `.voice_reference.wav`. Select **My custom voice**, choose English or Urdu, enter the script, and generate the WAV result.

Use a quiet 10–30 second recording with one speaker and clear speech. Urdu script generally produces better pronunciation than informal Roman Urdu. Do not upload another person’s voice without explicit permission.

The local voice engine requires the GPU path; the Edge TTS path can still run without CUDA. If CUDA is unavailable, use the built-in neural voices or run the GPU studio on a CUDA-enabled Windows/WSL2, Linux, Colab, or RunPod environment.

Naturalness usually improves when the script uses short paragraphs, punctuation, contractions, and explicit pauses. This tool does not attempt to bypass AI-detection or platform labeling systems.