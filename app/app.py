import streamlit as st
import sounddevice as sd
import numpy as np
import time
import json
import os
import threading
from collections import deque

# ===== 設定（秒） =====
TIME_WARNING = 60
TIME_SHAME = 180
TIME_SPECTATOR = 190
TIME_TALK_LIMIT = 30

# ===== 音声ファイル =====
SOUND_WARNING = "alarm.wav"
SOUND_SHAME = "shame.wav"
SOUND_SPECTATOR = "spectator.wav"
SOUND_TALK_TOO_MUCH = "shame.wav"
SOUND_APOLOGY = "apology.wav"

STATE_FILE = "state.json"
SAMPLE_RATE = 44100
CHECK_INTERVAL = 0.1
DEFAULT_THRESHOLD = 0.05


# ===== state load/save =====
def read_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {
        "last_voice_time": time.time(),
        "talk_duration": 0.0,
        "threshold": DEFAULT_THRESHOLD,
        "is_spectator": False,
        "current_volume": 0.0,
        "device_id": None
    }


def write_state(updates: dict):
    state = read_state()
    state.update(updates)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except:
        pass


# ===== TalkTimer =====
class TalkTimer:
    def __init__(self, penalty_limit=30, silence_tolerance=2.0):
        self.speech_start_time = None
        self.last_sound_time = 0
        self.is_talking_session = False
        self.penalty_limit = penalty_limit
        self.silence_tolerance = silence_tolerance

    def update(self, is_talking_now):
        current_time = time.time()

        if is_talking_now:
            self.last_sound_time = current_time
            if not self.is_talking_session:
                self.is_talking_session = True
                self.speech_start_time = current_time

        elif self.is_talking_session:
            if current_time - self.last_sound_time > self.silence_tolerance:
                self.is_talking_session = False
                self.speech_start_time = None

        if self.is_talking_session and self.speech_start_time:
            return current_time - self.speech_start_time

        return 0.0


# ===== AudioMonitor =====
class AudioMonitor(threading.Thread):
    def __init__(self, sample_rate=44100, interval=0.1, default_threshold=DEFAULT_THRESHOLD):
        super().__init__(daemon=True)
        self.sample_rate = sample_rate
        self.interval = interval
        self.default_threshold = default_threshold
        self.talk_timer = TalkTimer(TIME_TALK_LIMIT, 1.0)
        self.running = True
        self.device_id = None

    def choose_device(self):
        state = read_state()
        dev = state.get("device_id", None)
        if dev is not None:
            self.device_id = dev
            return

        try:
            devices = sd.query_devices()
            for i, d in enumerate(devices):
                if "BlackHole" in d["name"]:
                    self.device_id = i
                    write_state({"device_id": i})
                    return
        except:
            pass

        self.device_id = None

    def rms(self, data):
        if data.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(data.astype(np.float64)))))

    def run(self):
        self.choose_device()
        try:
            with sd.InputStream(device=self.device_id, channels=1, samplerate=self.sample_rate) as stream:
                frames = int(self.sample_rate * self.interval)
                while self.running:
                    try:
                        data, overflow = stream.read(frames)
                    except:
                        time.sleep(0.5)
                        self.choose_device()
                        continue

                    arr = data[:, 0] if data.ndim > 1 else data
                    volume = self.rms(arr)

                    s = read_state()
                    threshold = s.get("threshold", self.default_threshold)
                    is_spectator = s.get("is_spectator", False)

                    updates = {"current_volume": volume}
                    is_talking_now = (volume > threshold)

                    if not is_spectator:
                        if is_talking_now:
                            updates["last_voice_time"] = time.time()
                        updates["talk_duration"] = self.talk_timer.update(is_talking_now)
                    else:
                        self.talk_timer.is_talking_session = False
                        updates["talk_duration"] = 0.0

                    write_state(updates)
                    time.sleep(self.interval)

        except Exception as e:
            write_state({"current_volume": 0.0})
            print("AudioMonitor stopped:", e)

    def stop(self):
        self.running = False


# ===== Streamlit UI =====
st.set_page_config(page_title="会話監視ボット（完全版）", layout="centered")

if "warning_played" not in st.session_state:
    st.session_state.warning_played = False
if "shame_played" not in st.session_state:
    st.session_state.shame_played = False
if "talk_limit_played" not in st.session_state:
    st.session_state.talk_limit_played = False

# 起動時にバックグラウンド監視を開始
if "audio_monitor" not in st.session_state:
    st.session_state.audio_monitor = AudioMonitor(SAMPLE_RATE, CHECK_INTERVAL)
    st.session_state.audio_monitor.start()

# state load
state = read_state()
last_voice_time = state["last_voice_time"]
talk_duration = state["talk_duration"]
current_vol = state["current_volume"]
is_spectator = state["is_spectator"]
threshold = state["threshold"]
device_id = state["device_id"]

elapsed_silence = time.time() - last_voice_time

# ===== Sidebar =====
st.sidebar.header("⚙️ 設定")

# 再スタートボタン（1回だけ押せる）
if "restart_used" not in st.session_state:
    st.session_state.restart_used = False

if not st.session_state.restart_used:
    if st.sidebar.button("再スタート"):
        # 状態リセット
        write_state({
            "is_spectator": False,
            "last_voice_time": time.time(),
            "talk_duration": 0.0,
        })
        st.session_state.warning_played = False
        st.session_state.shame_played = False
        st.session_state.talk_limit_played = False
        st.session_state.restart_used = True  # 1回押したら無効化

        st.experimental_rerun()
else:
    st.sidebar.button("再スタート", disabled=True)  # 無効化ボタン

# Device selection
try:
    devices = sd.query_devices()
    names = [f"{i}: {d['name']}" for i, d in enumerate(devices)]
except:
    devices = []
    names = []

if names:
    default_idx = device_id if device_id is not None else 0
    selected = st.sidebar.selectbox("入力デバイス", names, index=default_idx)
    sel_idx = int(selected.split(":")[0])
    if sel_idx != device_id:
        write_state({"device_id": sel_idx})
        st.session_state.audio_monitor.device_id = sel_idx

new_th = st.sidebar.slider("マイク感度", 0.001, 0.5, threshold, 0.01)
if new_th != threshold:
    write_state({"threshold": new_th})

# ===== Main UI =====
st.title("🤐 沈黙＆多弁警察 — 完全版")

# spectator mode
if is_spectator:
    st.error("👻 あなたは観戦モードです")
    st.metric("放置時間", f"{int(elapsed_silence)} 秒")
    st.write("---")

    if not os.path.exists(SOUND_APOLOGY):
        st.warning(f"{SOUND_APOLOGY} が無いので復活できません。")
    else:
        if st.button("謝罪して復活"):
            st.audio(SOUND_APOLOGY, autoplay=True)
            time.sleep(0.3)
            write_state({
                "is_spectator": False,
                "last_voice_time": time.time()
            })
            st.rerun()

else:
    col1, col2 = st.columns(2)
    col1.metric("無音時間", f"{int(elapsed_silence)} 秒")
    col2.metric("連続発話", f"{talk_duration:.1f} 秒")

    st.progress(min(current_vol / 0.5, 1.0))

    # A. talk too much
    if talk_duration > TIME_TALK_LIMIT:
        st.error(f"🛑 喋りすぎ！（{int(talk_duration)}秒）")
        if not st.session_state.talk_limit_played:
            if os.path.exists(SOUND_TALK_TOO_MUCH):
                st.audio(SOUND_TALK_TOO_MUCH, autoplay=True)
            st.session_state.talk_limit_played = True

    # B. spectator mode
    elif elapsed_silence >= TIME_SPECTATOR:
        write_state({"is_spectator": True})
        if os.path.exists(SOUND_SPECTATOR):
            st.audio(SOUND_SPECTATOR, autoplay=True)
        st.rerun()

    # C. shame
    elif elapsed_silence >= TIME_SHAME:
        st.warning("😱 危険域！恥ずかしい音が鳴ります！")
        if not st.session_state.shame_played:
            if os.path.exists(SOUND_SHAME):
                st.audio(SOUND_SHAME, autoplay=True)
            st.session_state.shame_played = True

    # D. warning
    elif elapsed_silence >= TIME_WARNING:
        st.info("⚠️ 会話が止まっています…")
        if not st.session_state.warning_played:
            if os.path.exists(SOUND_WARNING):
                st.audio(SOUND_WARNING, autoplay=True)
            st.session_state.warning_played = True

    else:
        st.success("✅ 正常運転中")

        if elapsed_silence < 2:
            st.session_state.warning_played = False
            st.session_state.shame_played = False
        if talk_duration < 1:
            st.session_state.talk_limit_played = False

    time.sleep(1)
    st.rerun()

