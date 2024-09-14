from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import openai

app = Flask(__name__)

# Twilio credentials
account_sid = 'ACa4c0b4989eafefdcd734ad279ebffad4'
auth_token = 'e03697c6deaa03286abf6b6103ad53bf'
client = Client(account_sid, auth_token)

# OpenAI API key
openai.api_key = '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'

# Twilio phone number and the number to call
twilio_number = '+12089032603'
number_to_call = '+81 90 5196 0993'

aws_ec2_url = "http://3.89.66.65:5000/voice"

@app.route("/start_call", methods=['GET'])
def start_call():
    call = client.calls.create(
        url=aws_ec2_url,  # ngrokのURLを使用
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
