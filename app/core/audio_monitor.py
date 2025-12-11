import sounddevice as sd
import numpy as np
import time
from pydub import AudioSegment
from pydub.playback import play
import threading

SAMPLE_RATE = 44100
THRESHOLD = 1
WARNING_SECONDS = 60
LIMIT_SECONDS = 190

class AudioMonitor:
    def __init__(self, sound_path):
        self.last_sound_time = time.time()
        self.penalty_sound = AudioSegment.from_file(sound_path)
        self.running = False

    def audio_callback(self, indata, frames, time_info, status):
        volume = np.linalg.norm(indata) / len(indata)
        if volume > THRESHOLD:
            self.last_sound_time = time.time()

    def start(self):
        self.running = True
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=SAMPLE_RATE
        )
        self.stream.start()

        threading.Thread(target=self._watch_loop, daemon=True).start()

    def _watch_loop(self):
        while self.running:
            if time.time() - self.last_sound_time >= LIMIT_SECONDS:
                play(self.penalty_sound)
                self.last_sound_time = time.time()
            time.sleep(1)

    def stop(self):
        self.running = False
        self.stream.stop()
        self.stream.close()