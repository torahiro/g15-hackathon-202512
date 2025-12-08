import streamlit as st
import time
import json
import os

# ===== 時間設定 =====
TIME_WARNING = 60      # 警告 (優先1)
TIME_SHAME = 180       # 恥ずかしい音
TIME_SPECTATOR = 190   # 観戦モード行き

# ===== 設定・初期化 =====
st.set_page_config(page_title="会話監視ボット", layout="centered")

# 音声ファイルのパス（同じフォルダに用意してください）
SOUND_WARNING = "alarm.wav"   # 警告音
SOUND_SHAME = "shame.wav"     # 恥ずかしい音
SOUND_SPECTATOR = "spectator.wav" # 観戦モード突入音

# セッション状態の初期化（フラグ管理）
if "warning_played" not in st.session_state:
    st.session_state.warning_played = False
if "shame_played" not in st.session_state:
    st.session_state.shame_played = False
if "spectator_mode" not in st.session_state:
    st.session_state.spectator_mode = False

# --- state.json 読み込み ---
# voice_monitor.py が書き込んだ最新の会話時刻を取得
try:
    if os.path.exists("state.json"):
        with open("state.json", "r") as f:
            state = json.load(f)
            last_voice_time = state.get("last_voice_time", time.time())
    else:
        # ファイルがまだない場合は現在時刻とする
        last_voice_time = time.time()
except Exception:
    last_voice_time = time.time()

# 経過時間の計算
elapsed = time.time() - last_voice_time

# ===== リセット処理 =====
# 誰かが喋って elapsed が 0 に戻ったら、フラグをリセットして通常モードに戻す
if elapsed < 2:
    if st.session_state.warning_played or st.session_state.shame_played or st.session_state.spectator_mode:
        st.session_state.warning_played = False
        st.session_state.shame_played = False
        st.session_state.spectator_mode = False
        st.rerun()

# ===== UI 表示 =====

st.title("🤐 沈黙警察チャットボット")

# プログレスバー（最大値を190秒とする）
progress_val = min(elapsed / TIME_SPECTATOR, 1.0)

# 状況に応じた表示ロジック
if elapsed < TIME_WARNING:
    # --- 正常 ---
    st.success(f"会話中... (無音: {int(elapsed)}秒)")
    st.write("今のところ順調ですね。この調子で話してください。")
    st.progress(progress_val)

elif TIME_WARNING <= elapsed < TIME_SHAME:
    # --- 60秒: 警告 ---
    st.warning(f"⚠️ 警告: 会話が止まっています！ (無音: {int(elapsed)}秒)")
    st.write(f"あと {TIME_SHAME - int(elapsed)} 秒で恥ずかしい音が鳴りますよ！")
    st.progress(progress_val)
    
    # 音を1回だけ鳴らす
    if not st.session_state.warning_played:
        try:
            st.audio(SOUND_WARNING, autoplay=True)
        except:
            st.error("警告音ファイルが見つかりません")
        st.session_state.warning_played = True

elif TIME_SHAME <= elapsed < TIME_SPECTATOR:
    # --- 180秒: 恥ずかしい音 ---
    st.error(f"😱 限界突破！ (無音: {int(elapsed)}秒)")
    st.write("やってしまいましたね...")
    st.progress(progress_val)

    # 音を1回だけ鳴らす
    if not st.session_state.shame_played:
        try:
            st.audio(SOUND_SHAME, autoplay=True)
        except:
            st.error("恥ずかしい音ファイルが見つかりません")
        st.session_state.shame_played = True

else:
    # --- 190秒: 観戦モード ---
    st.session_state.spectator_mode = True
    
    # 画面全体を「観戦モード」の雰囲気に
    st.markdown("""
        <style>
        .stApp {
            background-color: #0e1117;
            color: #555555;
        }
        </style>
        """, unsafe_allow_html=True)
    
    st.header("👻 観戦モード")
    st.write("あなたは会話に参加する権利を失いました。")
    st.metric("放置された時間", f"{int(elapsed)} 秒")
    
    # 観戦モード突入音（ループしないようにチェックが必要だが、ここは継続的に煽るなら毎回鳴らしてもよい）
    # 今回は1回だけ鳴らす設計にします
    if "spectator_sound_played" not in st.session_state:
        st.session_state.spectator_sound_played = False
    
    if not st.session_state.spectator_sound_played:
         try:
            st.audio(SOUND_SPECTATOR, autoplay=True)
            st.session_state.spectator_sound_played = True
         except:
             pass

# 自動更新 (0.5秒ごとに画面をリロードして時間をチェック)
time.sleep(0.5)
st.rerun()