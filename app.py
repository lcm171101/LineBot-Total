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
