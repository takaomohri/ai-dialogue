# communication_server.py
from flask import Flask, request, jsonify
import threading
import queue

app = Flask(__name__)

# 音声データを保存するキュー
audio_from_client_queue = queue.Queue()
audio_from_server_queue = queue.Queue()

call_active = False

@app.route('/start_call', methods=['POST'])
def start_call():
    global call_active
    call_active = True
    print("📞 通話が開始されました")
    return jsonify({'status': 'call_started'})

@app.route('/send_audio_to_client', methods=['POST'])
def send_audio_to_client():
    # サーバー（main.py）から受信した音声データを保存
    audio_data = request.data
    audio_from_server_queue.put(audio_data)
    return jsonify({'status': 'audio_received'})

@app.route('/send_audio_to_server', methods=['POST'])
def send_audio_to_server():
    # クライアント（client.py）から受信した音声データを保存
    audio_data = request.data
    audio_from_client_queue.put(audio_data)
    return jsonify({'status': 'audio_received'})

@app.route('/get_audio_from_client', methods=['GET'])
def get_audio_from_client():
    # サーバー（main.py）にクライアントからの音声データを提供
    try:
        audio_data = audio_from_client_queue.get(timeout=30)  # 最大 30 秒待機
        return audio_data
    except queue.Empty:
        return '', 204  # データがない場合

@app.route('/get_audio_from_server', methods=['GET'])
def get_audio_from_server():
    # クライアント（client.py）にサーバーからの音声データを提供
    try:
        audio_data = audio_from_server_queue.get(timeout=30)  # 最大 30 秒待機
        return audio_data
    except queue.Empty:
        return '', 204  # データがない場合

@app.route('/end_call', methods=['POST'])
def end_call():
    global call_active
    call_active = False
    print("📞 通話が終了されました")
    return jsonify({'status': 'call_ended'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
