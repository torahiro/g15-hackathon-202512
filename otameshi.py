
import streamlit as st
import time

st.title('ホイスチャットへようこそ')
st.header('会話を始めましょう')
st.subheader('モードを選択してください')
st.text('以下のオプションからモードを選択してください。')
st.write('①', '②', '③', sep='\n')

# ボタンを押したら3秒間出力を待つ
if st.button('start'):
    with st.spinner('processiong...'):
        time.sleep(3)
        st.write('end!')
# Sidebarの選択肢を定義する
options = ["Option 1", "Option 2", "Option 3"]
choice = st.sidebar.selectbox("Select an option", options)

# Mainコンテンツの表示を変える
if choice == "Option 1":
    st.write("You selected Option 1")
elif choice == "Option 2":
    st.write("You selected Option 2")
else:
    st.write("You selected Option 3")

mode = st.selectbox('モード選択', ['カジュアル', 'ビジネス', '教育'])

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

