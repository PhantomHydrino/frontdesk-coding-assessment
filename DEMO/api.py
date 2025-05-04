from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
import sqlite3

app = FastAPI()
DB = "help_requests.db"

# ✅ Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # Allow the frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HelpRequest(BaseModel):
    id: str = None
    question: str
    caller_id: str
    status: str
    created_at: str
    resolved_at: str = None
    response: str = None

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS help_requests (
                id TEXT PRIMARY KEY,
                question TEXT,
                caller_id TEXT,
                status TEXT,
                created_at TEXT,
                resolved_at TEXT,
                response TEXT
            )
        ''')

@app.on_event("startup")
def startup():
    init_db()

@app.post("/help")
def create_help(request: HelpRequest):

    request.id = str(uuid4())
    with sqlite3.connect(DB) as conn:
        conn.execute('''
            INSERT INTO help_requests (id, question, caller_id, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (request.id, request.question, request.caller_id, request.status, request.created_at))
    return {"status": "created","id": request.id}

@app.get("/help")
def list_help_requests():
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM help_requests WHERE status != 'resolved'")
        rows = cur.fetchall()
    return rows

# @app.post("/resolve/{req_id}")
# def resolve_request(req_id: str, answer: str):
#     with sqlite3.connect(DB) as conn:
#         conn.execute('''
#             UPDATE help_requests
#             SET status = 'resolved', resolved_at = ?, response = ?
#             WHERE id = ?
#         ''', (datetime.utcnow().isoformat(), answer, req_id))
#     return {"status": "resolved"}



from knowledge_base import update_kb
from difflib import SequenceMatcher

THRESHOLD = 0.8  # similarity threshold
FREQ_REQUIRED = 3

def is_similar(a: str, b: str, threshold=THRESHOLD) -> bool:
    return SequenceMatcher(None, a, b).ratio() > threshold

@app.post("/resolve/{req_id}")
def resolve_request(req_id: str, answer: str):
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT question FROM help_requests WHERE id = ?", (req_id,))
        row = cur.fetchone()
        if not row:
            return {"status": "error", "message": "Request not found"}
        question = row[0]

        # Update the current request
        cur.execute('''
            UPDATE help_requests
            SET status = 'resolved', resolved_at = ?, response = ?
            WHERE id = ?
        ''', (datetime.utcnow().isoformat(), answer, req_id))

        # Check for similar answers for the same question
        cur.execute('''
            SELECT response FROM help_requests 
            WHERE question = ? AND status = 'resolved' AND response IS NOT NULL
        ''', (question,))
        responses = cur.fetchall()

        match_count = sum(1 for r in responses if is_similar(r[0], answer))

        if match_count + 1 >= FREQ_REQUIRED:
            update_kb(question, answer)
            print(f"✅ KB updated for: {question}")

        conn.commit()

    return {"status": "resolved", "matches": match_count + 1}

def create_help_request(question, caller_id):
    req_id = str(uuid4())
    payload = HelpRequest(
        id=req_id,
        question=question,
        caller_id=caller_id,
        status="pending",
        created_at=datetime.utcnow().isoformat()
    )
    create_help(payload)
    return req_id

def get_resolved_answer(req_id):
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT response FROM help_requests WHERE id=? AND status='resolved'", (req_id,))
        row = cur.fetchone()
        return row[0] if row else None
    
def mark_as_unresolved(request_id: str):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE help_requests SET status = 'unresolved' WHERE id = ?",
        (request_id,)
    )
    conn.commit()
    conn.close()
