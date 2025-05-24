from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from firestore_utils_lazy_env import log_task
from datetime import datetime
import os, traceback

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/", methods=["GET"])
def index():
    return "✅ LINE Bot is running."

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
    try:
        text = event.message.text.strip()
        if text.startswith("#"):
            command = text[1:].strip()  # 例如：任務A
            if command == "任務A":
                result = "🚀 任務A 已啟動中..."
            elif command == "任務B":
                result = "🔧 任務B 執行完成 ✅"
            else:
                result = f"⚠️ 指令「{command}」尚未支援"
        else:
            result = f"✅ 你成功連到我了：{text}"

        log_task({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "command": text,
            "source_id": getattr(event.source, "user_id", ""),
            "source_type": "User" if hasattr(event.source, "user_id") else "Group",
            "result": result
        })

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
    except Exception as e:
        err_msg = f"❌ 發生錯誤：{str(e)}\n{traceback.format_exc(limit=2)}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=err_msg))
        raise e
