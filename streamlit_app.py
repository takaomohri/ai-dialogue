# streamlit_app.py
import streamlit as st
import requests
import os

def main():
    st.title("📞 通話管理システム")
    st.write("通話を開始するクライアントを選択してください。")

    client_option = st.selectbox(
        "クライアントの選択",
        ("Twilio", "Macクライアント")
    )

    if st.button("📞 通話を開始"):
        # サーバーにリクエストを送信
        response = requests.post(
            "http://localhost:5000/start_call",
            json={"client_option": client_option}
        )
        if response.status_code == 200:
            st.success("通話を開始しました。")
        else:
            st.error("通話の開始に失敗しました。")

if __name__ == "__main__":
    main()
