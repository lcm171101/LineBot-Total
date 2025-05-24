from firestore_utils_lazy_env import update_keywords, update_description

# 建立任務A
update_keywords("任務A", ["任務A", "執行A", "今天星期幾"])
update_description("任務A", "任務A：顯示今天是星期幾")

# 建立任務B
update_keywords("任務B", ["任務B", "測試B", "執行B"])
update_description("任務B", "任務B：示範測試訊息")

print("✅ Firestore 已完成初始化！")
