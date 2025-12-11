import streamlit as st
import threading
import subprocess
import time
import queue
import numpy as np
import sounddevice as sd
import pyautogui
import webrtcvad
import sys

# ---------------------------------------------------------
# Zoom 起動（③）
# ---------------------------------------------------------
def launch_zoom():
    if sys.platform.startswith("win"):
        subprocess.Popen(r"C:\Users\%USERNAME%\AppData\Roaming\Zoom\bin\Zoom.exe")
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-a", "zoom.us"])
    else:
        st.warning("Linux は Zoom のパスを手動設定してください。")


# ---------------------------------------------------------
# Zoom ミュート切り替えショートカット
# ---------------------------------------------------------
def toggle_zoom_mute():
    if sys.platform.startswith("win"):
        pyautogui.hotkey("alt", "a")
    elif sys.platform == "darwin":
        pyautogui.hotkey("command", "shift", "a")
    else:
        pyautogui.hotkey("ctrl", "shift", "m")


# ---------------------------------------------------------
# 音声処理クラス（auto_unmute_on_speech）
# ---------------------------------------------------------
class VADDetector:
    def __init__(self, sample_rate=16000, frame_duration_ms=30, aggressiveness=2):
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.vad = webrtcvad.Vad(aggressiveness)

    def is_speech(self, pcm_bytes):
        return self.vad.is_speech(pcm_bytes, self.sample_rate)


def audio_capture_worker(q, samplerate=16000, channels=1):
    blocksize = int(samplerate * 0.03)
    stream = sd.RawInputStream(
        samplerate=samplerate, blocksize=blocksize,
        dtype='int16', channels=channels
    )
    with stream:
        while True:
            data, _ = stream.read(blocksize)
            q.put(bytes(data))


class AutoUnmuteController:
    def __init__(self, vad, input_q, silence_seconds_to_mute=1.0):
        self.vad = vad
        self.q = input_q
        self.silence_seconds_to_mute = silence_seconds_to_mute
        self.muted = True
        self.speaking = False
        self.last_speech_time = 0

    def run(self, stop_flag):
        frame_bytes = self.vad.frame_size * 2

        while not stop_flag.is_set():
            try:
                pcm = self.q.get(timeout=0.3)
            except queue.Empty:
                pcm = None

            if pcm:
                buf = pcm
                i = 0
                while i + frame_bytes <= len(buf):
                    frame = buf[i:i + frame_bytes]
                    i += frame_bytes
                    if self.vad.is_speech(frame):
                        self.last_speech_time = time.time()
                        if not self.speaking:
                            self.speaking = True
                            if self.muted:
                                toggle_zoom_mute()
                                self.muted = False
                    else:
                        pass

            now = time.time()
            if self.speaking and (now - self.last_speech_time) > self.silence_seconds_to_mute:
                self.speaking = False
                if not self.muted:
                    toggle_zoom_mute()
                    self.muted = True

            time.sleep(0.01)


# ---------------------------------------------------------
# Streamlit UI（①モード選択 + ③Zoom起動）
# ---------------------------------------------------------
st.title("🎤 Zoom 音声モードコントロールツール")

# (③) Zoom 起動ボタン
st.subheader("Zoom 起動")
if st.button("Zoom を起動する"):
    launch_zoom()
    st.success("Zoom を起動しました！")

st.divider()

# (①) モード選択
st.subheader("音声モードを選択")

mode = st.radio(
    "モードを選んでください",
    [
        "Push-to-talk（スペースキーで発話）",
        "Auto Unmute on Speech（自動ミュート解除）",
        "Priority Mode（相手が話したら自分をミュート）※上級者"
    ]
)

st.write(f"選択中のモード：**{mode}**")

st.divider()

# ---------------------------------------------------------
# バックグラウンド実行管理
# ---------------------------------------------------------
if "thread" not in st.session_state:
    st.session_state.thread = None
    st.session_state.stop_flag = threading.Event()


def start_tool():
    stop_flag = st.session_state.stop_flag
    stop_flag.clear()

    selected_mode = mode

    if "Auto Unmute" in selected_mode:
        q = queue.Queue()
        vad = VADDetector()

        capture_thread = threading.Thread(
            target=audio_capture_worker,
            args=(q,),
            daemon=True
        )
        capture_thread.start()

        controller = AutoUnmuteController(vad, q)

        worker = threading.Thread(
            target=controller.run,
            args=(stop_flag,),
            daemon=True
        )
        worker.start()

        st.session_state.thread = worker

    elif "Push-to-talk" in selected_mode:
        st.warning("Push-to-talk はローカルキーボード監視が必要で\nStreamlit では完全動作しません。")
        st.info("→ ローカルPython版では動作します。")

    elif "Priority" in selected_mode:
        st.warning("Priority Mode は loopback デバイス設定が必要です。")
        st.info("必要なら環境に合わせて実装します。")

    st.success("ツールを開始しました！")


def stop_tool():
    if st.session_state.thread is not None:
        st.session_state.stop_flag.set()
        st.session_state.thread = None
        st.success("ツールを停止しました！")


col1, col2 = st.columns(2)
with col1:
    if st.button("▶ Start"):
        start_tool()
with col2:
    if st.button("■ Stop"):
        stop_tool()
# streamlit run voice.pyをターミナルで実行
