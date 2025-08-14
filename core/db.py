import json
import sqlite3
from typing import Dict, Any, List, Optional

_DB_PATH = "prescriptions.sqlite"

def _conn():
    return sqlite3.connect(_DB_PATH)

def init_db():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS prescriptions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                patient_age INTEGER,
                drugs_json TEXT,
                result_json TEXT,
                risk_score INTEGER,
                raw_text TEXT
            )"""
        )

def save_case(parsed: Dict[str, Any], result: Dict[str, Any], risk_score: int) -> int:
    with _conn() as c:
        cur = c.cursor()
        cur.execute(
            """INSERT INTO prescriptions(patient_age, drugs_json, result_json, risk_score, raw_text)
                   VALUES (?, ?, ?, ?, ?)""",
            (
                parsed.get("patient_age"),
                json.dumps(parsed.get("drugs", []), ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                int(risk_score),
                parsed.get("raw_text", "")[:4000]
            )
        )
        return cur.lastrowid

def list_cases() -> List[Dict[str, Any]]:
    with _conn() as c:
        rows = c.execute("SELECT id, ts, patient_age, risk_score FROM prescriptions ORDER BY id DESC").fetchall()
        return [
            {"id": r[0], "timestamp": r[1], "patient_age": r[2], "risk_score": r[3]}
            for r in rows
        ]

def get_case(case_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute("SELECT id, ts, patient_age, drugs_json, result_json, risk_score, raw_text FROM prescriptions WHERE id=?", (case_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "timestamp": row[1],
            "patient_age": row[2],
            "drugs": json.loads(row[3] or "[]"),
            "result": json.loads(row[4] or "{}"),
            "risk_score": row[5],
            "raw_text": row[6] or ""
        }
