from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import openai
import os
import dotenv

dotenv.load_dotenv()

###

# Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
# OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Twilio phone number and the number to call
twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
number_to_call = os.getenv('NUMBER_TO_CALL')

SERVER_HOST = os.getenv('SERVER_HOST')

###

server_url = f"http://{SERVER_HOST}:5000/voice"

client = Client(account_sid, auth_token)
app = Flask(__name__)


@app.route("/start_call", methods=['GET'])
def start_call():
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
    gather = Gather(input='speech', action='/process_speech', method='POST', language='ja-JP', speechTimeout='auto')
    gather.say('こんにちは。ChatGPTとの会話を始めます。何か話してください。')
    response.append(gather)
    return str(response)

@app.route("/process_speech", methods=['POST'])
def process_speech():
    user_speech = request.values.get('SpeechResult', '')

    if not user_speech:
        response = VoiceResponse()
        response.say('すみません、聞き取れませんでした。もう一度お願いします。')
        response.redirect('/voice')
        return str(response)

    chat_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_speech}
        ]
    )
    ai_response = chat_response.choices[0].message.content

    response = VoiceResponse()
    response.say(ai_response, language='ja-JP')

    gather = Gather(input='speech', action='/process_speech', method='POST', language='ja-JP', speechTimeout='auto')
    gather.say('他に何か話したいことはありますか？')
    response.append(gather)

    return str(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
