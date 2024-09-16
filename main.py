# main.py
from abstract_call_manager import AbstractCallManager
from http_call_manager import HTTPCallManager
import threading
import time
import os
import tempfile
from chatgpt_dialogue import ChatGPTDialogue
from text_to_speech import TextToSpeechSBV2
import openai
from dotenv import load_dotenv

load_dotenv()

# OpenAI の API キーを設定
openai.api_key = os.getenv("OPENAI_API_KEY")

class ChatHandler:
    def __init__(self):
        self.chat_instance = None

    def start_chat(self, callback):
        self.chat_instance = ChatGPTDialogue(callback=callback)
        self.chat_instance.open_chat()

    def send_message(self, message):
        if self.chat_instance:
            return self.chat_instance.send(message)
        return None

    def close_chat(self):
        if self.chat_instance:
            self.chat_instance.close_chat()
            self.chat_instance = None

class TextToSpeechManager:
    def __init__(self):
        self.tts = TextToSpeechSBV2()

    def convert_text_to_speech(self, text):
        # テキストを音声ファイルに変換し、ファイル名を返す
        return self.tts.text_to_speech_to_file(text)

# グローバルインスタンス
call_manager = HTTPCallManager(server_url='http://localhost:5001')  # communication_server の URL
chat_handler = ChatHandler()
tts_manager = TextToSpeechManager()

def main():
    # 通話を開始
    chat_handler.start_chat(callback=chatgpt_callback)
    call_sid = call_manager.initiate_call()
    # 通話フローを開始
    voice()

def voice():
    response = call_manager.create_voice_response()
    ai_response = chat_handler.send_message("もしもし")
    if ai_response:
        audio_filename = tts_manager.convert_text_to_speech(ai_response)
        with open(audio_filename, 'rb') as f:
            audio_data = f.read()
        call_manager.play_audio(response, audio_data)
        os.unlink(audio_filename)
    gather_input()

def gather_input():
    # ユーザーの入力を待機
    threading.Thread(target=process_user_input).start()

def process_user_input():
    audio_data = call_manager.get_user_input()
    if audio_data:
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_audio_file:
            tmp_audio_file.write(audio_data)
            audio_filename = tmp_audio_file.name
        # 音声をテキストに変換
        user_speech = transcribe_audio(audio_filename)
        print(f"DEBUG: user_speech: {user_speech}")
        os.unlink(audio_filename)
        if not user_speech:
            _handle_no_speech()
            return
        ai_response = chat_handler.send_message(user_speech)
        print(f"DEBUG: ai_response: {ai_response}")
        response = call_manager.create_voice_response()
        audio_filename = tts_manager.convert_text_to_speech(ai_response)
        with open(audio_filename, 'rb') as f:
            audio_data = f.read()
        call_manager.play_audio(response, audio_data)
        os.unlink(audio_filename)
        if "***電気料金の督促業務が完了しました***" in ai_response:
            end_call()
            return
        gather_input()
    else:
        _handle_no_speech()

def _handle_no_speech():
    response = call_manager.create_voice_response()
    ai_response = 'すみません、聞き取れませんでした。もう一度お願いします。'
    audio_filename = tts_manager.convert_text_to_speech(ai_response)
    with open(audio_filename, 'rb') as f:
        audio_data = f.read()
    call_manager.play_audio(response, audio_data)
    os.unlink(audio_filename)
    gather_input()

def end_call():
    chat_handler.close_chat()
    response = call_manager.create_voice_response()
    ai_response = 'お話ありがとうございました。さようなら。'
    audio_filename = tts_manager.convert_text_to_speech(ai_response)
    with open(audio_filename, 'rb') as f:
        audio_data = f.read()
    call_manager.play_audio(response, audio_data)
    os.unlink(audio_filename)
    call_manager.hangup(response)

def chatgpt_callback(response):
    pass

def transcribe_audio(audio_filename):
    # OpenAI Whisper API を使用して音声をテキストに変換
    with open(audio_filename, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file, language='ja')
    return transcript['text']

if __name__ == "__main__":
    main()
