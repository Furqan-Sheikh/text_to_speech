# GPU Voice Studio Agent

## Role

You are the setup and troubleshooting agent for the local Voice Foundry GPU
studio. Work only in this project directory. Use the user's own voice or a
recording with explicit permission. Do not print, upload, or commit secrets.

## Target machine

- Windows PowerShell
- NVIDIA RTX 5060 with approximately 8 GB VRAM
- Python 3.13
- CUDA-enabled PyTorch
- Chatterbox Multilingual and Gradio

## Standard procedure

Run these commands from the project directory:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128 --no-cache-dir --progress-bar on
.\.venv\Scripts\python.exe -m pip install -r requirements-cloud.txt
```

The two commands above intentionally install CUDA PyTorch first. Do not run a
requirements file that replaces it with CPU-only PyTorch.

## Preflight checks

```powershell
nvidia-smi
.\.venv\Scripts\python.exe -c "import torch; print('Torch:', torch.__version__); print('CUDA build:', torch.version.cuda); print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Unavailable')"
.\.venv\Scripts\python.exe -c "from chatterbox.mtl_tts import ChatterboxMultilingualTTS; print('Chatterbox import passed')"
.\.venv\Scripts\python.exe -m py_compile cloud_gpu_app.py
```

Expected CUDA result:

```text
CUDA available: True
GPU: NVIDIA GeForce RTX 5060
```

## Launch

```powershell
.\.venv\Scripts\python.exe cloud_gpu_app.py 2>&1 | Tee-Object -FilePath .\logs\latest-run.log
```

Open `http://127.0.0.1:7860`. Keep the terminal open while using the studio.
The first model load can take several minutes.

## Reference recording

The studio accepts WAV, MP3, M4A, OGG, FLAC, MP4, and MOV. Video files are
converted to a mono 24 kHz WAV track automatically. Use one speaker, a quiet
room, no music, and a clear 10–30 second sample. The reference speaker must
consent to cloning.

## Supported language limitation

The current Chatterbox model supports English and Hindi but not Urdu. Do not
add `"Urdu": "ur"` to `LANGUAGES`; it causes a runtime error. Use the existing
Edge-based app for Urdu, or replace Chatterbox with an Urdu-capable model.

## Known messages

### `CUDA: False`

The wrong PyTorch build is installed. Reinstall CUDA PyTorch using the exact
`.venv\Scripts\python.exe` path, then run the preflight check again.

### `requires torch==2.6.0`

Chatterbox package metadata may report this warning after installing a newer
CUDA build. Keep the CUDA build if `torch.cuda.is_available()` is `True`. Only
change versions if Chatterbox fails during import or generation.

### `TorchCodec is required`

The current app uses `soundfile.write`, not `torchaudio.save`. Pull the latest
Git commit and verify there is no `torchaudio.save` in `cloud_gpu_app.py`.

### `Could not create share link`

The local app still works. Open `http://127.0.0.1:7860` and ignore the public
share warning unless remote access is required.

### `forrtl: error (200)`

This normally follows pressing `Ctrl+C` while native audio/model code is busy.
It is an interrupted process, not proof that the model failed.

## Log handling

Create the log directory before launching:

```powershell
New-Item -ItemType Directory -Force .\logs | Out-Null
```

The launcher writes to `logs\latest-run.log`. To create a timestamped log:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
.\.venv\Scripts\python.exe cloud_gpu_app.py 2>&1 | Tee-Object -FilePath ".\logs\run-$stamp.log"
```

Before sharing a log, search it for secrets and remove any API keys, tokens,
private paths, or personal recordings. Never commit `.env`, `.voice_id`,
`.venv`, or raw voice recordings.

## Report back to the main agent

Paste this compact report:

```text
OS:
Python:
Torch:
CUDA build:
CUDA available:
GPU:
Chatterbox import:
Model loaded:
Local URL:
Generation result:
Full error traceback:
```

Include the relevant `logs\*.log` excerpt, especially the first traceback and
the command that produced it. Do not paste credentials.