"""
config.py – Data models and path helpers for NEO SSH-Win Manager.

Passwords are stored in the SQLite database, AES-GCM encrypted with a
per-user key.  This module only provides the Connection / AppSettings
data classes and the legacy config-file path (used for the admin-
elevation check in main.py before the DB is initialised).
"""

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
    auth_method: str = "password"   # "password" | "key" | "ask"
    password: str = ""              # runtime only – never written to disk here
    key_path: str = ""
    putty_key_path: str = ""        # .ppk format key for PuTTY/plink
    drive_letter: str = "Z:"
    cli_access_enabled: bool = False
    cli_access_key: Optional[str] = None
    groups: str = ""                # Kommaseparierte Gruppen/Tags
    is_template: bool = False       # True = Template, False = normale Verbindung
    template_id: Optional[str] = None  # Referenz zu Template
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


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
    auto_login: bool = False
    auto_reconnect_mounts: bool = True
    language: str = "en"
    theme: str = "dark"
    allow_passwordless_key_auth: bool = False
    security_level: int = 0  # 0=Strict, 1=Keys, 2=Passwords
    allow_insecure_password_auth: bool = False
    telemetry_enabled: bool = False
    telemetry_prompt_shown: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        return cls(**{k: data.get(k, v) for k, v in asdict(cls()).items()})


# ---------------------------------------------------------------------------
# Legacy config file path
# (only used in main.py to read require_admin before the DB is open)
# ---------------------------------------------------------------------------

def get_config_dir() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    config_dir = Path(appdata) / "SSHWinManager"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    return get_config_dir() / "config.json"
