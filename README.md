# LINE Bot 推播系統 (Flask + Firebase)

本專案為一個以 Flask 建立的 LINE Bot 推播平台，支援文字、圖片、圖片連結等訊息類型，並可從後台管理使用者、記錄推播日誌。

## 🚀 部署與啟動

### 1. 安裝套件
```bash
pip install -r requirements.txt
```

### 2. 啟動伺服器（本地開發）
```bash
python app.py
```

### 3. Render 部署指令
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`

### 4. 環境變數設定

| 變數名稱 | 說明 |
|----------|------|
| `LINE_CHANNEL_SECRET` | 你的 LINE Bot 密鑰 |
| `LINE_CHANNEL_ACCESS_TOKEN` | 推播 token |
| `FIREBASE_KEY_B64` | base64 編碼後的 Firebase 憑證 JSON |
| `PUSH_API_KEY` | 推播 API 安全驗證用 |

---

## 🔐 登入資訊

| 項目 | 資訊 |
|------|------|
| 使用者名稱 | `lcm171101` |
| 密碼 | `Mm60108511` |

---

## 📡 API 使用方式

### 1. 推播訊息 `/push`

以下是使用 `curl` 指令呼叫 API 的範例：

```
curl -X POST https://your-domain.com/push \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <你的 PUSH_API_KEY>" \
  -d "{\"to\":\"Uxxxxxxxxx\",\"type\":\"text\",\"content\":\"這是訊息\"}"
```


- Header:
  ```
  Content-Type: application/json
  X-API-KEY: <你的 PUSH_API_KEY>
  ```
- JSON Body 範例：


#### 📄 純文字
```bash
curl -X POST https://your-domain.com/push \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <你的 PUSH_API_KEY>" \
  -d '{ "to": "Uxxxxxxxxx", "type": "text", "content": "這是文字內容 https://example.com" }'
```

#### 🖼️ 圖片
```bash
curl -X POST https://your-domain.com/push \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <你的 PUSH_API_KEY>" \
  -d '{ "to": "Uxxxxxxxxx", "type": "image", "content": "https://example.com/image.jpg" }'
```

#### 🖼️+🔗 圖片連結
```bash
curl -X POST https://your-domain.com/push \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <你的 PUSH_API_KEY>" \
  -d '{ 
    "to": "Uxxxxxxxxx",
    "type": "image_link",
    "content": {
      "image": "https://example.com/image.jpg",
      "link": "https://example.com"
    }
  }'
```


## 🧪 測試與後台

| 路由 | 說明 |
|------|------|
| `/` | 健康檢查，回傳「我還活著」 |
| `/admin` | 使用者/群組管理 |
| `/logs` | 推播日誌 |
| `/push-test` | 推播測試表單 |
| `/callback` | LINE Webhook 接收點 |
| `/webhook` | 相容式 redirect 到 `/callback` |

---

## 🗃️ Firestore 結構

- `line_sources`：儲存 user_id / group_id、類型、封鎖狀態、更新時間
- `push_logs`：記錄每次推播的內容、對象、型別與時間

---

## 📷 Flex Message 限制提醒
- Flex 僅支援圖片搭配超連結
- 純文字中若要含可點連結，請用 `type: text` 且內容含 `https://`

---

## ✅ 健康檢查確認

部署後可用：
```
https://你的網址/
```
看到：
```
我還活著
```

---

## 📬 聯絡與授權

請依實際需求補充聯絡方式與授權條款。