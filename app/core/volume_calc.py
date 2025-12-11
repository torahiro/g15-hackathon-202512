from app.config.config import load_config

def should_penalize(volume, silence_time, speak_time):
    config = load_config()

    if config.get("listener_only", False):
        return False 

    # ▼ ここから通常判定（後で処理を拡張）
    if silence_time >= 60:
        return "warning"
    if silence_time >= 180:
        return "embarrassing_sound"
    if silence_time >= 190:
        return "spectator"
    if speak_time >= 30:
        return "penalty"

    return None
