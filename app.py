from flask import Flask, render_template, request, send_file
from firestore_utils_lazy_env import (
    get_all_keywords, get_all_descriptions,
    update_keywords, update_description,
    delete_keywords, delete_description,
    export_logs
)
import csv, os
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/task_registry")
def task_registry():
    keywords = get_all_keywords()
    descriptions = get_all_descriptions()
    return render_template("task_registry.html", keywords=keywords, descriptions=descriptions)

@app.route("/edit_description", methods=["GET", "POST"])
def edit_description():
    keywords = get_all_keywords()
    descriptions = get_all_descriptions()
    all_tasks = list(keywords.keys())
    current_description = ""

    if request.method == "POST":
        task = request.form["task_name"]
        desc = request.form["description"]
        update_description(task, desc)
        current_description = desc
        return render_template("edit_description.html", all_tasks=all_tasks, current_description=desc, message="✅ 任務說明已更新")
    else:
        if all_tasks:
            current_description = descriptions.get(all_tasks[0], "")
        return render_template("edit_description.html", all_tasks=all_tasks, current_description=current_description)

@app.route("/add_keyword", methods=["GET", "POST"])
def add_keyword():
    message = ""
    if request.method == "POST":
        task = request.form["task_name"]
        keyword_list = [k.strip() for k in request.form["keywords"].split(",")]
        update_keywords(task, keyword_list)
        try:
            code = f"def run(event):\n    return \"✅ 任務{task[-1]} 執行成功\""
            os.makedirs("tasks", exist_ok=True)
            with open(f"tasks/task_{task[-1].lower()}.py", "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            message = f"任務已新增，但建立模組失敗：{e}"
        else:
            message = "✅ 任務與模組已建立完成"
    return render_template("add_keyword.html", message=message)

@app.route("/manage", methods=["GET", "POST"])
def manage():
    keywords = get_all_keywords()
    descriptions = get_all_descriptions()
    all_tasks = list(keywords.keys())

    if request.method == "POST":
        task = request.form["task_name"]
        delete_keywords(task)
        delete_description(task)
        return render_template("manage.html", all_tasks=get_all_keywords().keys(), message=f"✅ 已刪除任務 {task}")

    return render_template("manage.html", all_tasks=all_tasks)

@app.route("/export_logs")
def export_logs():
    logs = export_logs()
    filename = f"task_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "source_type", "source_id", "command", "result"])
        writer.writeheader()
        for row in logs:
            writer.writerow(row)
    return send_file(filename, as_attachment=True)

@app.route("/tasks")
def tasks():
    logs = export_logs()
    return render_template("task_table.html", logs=logs)

if __name__ == "__main__":
    app.run(debug=True)
