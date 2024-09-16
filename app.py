from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import os
import dotenv
from chatgpt_dialogue import ChatGPTDialogue
from io import BytesIO
from text_to_speech import TextToSpeechSBV2
from flask import url_for

dotenv.load_dotenv()

# Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')

# Twilio phone number and the number to call
twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
number_to_call = os.getenv('NUMBER_TO_CALL')

SERVER_HOST = os.getenv('SERVER_HOST')

server_url = f"http://{SERVER_HOST}:5000/voice"

client = Client(account_sid, auth_token)

app = Flask(__name__)

# ChatGPTDialogueインスタンスの初期化
chat_instance = None

def chatgpt_callback(response):
    pass

tts = TextToSpeechSBV2()

@app.route("/start_call", methods=['GET'])
def start_call():
    global chat_instance
    chat_instance = ChatGPTDialogue(callback=chatgpt_callback)
    chat_instance.open_chat()
    
    call = client.calls.create(
        url=server_url, 
        to=number_to_call,
        from_=twilio_number
    )
    print(call.sid)
    return f"Call initiated with SID: {call.sid}"

@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()

    ai_response = chat_instance.send("もしもし")
    response.play(url_for('serve_audio', text=ai_response))

    gather = Gather(input='speech', action='/process_speech', method='POST', language='ja-JP', speechTimeout='auto')
    response.append(gather)
    
    return str(response)

@app.route("/process_speech", methods=['POST'])
def process_speech():
    global chat_instance
    user_speech = request.values.get('SpeechResult', '')
    print(f"DEBUG: user_speech: {user_speech}")

    if not user_speech:
        response = VoiceResponse()
        response.play(url_for('serve_audio', text='すみません、聞き取れませんでした。もう一度お願いします。'))
        response.redirect('/voice')
        return str(response)

    ai_response = chat_instance.send(user_speech)
    print(f"DEBUG: ai_response: {ai_response}")

    response = VoiceResponse()
    response.play(url_for('serve_audio', text=ai_response))

    if "***電気料金の督促業務が完了しました***" in ai_response:
        print("### END CALL ### ")
        print(ai_response)
        return end_call()
    
    gather = Gather(input='speech', action='/process_speech', method='POST', language='ja-JP', speechTimeout='auto')
    response.append(gather)

    return str(response)

@app.route("/end_call", methods=['POST'])
def end_call():
    global chat_instance
    if chat_instance:
        chat_instance.close_chat()
        chat_instance = None
    response = VoiceResponse()
    response.play(url_for('serve_audio', text='お話ありがとうございました。さようなら。'))
    response.hangup()
    return str(response)

def get_url_for(route, text):
    filename = tts.text_to_speech_to_file(text)
        
    

@app.route("/serve_audio")
def serve_audio():
    text = request.args.get('text', '')
    filename = tts.text_to_speech_to_file(text)
    return send_file(filename, mimetype="audio/wav")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")