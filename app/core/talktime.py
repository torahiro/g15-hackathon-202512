import sounddevice as sd
import numpy as np
import time

SAMPLE_RATE = 44100
THRESHOLD = 0.02      # 喋っていると判断する音量
PENALTY_TIME = 30    # 秒

talking = False
talk_start_time = None

def callback(indata, frames, time_info, status):
    global talking, talk_start_time

    volume = np.linalg.norm(indata)

    if volume > THRESHOLD:
        if not talking:
            talking = True
            talk_start_time = time.time()
            print("🎤 発話開始")

        else:
            elapsed = time.time() - talk_start_time
            if elapsed >= PENALTY_TIME:
                print("🚨 ペナルティ発動！（30秒超え）")
                # ここに制限処理を書く
                talk_start_time = time.time()  # 再発防止用リセット

    else:
        if talking:
            print("🔇 発話終了")
        talking = False
        talk_start_time = None

with sd.InputStream(callback=callback, channels=1, samplerate=SAMPLE_RATE):
    print("監視中...")
    while True:
        time.sleep(0.1)