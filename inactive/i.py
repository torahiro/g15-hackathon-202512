import streamlit as st

# 初期状態（セッションに値が無い場合のみ実行）
if "penalty_mode" not in st.session_state:
    st.session_state.penalty_mode = False  # 初期はOFF

# ボタンが押されたら状態を切り替える
if st.button("ペナルティモード on/off"):
    st.session_state.penalty_mode = not st.session_state.penalty_mode

# 現在の状態を表示
if st.session_state.penalty_mode:
    st.success("ペナルティモード：ON")
else:
    st.info("ペナルティモード：OFF")
# streamlit run i.pyをターミナルで実行
