import streamlit as st
import time
import json
import os
import speech_recognition as sr  # 音声認識ライブラリ

# ===== 時間設定 =====
TIME_WARNING = 60      # 警告
TIME_SHAME = 180       # 恥ずかしい音
TIME_SPECTATOR = 190   # 観戦モード行き

# ===== 設定・初期化 =====
st.set_page_config(page_title="会話監視ボット", layout="centered")

SOUND_WARNING = "alarm.wav"
SOUND_SHAME = "shame.wav"
SOUND_SPECTATOR = "spectator.wav"

if "warning_played" not in st.session_state:
    st.session_state.warning_played = False
if "shame_played" not in st.session_state:
    st.session_state.shame_played = False
if "spectator_mode" not in st.session_state:
    st.session_state.spectator_mode = False

# --- state.json 読み書き関数 ---
STATE_FILE = "state.json"

def get_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {"last_voice_time": time.time(), "is_spectator": False}

def update_spectator_status(is_spectator):
    current_state = get_state()
    if current_state.get("is_spectator") != is_spectator:
        current_state["is_spectator"] = is_spectator
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(current_state, f)
        except:
            pass

def reset_game():
    """ゲームをリセットして会話に戻す"""
    st.session_state.spectator_mode = False
    st.session_state.warning_played = False
    st.session_state.shame_played = False
    update_spectator_status(False)
    
    # 時間もリセット（現在時刻にする）
    state = get_state()
    state["last_voice_time"] = time.time()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    
    st.rerun()

# --- メイン処理 ---
state_data = get_state()
last_voice_time = state_data.get("last_voice_time", time.time())
elapsed = time.time() - last_voice_time

# ===== リセット処理 (通常時) =====
if elapsed < 2 and not st.session_state.spectator_mode:
    if st.session_state.warning_played or st.session_state.shame_played:
        st.session_state.warning_played = False
        st.session_state.shame_played = False
        st.rerun()

# ===== UI 表示 =====
st.title("🤐 沈黙警察チャットボット")
progress_val = min(elapsed / TIME_SPECTATOR, 1.0)

# 状況に応じた表示ロジック
if st.session_state.spectator_mode:
    # --- 190秒以降: 観戦モード ---
    update_spectator_status(True)

    st.markdown("""
        <style>
        .stApp { background-color: #0e1117; color: #dcdcdc; }
        </style>
        """, unsafe_allow_html=True)
    
    st.header("👻 観戦モード")
    st.error("会話に参加する権利を失いました。")
    st.metric("放置された時間", f"{int(elapsed)} 秒")

    st.write("---")
    st.write("### 🙇 復活の儀式")
    st.write("マイクに向かって、心を込めて**「申し訳ありません」**と言えば許されるかもしれません。")

    # 音声認識ボタン
    if st.button("🎤 謝罪する（録音開始）"):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("聞いています... 話してください！")
            # 環境音のノイズ対策
            r.adjust_for_ambient_noise(source)
            try:
                # 5秒間聞き取る
                audio = r.listen(source, timeout=5)
                st.write("解析中...")
                # Googleの音声認識APIを使用 (日本語)
                text = r.recognize_google(audio, language='ja-JP')
                st.write(f"あなたの言葉: 「{text}」")

                # 判定ロジック：キーワードが含まれているか
                keywords = ["ごめんなさい", "すいません", "申し訳", "許して"]
                
                if any(word in text for word in keywords):
                    st.success("誠意が伝わりました。会話への復帰を許可します！")
                    time.sleep(2)
                    reset_game()
                else:
                    st.warning("気持ちが足りません。「申し訳ありません」と言ってください。")
            
            except sr.UnknownValueError:
                st.error("何を言っているか聞き取れませんでした。もっとハッキリ謝ってください。")
            except sr.RequestError:
                st.error("通信エラーです（インターネット接続を確認してください）。")
            except Exception as e:
                st.error(f"エラー: {e}")

elif elapsed < TIME_WARNING:
    # --- 正常 ---
    update_spectator_status(False)
    st.success(f"会話中... (無音: {int(elapsed)}秒)")
    st.progress(progress_val)

elif TIME_WARNING <= elapsed < TIME_SHAME:
    # --- 60秒: 警告 ---
    st.warning(f"⚠️ 警告: 会話が止まっています！ (無音: {int(elapsed)}秒)")
    st.progress(progress_val)
    if not st.session_state.warning_played:
        try: st.audio(SOUND_WARNING, autoplay=True)
        except: pass
        st.session_state.warning_played = True

elif TIME_SHAME <= elapsed < TIME_SPECTATOR:
    # --- 180秒: 恥ずかしい音 ---
    st.error(f"😱 限界突破！ (無音: {int(elapsed)}秒)")
    st.progress(progress_val)
    if not st.session_state.shame_played:
        try: st.audio(SOUND_SHAME, autoplay=True)
        except: pass
        st.session_state.shame_played = True

else:
    # --- 190秒になった瞬間 ---
    st.session_state.spectator_mode = True
    try: st.audio(SOUND_SPECTATOR, autoplay=True)
    except: pass
    st.rerun()

# 観戦モード中は自動更新を止めないと、ボタンを押した瞬間にリロードされてしまうことがある
# そのため、観戦モード以外の時だけ自動リロードする
if not st.session_state.spectator_mode:
    time.sleep(0.5)
    st.rerun()