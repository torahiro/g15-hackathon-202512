import streamlit as st
import pyaudio
import webrtcvad
import numpy as np
import pyautogui
import time
import threading
import subprocess
import sys

# =====================
# Audio settings
# =====================
RATE = 16000
FRAME_MS = 10
FRAME_SAMPLES = int(RATE * FRAME_MS / 1000)

RMS_THRESHOLD = 300     # 無音除外
SILENCE_LIMIT = 5      # 50ms
VAD_MODE = 0           # 最速

# =====================
# Zoom control
# =====================
def zoom_toggle_mute():
    # Zoom / Google Meet 共通
    pyautogui.hotkey("command", "shift", "a")

def launch_zoom():
    if sys.platform == "darwin":
        subprocess.Popen(["open", "-a", "zoom.us"])
    else:
        st.warning("Zoom起動はmacOSのみ対応しています")

# =====================
# RMS
# =====================
def rms(frame):
    audio = np.frombuffer(frame, dtype=np.int16)
    return np.sqrt(np.mean(audio.astype(np.float32) ** 2))

# =====================
# Audio loop
# =====================
def audio_loop(auto_mute, priority_mode, status_box, stop_event):
    vad = webrtcvad.Vad(VAD_MODE)

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=FRAME_SAMPLES,
    )

    muted = True
    silence_frames = 0

    status_box.markdown("🔇 **Muted（Waiting）**")

    while not stop_event.is_set():
        frame = stream.read(FRAME_SAMPLES, exception_on_overflow=False)

        volume = rms(frame)

        if volume < RMS_THRESHOLD:
            is_speech = False
        else:
            try:
                is_speech = vad.is_speech(frame, RATE)
            except Exception:
                is_speech = False

        # -------- Priority Mode --------
        if priority_mode and is_speech:
            if not muted:
                zoom_toggle_mute()
                muted = True
                status_box.markdown("🔇 **Muted（Priority Mode）**")
            continue

        # -------- Auto Mute --------
        if auto_mute:
            if is_speech:
                silence_frames = 0
                if muted:
                    zoom_toggle_mute()
                    muted = False
                status_box.markdown("🎤 **ON（Speaking）**")
            else:
                silence_frames += 1
                if silence_frames >= SILENCE_LIMIT and not muted:
                    zoom_toggle_mute()
                    muted = True
                    status_box.markdown("🔇 **Muted**")

        time.sleep(0.003)

    stream.stop_stream()
    stream.close()
    p.terminate()

# =====================
# Streamlit UI
# =====================
st.set_page_config(page_title="Zoom Auto Mute Tool")
st.title("🎙 Zoom Auto Mute Tool")

st.subheader("Zoom 操作")
if st.button("🚀 Zoom を起動"):
    launch_zoom()
    st.success("Zoomを起動しました")

st.divider()

auto_mute = st.checkbox("Auto Mute（話していない時は自動ミュート）", value=True)
priority_mode = st.checkbox("Priority Mode（相手が話したら強制ミュート）")

status_box = st.empty()

if "thread" not in st.session_state:
    st.session_state.thread = None
    st.session_state.stop_event = None

col1, col2 = st.columns(2)

with col1:
    if st.button("▶ Start"):
        if st.session_state.thread is None:
            stop_event = threading.Event()
            t = threading.Thread(
                target=audio_loop,
                args=(auto_mute, priority_mode, status_box, stop_event),
                daemon=True,
            )
            t.start()
            st.session_state.thread = t
            st.session_state.stop_event = stop_event

with col2:
    if st.button("⏹ Stop"):
        if st.session_state.stop_event:
            st.session_state.stop_event.set()
            st.session_state.thread = None
            st.session_state.stop_event = None
            status_box.markdown("⏹ **Stopped**")
# streamlit run voice.pyをターミナルで実行