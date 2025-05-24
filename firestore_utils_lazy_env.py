import firebase_admin
from firebase_admin import credentials, firestore
import os, json, base64

_db = None

def get_db():
    global _db
    if _db is None:
        key_json = base64.b64decode(os.environ["FIREBASE_KEY"]).decode("utf-8")
        cred = credentials.Certificate(json.loads(key_json))
        firebase_admin.initialize_app(cred)
        _db = firestore.client()
    return _db

def get_all_keywords():
    docs = get_db().collection("keywords").stream()
    return {doc.id: doc.to_dict().get("keywords", []) for doc in docs}

def update_keywords(task_name, keywords):
    get_db().collection("keywords").document(task_name).set({"keywords": keywords})

def delete_keywords(task_name):
    get_db().collection("keywords").document(task_name).delete()

def get_all_descriptions():
    docs = get_db().collection("descriptions").stream()
    return {doc.id: doc.to_dict().get("description", "") for doc in docs}

def update_description(task_name, description):
    get_db().collection("descriptions").document(task_name).set({"description": description})

def delete_description(task_name):
    get_db().collection("descriptions").document(task_name).delete()

def log_task(entry: dict):
    get_db().collection("logs").add(entry)

def export_logs():
    logs = get_db().collection("logs").order_by("timestamp").stream()
    return [doc.to_dict() for doc in logs]
