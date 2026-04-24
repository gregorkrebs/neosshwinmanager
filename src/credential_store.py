# credential_store.py – Sichere Passwortspeicherung via Windows Credential Manager.
#
# Statt Klartext in config.json wird das Passwort in den Windows Credential Manager
# gespeichert (gleicher Mechanismus wie Browser-Passwörter und WLAN-Schlüssel).
# Verschlüsselung durch Windows DPAPI – nur der angemeldete Benutzer kann es lesen.
#
# Voraussetzung:
#   pip install keyring
#
# Falls keyring nicht verfügbar ist (z.B. Linux-Build), fällt die Klasse
# transparent auf Klartext-Speicherung in config.json zurück – mit Warnung.

import sys

APP_NAME = "NeoSSHWinManager"

try:
    import keyring
    _KEYRING_AVAILABLE = True
except ImportError:
    _KEYRING_AVAILABLE = False


def save_password(conn_id: str, password: str) -> bool:
    """
    Passwort sicher im Windows Credential Manager speichern.
    Gibt True zurück wenn erfolgreich, sonst False (Fallback auf JSON).
    """
    if not _KEYRING_AVAILABLE or not password:
        return False
    try:
        keyring.set_password(APP_NAME, conn_id, password)
        return True
    except Exception as e:
        _warn(f"Passwort konnte nicht im Credential Manager gespeichert werden: {e}")
        return False


def load_password(conn_id: str) -> str:
    """
    Passwort aus dem Windows Credential Manager laden.
    Gibt '' zurück wenn nicht gefunden oder keyring nicht verfügbar.
    """
    if not _KEYRING_AVAILABLE:
        return ""
    try:
        pw = keyring.get_password(APP_NAME, conn_id)
        return pw or ""
    except Exception as e:
        _warn(f"Passwort konnte nicht aus Credential Manager geladen werden: {e}")
        return ""


def delete_password(conn_id: str) -> bool:
    """Passwort aus dem Credential Manager löschen (beim Löschen einer Verbindung)."""
    if not _KEYRING_AVAILABLE:
        return False
    try:
        keyring.delete_password(APP_NAME, conn_id)
        return True
    except Exception:
        # PasswordDeleteError oder KeyError wenn der Eintrag nicht existiert
        return True  # war schon nicht da – kein Fehler
    except Exception:
        return False


def is_available() -> bool:
    return _KEYRING_AVAILABLE


def _warn(msg: str):
    try:
        from src.app_logger import logger
        logger.warning(msg)
    except Exception:
        print(f"[WARN] {msg}", file=sys.stderr)
