# app.py
import streamlit as st
import time

# 仮の状態（あとで音声側と共有）
if "infected" not in st.session_state:
    st.session_state.infected = False

st.set_page_config(layout="centered")

if st.session_state.infected:
    st.markdown(
        """
        <style>
        body {
            background-color: #8B0000;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("## 観戦者モード")
    st.markdown("### 会話が停止しました…")
    st.markdown("⚠ 発話してください")

else:
    st.markdown(
        """
        <style>
        body {
            background-color: #E8FFE8;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("## ✅ 生存者")
    st.markdown("会話が続いています")