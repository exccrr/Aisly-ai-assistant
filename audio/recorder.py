import numpy as np
import time
import sounddevice as sd

SAMPLE_RATE = 16000
THRESHOLD = 0.01

class AudioRecorder:
    def __init__(self, callback):
        self.callback = callback
        self.audio_data = []
        self.last_voice_time = 0
        self.recording = False
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=2,
            device='BlackHole 2ch',
            callback=self.audio_callback
        )

    def start(self):
        self.audio_data.clear()
        self.recording = True
        self.stream.start()

    def stop(self):
        self.recording = False
        self.stream.stop()

    def audio_callback(self, indata, frames, time_info, status):
        if not self.recording:
            return
        if np.linalg.norm(indata) > THRESHOLD:
            self.last_voice_time = time.time()
            self.audio_data.append(indata.copy())
