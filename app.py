from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import os, requests

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))
B_API_URL = os.environ.get("TASK_API_URL")  # 專案 B 的 API 網址

@app.route("/", methods=["GET"])
def index():
    return "✅ LINE Bot Proxy is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    reply_token = event.reply_token
    source_id = getattr(event.source, "user_id", "unknown")
    source_type = "user" if hasattr(event.source, "user_id") else "group"

    if not text.startswith("#"):
        line_bot_api.reply_message(reply_token, TextSendMessage(text="請輸入 #指令 來執行任務"))
        return

    try:
        resp = requests.post(B_API_URL, json={
            "task": text[1:].strip(),
            "source_id": source_id,
            "source_type": source_type,
            "original_text": text
        }, timeout=30)
        result = resp.json().get("result", "❌ 專案B未回傳結果")
    except Exception as e:
        result = f"❌ 呼叫任務API失敗：{e}"

    line_bot_api.reply_message(reply_token, TextSendMessage(text=result))
