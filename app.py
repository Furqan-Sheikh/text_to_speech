#!/usr/bin/env python3
"""Local browser interface for the transparent neural TTS tool."""

from __future__ import annotations

import asyncio
import io
import os
import re
from pathlib import Path

import edge_tts
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file


load_dotenv()
app = Flask(__name__)
MAX_TEXT_LENGTH = 10_000
RATE_PATTERN = re.compile(r"^[+-]\d+%$")
PITCH_PATTERN = re.compile(r"^[+-](?:\d|10)Hz$")
ELEVENLABS_API = "https://api.elevenlabs.io/v1"
VOICE_ID_PATH = Path(".voice_id")
cloned_voice_id = VOICE_ID_PATH.read_text(encoding="utf-8").strip() if VOICE_ID_PATH.exists() else None


def cloning_error(response: requests.Response) -> tuple[str, int]:
    """Turn provider errors into useful UI messages without exposing raw details."""
    try:
        payload = response.json()
        detail = payload.get("detail", {})
        if detail.get("code") == "paid_plan_required":
            return (
                "Instant voice cloning is not enabled on this ElevenLabs plan. "
                "Upgrade the plan or use a voice-cloning provider that supports your subscription.",
                402,
            )
    except (ValueError, AttributeError):
        pass
    return ("Voice cloning service rejected the recording. Check the file and your account settings.", 502)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/voice-status")
def voice_status():
    return jsonify(ready=bool(cloned_voice_id))


async def render_audio(text: str, voice: str, rate: str, pitch: str) -> bytes:
    audio = io.BytesIO()
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.write(chunk["data"])
    return audio.getvalue()


def render_cloned_audio(text: str, voice_id: str, rate: str) -> bytes:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Set ELEVENLABS_API_KEY before using a cloned voice.")

    rate_value = max(0.7, min(1.2, 1 + int(rate[:-1]) / 250))
    response = requests.post(
        f"{ELEVENLABS_API}/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Accept": "audio/mpeg"},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.48,
                "similarity_boost": 0.82,
                "style": 0.12,
                "use_speaker_boost": True,
                "speed": rate_value,
            },
        },
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(f"Voice provider returned {response.status_code}: {response.text[:300]}")
    return response.content


@app.post("/api/synthesize")
def synthesize():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    voice = str(data.get("voice", "ur-PK-AsadNeural"))
    rate = str(data.get("rate", "+0%"))
    pitch = str(data.get("pitch", "+0Hz"))
    provider = str(data.get("provider", "edge"))

    if not text:
        return jsonify(error="Write or import some text first."), 400
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify(error=f"Please keep the script under {MAX_TEXT_LENGTH:,} characters."), 400
    if not RATE_PATTERN.fullmatch(rate) or not -50 <= int(rate[:-1]) <= 50:
        return jsonify(error="Speed must be between -50% and +50%."), 400
    if not PITCH_PATTERN.fullmatch(pitch):
        return jsonify(error="Pitch must be between -10Hz and +10Hz."), 400

    try:
        if provider == "clone":
            if not cloned_voice_id:
                return jsonify(error="Upload and create your voice first."), 400
            audio = render_cloned_audio(text, cloned_voice_id, rate)
        else:
            audio = asyncio.run(render_audio(text, voice, rate, pitch))
    except Exception as error:
        app.logger.exception("Speech generation failed")
        return jsonify(error=f"Speech generation failed: {error}"), 502

    return send_file(
        io.BytesIO(audio),
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name="narration.mp3",
    )


@app.post("/api/clone-voice")
def clone_voice():
    global cloned_voice_id

    if not os.getenv("ELEVENLABS_API_KEY"):
        return jsonify(error="Set ELEVENLABS_API_KEY in your terminal before cloning."), 503
    if request.form.get("consent") != "true":
        return jsonify(error="Confirm that you own this voice or have permission to use it."), 400

    recording = request.files.get("recording")
    if not recording or not recording.filename:
        return jsonify(error="Choose a voice recording first."), 400
    if Path(recording.filename).suffix.lower() not in {".wav", ".mp3", ".m4a", ".ogg", ".flac"}:
        return jsonify(error="Use a WAV, MP3, M4A, OGG, or FLAC recording."), 400

    try:
        response = requests.post(
            f"{ELEVENLABS_API}/voices/add",
            headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
            data={
                "name": "Voice Foundry custom voice",
                "description": "Consent-based custom narration voice",
            },
            files={"files": (recording.filename, recording.stream, recording.mimetype)},
            timeout=120,
        )
        if not response.ok:
            app.logger.warning("Voice cloning provider rejected request: HTTP %s", response.status_code)
            message, status = cloning_error(response)
            return jsonify(error=message), status
        cloned_voice_id = response.json()["voice_id"]
        VOICE_ID_PATH.write_text(cloned_voice_id, encoding="utf-8")
    except (requests.RequestException, KeyError, ValueError) as error:
        app.logger.exception("Voice cloning failed")
        return jsonify(error=f"Voice cloning failed: {error}"), 502

    return jsonify(message="Your custom voice is ready.", voice_id=cloned_voice_id)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=False)