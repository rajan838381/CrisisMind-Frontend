"""Print everything stored in the SQL database:  python view_db.py"""
import sqlite3, sys
from database.database import DB_PATH
conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
print("Database:", DB_PATH)
for t in ("users", "incident_reports", "simulation_runs", "action_log"):
    rows = conn.execute(f"SELECT * FROM {t} ORDER BY id DESC LIMIT 20").fetchall()
    print(f"\n=== {t} ({conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]} rows) ===")
    for r in rows:
        d = dict(r); d.pop("password_hash", None); d.pop("password_salt", None)
        print(d)
