from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os
import pytz
import requests

# === 初始化 Flask App ===
app = Flask(__name__)
app.secret_key = "supersecret"

# === 初始化 Firebase ===
if not firebase_admin._apps:
    import base64
from io import StringIO
import json

firebase_b64 = os.environ.get("FIREBASE_KEY_B64")
firebase_json = base64.b64decode(firebase_b64).decode("utf-8")
cred = credentials.Certificate(json.load(StringIO(firebase_json)))
firebase_admin.initialize_app(cred)
db = firestore.client()

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
    to = request.form.get("to")
    msg_type = request.form.get("type")

    if msg_type == "image_link":
        content = {
            "image": request.form.get("image_url"),
            "link": request.form.get("link_url")
        }
    else:
        content = request.form.get("content")

    from flask import json
    with app.test_request_context("/push", method="POST",
                                  json={"to": to, "type": msg_type, "content": content},
                                  headers={"X-API-KEY": os.environ.get("PUSH_API_KEY")}):
("/push", method="POST", json={"to": to, "type": msg_type, "content": content}, headers={"X-API-KEY": os.environ.get("PUSH_API_KEY")}):
            resp = push()
            result = resp[0].get_json() if isinstance(resp, tuple) else resp.get_json()
            message = json.dumps(result, ensure_ascii=False, indent=2)

    return render_template_string("""
    <h2>推播測試工具</h2>
    <form method="post">
        推播對象：<input name="to" placeholder="user_id / group_id / all_users / all_groups"><br>
        類型：
        <select name="type">
            <option value="text">文字</option>
            <option value="image">圖片</option>
        </select><br>
        內容：<input name="content" placeholder="文字內容或圖片 URL"><br>
        <button type="submit">推播</button>
    </form>
    {% if message %}
    <h3>結果</h3>
    <pre style="background:#eef;padding:10px;border:1px solid #ccc">{{ message }}</pre>
    {% endif %}
    <a href="/admin">回管理頁</a>
    """, message=message)

from flask import abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import FollowEvent, JoinEvent
from linebot.exceptions import InvalidSignatureError

line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    print("[Webhook] Payload received:\n", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    from datetime import datetime
    db.collection("line_sources").document(user_id).set({
        "type": "user",
        "blocked": False,
        "updated_at": datetime.now(pytz.timezone("Asia/Taipei"))
    })

@handler.add(JoinEvent)
def handle_join(event):
    group_id = event.source.group_id
    from datetime import datetime
    db.collection("line_sources").document(group_id).set({
        "type": "group",
        "blocked": False,
        "updated_at": datetime.now(pytz.timezone("Asia/Taipei"))
    })

@app.route("/webhook", methods=["POST"])
def webhook_compat():
    from flask import redirect
    return redirect("/callback", code=307)