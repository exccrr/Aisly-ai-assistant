import io
import numpy as np
from scipy.io.wavfile import write
from faster_whisper import WhisperModel

class Transcriber:
    def __init__(self):
        self.model = WhisperModel("small", device="cpu", compute_type="int8")

    def transcribe(self, audio_data: np.ndarray) -> str:
        buf = io.BytesIO()
        write(buf, 16000, audio_data)
        buf.seek(0)
        segments, _ = self.model.transcribe(buf, language="ru")
        return " ".join(seg.text for seg in segments)
