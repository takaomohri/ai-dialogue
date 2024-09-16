# twilio_call_manager.py
from abstract_call_manager import AbstractCallManager
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import os

class TwilioCallManager(AbstractCallManager):
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.number_to_call = os.getenv('NUMBER_TO_CALL')
        self.server_host = os.getenv('SERVER_HOST')
        self.server_url = f"http://{self.server_host}:5000/voice"
        self.client = Client(self.account_sid, self.auth_token)

    def initiate_call(self):
        call = self.client.calls.create(
            url=self.server_url,
            to=self.number_to_call,
            from_=self.twilio_number
        )
        return call.sid

    def create_voice_response(self):
        return VoiceResponse()

    def play_audio(self, response, audio_url):
        response.play(audio_url)

    def gather_input(self, response):
        gather = Gather(
            input='speech',
            action='/process_speech',
            method='POST',
            language='ja-JP',
            speech_timeout='auto'
        )
        response.append(gather)

    def hangup(self, response):
        print("DEBUG: hangup start")
        response.hangup()
        print("DEBUG: hangup end")

    def redirect(self, response, url):
        response.redirect(url)

    def convert_response_to_str(self, response):
        return str(response)
