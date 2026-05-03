# database.py – SQLite-Datenbank für NEO SSH-Win Manager.
#
# Schema:
#   users       – App-eigene Benutzer (unabhängig von Windows-Accounts)
#   connections – SSH-Verbindungen, pro Benutzer getrennt
#   settings    – App-Einstellungen, pro Benutzer
#
# Passwörter:
#   - App-Passwort: PBKDF2-HMAC-SHA256 Hash (nie im Klartext)
#   - SSH-Passwörter: AES-256-GCM verschlüsselt mit user-spezifischem Key
#
# pip install cryptography

import sqlite3
import os
from pathlib import Path


def get_db_path() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    db_dir = Path(appdata) / "SSHWinManager"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "data.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    """Erstellt alle Tabellen falls sie noch nicht existieren."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,
                username    TEXT NOT NULL UNIQUE COLLATE NOCASE,
                pw_hash     TEXT NOT NULL,   -- PBKDF2 hex
                pw_salt     TEXT NOT NULL,   -- random salt hex
                enc_key_enc TEXT NOT NULL,   -- AES-key verschlüsselt mit user-pw
                enc_key_iv  TEXT NOT NULL,   -- IV für enc_key_enc
                is_admin    INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS connections (
                id           TEXT PRIMARY KEY,
                user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name         TEXT NOT NULL,
                host         TEXT NOT NULL,
                ssh_user     TEXT NOT NULL,
                remote_path  TEXT NOT NULL DEFAULT '/',
                port         INTEGER NOT NULL DEFAULT 22,
                auth_method  TEXT NOT NULL DEFAULT 'password',
                pw_enc       TEXT,   -- SSH-Passwort AES verschlüsselt (hex)
                pw_iv        TEXT,   -- IV für pw_enc (hex)
                key_path     TEXT,
                drive_letter TEXT NOT NULL DEFAULT 'Z:',
                sort_order   INTEGER NOT NULL DEFAULT 0,
                cli_access_enabled INTEGER NOT NULL DEFAULT 0,
                cli_access_key     TEXT UNIQUE,
                created_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                user_id                  TEXT PRIMARY KEY
                    REFERENCES users(id) ON DELETE CASCADE,
                start_with_windows       INTEGER DEFAULT 0,
                minimize_to_tray         INTEGER DEFAULT 1,
                check_interval_seconds   INTEGER DEFAULT 30,
                debug_mode               INTEGER DEFAULT 0,
                require_admin            INTEGER DEFAULT 0,
                use_putty                INTEGER DEFAULT 0,
                putty_path               TEXT    DEFAULT '',
                auto_login               INTEGER DEFAULT 0,  -- Windows Auto-Login
                auto_reconnect           INTEGER DEFAULT 1,  -- Beim Start automatisch reconnecten
                language                 TEXT    DEFAULT 'en',  -- UI Sprache (en, de)
                updated_at               TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS active_mounts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                conn_id     TEXT NOT NULL,
                mounted_at  TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, conn_id)
            );
        """)

        # Migration: Add CLI columns if they don't exist
        try:
            cursor = conn.execute("PRAGMA table_info(connections)")
            cols = [row[1] for row in cursor.fetchall()]
            if "cli_access_enabled" not in cols:
                conn.execute("ALTER TABLE connections ADD COLUMN cli_access_enabled INTEGER NOT NULL DEFAULT 0")
            if "cli_access_key" not in cols:
                conn.execute("ALTER TABLE connections ADD COLUMN cli_access_key TEXT UNIQUE")
        except Exception:
            pass

        # Migration: language column in app_settings
        try:
            cursor = conn.execute("PRAGMA table_info(app_settings)")
            cols = [row[1] for row in cursor.fetchall()]
            if "language" not in cols:
                conn.execute("ALTER TABLE app_settings ADD COLUMN language TEXT DEFAULT 'en'")
            if "theme" not in cols:
                conn.execute("ALTER TABLE app_settings ADD COLUMN theme TEXT DEFAULT 'dark'")
        except Exception:
            pass
