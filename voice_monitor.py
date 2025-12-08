import sounddevice as sd
import numpy as np
import time
import json

# ===== 設定 =====
SAMPLE_RATE = 44100
THRESHOLD = 0.5    # 感度（環境に合わせて調整してください。小さいほど敏感）
CHECK_INTERVAL = 0.1

print(f"🎤 音声監視を開始しました (閾値: {THRESHOLD})")

def write_state():
    """現在時刻をファイルに記録"""
    state = {
        "last_voice_time": time.time()
    }
    try:
        with open("state.json", "w") as f:
            json.dump(state, f)
        # print("LOG: 音声を検知しました") # デバッグ用
    except Exception as e:
        print(f"Error writing state: {e}")

def audio_callback(indata, frames, time_info, status):
    """マイク入力の音量をチェック"""
    volume = np.linalg.norm(indata)
    if volume > THRESHOLD:
        write_state()

# マイク入力開始
with sd.InputStream(
    channels=1,
    samplerate=SAMPLE_RATE,
    callback=audio_callback
):
    while True:
        time.sleep(CHECK_INTERVAL)