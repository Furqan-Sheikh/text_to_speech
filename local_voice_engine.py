"""Local open-source voice cloning for English and Urdu."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
import librosa
import numpy as np
import soundfile as sf
import torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from chatterbox.vc import ChatterboxVC
from transformers import AutoTokenizer, VitsModel


URDU_MODEL_ID = "facebook/mms-tts-urd-script_arabic"


class LocalVoiceEngine:
    def __init__(self, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device != "cuda":
            raise RuntimeError("A CUDA GPU is required for local voice cloning.")
        self.chatterbox = ChatterboxMultilingualTTS.from_pretrained(device=self.device)
        self.voice_converter = ChatterboxVC.from_pretrained(device=self.device)
        self.urdu_tokenizer = AutoTokenizer.from_pretrained(URDU_MODEL_ID)
        self.urdu_model = VitsModel.from_pretrained(URDU_MODEL_ID).to(self.device).eval()

    @staticmethod
    def prepare_reference(recording_paths: list[str], output_path: str) -> str:
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        chunks = []
        with tempfile.TemporaryDirectory(prefix="voice-reference-") as temp_dir:
            for index, recording_path in enumerate(recording_paths):
                extracted_path = Path(temp_dir) / f"sample-{index}.wav"
                subprocess.run(
                    [
                        ffmpeg_path,
                        "-y",
                        "-i",
                        recording_path,
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
                audio, _ = librosa.load(extracted_path, sr=24000, mono=True)
                chunks.append(np.asarray(audio, dtype=np.float32))

        if not chunks:
            raise ValueError("No reference audio was provided.")
        audio = np.concatenate(chunks)[:24000 * 30]
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.95
        sf.write(output_path, audio, 24000, subtype="PCM_16")
        return output_path

    def _urdu_base_audio(self, text: str, output_path: str) -> str:
        inputs = self.urdu_tokenizer(text, return_tensors="pt").to(self.device)
        with torch.inference_mode():
            waveform = self.urdu_model(**inputs).waveform
        sf.write(output_path, waveform.squeeze().detach().cpu().numpy(), self.urdu_model.config.sampling_rate)
        return output_path

    def synthesize(self, text: str, language: str, reference_path: str, output_path: str) -> str:
        if language == "english":
            with torch.inference_mode():
                waveform = self.chatterbox.generate(
                    text,
                    language_id="en",
                    audio_prompt_path=reference_path,
                )
            audio = waveform.squeeze().detach().cpu().numpy()
            sf.write(output_path, audio, self.chatterbox.sr, subtype="PCM_16")
            return output_path

        if language != "urdu":
            raise ValueError("Only English and Urdu are supported.")

        with tempfile.TemporaryDirectory(prefix="urdu-base-") as temp_dir:
            base_path = self._urdu_base_audio(text, str(Path(temp_dir) / "urdu-base.wav"))
            waveform = self.voice_converter.generate(base_path, target_voice_path=reference_path)
        sf.write(output_path, waveform.squeeze().detach().cpu().numpy(), self.voice_converter.sr, subtype="PCM_16")
        return output_path
