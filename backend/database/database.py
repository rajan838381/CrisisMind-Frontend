"""
CrisisMind SQL layer (SQLite).
Schema lives in database/schema.sql and is applied on startup.
Set DATABASE_PATH in backend/.env to move the DB file.
"""
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"
DB_PATH = os.environ.get("DATABASE_PATH") or str(BASE_DIR.parent / "crisismind.db")
SESSION_DAYS = 7
PROFILE_FIELDS = ("city", "address", "blood_group", "emergency_contact_name", "emergency_contact_phone")


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        # migrate databases created by v4 (add profile columns if missing)
        have = {r["name"] for r in conn.execute("PRAGMA table_info(users)")}
        for col in PROFILE_FIELDS:
            if col not in have:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        if conn.execute("SELECT COUNT(*) FROM integrity_ledger").fetchone()[0] == 0:
            conn.executemany("INSERT INTO integrity_ledger VALUES (?,?,?,?,?,?,?)", SEED_BLOCKS)


SEED_BLOCKS = [
    (1, "10:31:02 UTC", "SYSTEM_BOOT: Multi-Crisis Node Online", "KERNEL_AI", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "GENESIS_00000000000000000000000000000000", "Verified"),
    (2, "10:31:15 UTC", "CRISIS_DETECTED: Thermal Runway Sector 7", "ACOUSTIC_ARRAY_9", "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "Verified"),
    (3, "10:33:40 UTC", "PREDICTION: Route Alpha Blockage in 18m", "CRISIS_PREDICTOR", "7d2b45ef1394a5303a74ef6f5287e07eb50974ad659c22d10330616b24de50b5", "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b", "Verified"),
    (4, "10:38:12 UTC", "ALERT: Hospital A Surge Pre-Warning", "CAP_DISPATCH", "9b882f07248bd8bc25b81a28a15998f804791fe65ea6a3449e0c7cc899605cb0", "7d2b45ef1394a5303a74ef6f5287e07eb50974ad659c22d10330616b24de50b5", "Verified"),
]


# ---------------------------------------------------------------- users / auth
def _hash_password(password: str, salt: Optional[str] = None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()
    return digest, salt


def _user_public(row) -> Dict[str, Any]:
    return {"id": row["id"], "name": row["name"], "email": row["email"], "phone": row["phone"],
            "role": row["role"], "createdAt": row["created_at"],
            "city": row["city"], "address": row["address"], "bloodGroup": row["blood_group"],
            "emergencyContactName": row["emergency_contact_name"],
            "emergencyContactPhone": row["emergency_contact_phone"]}


def update_profile(user_id: int, data: Dict[str, Any]):
    cols = {"name": "name", "phone": "phone", "city": "city", "address": "address", "bloodGroup": "blood_group",
            "emergencyContactName": "emergency_contact_name", "emergencyContactPhone": "emergency_contact_phone"}
    sets, vals = [], []
    for k, c in cols.items():
        if k in data and data[k] is not None:
            sets.append(f"{c}=?"); vals.append(str(data[k]).strip() or None)
    with connect() as conn:
        if sets:
            conn.execute(f"UPDATE users SET {', '.join(sets)} WHERE id=?", (*vals, user_id))
        return _user_public(conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())


def create_user(name: str, email: str, password: str, phone: Optional[str] = None, role: str = "operator", city: Optional[str] = None):
    pw_hash, salt = _hash_password(password)
    with connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (name,email,phone,role,city,password_hash,password_salt) VALUES (?,?,?,?,?,?,?)",
                (name.strip(), email.strip().lower(), phone, role, city, pw_hash, salt))
        except sqlite3.IntegrityError:
            return None
        return _user_public(conn.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone())


def verify_login(email: str, password: str):
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
        if not row:
            return None
        digest, _ = _hash_password(password, row["password_salt"])
        if not hmac.compare_digest(digest, row["password_hash"]):
            return None
        conn.execute("UPDATE users SET last_login_at=datetime('now') WHERE id=?", (row["id"],))
        return _user_public(row)


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(days=SESSION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    with connect() as conn:
        conn.execute("INSERT INTO sessions (token,user_id,expires_at) VALUES (?,?,?)", (token, user_id, expires))
    return token


def get_user_by_token(token: Optional[str]):
    if not token:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id "
            "WHERE s.token=? AND s.expires_at > datetime('now')", (token,)).fetchone()
        return _user_public(row) if row else None


def delete_session(token: str):
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))


# ---------------------------------------------------------------- reports / logs
def add_report(user_id: Optional[int], data: Dict[str, Any]):
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO incident_reports (user_id,category,title,description,severity,latitude,longitude,address) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (user_id, data["category"], data["title"], data.get("description"), data.get("severity", "medium"),
             data.get("latitude"), data.get("longitude"), data.get("address")))
        return _report(conn.execute("SELECT * FROM incident_reports WHERE id=?", (cur.lastrowid,)).fetchone())


def _report(r):
    return {"id": r["id"], "userId": r["user_id"], "category": r["category"], "title": r["title"],
            "description": r["description"], "severity": r["severity"], "latitude": r["latitude"],
            "longitude": r["longitude"], "address": r["address"], "status": r["status"], "createdAt": r["created_at"]}


def list_reports(user_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
    with connect() as conn:
        if user_id:
            rows = conn.execute("SELECT * FROM incident_reports WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM incident_reports ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [_report(r) for r in rows]


def delete_report(report_id: int, user_id: int) -> bool:
    with connect() as conn:
        return conn.execute("DELETE FROM incident_reports WHERE id=? AND user_id=?", (report_id, user_id)).rowcount > 0


def log_action(user_id: Optional[int], scenario: str, action: str, payload: Optional[dict] = None):
    with connect() as conn:
        conn.execute("INSERT INTO action_log (user_id,scenario,action,payload) VALUES (?,?,?,?)",
                     (user_id, scenario, action, json.dumps(payload or {})))


def list_actions(user_id: Optional[int] = None, limit: int = 100):
    with connect() as conn:
        q = "SELECT * FROM action_log " + ("WHERE user_id=? " if user_id else "") + "ORDER BY id DESC LIMIT ?"
        rows = conn.execute(q, (user_id, limit) if user_id else (limit,)).fetchall()
        return [{"id": r["id"], "scenario": r["scenario"], "action": r["action"],
                 "payload": json.loads(r["payload"] or "{}"), "createdAt": r["created_at"]} for r in rows]


def save_simulation(user_id: Optional[int], scenario: str, actions: dict, result: dict):
    with connect() as conn:
        conn.execute("INSERT INTO simulation_runs (user_id,scenario,actions,baseline_risk,simulated_risk) VALUES (?,?,?,?,?)",
                     (user_id, scenario, json.dumps(actions), result.get("baseline_risk"), result.get("simulated_risk")))


def list_simulations(user_id: int, limit: int = 50):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM simulation_runs WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
        return [{"id": r["id"], "scenario": r["scenario"], "actions": json.loads(r["actions"]),
                 "baselineRisk": r["baseline_risk"], "simulatedRisk": r["simulated_risk"], "createdAt": r["created_at"]} for r in rows]


# ---------------------------------------------------------------- ledger / scenario data
def get_ledger_records():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM integrity_ledger ORDER BY block_number DESC").fetchall()
    return [{"blockNumber": r["block_number"], "timestamp": r["timestamp"], "action": r["action"], "actor": r["actor"],
             "payloadHash": r["payload_hash"], "previousHash": r["previous_hash"], "status": r["status"]} for r in rows]

def get_scenario_data(scenario_id: str):
    return {
        "scenario": scenario_id,
        "title": "Industrial Solvent & Battery Chemical Fire",
        "current_risk": 78,
        "risk_severity": "HIGH",
        "recommended_route": "Route Bravo",
        "avoid_route": "Route Alpha",
        "backup_route": "Route Charlie",
        "why": "Route Alpha predicted blockage in 18-22 min due to heavy toxic plume.",
        "ai_action": "Deploy F02 via Route B + prepare Hospital B + open Shelter 2",
        "expected_result": "Risk 78 -> 49 | ETA 14 -> 8 min (-43%)"
    }

def get_cascade_nodes(scenario_id: str):
    return [
        {"id": "c-fire", "label": "Chemical Warehouse Fire", "severity": 95, "next": ["c-plume", "c-power"]},
        {"id": "c-plume", "label": "Toxic Vapor Drift", "severity": 78, "next": ["c-road"]},
        {"id": "c-road", "label": "Route A Gridlock", "severity": 62, "next": ["c-ambulance"]},
        {"id": "c-ambulance", "label": "Ambulance Delay", "severity": 55, "next": ["c-er"]},
        {"id": "c-er", "label": "Hospital Trauma Saturation", "severity": 48, "next": []}
    ]
