import csv
from datetime import datetime
from linebot.models import SourceUser, SourceGroup

def write_csv_log(command, event, result, filename="task_log.csv"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_type = "User" if isinstance(event.source, SourceUser) else "Group"
    source_id = event.source.user_id if isinstance(event.source, SourceUser) else event.source.group_id

    row = [timestamp, command, source_id, source_type, result]

    with open(filename, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)
