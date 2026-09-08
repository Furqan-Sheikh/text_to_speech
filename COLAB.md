# Free Cloud GPU Voice Studio

This is a free/open-source alternative to the paid cloning path. It runs on a Google Colab GPU and does not use ElevenLabs. It clones only a consented reference voice.

## Google Colab

1. Open a new notebook at <https://colab.research.google.com/>.
2. Select **Runtime -> Change runtime type -> T4 GPU** when available.
3. Run this installation cell:

```python
!pip install -q -r https://raw.githubusercontent.com/REPLACE_WITH_YOUR_REPO/main/requirements-cloud.txt
```

If the project is only on your computer, upload `cloud_gpu_app.py` and `requirements-cloud.txt` to Colab first, then run:

```python
!pip install -q -r requirements-cloud.txt
!python cloud_gpu_app.py
```

Colab already provides PyTorch. On a local NVIDIA machine, install the CUDA
build first by following [GPU_SETUP.md](GPU_SETUP.md).

4. Open the generated Gradio public URL.
5. Upload a clean 10–30 second recording of your own voice, choose Urdu, enter Urdu-script text, and generate audio.

## Your NVIDIA GPU machine

The same studio can run locally on an NVIDIA machine. Follow [GPU_SETUP.md](GPU_SETUP.md) for CUDA installation, then run:

```bash
python cloud_gpu_app.py
```

## RunPod

Use a PyTorch GPU pod, upload this project, then run:

```bash
pip install -r requirements-cloud.txt
python cloud_gpu_app.py
```

Expose the Gradio port or use the printed share URL.

If pip reports that Chatterbox requires an older exact PyTorch version, first
run the CUDA verification command from `GPU_SETUP.md`. Keep the installed CUDA
build when `torch.cuda.is_available()` is `True`; the warning is about
Chatterbox's package metadata. Replace it only if Chatterbox fails during model
import or generation.

## Quality notes

Use one speaker, no music or echo, and a consistent microphone distance. Urdu script is generally more reliable than inconsistent Roman Urdu spellings. Expression and voice-adherence sliders affect the tradeoff between natural delivery and similarity. This is synthetic audio and should be disclosed where required; it is not intended to evade platform detection or labeling.