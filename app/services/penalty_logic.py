# app/services/penalty_logic.py
from app.config.config import load_config

# 閾値は必要なら config に移してください
NO_SPEAK_WARNING = 60
NO_SPEAK_EMBARRASS = 180
NO_SPEAK_SPECTATOR = 190
TALK_TOO_LONG = 30

def should_penalize(silence_time, speak_time):
    """
    silence_time, speak_time は秒
    戻り値:
      None -> ペナルティ無し
      {"type": "<warning|embarrassing_sound|spectator|long_talk>", "scope": "個人" or "全体"}
    """
    config = load_config()

    # 聞くだけモードの参加者は無条件免除
    if config.get("listener_only", False):
        return None

    mode = config.get("mode", "個人")  # "個人" or "全体"

    # 判定（優先度順に）
    if silence_time >= NO_SPEAK_SPECTATOR:
        return {"type": "spectator", "scope": mode}
    if silence_time >= NO_SPEAK_EMBARRASS:
        return {"type": "embarrassing_sound", "scope": mode}
    if silence_time >= NO_SPEAK_WARNING:
        return {"type": "warning", "scope": mode}
    if speak_time >= TALK_TOO_LONG:
        return {"type": "long_talk", "scope": mode}

    return None
