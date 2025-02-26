from flask import Flask, request, jsonify
import openai
import requests

app = Flask(__name__)

# OpenAI APIキー
OPENAI_API_KEY = "your_openai_api_key"
openai.api_key = OPENAI_API_KEY

# LINE API設定
LINE_ACCESS_TOKEN = "your_line_access_token"
LINE_API_URL = "https://api.line.me/v2/bot/message/reply"

def chatgpt_response(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}]
    )
    return response["choices"][0]["message"]["content"].strip()

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json()
    print("Received request:", body)  # ✅ デバッグ用のログ追加

    if not body or "events" not in body:
        return jsonify({"status": "error", "message": "Invalid request"}), 400  # ✅ バリデーション追加

    events = body.get("events", [])
    for event in events:
        if event.get("type") == "message" and "text" in event.get("message", {}):
            user_message = event["message"]["text"]
            reply_token = event["replyToken"]

            reply_text = chatgpt_response(user_message)
            reply(reply_token, reply_text)

    return jsonify({"status": "ok"}), 200  # ✅ 正常時は 200 を返す

def reply(reply_token, text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    response = requests.post(LINE_API_URL, headers=headers, json=data)
    print("LINE Reply Response:", response.status_code, response.text)  # ✅ デバッグ用のログ追加

# ✅ ルートページ（"GET /"）の処理を先に記述
@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!", 200

# ✅ Flaskアプリの起動処理は最後に記述
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
