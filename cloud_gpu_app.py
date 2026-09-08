"""Colab/RunPod voice studio using Chatterbox Multilingual.

Run this file in a GPU notebook or Linux GPU VM. Only use reference audio
from a speaker who has explicitly agreed to voice cloning.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import gradio as gr
import soundfile as sf
import torch
from local_voice_engine import LocalVoiceEngine


LANGUAGES = {
    "English": "english",
    "Urdu": "urdu",
}

if not torch.cuda.is_available():
    raise RuntimeError(
        "CUDA is unavailable. Install the NVIDIA CUDA PyTorch build and verify "
        "torch.cuda.is_available() before starting the voice studio."
    )

engine = LocalVoiceEngine()


def generate_speech(text: str, language: str, reference_audio: str, exaggeration: float, cfg_weight: float):
    if not text or not text.strip():
        raise gr.Error("Write some text first.")
    if not reference_audio:
        raise gr.Error("Upload a clean reference recording first.")

    references = reference_audio if isinstance(reference_audio, list) else [reference_audio]
    reference_path = Path(tempfile.gettempdir()) / "voice_reference_24k.wav"
    engine.prepare_reference(references, str(reference_path))
    output_path = Path(tempfile.gettempdir()) / "voice_foundry_output.wav"
    return engine.synthesize(text.strip(), LANGUAGES[language], str(reference_path), str(output_path))


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Voice Foundry Cloud Studio") as demo:
        gr.Markdown(
            "# Voice Foundry Cloud Studio\n"
            "Generate transparent synthetic narration with your own consented reference voice. "
            "This local studio supports English and Urdu without an API key."
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
                    label="Your voice reference samples (audio or video)",
                    file_count="multiple",
                )
            with gr.Column():
                exaggeration = gr.Slider(0.3, 1.0, value=0.5, step=0.05, label="Expression")
                cfg_weight = gr.Slider(0.2, 1.0, value=0.5, step=0.05, label="Voice adherence")
                generate = gr.Button("Generate narration", variant="primary")
                output = gr.Audio(label="Generated audio", type="filepath")
        gr.Markdown(
            "Use a quiet 10–30 second recording with one speaker. Do not upload another person's voice without explicit permission. "
            "English uses Chatterbox and Urdu uses an Urdu base model followed by local voice conversion."
        )
        generate.click(generate_speech, [text, language, reference, exaggeration, cfg_weight], output)
    return demo


if __name__ == "__main__":
    build_ui().launch(share=True)