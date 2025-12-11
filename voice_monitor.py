import sounddevice as sd
import numpy as np
import time
import json
import os
from talktime import update_talk_state

# ===== 設定 =====
SAMPLE_RATE = 44100
# デフォルト閾値（state.jsonの値が優先されます）
DEFAULT_THRESHOLD = 0.05
CHECK_INTERVAL = 0.1
STATE_FILE = "state.json"
TARGET_DEVICE_NAME = "BlackHole"

current_spectator_mode = False
# JSON読み書きの負荷を減らすため、音量書き込みは数回に1回にする
write_counter = 0

def get_blackhole_device_id():
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if TARGET_DEVICE_NAME in dev['name'] and dev['max_input_channels'] > 0:
            print(f"✅ 接続成功: {dev['name']} (ID: {i})")
            return i
    print("⚠️ BlackHoleが見つかりません。標準マイクを使います。")
    return None

def get_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def update_state(updates):
    """JSONを更新する（辞書形式で渡す）"""
    try:
        # 読み込んでから更新（競合回避）
        state = get_state()
        for k, v in updates.items():
            state[k] = v
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        pass

def audio_callback(indata, frames, time_info, status):
    global current_spectator_mode, write_counter
    
    # 音量計算
    volume = np.linalg.norm(indata)
    
    # UIから現在の閾値を取得したいが、callback内で毎回ファイル読み込みは重すぎる。
    # そのため、後述のメインループで取得した値をここで使いたいが、
    # 簡易的に「音量が十分大きい時だけ書き込む」などの工夫をするか、
    # ここでは計算結果だけグローバル変数に入れて、メインループで処理するのが安全。
    pass # 実際の処理はメインループで行います（下を参照）

# ストリームはcallbackなしのブロッキングモード、または
# グローバル変数経由での連携の方が安定するため、今回は
# 処理をわかりやすくメインループに集約します。

print(f"🎤 監視デバイスを検索中...")
device_id = get_blackhole_device_id()

print(f"🚀 監視スタート")

# ブロッキングモードで読み取る方がJSON連携しやすい
try:
    with sd.InputStream(device=device_id, channels=1, samplerate=SAMPLE_RATE) as stream:
        while True:
            # 1. 音声データを少しだけ読み取る
            data, overflowed = stream.read(int(SAMPLE_RATE * CHECK_INTERVAL))
            volume = np.linalg.norm(data)
            
            # 2. JSONから現在の設定（閾値など）を読む
            state = get_state()
            threshold = state.get("threshold", DEFAULT_THRESHOLD)
            is_spectator = state.get("is_spectator", False)
            
            # 3. 判定ロジック
            updates = {}
            
            # 常に現在の音量を記録（UIのメーター用）
            updates["current_volume"] = float(volume)
            
            is_talking = (not is_spectator) and (volume > threshold)
            update_talk_state(is_talking)  # ★追加

            if not is_spectator:
                if volume > threshold:
                    updates["last_voice_time"] = time.time()
                    print(f"\r🗣️ 音量: {volume:.4f} > 閾値: {threshold} (検知！)", end="")
                else:
                    print(f"\r... 音量: {volume:.4f} < 閾値: {threshold}", end="")
            else:
                print(f"\r👻 観戦モード中...", end="")
            
            # 4. JSONにまとめて書き込み
            update_state(updates)
            
            # 少し待つ必要はない（readで待機しているので）
            
except KeyboardInterrupt:
    print("\n終了")