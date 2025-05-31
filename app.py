from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os
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
    <form method="post" action="/create-id">
        <strong>手動建立 ID：</strong><br>
        ID：<input name="id"> 類型：
        <select name="type">
            <option value="user">user</option>
            <option value="group">group</option>
        </select>
        <button type="submit">新增</button>
    </form><br>
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
                {% endif %} |
                <a href="{{ url_for('delete_id', uid=u.id) }}" onclick="return confirm('確定要刪除這個 ID 嗎？');">刪除</a>
            </td>
        </tr>
        {% endfor %}
    </table>
    <br><a href="/logs">查看推播日誌</a> | <a href="/logout">登出</a>
    <br><a href="/push-test">前往推播測試</a>
    """, users=users)

@app.route("/create-id", methods=["POST"])
@require_login
def create_id():
    uid = request.form.get("id")
    utype = request.form.get("type")
    if uid and utype in ["user", "group"]:
        db.collection("line_sources").document(uid).set({
            "type": utype,
            "blocked": False
        }, merge=True)
    return redirect(url_for("admin"))

@app.route("/delete/<uid>")
@require_login
def delete_id(uid):
    db.collection("line_sources").document(uid).delete()
    return redirect(url_for("admin"))

@app.route("/push-test", methods=["GET", "POST"])
@require_login
def push_test():
    result = None
    if request.method == "POST":
        to = request.form.get("to")
        msg_type = request.form.get("type")
        content = request.form.get("content")
        try:
            server_url = request.host_url.rstrip("/")
            resp = requests.post(f"{server_url}/push", json={
                "to": to,
                "type": msg_type,
                "content": content
            })
            result = resp.json()
        except Exception as e:
            result = {"error": str(e)}

    return render_template_string("""
    <h2>推播測試</h2>
    <form method="post">
        推播對象 (user_id / group_id / all_users / all_groups):<br>
        <input type="text" name="to"><br>
        訊息類型：<select name="type">
            <option value="text">文字</option>
            <option value="image">圖片</option>
        </select><br>
        內容（文字或圖片網址）：<br>
        <input type="text" name="content" style="width: 400px"><br>
        <button type="submit">推播</button>
    </form>
    
    
    {% if result %}
        {% if result.error %}
            <h3 style="color:red;">❌ 發生錯誤：{{ result.error }}</h3>
        {% else %}
            <h3 style="color:green;">✅ 推播完成</h3>
            <ul>
            {% for k, v in result.result.items() %}
                <li>
                    <strong>{{ k }}</strong>：
                    {% if v == true %}
                        成功
                    {% else %}
                        <span style="color:red">錯誤：{{ v }}</span>
                    {% endif %}
                </li>
            {% endfor %}
            </ul>
        {% endif %}
    {% endif %}

    {% endif %}

    <br><a href="/admin">回管理頁</a>
    """, result=result)

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

@app.route("/push", methods=["POST"])
def push():
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
            elif msg_type == "image":
                line_bot_api.push_message(to_id, ImageSendMessage(original_content_url=content, preview_image_url=content))
            return True
        except Exception as e:
            return str(e)

    results = {}
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

    with open("push_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{now}] TO: {to} TYPE: {msg_type} CONTENT: {content}\n")

    return jsonify({"result": results})
