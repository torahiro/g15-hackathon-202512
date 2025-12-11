import sounddevice as sd
import numpy as np
import time
from scipy.signal import butter, lfilter

from app.config.config import load_config
from app.services.penalty_logic import should_penalize

SAMPLE_RATE = 44100
FRAME = 1024
VOICE_BAND = (300, 3400)  # 人間の声帯域

THRESHOLD = 0.02
TALKING_LIMIT = 60

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    return lfilter(b, a, data)

def main():
    print("🎤 声帯域フィルタ版 監視システム起動中...")

    config = load_config()

    stream = sd.InputStream(
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=FRAME
    )
    stream.start()

    talking_time = 0
    last_talk = None

    while True:
        audio, _ = stream.read(FRAME)

        # ===== 声帯域だけ通す =====
        filtered = bandpass_filter(audio[:, 0], VOICE_BAND[0], VOICE_BAND[1], SAMPLE_RATE)

        # 振幅から音量を計算
        volume = np.linalg.norm(filtered) / len(filtered)

        if volume > THRESHOLD:
            if last_talk is None:
                last_talk = time.time()

            talking_time = time.time() - last_talk
            print(f"🗣️ 声検出中: {talking_time:.1f} 秒", end="\r")
        else:
            last_talk = None
            talking_time = 0
            print("... 無音（声なし） ...            ", end="\r")

        time.sleep(0.05)

        if config.get("listener_only", False):
            continue

        decision = should_penalize(volume, silence_time, talking_time)

        if decision:
            print(f"\n⚠ ペナルティ発動: {decision}")

try:
    main()
except KeyboardInterrupt:
    print("\n終了")