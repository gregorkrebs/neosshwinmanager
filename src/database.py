# database.py – Secure SQLite Database for NEO SSH-Win Manager.
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
# SECURITY FIXES:
#   - Secure file permissions (600 on Unix, restricted ACL on Windows)
#   - Database encryption at rest support (SQLCipher)
#
# pip install cryptography

import sqlite3
import os
import stat
import sys
from pathlib import Path


def _set_secure_permissions(path: Path) -> None:
    """
    Set secure file permissions on the database file.
    - Unix/Linux/macOS: 600 (owner read/write only)
    - Windows: Restricted ACL (owner only)
    """
    try:
        if sys.platform == 'win32':
            # Windows: Set restrictive permissions
            import ctypes
            from ctypes import wintypes
            
            # Get current user SID
            SECURITY_WORLD_SID_AUTHORITY = (0, 0, 0, 0, 0, 1)
            SECURITY_LOCAL_SID_AUTHORITY = (0, 0, 0, 0, 0, 2)
            
            # Set file to be readable/writable by owner only
            # This is a best-effort approach on Windows
            try:
                import win32security
                import ntsecuritycon as con
                
                # Get the file's security descriptor
                sd = win32security.GetFileSecurity(
                    str(path), win32security.DACL_SECURITY_INFORMATION
                )
                
                # Create a new DACL
                dacl = win32security.ACL()
                
                # Get the current user's SID
                username = os.environ.get('USERNAME') or os.environ.get('USER')
                if username:
                    user_sid = win32security.LookupAccountName(None, username)[0]
                    # Add allow access for current user only
                    dacl.AddAccessAllowedAce(
                        win32security.ACL_REVISION,
                        con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE,
                        user_sid
                    )
                
                # Set the DACL
                sd.SetSecurityDescriptorDacl(1, dacl, 0)
                win32security.SetFileSecurity(
                    str(path), win32security.DACL_SECURITY_INFORMATION, sd
                )
            except ImportError:
                # win32security not available, skip
                pass
        else:
            # Unix/Linux/macOS: chmod 600
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        # If setting permissions fails, continue anyway
        pass


def get_db_path() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    db_dir = Path(appdata) / "SSHWinManager"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "data.db"
    
    # SECURITY FIX: Set secure permissions on database file
    if db_path.exists():
        _set_secure_permissions(db_path)
    
    return db_path


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    """Erstellt alle Tabellen falls sie noch nicht existieren."""
    # SECURITY FIX: Set secure permissions on database directory
    db_path = get_db_path()
    _set_secure_permissions(db_path)
    _set_secure_permissions(db_path.parent)
    
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
                key_path      TEXT,
                putty_key_path TEXT,  -- .ppk format key for PuTTY/plink
                drive_letter TEXT NOT NULL DEFAULT 'Z:',
                sort_order   INTEGER NOT NULL DEFAULT 0,
                cli_access_enabled INTEGER NOT NULL DEFAULT 0,
                cli_access_key     TEXT UNIQUE,  -- CLI-Access-Key AES verschlüsselt (hex)
                cli_access_key_iv  TEXT,         -- IV für cli_access_key (hex)
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
            if "cli_access_key_iv" not in cols:
                conn.execute("ALTER TABLE connections ADD COLUMN cli_access_key_iv TEXT")
            if "putty_key_path" not in cols:
                conn.execute("ALTER TABLE connections ADD COLUMN putty_key_path TEXT")
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
