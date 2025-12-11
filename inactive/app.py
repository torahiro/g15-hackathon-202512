import streamlit as st
import time
import json
import os
import speech_recognition as sr

# ===== 設定・初期化 =====
st.set_page_config(page_title="会話監視ボット", layout="centered")

# デフォルト設定
TIME_WARNING = 60
TIME_SHAME = 180
TIME_SPECTATOR = 190
STATE_FILE = "state.json"

SOUND_WARNING = "alarm.wav"
SOUND_SHAME = "shame.wav"
SOUND_SPECTATOR = "spectator.wav"

# セッション状態の初期化
if "warning_played" not in st.session_state:
    st.session_state.warning_played = False
if "shame_played" not in st.session_state:
    st.session_state.shame_played = False
if "spectator_mode" not in st.session_state:
    st.session_state.spectator_mode = False

# --- state.json 読み書き関数 ---
def get_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    # 初期値
    return {
        "last_voice_time": time.time(), 
        "is_spectator": False, 
        "current_volume": 0.0,
        "threshold": 0.05
    }

def update_state(key, value):
    """指定したキーの値を更新する"""
    current_state = get_state()
    current_state[key] = value
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(current_state, f)
    except:
        pass

def reset_game():
    st.session_state.spectator_mode = False
    st.session_state.warning_played = False
    st.session_state.shame_played = False
    update_state("is_spectator", False)
    update_state("last_voice_time", time.time())
    st.rerun()

# ===== UI サイドバー（設定） =====
st.sidebar.header("⚙️ 感度設定")
st.sidebar.write("声が拾われない場合は、バーを左（敏感）に、雑音を拾う場合は右（鈍感）にしてください。")

# 閾値スライダー (0.01 〜 0.5)
state = get_state()
current_threshold = state.get("threshold", 0.05)
new_threshold = st.sidebar.slider(
    "マイク感度 (閾値)", 
    min_value=0.01, 
    max_value=0.50, 
    value=current_threshold, 
    step=0.01,
    format="%.2f"
)

# スライダーの値が変わったらJSONを更新
if new_threshold != current_threshold:
    update_state("threshold", new_threshold)


# ===== メイン処理 =====
last_voice_time = state.get("last_voice_time", time.time())
elapsed = time.time() - last_voice_time
current_vol = state.get("current_volume", 0.0)

# リセット判定
if elapsed < 2 and not st.session_state.spectator_mode:
    if st.session_state.warning_played or st.session_state.shame_played:
        st.session_state.warning_played = False
        st.session_state.shame_played = False
        st.rerun()

# ===== UI 表示 =====
st.title("🤐 沈黙警察チャットボット")

# 音量メーターの表示 (視覚フィードバック)
col1, col2 = st.columns([3, 1])
with col1:
    # 音量をバーで表示 (最大値を適当に0.5として正規化)
    vol_percent = min(current_vol / 0.5, 1.0)
    st.write("現在の声の大きさ:")
    st.progress(vol_percent)
with col2:
    if current_vol > new_threshold:
        st.success("🗣️ OK")
    else:
        st.write("...")

# 経過時間バー
progress_val = min(elapsed / TIME_SPECTATOR, 1.0)

# 状況に応じた表示
if st.session_state.spectator_mode:
    update_state("is_spectator", True)
    st.markdown("""<style>.stApp { background-color: #0e1117; color: #dcdcdc; }</style>""", unsafe_allow_html=True)
    st.header("👻 観戦モード")
    st.error("会話に参加する権利を失いました。")
    st.metric("放置された時間", f"{int(elapsed)} 秒")
    
    st.write("---")
    st.write("### 🙇 復活の儀式")
    if st.button("🎤 謝罪する（録音開始）"):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("聞いています...")
            r.adjust_for_ambient_noise(source)
            try:
                audio = r.listen(source, timeout=5)
                text = r.recognize_google(audio, language='ja-JP')
                st.write(f"あなたの言葉: 「{text}」")
                if any(word in text for word in ["ごめん", "すいません", "申し訳", "許して"]):
                    st.success("誠意が伝わりました。")
                    time.sleep(2)
                    reset_game()
                else:
                    st.warning("気持ちが足りません。")
            except:
                st.error("聞き取れませんでした。")

elif elapsed < TIME_WARNING:
    update_state("is_spectator", False)
    st.success(f"会話中... (無音: {int(elapsed)}秒)")
    st.progress(progress_val)

elif TIME_WARNING <= elapsed < TIME_SHAME:
    st.warning(f"⚠️ 警告: 会話が止まっています！ (無音: {int(elapsed)}秒)")
    st.progress(progress_val)
    if not st.session_state.warning_played:
        try: st.audio(SOUND_WARNING, autoplay=True)
        except: pass
        st.session_state.warning_played = True

elif TIME_SHAME <= elapsed < TIME_SPECTATOR:
    st.error(f"😱 限界突破！ (無音: {int(elapsed)}秒)")
    st.progress(progress_val)
    if not st.session_state.shame_played:
        try: st.audio(SOUND_SHAME, autoplay=True)
        except: pass
        st.session_state.shame_played = True

else:
    st.session_state.spectator_mode = True
    try: st.audio(SOUND_SPECTATOR, autoplay=True)
    except: pass
    st.rerun()

if not st.session_state.spectator_mode:
    time.sleep(0.5)
    st.rerun()
