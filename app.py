from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from linebot.exceptions import InvalidSignatureError
import os, requests, json, logging
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from io import StringIO

# === 初始化 Flask App 與 LINE SDK ===
app = Flask(__name__)
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))
B_API_URL = os.environ.get("TASK_API_URL")  # 專案 B 的 API 網址

# === 初始化 Firebase Admin SDK（透過環境變數） ===
import base64
firebase_b64 = os.environ.get("FIREBASE_KEY_B64")
firebase_json = base64.b64decode(firebase_b64).decode("utf-8")
cred = credentials.Certificate(json.load(StringIO(firebase_json)))
firebase_admin.initialize_app(cred)
db = firestore.client()

# === 初始化 Logging ===
logging.basicConfig(filename="push_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

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

def save_source_id_firestore(source_id, source_type):
    doc_ref = db.collection("line_sources").document(source_id)
    doc_ref.set({
        "type": source_type,
        "updated_at": datetime.utcnow(),
        "blocked": False
    }, merge=True)

def get_all_ids(source_type):
    docs = db.collection("line_sources").where("type", "==", source_type).where("blocked", "==", False).stream()
    return [doc.id for doc in docs]

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    reply_token = event.reply_token
    source_id = getattr(event.source, "user_id", getattr(event.source, "group_id", "unknown"))
    source_type = "user" if hasattr(event.source, "user_id") else "group"

    save_source_id_firestore(source_id, source_type)

    if not text.startswith("#"):
        line_bot_api.reply_message(reply_token, TextSendMessage(text="請輸入 #指令 來執行任務"))
        return

    try:
        resp = requests.post(B_API_URL, json={
            "task": text[1:].strip(),
            "source_id": source_id,
            "source_type": source_type,
            "original_text": text
        }, timeout=10)
        result = resp.json().get("result", "❌ 專案B未回傳結果")
    except Exception as e:
        result = f"❌ 呼叫任務API失敗：{e}"

    line_bot_api.reply_message(reply_token, TextSendMessage(text=result))

@app.route("/push", methods=["POST"])
def push_message():
    data = request.json
    to = data.get("to")
    msg_type = data.get("type", "text")
    content = data.get("content")

    try:
        if to == "all_users":
            targets = get_all_ids("user")
        elif to == "all_groups":
            targets = get_all_ids("group")
        else:
            targets = [to]

        sent_ids = []
        for tid in targets:
            try:
                if msg_type == "text":
                    line_bot_api.push_message(tid, TextSendMessage(text=content))
                elif msg_type == "image":
                    line_bot_api.push_message(tid, ImageSendMessage(
                        original_content_url=content,
                        preview_image_url=content
                    ))
                logging.info(f"PUSH SUCCESS - to: {tid}, type: {msg_type}")
                sent_ids.append(tid)
            except Exception as e:
                logging.error(f"PUSH FAILED - to: {tid}, error: {str(e)}")

        return {"status": "success", "sent_to": sent_ids}, 200

    except Exception as e:
        logging.error(f"PUSH ERROR - {str(e)}")
        return {"status": "error", "message": str(e)}, 500

# === 管理後台功能整合 ===

from flask import Flask, render_template_string, request, redirect, url_for, session
import os

# === 初始化 Flask App ===
app.secret_key = "supersecret"

# === 初始化 Firebase ===

# === 登入檢查 ===
def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == "lcm171101" and request.form.get("password") == "Mm60108511":
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            return "登入失敗"
    return render_template_string("""
        <form method="post">
            <h2>登入管理系統</h2>
            使用者名稱：<input type="text" name="username"><br>
            密碼：<input type="password" name="password"><br>
            <button type="submit">登入</button>
        </form>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# === 用戶列表畫面 ===
@app.route("/admin")
@require_login
def admin():
    docs = db.collection("line_sources").stream()
    users = [
        {
            "id": doc.id,
            "type": doc.to_dict().get("type"),
            "blocked": doc.to_dict().get("blocked", False),
            "updated_at": doc.to_dict().get("updated_at")
        }
        for doc in docs
    ]
    return render_template_string("""
    <h2>LINE 使用者/群組管理</h2>
    <table border=1 cellpadding=8>
        <tr><th>ID</th><th>類型</th><th>更新時間</th><th>封鎖狀態</th><th>操作</th></tr>
        {% for u in users %}
        <tr>
            <td>{{ u.id }}</td>
            <td>{{ u.type }}</td>
            <td>{{ u.updated_at }}</td>
            <td>{{ '✅' if u.blocked else '❌' }}</td>
            <td>
                {% if not u.blocked %}
                <a href="{{ url_for('block_user', uid=u.id) }}">封鎖</a>
                {% else %}
                <a href="{{ url_for('unblock_user', uid=u.id) }}">解鎖</a>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    <br><a href="/logs">查看推播日誌</a> | <a href="/logout">登出</a>
    """, users=users)

@app.route("/block/<uid>")
@require_login
def block_user(uid):
    db.collection("line_sources").document(uid).update({"blocked": True})
    return redirect(url_for("admin"))

@app.route("/unblock/<uid>")
@require_login
def unblock_user(uid):
    db.collection("line_sources").document(uid).update({"blocked": False})
    return redirect(url_for("admin"))

@app.route("/logs")
@require_login
def logs():
    try:
        with open("push_log.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()[-100:]
    except FileNotFoundError:
        lines = ["尚未產生日誌。"]
    return render_template_string("""
    <h2>推播日誌</h2>
    <pre style="background:#f4f4f4;padding:10px;border:1px solid #ccc">{{ log }}</pre>
    <a href="/admin">回管理頁</a>
    """, log="".join(lines))