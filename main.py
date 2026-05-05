"""
main.py - Entry point for NEO SSH-Win Manager.
"""

import sys
import os

# ── 0. SSH askpass helper (MUST BE FIRST, before anything else) ───────────
# When sshfs.exe needs a password, it calls this process with --pass-helper.
# We output the password and exit immediately.
# IMPORTANT: Before single_instance check, otherwise the helper would be detected
# as a second instance and exit without outputting the password.
if len(sys.argv) > 1 and sys.argv[1] == "--pass-helper":
    print(os.environ.get("SSH_PASSWORD", ""))
    sys.exit(0)

# ── 0.5 CLI-Modus ist nicht Sache der GUI-EXE ───────────────────────────────
# Eine --windowed EXE hat keine nutzbare stdin/stdout im Parent-Terminal.
# Für CLI-Zugriff existiert NeoSSHWinManager-cli.exe (console-subsystem).
if any(arg in sys.argv for arg in ("--connect-cli", "-connectssh")):
    import ctypes
    ctypes.windll.user32.MessageBoxW(
        None,
        "Für CLI-Zugriff bitte NeoSSHWinManager-cli.exe verwenden.\n\n"
        "Beispiel:\n  NeoSSHWinManager-cli.exe --connect-cli <key>",
        "SSH Win Manager – falscher Einstiegspunkt",
        0x30,  # MB_ICONWARNING
    )
    sys.exit(2)

# ── 1. Single-instance check (before QApplication and all others) ─────────────
from src.single_instance import ensure_single_instance
ensure_single_instance()

# ── 2. Now import everything else ────────────────────────────────
import ctypes
import json

# Ensure src/ is importable from project root
sys.path.insert(0, os.path.dirname(__file__))


def _is_admin() -> bool:
    """Check if the process is running with administrator rights."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _request_elevation() -> bool:
    """
    Restart the app with admin rights (UAC dialog).
    Returns True if the app was restarted (caller should exit).
    """
    if _is_admin():
        return False
    if "--no-elevate" in sys.argv:
        return False
    
    try:
        from src.config import get_config_path, AppSettings
        config_file = get_config_path()
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                settings = AppSettings.from_dict(data.get('settings', {}))
                if not settings.require_admin:
                    return False
    except Exception:
        pass
    
    try:
        params = " ".join(f'"{a}"' if " " in a else a for a in sys.argv[1:] if a != "--no-elevate")
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1  # SW_SHOWNORMAL
        )
        if ret > 32:
            return True
    except Exception:
        pass
    return False


from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from src.ui.theme import STYLESHEET, get_stylesheet
from src.ui.main_window import MainWindow
from src.database import init_db
from src.ui.dialogs.login_dialog import LoginDialog
from src.auth_manager import Session


def main():
    # Admin elevation only if permanently enabled in settings
    if os.name == "nt":
        try:
            from src.config import get_config_path, AppSettings
            config_file = get_config_path()
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    settings = AppSettings.from_dict(data.get('settings', {}))
                    if settings.require_admin and _request_elevation():
                        sys.exit(0)
        except Exception:
            pass

    # Enable HiDPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Windows taskbar icon fix (AppUserModelID)
    try:
        myappid = 'neo.sshwinmanager.v1.3.1.rev1'
        if os.name == 'nt':
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("NEO SSH-Win Manager")
    app.setApplicationDisplayName("NEO SSH-Win Manager")
    app.setApplicationVersion("1.3.1")
    app.setOrganizationName("NeoSSHWinManager")

    def get_resource_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(__file__), relative_path)

    for icon_file in ("app_icon.ico", "app_icon.png"):
        icon_path = get_resource_path(os.path.join("assets", icon_file))
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            break

    # Init logger AFTER QApplication (QObject requires QApplication to exist)
    from src.app_logger import init_logger, logger
    init_logger()
    logger.info("Application started (Standard Mode)")

    # Apply global stylesheet
    app.setStyleSheet(get_stylesheet("dark"))

    # Default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # ── 3. Database Initialization ────────────────────────────────
    init_db()

    # ── 3.5 Windows Auto-Login (wenn aktiviert) ────────────────────
    windows_user = os.environ.get("USERNAME", "").strip()
    if windows_user:
        from src.auth_manager import AuthManager, Session
        user_data = AuthManager.get_user_by_username(windows_user)
        if user_data:
            # Prüfe ob Auto-Login aktiviert ist für diesen Benutzer
            from src.database import get_connection
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT auto_login FROM app_settings WHERE user_id = ?",
                    (user_data["id"],)
                ).fetchone()
                auto_login_enabled = row and bool(row["auto_login"])
            
            if auto_login_enabled:
                logger.info(f"Windows Auto-Login: Benutzer '{windows_user}' gefunden.")
                # Für Auto-Login ohne Passwort können wir den Encryption Key nicht laden
                # Wir zeigen trotzdem den Login-Dialog, aber mit vorausgefülltem Benutzernamen
                # Der Benutzer muss nur das Passwort eingeben
            else:
                logger.debug(f"Auto-Login deaktiviert für '{windows_user}'")

    # ── 4. Login / Registration ──────────────────────────────────
    login_dlg = LoginDialog()
    if login_dlg.exec() != LoginDialog.DialogCode.Accepted:
        sys.exit(0)

    if not Session.is_logged_in():
        sys.exit(0)

    # Apply user's preferred language
    try:
        from src.auth_manager import UserConnectionManager
        from src.i18n import set_language
        ucm = UserConnectionManager(Session.current())
        user_settings = ucm.get_settings()
        set_language(user_settings.language)
        app.setStyleSheet(get_stylesheet(user_settings.theme))
    except Exception as e:
        logger.warning(f"Language/theme init failed: {e}")

    # Don't quit when the last window is hidden (tray support)
    app.setQuitOnLastWindowClosed(False)

    try:
        # Create and show main window (maximiert mit Titelleiste)
        window = MainWindow()
        window.showMaximized()

        sys.exit(app.exec())
    except Exception as e:
        import traceback
        err_msg = f"FATAL CRASH during startup/main loop: {e}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        with open("crash_report.txt", "w", encoding="utf-8") as f:
            f.write(err_msg)
        try:
            from src.app_logger import logger
            logger.error(err_msg)
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
