"""
config.py – Data models and persistent configuration for NEO SSH-Win Manager.

Passwort-Sicherheit:
  - Passwörter werden im Windows Credential Manager gespeichert (DPAPI-verschlüsselt)
  - config.json enthält KEIN Klartext-Passwort mehr (nur einen Marker ob eines gesetzt ist)
  - Fallback auf Klartext wenn keyring nicht installiert ist (mit Warnung)
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from pathlib import Path


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Connection:
    name: str
    host: str
    user: str
    remote_path: str = "/"
    port: int = 22
    auth_method: str = "password"   # "password" | "key"
    password: str = ""              # Laufzeit-only; wird NICHT in JSON gespeichert
    key_path: str = ""
    drive_letter: str = "Z:"
    cli_access_enabled: bool = False
    cli_access_key: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        d = asdict(self)
        # Passwort NICHT in JSON speichern – nur Marker ob eines gesetzt ist
        has_pw = bool(d.get("password", ""))
        d["password"] = ""          # immer leer in Datei
        d["_has_password"] = has_pw # Marker damit UI weiß ob Passwort gesetzt
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Connection":
        defaults = {
            "port": 22,
            "auth_method": "password",
            "password": "",
            "key_path": "",
            "remote_path": "/",
            "drive_letter": "Z:",
            "cli_access_enabled": False,
            "cli_access_key": None,
            "id": str(uuid.uuid4()),
        }
        merged = {**defaults, **data}
        # _has_password ist kein Dataclass-Feld → entfernen
        merged.pop("_has_password", None)
        return cls(**{k: merged[k] for k in cls.__dataclass_fields__})


@dataclass
class AppSettings:
    start_with_windows: bool = False
    minimize_to_tray: bool = True
    auto_reconnect: bool = False
    auto_remount_on_lost: bool = True
    check_interval_seconds: int = 30
    debug_mode: bool = False
    require_admin: bool = False
    use_putty: bool = False
    putty_path: str = r"C:\Program Files\PuTTY\putty.exe"
    auto_login: bool = False  # Automatisch mit Windows-Account einloggen
    auto_reconnect_mounts: bool = True  # Beim Start aktive Mounts wiederherstellen
    language: str = "en"  # UI-Sprache: "en" oder "de"
    theme: str = "dark"  # UI-Theme: "dark" oder "light"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        return cls(**{k: data.get(k, v) for k, v in asdict(cls()).items()})


# ---------------------------------------------------------------------------
# Config file location
# ---------------------------------------------------------------------------

def get_config_dir() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    config_dir = Path(appdata) / "SSHWinManager"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


# ---------------------------------------------------------------------------
# Load / Save  (mit sicherer Passwort-Handhabung)
# ---------------------------------------------------------------------------

def load_config() -> tuple[List[Connection], AppSettings]:
    from src.credential_store import load_password, is_available, save_password

    path = get_config_path()
    if not path.exists():
        return [], AppSettings()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        connections = []
        migrated = False  # track if legacy plaintext passwords were found
        for c in data.get("connections", []):
            conn = Connection.from_dict(c)

            if is_available():
                # Passwort sicher aus Credential Manager laden
                pw = load_password(conn.id)
                if pw:
                    conn.password = pw
                else:
                    # Legacy: Klartext-Passwort noch in JSON → migrieren
                    legacy_pw = c.get("password", "")
                    if legacy_pw:
                        save_password(conn.id, legacy_pw)
                        conn.password = legacy_pw
                        migrated = True  # JSON muss neu geschrieben werden
            else:
                # Kein keyring → Klartext aus JSON (Legacy-Fallback mit Warnung)
                conn.password = c.get("password", "")
                _warn_no_keyring()

            connections.append(conn)

        settings = AppSettings.from_dict(data.get("settings", {}))

        # Sofort neu speichern wenn Legacy-Passwörter migriert wurden
        # → JSON-Datei enthält danach kein Klartext-Passwort mehr
        if migrated:
            _do_save(connections, settings)

        return connections, settings

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        _log_error(f"Konfiguration konnte nicht geladen werden: {e}")
        return [], AppSettings()


def save_config(connections: List[Connection], settings: AppSettings) -> None:
    from src.credential_store import save_password, is_available

    path = get_config_path()

    # Passwörter sicher speichern (vor dem JSON-Schreiben)
    for conn in connections:
        if conn.password and conn.auth_method == "password":
            if is_available():
                save_password(conn.id, conn.password)
            # else: Klartext bleibt in JSON (Legacy ohne keyring, to_dict liefert dann das pw)

    _do_save(connections, settings)


def _do_save(connections: List[Connection], settings: AppSettings) -> None:
    """Interne Hilfsfunktion: JSON schreiben ohne Keyring-Operationen.
    Wird für die Migration genutzt damit load_config direkt bereinigen kann."""
    path = get_config_path()
    data = {
        "connections": [c.to_dict() for c in connections],
        "settings": settings.to_dict(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def delete_connection_credentials(conn_id: str) -> None:
    """Beim Löschen einer Verbindung auch das Passwort aus dem Credential Manager entfernen."""
    from src.credential_store import delete_password
    delete_password(conn_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_no_keyring_warned = False


def _warn_no_keyring():
    global _no_keyring_warned
    if _no_keyring_warned:
        return
    _no_keyring_warned = True
    try:
        from src.app_logger import logger
        logger.warning(
            "keyring nicht installiert – Passwörter werden als Klartext in config.json gespeichert.\n"
            "Installiere keyring für sichere Speicherung: pip install keyring"
        )
    except Exception:
        pass


def _log_error(msg: str):
    try:
        from src.app_logger import logger
        logger.error(msg)
    except Exception:
        import sys
        print(f"[ERROR] {msg}", file=sys.stderr)
