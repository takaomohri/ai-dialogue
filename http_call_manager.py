# http_call_manager.py
from abstract_call_manager import AbstractCallManager
import requests
import threading
import queue

class HTTPCallManager(AbstractCallManager):
    def __init__(self, server_url):
        self.server_url = server_url  # communication_server.py の URL
        self.call_active = False
        self.audio_queue = queue.Queue()
        self.input_queue = queue.Queue()

    def initiate_call(self):
        self.call_active = True
        print("📞 通話を開始します")
        # 通話を開始
        threading.Thread(target=self._start_call_flow).start()
        return "HTTP_CALL_SID"

    def _start_call_flow(self):
        # communication_server に通話開始を通知
        requests.post(f'{self.server_url}/start_call')

    def create_voice_response(self):
        # レスポンスは不要
        return {}

    def play_audio(self, response, audio_data):
        # communication_server に音声データを送信
        requests.post(f'{self.server_url}/send_audio_to_client', data=audio_data)

    def gather_input(self, response):
        # クライアントからの入力を待機
        pass

    def hangup(self, response):
        print("📞 通話を終了します")
        self.call_active = False
        # communication_server に通話終了を通知
        requests.post(f'{self.server_url}/end_call')

    def redirect(self, response, url):
        if url == '/voice':
            # 通話フローを再開
            threading.Thread(target=self._start_call_flow).start()

    def convert_response_to_str(self, response):
        # 不要
        pass

    def get_user_input(self):
        # クライアントからの音声データを取得
        response = requests.get(f'{self.server_url}/get_audio_from_client')
        if response.status_code == 200:
            return response.content
        else:
            return None
