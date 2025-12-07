import time

last_sound_time = time.time()
SILENCE_LIMIT = 10  # ← 秒を短く！

print("開始")

while True:
    elapsed = time.time() - last_sound_time
    remaining = SILENCE_LIMIT - elapsed

    print(f"remaining: {remaining:.1f}")

    if remaining <= 0:
        print("★★★ 時間切れ ★★★")
        last_sound_time = time.time()

    time.sleep(1)