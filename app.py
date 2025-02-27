from flask import Flask, request, jsonify
import openai
import requests
import hashlib
import hmac
import base64

app = Flask(__name__)

# OpenAI APIキー
OPENAI_API_KEY = "your_openai_api_key"
openai.api_key = OPENAI_API_KEY

# LINE API設定
LINE_ACCESS_TOKEN = "your_line_access_token"
LINE_API_URL = "https://api.line.me/v2/bot/message/reply"

# LINEのチャネルシークレット（LINE Developersで確認可能）
CHANNEL_SECRET = "your_channel_secret"

def verify_signature(request):
    """ LINEの署名を検証 """
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    hash = hmac.new(CHANNEL_SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash).decode()
    return hmac.compare_digest(expected_signature, signature)

def chatgpt_response(user_message):
    """ ChatGPT APIを使って返信を生成 """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}]
    )
    return response["choices"][0]["message"]["content"].strip()

def reply(reply_token, text):
    """ LINE API を使って返信する """
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

@app.route("/callback", methods=["POST"])
def callback():
    """ LINEのWebhookを処理 """
    if not verify_signature(request):
        return jsonify({"status": "error", "message": "Invalid signature"}), 403  # 🚨 署名エラー時は403を返す

    body = request.get_json()
    print("Received request:", body)  # ✅ デバッグ用ログ追加

    if not body or "events" not in body:
        return jsonify({"status": "ok"}), 200  # ✅ Webhookイベントなしでも200を返す

    events = body.get("events", [])
    for event in events:
        if event.get("type") == "message" and "text" in event.get("message", {}):
            user_message = event["message"]["text"]
            reply_token = event["replyToken"]

            reply_text = chatgpt_response(user_message)
            reply(reply_token, reply_text)

    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def home():
    """ 確認用のルート """
    return "LINE Bot is running!", 200

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # PORT環境変数を取得（デフォルト5000）
    app.run(host="0.0.0.0", port=port)
