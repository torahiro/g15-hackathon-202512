# app/ui/audience.py
import streamlit as st
from app.config.config import load_config, save_config

st.set_page_config(layout="centered")
st.title("発話状態ビューア")

# load config
config = load_config()
listener_only = config.get("listener_only", False)
mode = config.get("mode", "個人")  # "個人" or "全体"

# infection flag (UI表示用)
if "infected" not in st.session_state:
    st.session_state["infected"] = False

# 背景／見た目
if st.session_state["infected"]:
    st.markdown("""<style>body{background-color:#8B0000;}</style>""", unsafe_allow_html=True)
    st.header("観戦者モード（感染）")
    st.write("⚠ 会話が停止しています… 発話してください")
else:
    st.markdown("""<style>body{background-color:#E8FFE8;}</style>""", unsafe_allow_html=True)
    st.header("生存者")
    st.write("会話が続いています")

st.write("---")
st.subheader("🔧 モード設定")

# 聞くだけモードトグル
new_listener_only = st.checkbox("聞くだけモード（ペナルティ無効）", value=listener_only)
if new_listener_only != listener_only:
    config["listener_only"] = new_listener_only
    save_config(config)
    st.experimental_rerun()

# 個人 / 全体 切替
new_mode = st.selectbox("ペナルティの対象", ["個人", "全体"], index=0 if mode == "個人" else 1)
if new_mode != mode:
    config["mode"] = new_mode
    save_config(config)
    st.success(f"ペナルティ対象を「{new_mode}」に変更しました")
    st.experimental_rerun()

# 現在の設定表示
st.write(f"現在のモード： **{config['mode']}**")
st.write(f"聞くだけモード： **{'ON' if config['listener_only'] else 'OFF'}**")
