from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage, SourceUser, SourceGroup
from linebot.exceptions import InvalidSignatureError
import os
import threading
from flask import render_template
import csv
from datetime import datetime
from task_logger import write_csv_log

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/", methods=["GET"])
def index():
    return "LINE 任務觸發 Bot 正常運作中"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ 驗證失敗")
        abort(400)
    except Exception as e:
        print("❌ webhook 錯誤：", str(e))
        abort(500)
    return "OK"

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
        # 任務處理邏輯
        if command == "任務A":
            from datetime import datetime
            weekday_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            today = datetime.now()
            result = f"✅ 任務A 執行成功：今天是 {weekday_map[today.weekday()]} {today.strftime('%Y-%m-%d')}"
        elif command == "任務B":
            result = "✅ 任務B 執行完畢"
        elif command == "任務C":
            result = "✅ 任務C 處理成功"
        elif command == "任務D":
            result = "✅ 任務D 任務完成"
        else:
            result = f"⚠️ 指令「{command}」尚未支援"

        target_id = event.source.user_id if isinstance(event.source, SourceUser) else event.source.group_id
        if not immediate:
        line_bot_api.push_message(target_id, TextSendMessage(text=result))
        write_csv_log(command, event, result)

    except Exception as e:
        print("❌ 任務處理錯誤：", e)

# 啟動時讀取 CSV 並執行對應任務
def update_task_status_in_csv(command, source_id, new_status, filename="task_log.csv"):
    try:
        updated_rows = []
        with open(filename, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            for row in rows:
                if len(row) < 5:
                    updated_rows.append(row)
                    continue
                if row[1] == command and row[2] == source_id and row[4] == "" and int(row[5]) < 3:
                    row[4] = new_status
                    row[5] = str(int(row[5]) + 1)
                updated_rows.append(row)
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
    except Exception as e:
        print("❌ 更新任務狀態錯誤：", e)

def process_pending_tasks_from_csv(filename="task_log.csv"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            for row in rows:
                if len(row) < 5:
                    continue  # 跳過不完整資料
                timestamp, command, source_id, source_type, result = row
                if "✅" in result or "⚠️" in result:
                    continue  # 已執行過的任務跳過

                # 模擬推播（重推未完成任務）
                response = f"📌 重啟任務紀錄：{command}，結果：{result}"
                line_bot_api.push_message(source_id, TextSendMessage(text=response))
                update_task_status_in_csv(command, source_id, f"🔁 已重推：{result}")
    except FileNotFoundError:
        print("📂 尚無任務記錄檔，略過 CSV 讀取")
    except Exception as e:
        print("❌ 啟動讀取任務 CSV 發生錯誤：", e)

# 啟動伺服器時處理歷史紀錄（僅第一次）
threading.Thread(target=process_pending_tasks_from_csv).start()


@app.route("/tasks", methods=["GET"])
def view_tasks():
    rows = []
    try:
        with open("task_log.csv", "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
    except Exception as e:
        print("⚠️ 無法讀取 task_log.csv：", e)
    return render_template("task_table.html", rows=rows)
