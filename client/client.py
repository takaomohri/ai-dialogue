# client.py
import sounddevice as sd
import soundfile as sf
import requests
import threading
import queue
import sys
import io
import time

SERVER_URL = 'http://98.83.63.87:5001'  # サーバーの IP アドレスとポート

class Client:
    def __init__(self):
        self.call_active = True

    def start(self):
        # クライアント通信を開始
        threading.Thread(target=self._receive_audio).start()
        threading.Thread(target=self._send_audio).start()

    def _receive_audio(self):
        while self.call_active:
            # サーバーから音声データを取得
            audio_data = self._get_audio_data_from_server()
            if audio_data:
                # 音声データを再生
                self._play_audio_data(audio_data)
            else:
                # データがない場合
                time.sleep(1)  # 再試行
        print("🔚 通話が終了しました")

    def _get_audio_data_from_server(self):
        # communication_server から音声データを取得
        response = requests.get(SERVER_URL + '/get_audio_from_server')
        if response.status_code == 200 and response.content:
            return response.content
        else:
            return None

    def _play_audio_data(self, audio_data):
        # 音声データを再生
        data, fs = sf.read(io.BytesIO(audio_data), dtype='float32')
        print("🔊 音声を再生します...")
        sd.play(data, fs)
        sd.wait()
        print("🔊 音声の再生が終了しました")

    def _send_audio(self):
        while self.call_active:
            # マイクから音声を録音
            audio_data = self._record_audio()
            if audio_data:
                # サーバーに音声データを送信
                self._send_audio_data_to_server(audio_data)
            else:
                # 録音に失敗した場合
                pass
        print("🔚 音声送信を終了します")

    def _record_audio(self, duration=5):
        fs = 16000  # サンプリングレート
        print(f"🎤 {duration} 秒間録音します...")
        try:
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()  # 録音終了まで待機
            # 録音データをバイト列に変換
            with io.BytesIO() as buf:
                sf.write(buf, recording, fs, format='WAV')
                audio_data = buf.getvalue()
            print("🎤 録音が終了しました")
            return audio_data
        except Exception as e:
            print(f"❗ 録音エラー: {e}")
            return None

    def _send_audio_data_to_server(self, audio_data):
        # communication_server に音声データを送信
        response = requests.post(SERVER_URL + '/send_audio_to_server', data=audio_data)
        if response.status_code == 200:
            print("📤 音声データを送信しました")
        else:
            print("❗ 音声データの送信に失敗しました")

if __name__ == "__main__":
    client = Client()
    client.start()
