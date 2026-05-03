# auth_manager.py – Benutzerverwaltung und Session für NEO SSH-Win Manager.
#
# Konzept:
#   - Benutzer registrieren sich mit Username + Passwort
#   - Login → Session (enc_key im Speicher, nie auf Disk im Klartext)
#   - Jeder Benutzer sieht nur seine eigenen Verbindungen
#   - Admin-Benutzer können andere Benutzer verwalten
#   - SSH-Passwörter werden mit dem benutzerspezifischen enc_key ver-/entschlüsselt

import uuid
import sqlite3
from dataclasses import dataclass, field
from typing import List, Optional

from src.database import get_connection
from src.crypto import (
    hash_password, verify_password, generate_enc_key,
    encrypt_key, decrypt_key, encrypt, decrypt, is_available
)
from src.config import Connection, AppSettings
from src.app_logger import logger


# ------------------------------------------------------------------
# Datenmodelle
# ------------------------------------------------------------------

@dataclass
class AppUser:
    id: str
    username: str
    is_admin: bool
    # enc_key wird NUR im RAM gehalten, nie persistiert
    _enc_key: bytes = field(default=b"", repr=False)

    @property
    def enc_key(self) -> bytes:
        return self._enc_key


# ------------------------------------------------------------------
# Session (Singleton – aktuell eingeloggter Benutzer)
# ------------------------------------------------------------------

class Session:
    _current_user: Optional[AppUser] = None

    @classmethod
    def login(cls, user: AppUser) -> None:
        cls._current_user = user
        logger.info(f"Benutzer eingeloggt: {user.username}")

    @classmethod
    def logout(cls) -> None:
        if cls._current_user:
            logger.info(f"Benutzer ausgeloggt: {cls._current_user.username}")
        cls._current_user = None

    @classmethod
    def current(cls) -> Optional[AppUser]:
        return cls._current_user

    @classmethod
    def is_logged_in(cls) -> bool:
        return cls._current_user is not None

    @classmethod
    def is_admin(cls) -> bool:
        return cls._current_user is not None and cls._current_user.is_admin


# ------------------------------------------------------------------
# Benutzerverwaltung
# ------------------------------------------------------------------

class AuthManager:

    @staticmethod
    def has_any_users() -> bool:
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()
            return row["c"] > 0

    @staticmethod
    def register(username: str, password: str, is_admin: bool = False) -> AppUser:
        """
        Neuen Benutzer registrieren.
        Beim ersten Benutzer wird is_admin automatisch True gesetzt.
        """
        if not is_available():
            raise RuntimeError(
                "cryptography nicht installiert.\n"
                "Bitte ausführen: pip install cryptography"
            )

        with get_connection() as conn:
            # Erster Benutzer wird automatisch Admin
            count = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
            if count == 0:
                is_admin = True

            pw_hash, salt = hash_password(password)
            enc_key = generate_enc_key()
            enc_key_enc, enc_key_iv = encrypt_key(enc_key, password, salt)
            user_id = str(uuid.uuid4())

            conn.execute(
                """INSERT INTO users
                   (id, username, pw_hash, pw_salt, enc_key_enc, enc_key_iv, is_admin)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, username.strip(), pw_hash, salt,
                 enc_key_enc, enc_key_iv, int(is_admin))
            )
            # Default-Einstellungen anlegen
            conn.execute(
                "INSERT INTO app_settings (user_id) VALUES (?)",
                (user_id,)
            )

        user = AppUser(
            id=user_id,
            username=username.strip(),
            is_admin=is_admin,
            _enc_key=enc_key,
        )
        logger.info(f"Benutzer registriert: {username} (admin={is_admin})")
        return user

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[AppUser]:
        """
        Login: Prüft Passwort und lädt den Encryption Key in den RAM.
        Returns None wenn Login fehlschlägt.
        """
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
                (username.strip(),)
            ).fetchone()

        if not row:
            logger.warning(f"Login fehlgeschlagen: Benutzer '{username}' nicht gefunden.")
            return None

        if not verify_password(password, row["pw_hash"], row["pw_salt"]):
            logger.warning(f"Login fehlgeschlagen: Falsches Passwort für '{username}'.")
            return None

        try:
            enc_key = decrypt_key(
                row["enc_key_enc"], row["enc_key_iv"],
                password, row["pw_salt"]
            )
        except Exception as e:
            logger.error(f"Encryption Key konnte nicht entschlüsselt werden: {e}")
            return None

        return AppUser(
            id=row["id"],
            username=row["username"],
            is_admin=bool(row["is_admin"]),
            _enc_key=enc_key,
        )

    @staticmethod
    def change_password(user_id: str, old_pw: str, new_pw: str) -> bool:
        """Passwort ändern und Encryption Key re-verschlüsseln."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()

        if not row or not verify_password(old_pw, row["pw_hash"], row["pw_salt"]):
            return False

        try:
            enc_key = decrypt_key(
                row["enc_key_enc"], row["enc_key_iv"],
                old_pw, row["pw_salt"]
            )
        except Exception:
            return False

        new_hash, new_salt = hash_password(new_pw)
        new_enc_key_enc, new_enc_key_iv = encrypt_key(enc_key, new_pw, new_salt)

        with get_connection() as conn:
            conn.execute(
                """UPDATE users SET pw_hash=?, pw_salt=?, enc_key_enc=?, enc_key_iv=?
                   WHERE id=?""",
                (new_hash, new_salt, new_enc_key_enc, new_enc_key_iv, user_id)
            )

        # Session-Key aktualisieren
        if Session.current() and Session.current().id == user_id:
            Session.current()._enc_key = enc_key

        logger.info(f"Passwort geändert für user_id={user_id}")
        return True

    @staticmethod
    def admin_reset_password(user_id: str) -> Optional[str]:
        """
        Admin-Reset: generiert neues Passwort + neuen enc_key für den User.
        Da der alte enc_key ohne altes Passwort nicht entschlüsselt werden kann,
        gehen vorhandene verschlüsselte SSH-Passwörter verloren. Diese Felder
        werden geleert; Key-Auth-Verbindungen bleiben funktionsfähig.

        Returns das neue Klartext-Passwort oder None wenn der User nicht existiert.
        """
        import secrets, string
        alphabet = string.ascii_letters + string.digits
        new_pw = ''.join(secrets.choice(alphabet) for _ in range(14))

        with get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if not row:
                return None

            new_hash, new_salt = hash_password(new_pw)
            new_enc_key = generate_enc_key()
            new_enc_key_enc, new_enc_key_iv = encrypt_key(new_enc_key, new_pw, new_salt)

            conn.execute(
                """UPDATE users SET pw_hash=?, pw_salt=?, enc_key_enc=?, enc_key_iv=?
                   WHERE id=?""",
                (new_hash, new_salt, new_enc_key_enc, new_enc_key_iv, user_id)
            )
            # Alte verschlüsselte SSH-Passwörter sind unlesbar → leeren
            conn.execute(
                "UPDATE connections SET pw_enc='', pw_iv='' WHERE user_id=?",
                (user_id,)
            )

        logger.warning(f"Admin-Reset: Passwort für user_id={user_id} neu generiert, SSH-Passwörter gelöscht.")
        return new_pw

    @staticmethod
    def delete_user(user_id: str) -> bool:
        """Benutzer und alle zugehörigen Verbindungen löschen (CASCADE)."""
        with get_connection() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return True

    @staticmethod
    def list_users() -> List[dict]:
        """Alle Benutzer auflisten (nur für Admins)."""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, username, is_admin, created_at FROM users ORDER BY username"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_user_by_username(username: str) -> Optional[dict]:
        """Sucht einen Benutzer anhand des Benutzernamens (für Windows Auto-Login)."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
                (username.strip(),)
            ).fetchone()
        return dict(row) if row else None


# ------------------------------------------------------------------
# Verbindungsverwaltung (mit Verschlüsselung)
# ------------------------------------------------------------------

class UserConnectionManager:
    """
    Verwaltet Verbindungen für den aktuell eingeloggten Benutzer.
    SSH-Passwörter werden transparent ver-/entschlüsselt.
    """

    def __init__(self, user: AppUser):
        self._user = user

    def _encrypt_pw(self, password: str) -> tuple[str, str]:
        if not password:
            return "", ""
        return encrypt(password, self._user.enc_key)

    def _decrypt_pw(self, pw_enc: str, pw_iv: str) -> str:
        if not pw_enc or not pw_iv:
            return ""
        try:
            val = decrypt(pw_enc, pw_iv, self._user.enc_key)
            logger.debug(f"SSH-Passwort für Verbindung erfolgreich entschlüsselt (Länge: {len(val)})")
            return val
        except Exception as e:
            logger.error(f"SSH-Passwort konnte nicht entschlüsselt werden: {e}")
            return ""

    def _row_to_conn(self, row) -> Connection:
        pw = self._decrypt_pw(row["pw_enc"] or "", row["pw_iv"] or "")
        return Connection(
            id=row["id"],
            name=row["name"],
            host=row["host"],
            user=row["ssh_user"],
            remote_path=row["remote_path"],
            port=row["port"],
            auth_method=row["auth_method"],
            password=pw,
            key_path=row["key_path"] or "",
            drive_letter=row["drive_letter"],
            cli_access_enabled=bool(row["cli_access_enabled"]),
            cli_access_key=row["cli_access_key"],
        )

    def get_all(self) -> List[Connection]:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM connections
                   WHERE user_id = ?
                   ORDER BY sort_order, name""",
                (self._user.id,)
            ).fetchall()
        return [self._row_to_conn(r) for r in rows]

    def get_by_id(self, conn_id: str) -> Optional[Connection]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM connections WHERE id = ? AND user_id = ?",
                (conn_id, self._user.id)
            ).fetchone()
        return self._row_to_conn(row) if row else None

    def get_by_cli_key(self, cli_key: str) -> Optional[Connection]:
        """Sucht eine Verbindung anhand des CLI-Keys (global)."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM connections WHERE cli_access_key = ? AND cli_access_enabled = 1",
                (cli_key,)
            ).fetchone()
        return self._row_to_conn(row) if row else None

    def add(self, c: Connection) -> Connection:
        if not c.id:
            c.id = str(uuid.uuid4())
        pw_enc, pw_iv = self._encrypt_pw(c.password)
        with get_connection() as conn:
            max_order = conn.execute(
                "SELECT COALESCE(MAX(sort_order), 0) FROM connections WHERE user_id = ?",
                (self._user.id,)
            ).fetchone()[0]
            conn.execute(
                """INSERT INTO connections
                   (id, user_id, name, host, ssh_user, remote_path, port,
                    auth_method, pw_enc, pw_iv, key_path, drive_letter, sort_order,
                    cli_access_enabled, cli_access_key)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (c.id, self._user.id, c.name, c.host, c.user, c.remote_path,
                 c.port, c.auth_method, pw_enc, pw_iv, c.key_path,
                 c.drive_letter, max_order + 1, int(c.cli_access_enabled), c.cli_access_key)
            )
        return c

    def update(self, c: Connection) -> bool:
        pw_enc, pw_iv = self._encrypt_pw(c.password)
        with get_connection() as conn:
            result = conn.execute(
                """UPDATE connections SET
                   name=?, host=?, ssh_user=?, remote_path=?, port=?,
                   auth_method=?, pw_enc=?, pw_iv=?, key_path=?, drive_letter=?,
                   cli_access_enabled=?, cli_access_key=?
                   WHERE id=? AND user_id=?""",
                (c.name, c.host, c.user, c.remote_path, c.port,
                 c.auth_method, pw_enc, pw_iv, c.key_path, c.drive_letter,
                 int(c.cli_access_enabled), c.cli_access_key,
                 c.id, self._user.id)
            )
        return result.rowcount > 0

    def delete(self, conn_id: str) -> bool:
        with get_connection() as conn:
            result = conn.execute(
                "DELETE FROM connections WHERE id=? AND user_id=?",
                (conn_id, self._user.id)
            )
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Einstellungen
    # ------------------------------------------------------------------

    def get_settings(self) -> AppSettings:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM app_settings WHERE user_id = ?",
                (self._user.id,)
            ).fetchone()
        if not row:
            return AppSettings()
        return AppSettings(
            start_with_windows=bool(row["start_with_windows"]),
            minimize_to_tray=bool(row["minimize_to_tray"]),
            check_interval_seconds=row["check_interval_seconds"],
            debug_mode=bool(row["debug_mode"]),
            require_admin=bool(row["require_admin"]),
            use_putty=bool(row["use_putty"]),
            putty_path=row["putty_path"] or "",
            auto_login=bool(row["auto_login"]) if "auto_login" in row.keys() else False,
            auto_reconnect_mounts=bool(row["auto_reconnect"]) if "auto_reconnect" in row.keys() else True,
            language=(row["language"] if "language" in row.keys() and row["language"] else "en"),
            theme=(row["theme"] if "theme" in row.keys() and row["theme"] else "dark"),
        )

    def save_settings(self, s: AppSettings) -> None:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO app_settings
                   (user_id, start_with_windows, minimize_to_tray,
                    check_interval_seconds, debug_mode, require_admin,
                    use_putty, putty_path, auto_login, auto_reconnect, language, theme, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
                   ON CONFLICT(user_id) DO UPDATE SET
                     start_with_windows=excluded.start_with_windows,
                     minimize_to_tray=excluded.minimize_to_tray,
                     check_interval_seconds=excluded.check_interval_seconds,
                     debug_mode=excluded.debug_mode,
                     require_admin=excluded.require_admin,
                     use_putty=excluded.use_putty,
                     putty_path=excluded.putty_path,
                     auto_login=excluded.auto_login,
                     auto_reconnect=excluded.auto_reconnect,
                     language=excluded.language,
                     theme=excluded.theme,
                     updated_at=excluded.updated_at""",
                (self._user.id,
                 int(s.start_with_windows), int(s.minimize_to_tray),
                 s.check_interval_seconds, int(s.debug_mode),
                 int(s.require_admin), int(s.use_putty), s.putty_path,
                 int(s.auto_login), int(s.auto_reconnect_mounts), s.language, s.theme)
            )

    # ------------------------------------------------------------------
    # Active Mounts Tracking (für Auto-Reconnect)
    # ------------------------------------------------------------------

    def add_active_mount(self, conn_id: str) -> None:
        """Markiert eine Verbindung als aktiv gemountet."""
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO active_mounts (user_id, conn_id)
                   VALUES (?, ?)
                   ON CONFLICT(user_id, conn_id) DO UPDATE SET
                   mounted_at = datetime('now')""",
                (self._user.id, conn_id)
            )

    def remove_active_mount(self, conn_id: str) -> None:
        """Entfernt eine Verbindung aus den aktiven Mounts."""
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM active_mounts WHERE user_id = ? AND conn_id = ?",
                (self._user.id, conn_id)
            )

    def get_active_mounts(self) -> List[str]:
        """Gibt Liste der aktiven Connection IDs zurück."""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT conn_id FROM active_mounts WHERE user_id = ?",
                (self._user.id,)
            ).fetchall()
        return [r["conn_id"] for r in rows]

    def clear_all_active_mounts(self) -> None:
        """Löscht alle aktiven Mounts (beim Logout)."""
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM active_mounts WHERE user_id = ?",
                (self._user.id,)
            )
