from flask import Flask, request, render_template, redirect, url_for, send_file
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage, SourceUser, SourceGroup
from linebot.exceptions import InvalidSignatureError
from datetime import datetime
import os, importlib
from firestore_utils import *

app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/edit_description", methods=["GET", "POST"])
def edit_description():
    descriptions = get_all_descriptions()
    if request.method == "POST":
        for key in descriptions:
            update_description(key, request.form.get(key, "").strip())
        return redirect(url_for("edit_description"))
    return render_template("edit_description.html", descriptions=descriptions)

@app.route("/registry")
def view_registry():
    return render_template("task_registry.html", keyword_map=get_all_keywords(), descriptions=get_all_descriptions())

@app.route("/manage", methods=["GET"])
def manage_tasks():
    return render_template("manage.html", task_list=list(get_all_keywords().keys()))

@app.route("/delete_task", methods=["POST"])
def delete_task():
    task = request.form.get("task", "").strip()
    if not task:
        return redirect(url_for("manage_tasks"))
    suffix = task[-1].lower()
    mod_path = f"tasks/task_{suffix}.py"
    if os.path.exists(mod_path):
        os.remove(mod_path)
    delete_keywords(task)
    delete_description(task.lower())
    return redirect(url_for("manage_tasks"))

@app.route("/download_log")
def download_log():
    logs = export_logs()
    csv_path = "/tmp/task_log.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("時間,指令,來源ID,來源類型,任務狀態
")
        for log in logs:
            f.write(f"{log['timestamp']},{log['command']},{log['source_id']},{log['source_type']},{log['result']}
")
    return send_file(csv_path, as_attachment=True)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()
    if user_msg.startswith("#"):
        command = user_msg[1:].strip()
        result = handle_custom_task(event, command, immediate=True)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請使用 #指令格式，例如：#任務A"))

def handle_custom_task(event, command, immediate=False):
    try:
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
            "source_id": event.source.user_id if isinstance(event.source, SourceUser) else event.source.group_id,
            "source_type": "User" if isinstance(event.source, SourceUser) else "Group",
            "result": result
        })

        return result
    except Exception as e:
        return f"❌ 任務執行錯誤：{e}"
