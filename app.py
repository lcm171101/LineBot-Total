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
        docs = db.collection("push_logs")             .order_by("timestamp", direction=firestore.Query.DESCENDING)             .limit(100).stream()
        lines = [
            f"[{doc.to_dict()['timestamp'].astimezone(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')}] "
            f"TO: {doc.to_dict().get('to')} TYPE: {doc.to_dict().get('type')} CONTENT: {doc.to_dict().get('content')}"
            for doc in docs
        ]
    except Exception as e:
        lines = [f"發生錯誤：{e}"]

    return render_template_string("""
<h2>推播日誌</h2>
<pre style="background:#f4f4f4;padding:10px;border:1px solid #ccc">{{ log }}</pre>
<a href="/admin">回管理頁</a>
""", log="\n".join(lines))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

@app.route("/push", methods=["POST"])
def push():
    # === API KEY 驗證 ===
    expected_key = os.environ.get("PUSH_API_KEY")
    client_key = request.headers.get("X-API-KEY")
    if not expected_key or client_key != expected_key:
        return jsonify({"error": "Unauthorized"}), 401

    from linebot import LineBotApi
    from linebot.models import TextSendMessage, ImageSendMessage
    import datetime

    channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not channel_access_token:
        return jsonify({"error": "LINE_CHANNEL_ACCESS_TOKEN not set"}), 500

    line_bot_api = LineBotApi(channel_access_token)

    data = request.get_json()
    to = data.get("to")
    msg_type = data.get("type")
    content = data.get("content")

    def send_message(to_id):
        try:
            if msg_type == "text":
                line_bot_api.push_message(to_id, TextSendMessage(text=content))

    elif msg_type == "image_link":
        from linebot.models import FlexSendMessage
        image_url = content.get("image")
        link_url = content.get("link")
        bubble = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            }
        }
        if link_url:
            bubble["hero"]["action"] = {
                "type": "uri",
                "uri": link_url
            }
        line_bot_api.push_message(to_id, FlexSendMessage(alt_text="圖片訊息", contents=bubble))

            elif msg_type == "image":
                line_bot_api.push_message(to_id, ImageSendMessage(original_content_url=content, preview_image_url=content))
            return True
        except Exception as e:
            return str(e)

    results = {}
    now = datetime.datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")

    if to in ["all_users", "all_groups"]:
        docs = db.collection("line_sources").stream()
        for doc in docs:
            doc_data = doc.to_dict()
            if doc_data.get("blocked", False):
                continue
            if (to == "all_users" and doc_data.get("type") == "user") or (to == "all_groups" and doc_data.get("type") == "group"):
                r = send_message(doc.id)
                results[doc.id] = r
    else:
        doc = db.collection("line_sources").document(to).get()
        if doc.exists and not doc.to_dict().get("blocked", False):
            r = send_message(to)
            results[to] = r
        else:
            results[to] = "Not found or blocked"

    db.collection("push_logs").add({
        "to": to,
        "type": msg_type,
        "raw": content,
        "content": content,
        "timestamp": datetime.datetime.now(pytz.timezone("Asia/Taipei"))
    })

    return jsonify({"result": results})
@app.route("/admin", methods=["GET", "POST"])
@require_login
def admin():
    message = ""
    if request.method == "POST":
        new_id = request.form.get("new_id")
        new_type = request.form.get("new_type")
        from datetime import datetime
        db.collection("line_sources").document(new_id).set({
            "type": new_type,
            "blocked": False,
            "updated_at": datetime.now(pytz.timezone("Asia/Taipei"))
        })
        message = f"已新增：{new_id}"

    docs = db.collection("line_sources").stream()
    data = []
    for doc in docs:
        item = doc.to_dict()
        data.append({
            "id": doc.id,
            "type": item.get("type", "N/A"),
            "blocked": item.get("blocked", False),
            "updated_at": item.get("updated_at", "")
        })

    return render_template_string("""
    <h2>使用者/群組管理</h2>
    <form method="post">
        ➕ 新增 ID：
        <input name="new_id" placeholder="輸入 user_id 或 group_id">
        <select name="new_type">
            <option value="user">user</option>
            <option value="group">group</option>
        </select>
        <button type="submit">新增</button>
    </form>
    {% if message %}
    <p style="color:green">{{ message }}</p>
    {% endif %}
    <table border='1' cellpadding='5'>
        <tr>
            <th>ID</th><th>類型</th><th>封鎖</th><th>操作</th><th>更新時間</th>
        </tr>
        {% for d in data %}
        <tr>
            <td>{{ d.id }}</td>
            <td>{{ d.type }}</td>
            <td>{{ "✅" if not d.blocked else "❌" }}</td>
            <td>
                {% if d.blocked %}
                    <a href='/unblock/{{ d.id }}'>🔓 解鎖</a>
                {% else %}
                    <a href='/block/{{ d.id }}'>🔒 封鎖</a>
                {% endif %}
                | <a href='/delete/{{ d.id }}'>❌ 刪除</a>
            </td>
            <td>{{ d.updated_at }}</td>
        </tr>
        {% endfor %}
    </table>
    <a href="/push-test">前往推播測試</a> | <a href="/logs">查看日誌</a> | <a href="/logout">登出</a>
    """, data=data, message=message)
@app.route("/delete/<uid>")
@require_login
def delete_user(uid):
    db.collection("line_sources").document(uid).delete()
    return redirect(url_for("admin"))
@app.route("/push-test", methods=["GET", "POST"])
@require_login
def push_test():
    message = ""
    if request.method == "POST":
        to = request.form.get("to")
        msg_type = request.form.get("type")
        content = request.form.get("content")

        from flask import json
        with app.test_request_context("/push", method="POST", json={"to": to, "type": msg_type, "content": content}, headers={"X-API-KEY": os.environ.get("PUSH_API_KEY")}):
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