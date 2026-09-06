# Local NVIDIA GPU Setup

Your second machine is a better fit for the open-source studio: RTX 5060 GPU, 16 GB RAM, and Ryzen 5 3600 CPU. The exact VRAM on the 5060 matters; 8 GB should be workable for inference, while more VRAM gives more headroom.

Use Windows with WSL2 or Ubuntu/Linux. Install the current NVIDIA driver first, then confirm the GPU is visible:

```bash
nvidia-smi
```

## Install

From this project directory:

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/WSL2
python -m pip install --upgrade pip
python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements-cloud.txt
```

On native Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

Check CUDA before launching:

```bash
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CUDA unavailable')"
```

The first launch downloads the open-source model and may take time. Start the studio:

```bash
python cloud_gpu_app.py
```

Open the local Gradio URL printed in the terminal. Upload a clean 10–30 second recording of your own voice, select Urdu, enter Urdu-script text, and generate audio.

## Quality and limits

Use a quiet recording with one speaker, no music, and consistent microphone distance. Urdu-script input is usually more reliable than informal Roman Urdu spelling. If you see CUDA out-of-memory errors, close other GPU applications and reduce the reference audio length. This tool is for consented voice use and transparent synthetic narration; it does not bypass platform AI labels or detection.