from flask import Flask, request, jsonify, render_template, redirect, url_for
import openai
import requests
import hashlib
import hmac
import base64
import os

app = Flask(__name__)

# Simple in-memory todo list
tasks = []

# ✅ OpenAI APIキー（環境変数から取得）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ 新しい OpenAI クライアントを作成
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# LINE API設定
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_API_URL = "https://api.line.me/v2/bot/message/reply"

# LINEのチャネルシークレット（環境変数から取得）
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

def verify_signature(request):
    """ LINEの署名を検証 """
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    hash = hmac.new(CHANNEL_SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash).decode()
    return hmac.compare_digest(expected_signature, signature)

def chatgpt_response(user_message):
    """ ✅ 最新の OpenAI API を使用 """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

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
    print("LINE Reply Response:", response.status_code, response.text)

@app.route("/callback", methods=["POST"])
def callback():
    """ LINEのWebhookを処理 """
    if not verify_signature(request):
        return jsonify({"status": "error", "message": "Invalid signature"}), 403

    body = request.get_json()
    print("Received request:", body)

    if not body or "events" not in body:
        return jsonify({"status": "ok"}), 200

    events = body.get("events", [])
    for event in events:
        if event.get("type") == "message" and "text" in event.get("message", {}):
            user_message = event["message"]["text"]
            reply_token = event["replyToken"]

            try:
                reply_text = chatgpt_response(user_message)
                reply(reply_token, reply_text)
            except Exception as e:
                print(f"Error: {e}")
                reply(reply_token, "エラーが発生しました。")

    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def home():
    """ 確認用のルート """
    return "LINE Bot is running!", 200


@app.route("/todo", methods=["GET"])
def todo_page():
    """Todo list page"""
    return render_template("todo.html", tasks=tasks, error=None)


@app.route("/add_todo", methods=["POST"])
def add_todo():
    """Handle adding a new todo item"""
    task = request.form.get("task", "").strip()
    if not task:
        return render_template("todo.html", tasks=tasks, error="Task cannot be empty"), 400
    tasks.append(task)
    return redirect(url_for("todo_page"))
