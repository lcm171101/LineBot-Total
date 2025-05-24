# 專案 A：LINE Bot Proxy（任務轉接機器人）

本專案負責接收 LINE 使用者訊息，將任務指令轉發給任務 API 中心（專案 B），並將處理結果回覆給 LINE 使用者。

---

## 🧠 功能簡介

- ✅ 接收 LINE webhook 訊息
- ✅ 偵測以 `#` 開頭的任務指令（例如 `#任務B`）
- ✅ 呼叫專案 B 的 `/api/execute_task` API
- ✅ 回傳執行結果給 LINE 使用者

---

## 📁 專案結構

```
專案資料夾/
├── app.py               # 主程式
├── requirements.txt     # 套件需求清單
```

---

## 🔑 環境變數設定（Render）

| 變數名稱 | 說明 |
|----------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot Access Token |
| `LINE_CHANNEL_SECRET`       | Channel Secret |
| `TASK_API_URL`              | 專案 B 任務 API 的網址（例如 https://task-api.onrender.com/api/execute_task） |

---

## 🌐 路由說明

| 路徑 | 方法 | 說明 |
|------|------|------|
| `/` | GET | 健康檢查（顯示 Bot 運作中） |
| `/webhook` | POST | 接收來自 LINE 的訊息並處理任務指令 |

---

## 🔁 呼叫流程

1. LINE 使用者傳送 `#任務B`
2. 本專案組成 POST 請求如下：

```json
POST {TASK_API_URL}
{
  "task": "任務B",
  "source_id": "Uxxxxxxxx",
  "source_type": "user",
  "original_text": "#任務B"
}
```

3. 將回傳的 `result` 欄位文字回覆給使用者

---

## ✅ 依賴套件

- `flask`
- `line-bot-sdk`
- `requests`
- `gunicorn`

---

## 📌 注意事項

- 請確保已將 `/webhook` 登記至 LINE Developers
- 請設定 `TASK_API_URL` 指向你的任務 API 中心（專案 B）

---

## 🔧 待擴充功能（可選）

- [ ] API Token 簽章驗證
- [ ] 群組權限控制
- [ ] 記錄任務執行歷程
