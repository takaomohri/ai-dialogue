# abstract_call_manager.py
from abc import ABC, abstractmethod

class AbstractCallManager(ABC):
    @abstractmethod
    def initiate_call(self):
        pass

    @abstractmethod
    def create_voice_response(self):
        pass

    @abstractmethod
    def play_audio(self, response, audio_data):
        pass

    @abstractmethod
    def gather_input(self, response):
        pass

    @abstractmethod
    def hangup(self, response):
        pass

    @abstractmethod
    def redirect(self, response, url):
        pass

    @abstractmethod
    def convert_response_to_str(self, response):
        pass
