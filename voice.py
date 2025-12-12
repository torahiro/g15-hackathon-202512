import streamlit as st
import pyaudio
import webrtcvad
import time

st.title("Auto Mute + Priority Mode")

# ------------------------
# 設定
# ------------------------
CHUNK = 256            # 小さくするほど反応が速い
RATE = 16000
VAD_MODE = 0           # 最速
SILENCE_FRAMES_END = 2 # 無音が2回続いたら終了扱い
DEVICE_INDEX = 0       # BlackHoleなど選択

priority_mode = st.checkbox("Priority Mode（相手の声を検知したら強制ミュート）")

# ------------------------
# VAD 初期化
# ------------------------
vad = webrtcvad.Vad(VAD_MODE)

# ------------------------
# 音声処理
# ------------------------
p = pyaudio.PyAudio()

stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
    input_device_index=DEVICE_INDEX,
)

status_placeholder = st.empty()

talking = False
silence_count = 0

while True:
    frame = stream.read(CHUNK, exception_on_overflow=False)

    is_speech = vad.is_speech(frame, RATE)

    # ------------------------
    # Priority Mode（相手の声を検知 → 強制ミュート）
    # ------------------------
    if priority_mode:
        if is_speech:
            talking = False
            silence_count = 0
            status_placeholder.markdown("🎤 **Muted（Priority Mode）**")
            continue

    # ------------------------
    # 通常処理（自分の声の検知）
    # ------------------------
    if is_speech:
        talking = True
        silence_count = 0
        status_placeholder.markdown("🎤 **ON（Speaking）**")
    else:
        silence_count += 1
        if silence_count >= SILENCE_FRAMES_END:
            talking = False
            status_placeholder.markdown("🔇 **Muted（Silence）**")

    time.sleep(0.01)
# streamlit run voice.pyをターミナルで実行