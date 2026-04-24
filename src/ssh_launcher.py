# ssh_launcher.py – Starts an SSH terminal session.
#
# Supports two backends:
#   1. Windows native ssh.exe (default) – opens cmd.exe with ssh
#      Password auth: SSH_ASKPASS + SSH_ASKPASS_REQUIRE=force mechanism
#      The app itself is called with --pass-helper to print the password.
#   2. PuTTY (optional) – opens putty.exe directly, auto-login with password
#
# PuTTY notes:
#   - Password auth: putty -pw <password> user@host -P <port>
#   - Key auth:      putty -i <keyfile.ppk> user@host -P <port>

import os
import subprocess
import shutil
from src.config import Connection, AppSettings
from src.app_logger import logger


def launch_ssh_terminal(conn: Connection, settings: AppSettings) -> tuple[bool, str]:
    """
    Start an SSH terminal for the given connection.
    Returns (success, error_message).
    """
    if getattr(settings, 'use_putty', False) and getattr(settings, 'putty_path', ''):
        return _launch_putty(conn, settings.putty_path)
    else:
        return _launch_native_ssh(conn)


# ------------------------------------------------------------------
# Native ssh.exe (default)
# ------------------------------------------------------------------

def _launch_native_ssh(conn: Connection) -> tuple[bool, str]:
    """
    Open cmd.exe with ssh.

    Passwort-Auth: SSH_ASKPASS + SSH_ASKPASS_REQUIRE=force
    SSH ruft das askpass-Programm auf statt nach Terminal-Eingabe zu fragen.
    Das Passwort wird über SSH_PASSWORD in der Umgebung übergeben.
    """
    ssh_exe = _find_native_ssh()
    if not ssh_exe:
        return False, "ssh.exe nicht gefunden. Prüfe ob OpenSSH unter Windows installiert ist."

    ssh_cmd_parts = [
        f'"{ssh_exe}"',
        "-o StrictHostKeyChecking=no",
        f"-p {conn.port}",
    ]

    if conn.auth_method == "key" and conn.key_path:
        ssh_cmd_parts.append(f'-i "{conn.key_path}"')

    ssh_cmd_parts.append(f"{conn.user}@{conn.host}")
    ssh_cmd = " ".join(ssh_cmd_parts)
    full_cmd = f'start "{conn.name} SSH" cmd /k "{ssh_cmd}"'

    env = os.environ.copy()

    if conn.auth_method == "password" and conn.password:
        import sys
        is_frozen = getattr(sys, "frozen", False)
        if is_frozen:
            # Im kompilierten EXE-Modus: EXE direkt als askpass aufrufen
            askpass_cmd = f'"{sys.executable}" --pass-helper'
        else:
            # Im Entwicklungsmodus: Python + main.py aufrufen
            askpass_cmd = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}" --pass-helper'

        env["SSH_PASSWORD"] = conn.password
        env["SSH_ASKPASS"] = askpass_cmd
        env["SSH_ASKPASS_REQUIRE"] = "force"
        # DISPLAY muss gesetzt sein damit SSH_ASKPASS_REQUIRE greift (auch unter Windows)
        env["DISPLAY"] = "dummy:0"

    logger.debug(f"Native SSH cmd: {full_cmd}")
    try:
        subprocess.Popen(full_cmd, shell=True, env=env)
        return True, ""
    except Exception as e:
        return False, str(e)


def launch_ssh_in_current_terminal(conn_data: dict, exec_command: str = None):
    """
    Startet eine interaktive SSH-Shell direkt in diesem Terminal via Paramiko.
    Kein extra Fenster, kein ssh.exe-Subprozess, keine SSH_ASKPASS-Probleme.
    Wird für den CLI-Modus verwendet.
    """
    try:
        import paramiko
    except ImportError:
        print("Fehler: paramiko ist nicht installiert. Bitte 'pip install paramiko' ausführen.")
        return

    import sys
    import msvcrt
    import threading
    import ctypes
    import ctypes.wintypes

    # Windows Console Handles direkt über CONOUT$/CONIN$ öffnen –
    # GetStdHandle liefert bei GUI-EXE nach AttachConsole INVALID_HANDLE_VALUE.
    GENERIC_READ  = 0x80000000
    GENERIC_WRITE = 0x40000000
    FILE_SHARE_RW = 0x00000003
    OPEN_EXISTING = 3
    _hOut = ctypes.windll.kernel32.CreateFileW("CONOUT$", GENERIC_READ | GENERIC_WRITE, FILE_SHARE_RW, None, OPEN_EXISTING, 0, None)
    _hErr = _hOut
    _hIn  = ctypes.windll.kernel32.CreateFileW("CONIN$",  GENERIC_READ | GENERIC_WRITE,  FILE_SHARE_RW, None, OPEN_EXISTING, 0, None)

    # ANSI/VT-Sequenzen aktivieren, damit Farben/Escape-Codes vom Remote korrekt
    # gerendert werden (statt als ←[32m sichtbar zu bleiben).
    ENABLE_PROCESSED_OUTPUT            = 0x0001
    ENABLE_WRAP_AT_EOL_OUTPUT          = 0x0002
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    ENABLE_PROCESSED_INPUT             = 0x0001
    ENABLE_VIRTUAL_TERMINAL_INPUT      = 0x0200
    _old_out_mode = ctypes.wintypes.DWORD(0)
    _old_in_mode  = ctypes.wintypes.DWORD(0)
    ctypes.windll.kernel32.GetConsoleMode(_hOut, ctypes.byref(_old_out_mode))
    ctypes.windll.kernel32.GetConsoleMode(_hIn,  ctypes.byref(_old_in_mode))
    ctypes.windll.kernel32.SetConsoleMode(
        _hOut,
        _old_out_mode.value | ENABLE_PROCESSED_OUTPUT | ENABLE_WRAP_AT_EOL_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING,
    )
    ctypes.windll.kernel32.SetConsoleMode(
        _hIn,
        (_old_in_mode.value & ~ENABLE_PROCESSED_INPUT) | ENABLE_VIRTUAL_TERMINAL_INPUT,
    )

    def _con_write(handle, data: bytes):
        """Schreibt bytes direkt über WriteFile auf einen Windows-Console-Handle."""
        written = ctypes.wintypes.DWORD(0)
        ctypes.windll.kernel32.WriteFile(
            handle, data, len(data), ctypes.byref(written), None
        )

    def _write_stdout(data: bytes):
        _con_write(_hOut, data)

    def _write_stderr(data: bytes):
        _con_write(_hErr, data)

    host = conn_data.get("host", "")
    port = int(conn_data.get("port", 22))
    user = conn_data.get("user", "")
    auth_method = conn_data.get("auth_method", "password")
    password = conn_data.get("password", "")
    key_path = conn_data.get("key_path", "")

    _write_stdout(f"Verbinde mit {user}@{host}:{port} ...\r\n".encode())

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if auth_method == "key" and key_path:
            client.connect(host, port=port, username=user, key_filename=key_path, timeout=15)
        else:
            client.connect(host, port=port, username=user, password=password, timeout=15)
    except Exception as e:
        _write_stderr(f"Fehler: SSH-Verbindung fehlgeschlagen: {e}\r\n".encode())
        return

    # ── Non-interaktiver Modus: einzelnen Befehl ausführen und beenden ──
    if exec_command:
        try:
            stdin_, stdout_, stderr_ = client.exec_command(exec_command, timeout=30)
            out = stdout_.read()
            err = stderr_.read()
            if out:
                _write_stdout(out)
            if err:
                _write_stderr(err)
        except Exception as e:
            _write_stderr(f"Fehler beim Ausführen des Befehls: {e}\r\n".encode())
        finally:
            client.close()
        return

    # Interaktive Shell öffnen
    channel = client.invoke_shell(term="xterm-256color", width=220, height=50)
    channel.settimeout(0.0)

    stop_event = threading.Event()

    def write_all(data: bytes):
        while data:
            written = channel.send(data)
            data = data[written:]

    def stdin_to_channel():
        """Liest zeichenweise von der Windows-Konsole und schreibt zum SSH-Channel."""
        try:
            while not stop_event.is_set() and not channel.closed:
                try:
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch()
                        if ch in ('\x00', '\xe0'):
                            ch2 = msvcrt.getwch()
                            arrow_map = {
                                'H': b'\x1b[A',  # Up
                                'P': b'\x1b[B',  # Down
                                'M': b'\x1b[C',  # Right
                                'K': b'\x1b[D',  # Left
                            }
                            seq = arrow_map.get(ch2)
                            if seq:
                                write_all(seq)
                            else:
                                write_all(('\x00' + ch2).encode('utf-8', errors='replace'))
                        else:
                            write_all(ch.encode('utf-8', errors='replace'))
                    else:
                        import time
                        time.sleep(0.01)
                except Exception:
                    import time
                    time.sleep(0.01)
        except Exception:
            stop_event.set()

    stdin_thread = threading.Thread(target=stdin_to_channel, daemon=True)
    stdin_thread.start()

    try:
        while not channel.closed:
            # Ausgabe vom Server lesen und direkt in stdout schreiben
            if channel.recv_ready():
                data = channel.recv(4096)
                if not data:
                    break
                _write_stdout(data)
            elif channel.recv_stderr_ready():
                data = channel.recv_stderr(4096)
                if data:
                    _write_stderr(data)
            elif channel.exit_status_ready():
                # Noch verbleibende Daten lesen
                while channel.recv_ready():
                    data = channel.recv(4096)
                    if data:
                        _write_stdout(data)
                break
            else:
                import time
                time.sleep(0.01)
    except KeyboardInterrupt:
        channel.send(b'\x03')  # Ctrl+C an remote senden
    finally:
        stop_event.set()
        channel.close()
        client.close()
        # Console-Mode wiederherstellen, damit die aufrufende Shell nicht im VT-Modus bleibt.
        try:
            ctypes.windll.kernel32.SetConsoleMode(_hOut, _old_out_mode.value)
            ctypes.windll.kernel32.SetConsoleMode(_hIn,  _old_in_mode.value)
        except Exception:
            pass


def _find_native_ssh() -> str | None:
    candidates = [
        r"C:\Windows\System32\OpenSSH\ssh.exe",
        r"C:\Windows\SysWOW64\OpenSSH\ssh.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return shutil.which("ssh")


# ------------------------------------------------------------------
# PuTTY
# ------------------------------------------------------------------

def _launch_putty(conn: Connection, putty_path: str) -> tuple[bool, str]:
    """Open PuTTY directly with appropriate flags."""
    if not os.path.exists(putty_path):
        return False, (
            f"PuTTY nicht gefunden unter:\n{putty_path}\n\n"
            "Bitte den Pfad in den Einstellungen korrigieren."
        )

    cmd = [putty_path, "-ssh", "-P", str(conn.port)]

    if conn.auth_method == "password" and conn.password:
        cmd += ["-pw", conn.password]

    elif conn.auth_method == "key" and conn.key_path:
        key_path = conn.key_path
        if not key_path.lower().endswith(".ppk"):
            logger.warning(
                f"PuTTY erwartet .ppk Schlüssel, gefunden: {key_path}\n"
                "Konvertiere mit PuTTYgen falls der Login fehlschlägt."
            )
        cmd += ["-i", key_path]

    cmd.append(f"{conn.user}@{conn.host}")

    logger.debug(f"PuTTY cmd: {' '.join(cmd)}")
    try:
        subprocess.Popen(cmd, creationflags=0x08000000)
        return True, ""
    except Exception as e:
        return False, str(e)
