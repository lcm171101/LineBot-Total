import firebase_admin
from firebase_admin import credentials, firestore
import os

if not firebase_admin._apps:
    cred = credentials.Certificate("inxtip-9c27a4f0b1c8.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_all_keywords():
    docs = db.collection("keywords").stream()
    return {doc.id: doc.to_dict().get("keywords", []) for doc in docs}

def update_keywords(task_name, keywords):
    db.collection("keywords").document(task_name).set({"keywords": keywords})

def delete_keywords(task_name):
    db.collection("keywords").document(task_name).delete()

def get_all_descriptions():
    docs = db.collection("descriptions").stream()
    return {doc.id: doc.to_dict().get("description", "") for doc in docs}

def update_description(task_name, description):
    db.collection("descriptions").document(task_name).set({"description": description})

def delete_description(task_name):
    db.collection("descriptions").document(task_name).delete()

def log_task(entry: dict):
    db.collection("logs").add(entry)

def export_logs():
    logs = db.collection("logs").order_by("timestamp").stream()
    return [doc.to_dict() for doc in logs]
