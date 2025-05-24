from flask import Flask, request, abort, render_template, redirect, url_for
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage, SourceUser, SourceGroup
from linebot.exceptions import InvalidSignatureError
import os, json, csv, importlib
from datetime import datetime
from task_logger import write_csv_log

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/edit_description", methods=["GET", "POST"])
def edit_description():
    desc_path = "task_descriptions.json"
    try:
        with open(desc_path, "r", encoding="utf-8") as f:
            descriptions = json.load(f)
    except Exception:
        descriptions = {}

    if request.method == "POST":
        for key in descriptions:
            descriptions[key] = request.form.get(key, "").strip()
        with open(desc_path, "w", encoding="utf-8") as f:
            json.dump(descriptions, f, ensure_ascii=False, indent=2)
        return redirect(url_for("edit_description"))
    return render_template("edit_description.html", descriptions=descriptions)


@app.route("/registry", methods=["GET"])
def view_registry():
    try:
        with open("task_keywords.json", "r", encoding="utf-8") as f:
            keyword_map = json.load(f)
    except Exception as e:
        print("❌ 無法載入任務詞庫：", e)
        keyword_map = {}

    try:
        with open("task_descriptions.json", "r", encoding="utf-8") as f:
            descriptions = json.load(f)
    except Exception:
        descriptions = {}

    return render_template("task_registry.html", keyword_map=keyword_map, descriptions=descriptions)


from flask import send_file

@app.route("/manage", methods=["GET"])
def manage_tasks():
    try:
        with open("task_keywords.json", "r", encoding="utf-8") as f:
            keyword_map = json.load(f)
    except:
        keyword_map = {}
    return render_template("manage.html", task_list=list(keyword_map.keys()))

@app.route("/delete_task", methods=["POST"])
def delete_task():
    task = request.form.get("task", "").strip()
    if not task:
        return redirect(url_for("manage_tasks"))

    # 刪除模組檔案
    suffix = task[-1].lower()
    mod_path = f"tasks/task_{suffix}.py"
    if os.path.exists(mod_path):
        os.remove(mod_path)

    # 移除任務關鍵字與說明
    for file, key in [("task_keywords.json", task), ("task_descriptions.json", task.lower())]:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if key in data:
                del data[key]
                with open(file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    return redirect(url_for("manage_tasks"))

@app.route("/download_log")
def download_log():
    return send_file("task_log.csv", as_attachment=True)

from linebot.models import MessageEvent, TextMessage, TextSendMessage

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
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="✅ 你的訊息我收到了！")
    )


import importlib
from firestore_utils import get_all_keywords, log_task

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()
    if user_msg.startswith("#"):
        command = user_msg[1:].strip()
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
                result = f"❌ 任務 {matched_task} 執行失敗：{e}"
        else:
            result = f"⚠️ 指令「{command}」尚未支援"

        log_task({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "command": command,
            "source_id": event.source.user_id if hasattr(event.source, "user_id") else "",
            "source_type": "User" if hasattr(event.source, "user_id") else "Group",
            "result": result
        })
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請使用 #指令格式，例如：#任務A"))
