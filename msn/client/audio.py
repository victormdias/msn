"""
MSN Messenger Audio System
Procedurally synthesizes and plays classic MSN sound effects (Online chime, Message, Nudge, Login, etc.)
and provides microphone voice clip recording and playback.
"""
import io
import math
import struct
import tempfile
import threading
import wave
from typing import Optional

try:
    from PyQt6.QtCore import QUrl
    from PyQt6.QtMultimedia import QSoundEffect
    HAS_QT_AUDIO = True
except ImportError:
    HAS_QT_AUDIO = False

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False


def _generate_wav(samples: list[float], sample_rate: int = 44100) -> bytes:
    """Encodes float samples in [-1.0, 1.0] to a 16-bit mono WAV byte buffer."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        int_samples = [max(-32767, min(32767, int(s * 32767))) for s in samples]
        wf.writeframes(struct.pack(f'<{len(int_samples)}h', *int_samples))
    return buf.getvalue()


def _gen_tone(freq: float, duration: float, volume: float = 0.5, sample_rate: int = 44100, fade_out: bool = True) -> list[float]:
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Envelope
        env = volume
        if fade_out:
            env *= math.exp(-3.0 * t / duration)
        # Add harmonic richness for a pleasing bell/chime sound
        val = math.sin(2 * math.pi * freq * t) * 0.7
        val += math.sin(2 * math.pi * freq * 2 * t) * 0.2
        val += math.sin(2 * math.pi * freq * 3 * t) * 0.1
        samples.append(val * env)
    return samples


def _gen_chord(freqs: list[float], duration: float, volume: float = 0.4, sample_rate: int = 44100) -> list[float]:
    num_samples = int(duration * sample_rate)
    samples = [0.0] * num_samples
    for f in freqs:
        tone = _gen_tone(f, duration, volume / len(freqs), sample_rate)
        for i in range(min(num_samples, len(tone))):
            samples[i] += tone[i]
    return samples


def create_online_chime() -> bytes:
    """Classic MSN contact online notification: Fast rising arpeggio (E5, G#5, B5, E6)."""
    sr = 44100
    notes = [659.25, 830.61, 987.77, 1318.51]  # E5, G#5, B5, E6
    note_dur = 0.08
    tail_dur = 0.5
    total_len = int((len(notes) * note_dur + tail_dur) * sr)
    samples = [0.0] * total_len

    for idx, freq in enumerate(notes):
        start_idx = int(idx * note_dur * sr)
        tone = _gen_tone(freq, 0.4, volume=0.55, sample_rate=sr)
        for j, s in enumerate(tone):
            if start_idx + j < total_len:
                samples[start_idx + j] += s

    return _generate_wav(samples, sr)


def create_message_sound() -> bytes:
    """Classic MSN incoming message sound: Crisp cheerful double-pop (C6, G6)."""
    sr = 44100
    tone1 = _gen_tone(1046.50, 0.06, volume=0.5, sample_rate=sr)  # C6
    gap = [0.0] * int(0.02 * sr)
    tone2 = _gen_tone(1567.98, 0.16, volume=0.6, sample_rate=sr)  # G6
    return _generate_wav(tone1 + gap + tone2, sr)


def create_nudge_sound() -> bytes:
    """
    Classic MSN Nudge sound: Rapid vibrating buzz (sawtooth + FM)
    followed by a punchy low-frequency thud/slam.
    """
    sr = 44100
    dur_buzz = 0.45
    dur_slam = 0.35
    total_samples = int((dur_buzz + dur_slam) * sr)
    samples = []

    # Buzz part (harsh vibrating rattle)
    num_buzz = int(dur_buzz * sr)
    for i in range(num_buzz):
        t = i / sr
        # Modulated frequency (80 Hz vibrato on 220 Hz base)
        mod = math.sin(2 * math.pi * 35 * t)
        val = math.sin(2 * math.pi * (180 + 90 * mod) * t) * 0.6
        # Add high rattle
        val += (math.sin(2 * math.pi * 540 * t) * 0.3)
        # Envelope swelling
        env = min(1.0, t / 0.1) * (1.0 - t / (dur_buzz * 1.5))
        samples.append(val * env * 0.7)

    # Heavy impact slam
    num_slam = int(dur_slam * sr)
    for i in range(num_slam):
        t = i / sr
        env = math.exp(-8.0 * t)
        val = math.sin(2 * math.pi * max(40, 140 - 200 * t) * t) * 0.8
        # Noise burst for slam punch
        noise = (math.sin(i * 999.123) % 1.0 - 0.5) * 0.4 * env
        samples.append((val + noise) * env * 0.85)

    return _generate_wav(samples, sr)


def create_login_sound() -> bytes:
    """MSN Live login welcome sound: Lush ascending major chord swell."""
    sr = 44100
    chord1 = _gen_chord([392.00, 493.88, 587.33], 0.25, volume=0.45, sample_rate=sr)  # G major
    chord2 = _gen_chord([523.25, 659.25, 783.99, 1046.50], 0.6, volume=0.55, sample_rate=sr)  # C major
    return _generate_wav(chord1 + chord2, sr)


class MSNAudioManager:
    """Singleton audio manager caching WAV buffers and playing sound effects."""
    _instance: Optional["MSNAudioManager"] = None

    def __init__(self):
        self.muted = False
        self._temp_files: dict[str, str] = {}
        self._qt_effects: dict[str, Any] = {}
        self._generate_cache()

    @classmethod
    def get_instance(cls) -> "MSNAudioManager":
        if cls._instance is None:
            cls._instance = MSNAudioManager()
        return cls._instance

    def _generate_cache(self):
        sounds = {
            "online": create_online_chime(),
            "message": create_message_sound(),
            "nudge": create_nudge_sound(),
            "login": create_login_sound(),
        }

        for name, data in sounds.items():
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tf.write(data)
            tf.flush()
            tf.close()
            self._temp_files[name] = tf.name

    def _play_file(self, filename: str):
        if self.muted:
            return

        def _worker():
            try:
                if HAS_WINSOUND:
                    winsound.PlaySound(filename, winsound.SND_FILENAME | winsound.SND_ASYNC)
                elif HAS_SOUNDDEVICE and HAS_SOUNDDEVICE:
                    data, fs = sf.read(filename)
                    sd.play(data, fs)
                    sd.wait()
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def play_online(self):
        if "online" in self._temp_files:
            self._play_file(self._temp_files["online"])

    def play_message(self):
        if "message" in self._temp_files:
            self._play_file(self._temp_files["message"])

    def play_nudge(self):
        if "nudge" in self._temp_files:
            self._play_file(self._temp_files["nudge"])

    def play_login(self):
        if "login" in self._temp_files:
            self._play_file(self._temp_files["login"])

    def record_voice_clip(self, duration: float = 3.5) -> Optional[bytes]:
        """Records a short voice clip from the microphone."""
        if not HAS_SOUNDDEVICE:
            # Generate a simulated voice chirp if no audio device
            sr = 22050
            samples = _gen_tone(440, 1.0, 0.4, sr)
            return _generate_wav(samples, sr)

        try:
            sample_rate = 22050
            recorded = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recorded.tobytes())
            return buf.getvalue()
        except Exception:
            return None

    def play_raw_wav(self, wav_bytes: bytes):
        """Plays custom WAV bytes (such as received voice clips)."""
        def _worker():
            try:
                tf = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                tf.write(wav_bytes)
                tf.flush()
                tf.close()
                if HAS_WINSOUND:
                    winsound.PlaySound(tf.name, winsound.SND_FILENAME)
                elif HAS_SOUNDDEVICE:
                    data, fs = sf.read(tf.name)
                    sd.play(data, fs)
                    sd.wait()
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()
