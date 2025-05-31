# LINE 推播管理系統

本系統為一個使用 Flask + Firebase Firestore 架構的 LINE 推播管理平台，提供後台登入、使用者管理、推播測試及日誌查詢等功能。

---

## 🔐 登入與驗證

- **登入頁 `/login`**
  - 使用固定帳號密碼（`lcm171101 / Mm60108511`）登入。
- **登出 `/logout`**
  - 清除 session。
- **權限保護**
  - 所有管理功能需登入（使用 `@require_login` 保護）。

---

## 👥 使用者/群組管理 `/admin`

- 顯示已儲存的 LINE user/group ID。
- 每筆資料包含：
  - ID
  - 類型（user/group）
  - 封鎖狀態（✅/❌）
  - 更新時間
- 操作功能：
  - ➕ 手動新增 ID（選擇 user/group）
  - 🔒 封鎖 ID（`/block/<uid>`）
  - 🔓 解鎖 ID（`/unblock/<uid>`）
  - ❌ 刪除 ID（`/delete/<uid>`）

---

## 📤 推播測試 `/push-test`

- 可推播至：
  - 單一 `user_id` 或 `group_id`
  - `all_users`
  - `all_groups`
- 推播訊息類型：
  - `text`：文字訊息
  - `image`：圖片 URL
- 顯示推播結果（成功 ✅ / 失敗 ❌）

---

## 🔧 實際推播 API `/push`

- 使用 `LINE_CHANNEL_ACCESS_TOKEN` 傳送訊息。
- 判斷是否封鎖，決定是否推播。
- 支援格式：
  - `TextSendMessage`
  - `ImageSendMessage`

---

## 📝 推播日誌 `/logs`

- 顯示最近 100 筆推播紀錄（`push_log.txt`）
- 格式範例：
  ```
  [2025-05-31 00:55:37] TO: Uxxxxxxxx TYPE: text CONTENT: Hello world
  ```

---

## 🧱 Firestore 結構（collection: `line_sources`）

| 欄位       | 說明             |
|------------|------------------|
| `type`     | "user" 或 "group" |
| `blocked`  | 是否封鎖 (bool)   |
| `updated_at` | 更新時間 (timestamp) |

---

## 📦 套件需求 `requirements.txt`

```txt
flask
firebase-admin
gunicorn
requests
line-bot-sdk==2.4.1
```

---

## 📁 啟動方式

```bash
python app.py
# 或部署到 Render 並設置環境變數：
# FIREBASE_KEY_B64 / LINE_CHANNEL_ACCESS_TOKEN
```

---