from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage, SourceUser, SourceGroup
from linebot.exceptions import InvalidSignatureError
import os, importlib
from datetime import datetime
from firestore_utils import get_all_keywords, log_task

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/", methods=["GET"])
def index():
    return "✅ I'm alive!"

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
    if not text.startswith("#"):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入 #任務名 來執行"))
        return

    command = text[1:].strip()
    keyword_map = get_all_keywords()
    matched_task = None
    for task, keywords in keyword_map.items():
        if any(k in command for k in keywords):
            matched_task = task
            break

    if matched_task:
        try:
            module_name = f"tasks.task_{matched_task[-1].lower()}"
            task_module = importlib.import_module(module_name)
            result = task_module.run(event)
        except Exception as e:
            result = f"❌ 執行 {matched_task} 錯誤：{e}"
    else:
        result = f"⚠️ 無法辨識指令：{command}"

    log_task({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "command": command,
        "source_id": getattr(event.source, "user_id", ""),
        "source_type": "User" if isinstance(event.source, SourceUser) else "Group",
        "result": result
    })
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
