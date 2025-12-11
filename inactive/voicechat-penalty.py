import sounddevice as sd
import numpy as np
import time
from pydub import AudioSegment
from pydub.playback import play

SAMPLE_RATE = 44100
THRESHOLD = 0.02      # 音があったとみなす音量
LIMIT_SECONDS = 180  # 無音の許容時間

last_sound_time = time.time()

# 恥ずかしい音
penalty_sound = AudioSegment.from_file("shame.mp3")

def audio_callback(indata, frames, time_info, status):
    global last_sound_time

    volume = np.linalg.norm(indata) / len(indata)
    
    if volume > THRESHOLD:
        last_sound_time = time.time()

with sd.InputStream(callback=audio_callback, channels=1, samplerate=SAMPLE_RATE):
    print("監視開始… 会話しないと恥ずかしい音が鳴ります")

    while True:
        now = time.time()
        if now - last_sound_time >= LIMIT_SECONDS:
            print("無音ペナルティ発動！")
            play(penalty_sound)
            last_sound_time = time.time()  # 鳴った後はリセット
        
        time.sleep(1)