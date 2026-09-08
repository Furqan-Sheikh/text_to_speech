#!/usr/bin/env python3
"""Local browser interface for the transparent neural TTS tool."""

from __future__ import annotations

import asyncio
import io
import re
import tempfile
from pathlib import Path

import edge_tts
from flask import Flask, jsonify, render_template, request, send_file
from local_voice_engine import LocalVoiceEngine


app = Flask(__name__)
MAX_TEXT_LENGTH = 10_000
RATE_PATTERN = re.compile(r"^[+-]\d+%$")
PITCH_PATTERN = re.compile(r"^[+-](?:\d|10)Hz$")
LANGUAGES = {"english": "en", "urdu": "ur"}
VOICE_REFERENCE_PATH = Path(".voice_reference.wav")
VOICE_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".mp4", ".mov"}
local_engine = None


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/voice-status")
def voice_status():
    return jsonify(ready=VOICE_REFERENCE_PATH.exists())


async def render_audio(text: str, voice: str, rate: str, pitch: str) -> bytes:
    audio = io.BytesIO()
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.write(chunk["data"])
    return audio.getvalue()


def get_local_engine() -> LocalVoiceEngine:
    global local_engine
    if local_engine is None:
        local_engine = LocalVoiceEngine()
    return local_engine


@app.post("/api/synthesize")
def synthesize():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    voice = str(data.get("voice", "ur-PK-AsadNeural"))
    language = str(data.get("language", "urdu"))
    rate = str(data.get("rate", "+0%"))
    pitch = str(data.get("pitch", "+0Hz"))
    provider = str(data.get("provider", "edge"))

    if not text:
        return jsonify(error="Write or import some text first."), 400
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify(error=f"Please keep the script under {MAX_TEXT_LENGTH:,} characters."), 400
    if language not in LANGUAGES:
        return jsonify(error="Choose English or Urdu."), 400
    if not RATE_PATTERN.fullmatch(rate) or not -50 <= int(rate[:-1]) <= 50:
        return jsonify(error="Speed must be between -50% and +50%."), 400
    if not PITCH_PATTERN.fullmatch(pitch):
        return jsonify(error="Pitch must be between -10Hz and +10Hz."), 400

    output_mimetype = "audio/mpeg"
    try:
        if provider == "clone":
            if not VOICE_REFERENCE_PATH.exists():
                return jsonify(error="Upload and create your voice first."), 400
            with tempfile.NamedTemporaryFile(suffix=".wav") as output_file:
                get_local_engine().synthesize(text, language, str(VOICE_REFERENCE_PATH), output_file.name)
                output_file.seek(0)
                audio = output_file.read()
            output_mimetype = "audio/wav"
        else:
            audio = asyncio.run(render_audio(text, voice, rate, pitch))
    except Exception as error:
        app.logger.exception("Speech generation failed")
        return jsonify(error=f"Speech generation failed: {error}"), 502

    return send_file(
        io.BytesIO(audio),
        mimetype=output_mimetype,
        as_attachment=False,
        download_name="narration.wav" if output_mimetype == "audio/wav" else "narration.mp3",
    )


@app.post("/api/clone-voice")
def clone_voice():
    if request.form.get("consent") != "true":
        return jsonify(error="Confirm that you own this voice or have permission to use it."), 400

    recordings = [recording for recording in request.files.getlist("recording") if recording.filename]
    if not recordings:
        return jsonify(error="Choose at least one voice recording first."), 400
    if any(Path(recording.filename).suffix.lower() not in VOICE_AUDIO_EXTENSIONS for recording in recordings):
        return jsonify(error="Use WAV, MP3, M4A, OGG, FLAC, MP4, or MOV recordings."), 400

    try:
        with tempfile.TemporaryDirectory(prefix="voice-upload-") as temporary_directory:
            paths = []
            for index, recording in enumerate(recordings):
                path = Path(temporary_directory) / f"sample-{index}{Path(recording.filename).suffix.lower()}"
                recording.save(path)
                paths.append(str(path))
            get_local_engine().prepare_reference(paths, str(VOICE_REFERENCE_PATH))
    except Exception as error:
        app.logger.exception("Voice cloning failed")
        return jsonify(error=f"Voice cloning failed: {error}"), 502

    return jsonify(message="Your local custom voice is ready. No API key was used.")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=False)