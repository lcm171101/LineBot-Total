def run(event):
    from datetime import datetime
    weekday_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    today = datetime.now()
    return f"✅ 任務A 執行成功：今天是 {weekday_map[today.weekday()]} {today.strftime('%Y-%m-%d')}"