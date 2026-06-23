import tempfile
import wave

import numpy as np
import sounddevice as sd

from config import MAX_RECORDING_SECONDS, SAMPLE_RATE


class AudioRecorder:
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._stream = None
        self._frames: list = []
        self._total_samples = 0
        self._max_samples = MAX_RECORDING_SECONDS * sample_rate

    def start(self) -> None:
        self._frames = []
        self._total_samples = 0
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        if self._total_samples < self._max_samples:
            self._frames.append(indata.copy())
            self._total_samples += frames

    def stop(self) -> str | None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return None

        audio = np.concatenate(self._frames, axis=0)

        # Créer le fichier temporaire puis le fermer immédiatement —
        # wave.open ne peut pas rouvrir un fichier déjà ouvert sur Windows.
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_name = tmp.name
        tmp.close()

        with wave.open(tmp_name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes((audio * 32767).astype(np.int16).tobytes())

        return tmp_name
