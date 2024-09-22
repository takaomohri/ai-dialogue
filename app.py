# main.py
from flask import Flask, request, send_file, url_for
from twilio_call_manager import TwilioCallManager
from abstract_call_manager import AbstractCallManager
import dotenv
from chatgpt_dialogue import ChatGPTDialogue
from text_to_speech import TextToSpeechSBV2

dotenv.load_dotenv()

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
        return self.tts.text_to_speech_to_file(text)

app = Flask(__name__)

# グローバルインスタンス
call_manager = TwilioCallManager()  # ここを他の実装に差し替え可能
chat_handler = ChatHandler()
tts_manager = TextToSpeechManager()

@app.route("/start_call", methods=['GET'])
def start_call():
    chat_handler.start_chat(callback=chatgpt_callback)
    call_sid = call_manager.initiate_call()
    return f"Call initiated with SID: {call_sid}"

@app.route("/voice", methods=['POST'])
def voice():
    response = call_manager.create_voice_response()
    ai_response = chat_handler.send_message("もしもし")
    if ai_response:
        audio_url = url_for('serve_audio', text=ai_response)
        call_manager.play_audio(response, audio_url)
    response = call_manager.gather_input(response)
    return call_manager.convert_response_to_str(response)

@app.route("/process_speech", methods=['POST'])
def process_speech():
    user_speech = request.values.get('SpeechResult', '')
    print(f"DEBUG: {user_speech}")

    if not user_speech:
        return _handle_no_speech()

    ai_response = chat_handler.send_message(user_speech)
    print(f"DEBUG: {ai_response=}")

    response = call_manager.create_voice_response()
    audio_url = url_for('serve_audio', text=ai_response)
    call_manager.play_audio(response, audio_url)

    if "***電気料金の督促業務が完了しました***" in ai_response:
        return end_call()

    response = call_manager.gather_input(response)
    return call_manager.convert_response_to_str(response)

@app.route("/end_call", methods=['POST'])
def end_call():
    chat_handler.close_chat()
    response = call_manager.create_voice_response()
    audio_url = url_for('serve_audio', text='お話ありがとうございました。さようなら。')
    call_manager.play_audio(response, audio_url)
    call_manager.hangup(response)
    return call_manager.convert_response_to_str(response)

@app.route("/serve_audio")
def serve_audio():
    text = request.args.get('text', '')
    filename = tts_manager.convert_text_to_speech(text)
    return send_file(filename, mimetype="audio/wav")

def _handle_no_speech():
    response = call_manager.create_voice_response()
    audio_url = url_for('serve_audio', text='すみません、聞き取れませんでした。もう一度お願いします。')
    call_manager.play_audio(response, audio_url)
    call_manager.redirect(response, '/voice')
    return call_manager.convert_response_to_str(response)

def chatgpt_callback(response):
    pass

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
