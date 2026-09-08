"""Colab/RunPod voice studio using Chatterbox Multilingual.

Run this file in a GPU notebook or Linux GPU VM. Only use reference audio
from a speaker who has explicitly agreed to voice cloning.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import gradio as gr
import imageio_ffmpeg
import librosa
import numpy as np
import soundfile as sf
import torch
import torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS


LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
}

device = "cuda" if torch.cuda.is_available() else "cpu"
if device != "cuda":
    raise RuntimeError(
        "CUDA is unavailable. Install the NVIDIA CUDA PyTorch build and verify "
        "torch.cuda.is_available() before starting the voice studio."
    )

model = ChatterboxMultilingualTTS.from_pretrained(device=device)


def prepare_reference(audio_path: str) -> str:
    source_path = Path(audio_path)
    extracted_path = Path(tempfile.gettempdir()) / "voice_reference_extracted.wav"
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg_path,
            "-y",
            "-i",
            str(source_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "24000",
            str(extracted_path),
        ],
        check=True,
        capture_output=True,
    )
    audio, sample_rate = librosa.load(extracted_path, sr=24000, mono=True)
    audio = np.asarray(audio, dtype=np.float32)
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.95
    normalized_path = Path(tempfile.gettempdir()) / "voice_reference_24k.wav"
    sf.write(normalized_path, audio, sample_rate, subtype="PCM_16")
    return str(normalized_path)


def generate_speech(text: str, language: str, reference_audio: str, exaggeration: float, cfg_weight: float):
    if not text or not text.strip():
        raise gr.Error("Write some text first.")
    if not reference_audio:
        raise gr.Error("Upload a clean reference recording first.")

    reference_path = prepare_reference(reference_audio)
    with torch.inference_mode():
        wav = model.generate(
            text.strip(),
            language_id=LANGUAGES[language],
            audio_prompt_path=reference_path,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
        )

    output_path = Path(tempfile.gettempdir()) / "voice_foundry_output.wav"
    model.sr = getattr(model, "sr", 24000)
    torchaudio.save(str(output_path), wav.cpu(), model.sr)
    return str(output_path)


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Voice Foundry Cloud Studio") as demo:
        gr.Markdown(
            "# Voice Foundry Cloud Studio\n"
            "Generate transparent synthetic narration with your own consented reference voice. "
            "Chatterbox currently supports Hindi and English, but not Urdu."
        )
        with gr.Row():
            with gr.Column():
                text = gr.Textbox(
                    label="Script",
                    lines=10,
                    placeholder="السلام علیکم، کیسے ہیں؟",
                )
                language = gr.Dropdown(list(LANGUAGES), value="English", label="Language")
                reference = gr.File(
                    type="filepath",
                    file_types=[".mp4", ".m4a", ".mov", ".wav", ".mp3", ".ogg", ".flac"],
                    label="Your voice reference (audio or video)",
                )
            with gr.Column():
                exaggeration = gr.Slider(0.3, 1.0, value=0.5, step=0.05, label="Expression")
                cfg_weight = gr.Slider(0.2, 1.0, value=0.5, step=0.05, label="Voice adherence")
                generate = gr.Button("Generate narration", variant="primary")
                output = gr.Audio(label="Generated audio", type="filepath")
        gr.Markdown(
            "Use a quiet 10–30 second recording with one speaker. Do not upload another person's voice without explicit permission. "
            "For Urdu output, use an Urdu-capable model/provider; selecting Hindi does not guarantee Urdu pronunciation."
        )
        generate.click(generate_speech, [text, language, reference, exaggeration, cfg_weight], output)
    return demo


if __name__ == "__main__":
    build_ui().launch(share=True)