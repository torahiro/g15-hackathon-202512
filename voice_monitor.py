import sounddevice as sd
import numpy as np
import time
import json
import os

# ===== 設定 =====
SAMPLE_RATE = 44100
# 【重要】ここを調整！ 0.5は敏感すぎたので2.0にしました。
# それでも勝手にリセットされるなら 5.0, 10.0 と上げてください
THRESHOLD = 2.0  
CHECK_INTERVAL = 0.1
STATE_FILE = "state.json"

# グローバル変数で観戦者モードかどうかを管理
current_spectator_mode = False

print(f"🎤 音声監視を開始しました (閾値: {THRESHOLD})")

def get_state():
    """現在のJSON状態を読み込む"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def update_voice_time():
    """現在時刻をファイルに記録 (観戦者モードでない場合のみ)"""
    # 最新の状態を読み込んでから更新（上書き防止）
    state = get_state()
    
    # 観戦者モードなら更新しない！(ここが重要)
    if state.get("is_spectator", False):
        return

    state["last_voice_time"] = time.time()
    
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
        # print("LOG: 音声を検知しました") 
    except Exception as e:
        print(f"Error writing state: {e}")

def audio_callback(indata, frames, time_info, status):
    """マイク入力の音量をチェック"""
    global current_spectator_mode
    
    # 観戦者モードならマイク処理自体をスキップしても良いが、
    # 念のため update_voice_time 内でもチェックしている
    if current_spectator_mode:
        return

    volume = np.linalg.norm(indata)
    if volume > THRESHOLD:
        update_voice_time()

# メインループ
# マイクを非同期(callback)で動かしつつ、メインループで定期的にJSONをチェックする
stream = sd.InputStream(
    channels=1,
    samplerate=SAMPLE_RATE,
    callback=audio_callback
)

with stream:
    while True:
        # 定期的にJSONを見て、今「観戦者モード」かどうかを確認する
        # (audio_callbackの中で毎回ファイルを開くと重いため、ここでチェック)
        state = get_state()
        current_spectator_mode = state.get("is_spectator", False)
        
        if current_spectator_mode:
            print("\r👻 現在観戦者モードです (発言無効)", end="")
        else:
            # 動作していることがわかるようにドットを表示
            print(".", end="", flush=True)
            
        time.sleep(CHECK_INTERVAL * 10) # 1秒ごとに設定確認