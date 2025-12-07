import sounddevice as sd
import numpy as np
import time
import subprocess
import sys

# ===== 設定 =====
SAMPLE_RATE = 44100
THRESHOLD = 1       # 音量しきい値
SILENCE_LIMIT = 60    # 無音許容秒数
COUNTDOWN_START = 10  # 残り何秒から警告するか

last_sound_time = time.time()
last_announced_second = None

def say(message):
    subprocess.Popen(["say", message])

def audio_callback(indata, frames, time_info, status):
    global last_sound_time, last_announced_second
    volume = np.linalg.norm(indata)

    if volume > THRESHOLD:
        last_sound_time = time.time()
        last_announced_second = None  # 喋ったらリセット

print("🎤 無音監視スタート（Ctrl+Cで終了）")

try:
    with sd.InputStream(
        callback=audio_callback,
        channels=1,
        samplerate=SAMPLE_RATE
    ):
        while True:
            elapsed = int(time.time() - last_sound_time)
            remaining = SILENCE_LIMIT - elapsed

            # ターミナル表示（上書き）
            sys.stdout.write(f"\r⏳ 残り {remaining:2d} 秒")
            sys.stdout.flush()

            # 無音到達
            if remaining <= 0:
                sys.stdout.write("\n⚠️無音状態になりました\n")
                sys.stdout.flush()
                say("喋ってください")
                last_sound_time = time.time()
                last_announced_second = None

            time.sleep(1)

except KeyboardInterrupt:
    print("\n終了しました")