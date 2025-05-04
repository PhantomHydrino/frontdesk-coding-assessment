import json

KB_PATH = "knowledge_base.json"

def load_kb():
    try:
        with open(KB_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_kb(kb):
    with open(KB_PATH, 'w') as f:
        json.dump(kb, f, indent=2)

def query_kb(question):
    kb = load_kb()
    return kb.get(question)

def update_kb(question, answer):
    kb = load_kb()
    kb[question] = answer
    save_kb(kb)
