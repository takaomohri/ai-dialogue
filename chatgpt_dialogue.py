import os
from openai import OpenAI

class ChatGPTDialogue:
    def __init__(self, callback):
        self.client = self._setup_openai_client()
        self.messages = []
        self.callback = callback
        self.initial_prompt = self._load_initial_prompt()

    def _setup_openai_client(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI APIキーが設定されていません。環境変数 OPENAI_API_KEY を設定してください。")
        return OpenAI(api_key=api_key)

    def _load_initial_prompt(self):
        try:
            with open("prompt.txt", "r", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError:
            print("警告: prompt.txt ファイルが見つかりません。デフォルトのプロンプトを使用します。")
            return "あなたは役立つアシスタントです。"

    def open_chat(self):
        self.messages = [{"role": "system", "content": self.initial_prompt}]
        #print("チャットを初期化しました。初期プロンプト:")
        #print(self.initial_prompt)

    def send(self, message):
        self.messages.append({"role": "user", "content": message})
        response = self._create_chat_completion()
        self.messages.append({"role": "assistant", "content": response})
        self.callback(response)
        return response

    def close_chat(self):
        print("チャットを終了します。")
        self.messages = []

    def _create_chat_completion(self):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages
        )
        return response.choices[0].message.content

# 使用例
def chatgpt_callback(response):
    print(f"ChatGPT: {response}")

if __name__ == "__main__":
    chat = ChatGPTDialogue(callback=chatgpt_callback)
    chat.open_chat()
    
    while True:
        user_input = input("あなた: ")
        if user_input.lower() == 'quit':
            break
        chat.send(user_input)
    
    chat.close_chat()