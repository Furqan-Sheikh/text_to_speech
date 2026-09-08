const voices = {
  urdu: [
    { id: 'ur-PK-AsadNeural', name: 'Asad · Male' },
    { id: 'ur-PK-UzmaNeural', name: 'Uzma · Female' },
  ],
  english: [
    { id: 'en-IN-PrabhatNeural', name: 'Prabhat · Male (India)' },
    { id: 'en-IN-NeerjaExpressiveNeural', name: 'Neerja · Expressive (India)' },
    { id: 'en-US-AndrewMultilingualNeural', name: 'Andrew · Male (US)' },
    { id: 'en-US-AvaMultilingualNeural', name: 'Ava · Female (US)' },
  ],
};

const script = document.querySelector('#script');
const voiceMode = document.querySelector('#voice-mode');
const language = document.querySelector('#language');
const voice = document.querySelector('#voice');
const speed = document.querySelector('#speed');
const speedRange = document.querySelector('#speed-range');
const pitch = document.querySelector('#pitch');
const count = document.querySelector('#character-count');
const speedValue = document.querySelector('#speed-value');
const pitchValue = document.querySelector('#pitch-value');
const error = document.querySelector('#error');
const result = document.querySelector('#result');
const audio = document.querySelector('#audio');
const download = document.querySelector('#download');
const generate = document.querySelector('#generate');
const recording = document.querySelector('#recording');
const consent = document.querySelector('#consent');
const cloneVoice = document.querySelector('#clone-voice');
const voiceStatus = document.querySelector('#voice-status');

let customVoiceReady = false;

async function loadVoiceStatus() {
  const response = await fetch('/api/voice-status');
  if (!response.ok) return;
  const payload = await response.json();
  customVoiceReady = payload.ready;
  if (customVoiceReady) {
    voiceStatus.textContent = 'Ready';
    voiceStatus.classList.add('ready');
  }
}

function populateVoices() {
  voice.replaceChildren(...voices[language.value].map((item) => {
    const option = new Option(item.name, item.id);
    return option;
  }));
}

function updateCount() {
  count.textContent = `${script.value.length.toLocaleString()} / 10,000`;
}

function updateRangeLabels() {
  const currentSpeed = Number(speedRange.value);
  speedValue.textContent = `${currentSpeed > 0 ? '+' : ''}${currentSpeed}%`;
  pitchValue.textContent = `${pitch.value > 0 ? '+' : ''}${pitch.value} Hz`;
}

function getRate() {
  const currentSpeed = Number(speedRange.value);
  return `${currentSpeed >= 0 ? '+' : ''}${currentSpeed}%`;
}

language.addEventListener('change', populateVoices);
script.addEventListener('input', updateCount);
speed.addEventListener('change', () => {
  if (speed.value !== 'custom') speedRange.value = speed.value;
  updateRangeLabels();
});
speedRange.addEventListener('input', () => {
  speed.value = ['-40', '0', '40'].includes(speedRange.value) ? speedRange.value : 'custom';
  updateRangeLabels();
});
pitch.addEventListener('input', updateRangeLabels);
document.querySelector('#file-input').addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (file) script.value = await file.text();
  updateCount();
});

generate.addEventListener('click', async () => {
  error.textContent = '';
  if (!script.value.trim()) {
    error.textContent = 'Write or import some text first.';
    script.focus();
    return;
  }

  generate.disabled = true;
  generate.querySelector('span').textContent = 'Creating your narration...';
  try {
    const response = await fetch('/api/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: script.value,
        language: language.value,
        provider: voiceMode.value,
        voice: voice.value,
        rate: getRate(),
        pitch: `${pitch.value >= 0 ? '+' : ''}${pitch.value}Hz`,
      }),
    });
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.error || 'Could not create audio.');
    }
    const url = URL.createObjectURL(await response.blob());
    audio.src = url;
    download.href = url;
    download.download = response.headers.get('content-type')?.includes('wav') ? 'narration.wav' : 'narration.mp3';
    result.hidden = false;
    result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (requestError) {
    error.textContent = requestError.message;
  } finally {
    generate.disabled = false;
    generate.querySelector('span').textContent = 'Generate narration';
  }
});

cloneVoice.addEventListener('click', async () => {
  error.textContent = '';
  if (!recording.files.length) {
    error.textContent = 'Choose at least one clean voice recording first.';
    return;
  }
  if (!consent.checked) {
    error.textContent = 'Confirm that you own this voice or have permission to use it.';
    return;
  }

  cloneVoice.disabled = true;
  cloneVoice.textContent = 'Creating voice...';
  const body = new FormData();
  [...recording.files].forEach((file) => body.append('recording', file));
  body.append('consent', 'true');
  try {
    const response = await fetch('/api/clone-voice', { method: 'POST', body });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'Could not create your voice.');
    customVoiceReady = true;
    voiceMode.value = 'clone';
    voiceStatus.textContent = 'Ready';
    voiceStatus.classList.add('ready');
    error.textContent = payload.message;
  } catch (requestError) {
    error.textContent = requestError.message;
  } finally {
    cloneVoice.disabled = false;
    cloneVoice.textContent = 'Create my voice';
  }
});

voiceMode.addEventListener('change', () => {
  if (voiceMode.value === 'clone' && !customVoiceReady) {
    error.textContent = 'Create your custom voice before selecting this mode.';
    voiceMode.value = 'edge';
  } else {
    error.textContent = '';
  }
});

populateVoices();
updateCount();
updateRangeLabels();
loadVoiceStatus();