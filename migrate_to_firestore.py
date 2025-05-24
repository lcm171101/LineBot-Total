import json
from firestore_utils import update_keywords, update_description

def migrate_keywords():
    with open("task_keywords.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for task, keywords in data.items():
            update_keywords(task, keywords)
            print(f"✅ 上傳關鍵字：{task} → {keywords}")

def migrate_descriptions():
    with open("task_descriptions.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for task, desc in data.items():
            update_description(task, desc)
            print(f"✅ 上傳說明：{task} → {desc}")

if __name__ == "__main__":
    migrate_keywords()
    migrate_descriptions()
    print("🎉 所有任務資料已成功搬入 Firestore")
