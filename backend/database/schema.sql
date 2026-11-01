-- CrisisMind SQL schema (SQLite). Auto-applied on backend startup by database.py.
-- Move to PostgreSQL/MySQL later by changing AUTOINCREMENT -> SERIAL / AUTO_INCREMENT.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    phone         TEXT,
    city          TEXT,
    address       TEXT,
    blood_group   TEXT,
    emergency_contact_name  TEXT,
    emergency_contact_phone TEXT,
    role          TEXT    NOT NULL DEFAULT 'operator',   -- operator | commander | citizen | admin
    password_hash TEXT    NOT NULL,
    password_salt TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    token       TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incident_reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    category    TEXT NOT NULL,                -- fire | flood | accident | chemical | crowd | storm | other
    title       TEXT NOT NULL,
    description TEXT,
    severity    TEXT NOT NULL DEFAULT 'medium', -- low | medium | high | critical
    latitude    REAL,
    longitude   REAL,
    address     TEXT,
    status      TEXT NOT NULL DEFAULT 'open',   -- open | verified | resolved
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS action_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    scenario    TEXT,
    action      TEXT NOT NULL,
    payload     TEXT,                          -- JSON string
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS simulation_runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER REFERENCES users(id) ON DELETE SET NULL,
    scenario      TEXT NOT NULL,
    actions       TEXT NOT NULL,               -- JSON string
    baseline_risk INTEGER,
    simulated_risk INTEGER,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS incidents (
    id         TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    severity   TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    epicenter  TEXT NOT NULL,
    status     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS integrity_ledger (
    block_number  INTEGER PRIMARY KEY,
    timestamp     TEXT NOT NULL,
    action        TEXT NOT NULL,
    actor         TEXT NOT NULL,
    payload_hash  TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    status        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_user  ON incident_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_actions_user  ON action_log(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
