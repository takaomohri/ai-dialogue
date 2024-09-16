# main.py
from flask import Flask, request, send_file, url_for
from abstract_call_manager import AbstractCallManager
from twilio_call_manager import TwilioCallManager
from http_call_manager import HTTPCallManager
import threading
import time
import os
import tempfile
from chatgpt_dialogue import ChatGPTDialogue
from text_to_speech import TextToSpeechSBV2
import openai

# 環境変数の読み込み
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

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

# グローバル変数
call_manager = None  # 使用する CallManager インスタンス
chat_handler = ChatHandler()
tts_manager = TextToSpeechManager()

@app.route("/voice", methods=['POST'])
def voice():
    response = call_manager.create_voice_response()
    ai_response = chat_handler.send_message("もしもし")
    if ai_response:
        audio_filename = tts_manager.convert_text_to_speech(ai_response)
        audio_url = url_for('serve_audio', filename=audio_filename, _external=True)
        if isinstance(call_manager, TwilioCallManager):
            call_manager.play_audio(response, audio_url)
        else:
            with open(audio_filename, 'rb') as f:
                audio_data = f.read()
            call_manager.play_audio(response, audio_data)
            os.unlink(audio_filename)
    call_manager.gather_input(response)
    if isinstance(call_manager, TwilioCallManager):
        return call_manager.convert_response_to_str(response)
    else:
        # Mac クライアントの場合、ユーザー入力を待機
        threading.Thread(target=wait_for_user_input).start()
        return ''

def wait_for_user_input():
    # ユーザーの入力を待機
    audio_data = call_manager.get_user_input()
    if audio_data:
        process_speech(audio_data)
    else:
        _handle_no_speech()

@app.route("/process_speech", methods=['POST'])
def process_speech_route():
    if isinstance(call_manager, TwilioCallManager):
        user_speech = request.values.get('SpeechResult', '')
        print(f"DEBUG: {user_speech=}")
        return process_speech(user_speech)
    else:
        # Mac クライアントの場合、このエンドポイントは使用しない
        return ''

def process_speech(input_data):
    if isinstance(call_manager, TwilioCallManager):
        user_speech = input_data
    else:
        # 音声データを一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_audio_file:
            tmp_audio_file.write(input_data)
            audio_filename = tmp_audio_file.name
        # 音声をテキストに変換
        user_speech = transcribe_audio(audio_filename)
        print(f"DEBUG: user_speech: {user_speech}")
        os.unlink(audio_filename)
    
    if not user_speech:
        return _handle_no_speech()
    
    flag_conversation_end = False
    ai_response = chat_handler.send_message(user_speech)
    print(f"DEBUG: ai_response: {ai_response}")
    if "***電気料金の督促業務が完了しました***" in ai_response:
        a = ai_response.split("***電気料金の督促業務が完了しました***")
        ai_response_before_endmark = a[0]
        ai_response_after_endmark = a[1]
        print(f"DEBUG: ai_response_after_endmark: {ai_response_after_endmark}")
        ai_response = ai_response_before_endmark
        flag_conversation_end = True
        
    response = call_manager.create_voice_response()
    audio_filename = tts_manager.convert_text_to_speech(ai_response)
    audio_url = url_for('serve_audio', filename=audio_filename, _external=True)
    if isinstance(call_manager, TwilioCallManager):
        call_manager.play_audio(response, audio_url)
    else:
        with open(audio_filename, 'rb') as f:
            audio_data = f.read()
        call_manager.play_audio(response, audio_data)
        os.unlink(audio_filename)

    #if flag_conversation_end:
    #    call_manager.hangup(response)
    #    #end_call()
    #    return ''
    
    call_manager.gather_input(response)
    if isinstance(call_manager, TwilioCallManager):
        return call_manager.convert_response_to_str(response)
    else:
        threading.Thread(target=wait_for_user_input).start()
        return ''

@app.route("/end_call", methods=['POST'])
def end_call():
    chat_handler.close_chat()
    response = call_manager.create_voice_response()
    ai_response = 'お話ありがとうございました。さようなら。'
    audio_filename = tts_manager.convert_text_to_speech(ai_response)
    audio_url = url_for('serve_audio', filename=audio_filename, _external=True)
    if isinstance(call_manager, TwilioCallManager):
        call_manager.play_audio(response, audio_url)
    else:
        with open(audio_filename, 'rb') as f:
            audio_data = f.read()
        call_manager.play_audio(response, audio_data)
        os.unlink(audio_filename)
    call_manager.hangup(response)
    if isinstance(call_manager, TwilioCallManager):
        return call_manager.convert_response_to_str(response)
    else:
        return ''

@app.route("/serve_audio")
def serve_audio():
    filename = request.args.get('filename', '')
    if not os.path.exists(filename):
        return "File not found", 404
    response = send_file(filename, mimetype="audio/wav")
    # 音声ファイルを送信後に削除
    threading.Thread(target=delete_file, args=(filename,)).start()
    return response

# main.py の追加部分
@app.route("/start_call", methods=['POST'])
def start_call():
    global call_manager
    client_option = request.json.get('client_option', 'Twilio')
    if client_option == 'Twilio':
        call_manager = TwilioCallManager()
    elif client_option == 'Macクライアント':
        call_manager = HTTPCallManager(server_url='http://localhost:5001')
    else:
        return "Invalid client option", 400

    chat_handler.start_chat(callback=chatgpt_callback)
    call_sid = call_manager.initiate_call()
    return "Call initiated", 200


def delete_file(filename):
    time.sleep(5)  # ファイル送信が完了するまで待機
    if os.path.exists(filename):
        os.unlink(filename)

def _handle_no_speech():
    response = call_manager.create_voice_response()
    ai_response = 'すみません、聞き取れませんでした。もう一度お願いします。'
    audio_filename = tts_manager.convert_text_to_speech(ai_response)
    audio_url = url_for('serve_audio', filename=audio_filename, _external=True)
    if isinstance(call_manager, TwilioCallManager):
        call_manager.play_audio(response, audio_url)
    else:
        with open(audio_filename, 'rb') as f:
            audio_data = f.read()
        call_manager.play_audio(response, audio_data)
        os.unlink(audio_filename)
    call_manager.gather_input(response)
    if isinstance(call_manager, TwilioCallManager):
        return call_manager.convert_response_to_str(response)
    else:
        threading.Thread(target=wait_for_user_input).start()
        return ''

def chatgpt_callback(response):
    pass

def transcribe_audio(audio_filename):
    # OpenAI の Whisper API を使用して音声をテキストに変換
    with open(audio_filename, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file, language='ja')
    return transcript['text']

if __name__ == "__main__":
    # Flask アプリを実行
    app.run(debug=False, host="0.0.0.0", port=5000)
