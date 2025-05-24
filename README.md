# LINE 任務觸發 Bot 系統

這是一套使用 Python + Flask + LINE Bot SDK 實作的模組化任務觸發系統，支援：
- LINE 群組或個人發送 `#指令` 自動觸發任務
- 使用 JSON 關鍵字詞庫進行模糊比對與指令解析
- 每個任務獨立模組化（`tasks/task_*.py`）方便維護
- 自動記錄任務執行結果與狀態至 `task_log.csv`
- 提供前端網頁介面查看任務紀錄與關鍵字註冊表
- 可從 UI 表單新增任務與關鍵字，自動建立對應 Python 模組

---

## 📦 功能清單

| 功能模組 | 說明 |
|----------|------|
| `/webhook` | LINE Webhook 接收指令並即時回覆 |
| `/tasks` | 前端 UI 查看所有任務執行紀錄 |
| `/registry` | 顯示所有已註冊任務與關鍵字 |
| `/add_keyword` | 表單新增任務與關鍵字，自動產生模組 |

---

## 🗂 專案結構

```
linebot_task_trigger/
├── app.py                         # 主程式
├── task_logger.py                 # 記錄任務到 CSV
├── task_keywords.json             # 任務關鍵字詞庫（支援模糊比對）
├── task_log.csv                   # 任務執行歷史紀錄
├── tasks/                         # 任務邏輯模組（每個任務一個檔）
│   ├── task_a.py
│   ├── task_b.py
│   ├── ...
├── templates/                     # HTML UI 模板
│   ├── task_table.html            # 任務紀錄頁
│   ├── task_registry.html         # 關鍵字註冊頁
│   └── add_keyword.html           # 新增關鍵字表單
└── requirements.txt               # 套件需求
```

---

## 🚀 快速部署（Render）

1. 建立 GitHub Repository 並推送本專案內容
2. 到 [Render](https://render.com) 建立 Web Service
3. 設定如下：

| 設定項目 | 值 |
|----------|----|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Environment Variables | `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET` |

4. Webhook URL 設定為：
```
https://你的服務網址/webhook
```

---

## ✨ LINE 使用方式

| 用戶輸入內容 | 說明 |
|--------------|------|
| `#任務A` | 執行 task_a.py 中的邏輯 |
| `#啟動A` | 透過模糊比對執行任務A |
| `#執行任務E` | 若詞庫有對應，將自動載入 `task_e.py` |
| `#未知指令` | 回覆尚未支援 |

---

## 🆕 表單新增任務

- 訪問 `/add_keyword`
- 輸入任務名稱與關鍵字
- 自動寫入 `task_keywords.json`
- 並於 `tasks/` 中建立對應模組（例如：`task_e.py`）

---

## 📌 技術堆疊

- Python 3.11
- Flask + Gunicorn
- LINE Messaging API (Webhook 模式)
- Bootstrap 5（UI）
- JSON + CSV 檔案儲存

---

## 📝 授權
MIT License
