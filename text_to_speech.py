import numpy as np
import wave
from client_sbv2 import init_abv2_api, call_TTS_API
import datetime

API_KEY = "sbv2_amitaro"
#API_KEY = "sbv2_jvnv-F1-jp"

class TextToSpeechSBV2:
    def __init__(self, folder="wav_folder"):
        self.folder = folder
        init_abv2_api(api_key = "sbv2_amitaro", model_name = "amitaro")
        init_abv2_api(api_key = "sbv2_jvnv-F1-jp", model_name = "jvnv-F1-jp")
        #self.text_to_speech_to_file("おはよう！")


    def text_to_speech_to_file(self, text, filename=None):
        if filename is None:
            current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = self.folder + "/" + current_time + ".wav"
        audio, sr = call_TTS_API(text, api_key = API_KEY)

        #print(f"DEBUG: client  {type(audio)=} ")
        #print(f"DEBUG: client  {audio[0:10]=} ")

        save_to_wav(sr, audio, filename=filename)
        #print(f"DEBUG: {filename=} text={text}")
        return filename




def save_to_wav(sr, audio, filename="output.wav"):
    audio_data = np.array(audio, dtype=np.int16)
    byte_data = audio_data.tobytes()

    # バイト列をbytearrayに変換
    byte_array = bytearray(byte_data)
    b = bytes(byte_array)

    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)  # モノラル
        wf.setsampwidth(2)  # 16bit (2バイト)
        wf.setframerate(sr  )  # サンプリングレート
        wf.writeframes(b)  # バイトデータとして書き込む

