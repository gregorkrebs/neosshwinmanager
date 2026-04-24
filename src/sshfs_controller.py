# sshfs_controller.py - Mount/unmount SSH drives using sshfs-win.
#
# Direkter WinFsp-Mount (kein Netzlaufwerk!):
#   - sshfs.exe mountet via WinFsp als lokales FUSE-Laufwerk
#   - WNetGetConnection() gibt None zurück (kein Netzlaufwerk)
#   - WNetCancelConnection2() schlägt fehl (Fehler 2250 = not connected)
#   - Unmount: sshfs.exe-Prozess für diesen Buchstaben finden und beenden
#   - Label: -ovolname=NAME setzt den Namen direkt via WinFsp

import subprocess
import os
import sys
import shutil
import time
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from src.config import Connection

SSHFS_EXE_PATHS = [
    r"C:\Program Files\SSHFS-Win\bin\sshfs.exe",
    r"C:\Program Files (x86)\SSHFS-Win\bin\sshfs.exe",
]
WINFSP_DLL_PATHS = [
    r"C:\Program Files\WinFsp",
    r"C:\Program Files (x86)\WinFsp",
]


@dataclass
class MountResult:
    success: bool
    message: str


def _find_sshfs_exe() -> str | None:
    for p in SSHFS_EXE_PATHS:
        if os.path.exists(p):
            return p
    return shutil.which("sshfs")


def _has_winfsp() -> bool:
    return any(os.path.isdir(p) for p in WINFSP_DLL_PATHS)


def _drive_letter_in_use(drive_letter: str) -> bool:
    letter = drive_letter.strip("\\").upper()
    if not letter.endswith(":"):
        letter += ":"
    idx = ord(letter[0]) - ord('A')
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    return bool(bitmask & (1 << idx))


def _find_sshfs_pid_for_drive(drive_letter: str) -> int | None:
    """
    Findet die PID des sshfs.exe-Prozesses der diesen Laufwerksbuchstaben mounted.
    Sucht in der CommandLine nach dem Buchstaben (z.B. 'F:').
    Nutzt WMI via PowerShell – zuverlässig ohne externe Abhängigkeiten.
    """
    letter = drive_letter.rstrip("\\").rstrip(":").upper()
    try:
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                f"Get-CimInstance Win32_Process -Filter \"Name='sshfs.exe'\" "
                f"| Where-Object {{ $_.CommandLine -match ' {letter}:' }} "
                f"| Select-Object -ExpandProperty ProcessId"
            ],
            capture_output=True, text=True, timeout=8,
            creationflags=0x08000000,
        )
        pid_str = result.stdout.strip()
        if pid_str.isdigit():
            return int(pid_str)
        # Mehrere PIDs
        for line in pid_str.splitlines():
            if line.strip().isdigit():
                return int(line.strip())
    except Exception:
        pass
    return None


class SSHFSController:

    @staticmethod
    def check_sshfs_win_installed() -> bool:
        return _find_sshfs_exe() is not None

    @staticmethod
    def get_install_status() -> dict:
        sshfs_exe = _find_sshfs_exe()
        return {
            "winfsp": _has_winfsp(),
            "sshfs_win": sshfs_exe is not None,
            "sshfs_exe": sshfs_exe,
        }

    # ------------------------------------------------------------------
    # Mount
    # ------------------------------------------------------------------

    def mount(self, conn: Connection) -> MountResult:
        """Nur sshfs.exe direkt – erzeugt ein lokales WinFsp-Laufwerk."""
        result = self._mount_direct(conn)
        if result.success:
            self._set_drive_label(conn)
        return result

    def _mount_direct(self, conn: Connection) -> MountResult:
        sshfs_exe = _find_sshfs_exe()
        if not sshfs_exe:
            return MountResult(False, "sshfs.exe nicht gefunden. Bitte SSHFS-Win installieren.")

        letter = conn.drive_letter.rstrip("\\").rstrip(":")
        remote = f"{conn.user}@{conn.host}:{conn.remote_path or '/'}"
        sshfs_bin_dir = os.path.dirname(sshfs_exe)

        # volname setzt den Label direkt in WinFsp – kein Registry-Trick nötig
        safe_name = conn.name[:32].replace("=", "_").replace(",", "_")

        cmd = [
            sshfs_exe,
            remote,
            f"{letter}:",
            f"-p{conn.port}",
            f"-ovolname={safe_name}",
            "-odebug",
            "-ologlevel=debug1",
            "-oStrictHostKeyChecking=no",
            "-oUserKnownHostsFile=/dev/null",
            "-oreconnect",
            "-oServerAliveInterval=15",
            "-oServerAliveCountMax=3",
            # WinFsp: Mount dem aktuellen User voll zugänglich machen.
            # Ohne diese Options taucht das Laufwerk im Explorer auf, aber
            # der Zugriff auf Inhalte triggert UAC ("Zugriff verweigert").
            "-oidmap=user",
            "-ouid=-1",
            "-ogid=-1",
            "-oumask=000",
            "-ocreate_umask=000",
            "-odefault_permissions",
        ]

        if conn.auth_method == "key" and conn.key_path:
            key_path = conn.key_path.replace("\\", "/")
            cmd.append(f"-oIdentityFile={key_path}")
            cmd.append("-oBatchMode=yes")
            cmd.append("-oPreferredAuthentications=publickey")
        elif conn.auth_method in ("password", "ask") and conn.password:
            cmd.append("-oPreferredAuthentications=password,keyboard-interactive")
            cmd.append("-opassword_stdin")
        else:
            return MountResult(False, "Kein Passwort oder Key konfiguriert.")

        env = os.environ.copy()
        env["PATH"] = f"{sshfs_bin_dir};{env.get('PATH', '')}"

        try:
            from src.app_logger import logger
            logger.debug(f"sshfs cmd: {' '.join(cmd)}")

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=0x08000000,
            )

            if conn.auth_method in ("password", "ask") and conn.password:
                try:
                    logger.debug(f"Sende Passwort ({len(conn.password)} Zeichen) an sshfs stdin...")
                    proc.stdin.write((conn.password + "\n").encode("utf-8"))
                    proc.stdin.flush()
                except Exception as e:
                    logger.error(f"stdin Fehler: {e}")

            import threading
            debug_lines = []
            done = threading.Event()

            def _read_stderr():
                try:
                    for raw in proc.stderr:
                        line = raw.decode("utf-8", errors="replace").strip()
                        if not line:
                            continue
                        logger.debug(f"sshfs: {line}")
                        debug_lines.append(line)
                        if "service sshfs has been started" in line:
                            done.set()
                            return
                        for err in ["Permission denied", "Connection refused",
                                    "Connection reset", "No route to host",
                                    "mount point in use", "no such identity",
                                    "bad port", "read: ", "Unable to authenticate"]:
                            if err in line:
                                done.set()
                                return
                except Exception:
                    done.set()

            threading.Thread(target=_read_stderr, daemon=True).start()
            done.wait(timeout=30)

            full = "\n".join(debug_lines)
            full_lower = full.lower()

            if proc.poll() is None:
                time.sleep(0.5)
                if _drive_letter_in_use(f"{letter}:"):
                    return MountResult(True, f"Laufwerk {letter}: eingebunden (sshfs.exe)")
                time.sleep(2.0)
                if _drive_letter_in_use(f"{letter}:"):
                    return MountResult(True, f"Laufwerk {letter}: eingebunden (sshfs.exe)")

            if "no such identity" in full_lower:
                return MountResult(False, f"Private Key (IdentityFile) wurde nicht gefunden:\n{conn.key_path}")
            if "mount point in use" in full_lower:
                return MountResult(False, f"Laufwerksbuchstabe {letter}: ist bereits belegt (oder wird gerade getrennt).")
            if "permission denied" in full_lower or "unable to authenticate" in full_lower:
                return MountResult(False, "Authentifizierung fehlgeschlagen.\nBitte Passwort oder SSH-Key überprüfen.")
            if "connection refused" in full_lower:
                return MountResult(False, f"Verbindung abgelehnt ({conn.host}:{conn.port}).\nIst der SSH-Dienst auf dem Zielgerät aktiv?")
            if "connection reset" in full_lower or "read: " in full_lower:
                return MountResult(False,
                    f"Die Verbindung wurde unterbrochen oder zurückgesetzt ({conn.host}:{conn.port}).\n"
                    f"Mögliches Netzwerkproblem oder Firewall-Blockade.")
            return MountResult(False, full[-300:] or "Ein unbekannter Fehler in sshfs.exe ist aufgetreten.")

        except Exception as e:
            return MountResult(False, str(e))

    # ------------------------------------------------------------------
    # Label – für direkte WinFsp-Mounts
    # ------------------------------------------------------------------

    def _set_drive_label(self, conn: Connection, delay: float = 1.5):
        """
        Setzt das Laufwerks-Label.

        Bei direkten WinFsp-Mounts:
          - -ovolname= setzt es schon beim Mount → Backup via label.exe + DriveIcons
          - WNetGetConnection gibt None zurück → kein MountPoints2 Trick nötig/möglich

        Bei net use Mounts (Fallback):
          - WNetGetConnection gibt den UNC-Pfad zurück → MountPoints2 Key setzen
        """
        import winreg
        import threading

        letter = conn.drive_letter.rstrip("\\").rstrip(":")
        name = conn.name

        def _apply():
            if delay > 0:
                time.sleep(delay)

            from src.app_logger import logger

            # Prüfen ob direkter WinFsp-Mount oder net use
            actual_unc = self._get_actual_unc(letter)
            logger.debug(f"Label: WNetGetConnection({letter}:) = {actual_unc!r}")

            # 1. label.exe – funktioniert für beide Mount-Typen
            try:
                subprocess.run(
                    ["label", f"{letter}:", name],
                    capture_output=True, timeout=5, shell=True,
                    creationflags=0x08000000,
                )
                logger.debug(f"label.exe gesetzt: {letter}: = {name!r}")
            except Exception as e:
                logger.debug(f"label.exe Fehler: {e}")

            # 2. DriveIcons Registry – Explorer-Override (höchste Priorität)
            try:
                di_path = (
                    f"Software\\Microsoft\\Windows\\CurrentVersion\\"
                    f"Explorer\\DriveIcons\\{letter}\\DefaultLabel"
                )
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, di_path) as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, name)
                logger.debug(f"DriveIcons gesetzt: {letter} = {name!r}")
            except Exception as e:
                logger.debug(f"DriveIcons Fehler: {e}")

            # 3. MountPoints2 – nur wenn net use (actual_unc vorhanden)
            if actual_unc:
                mp_base = (
                    "Software\\Microsoft\\Windows\\CurrentVersion\\"
                    "Explorer\\MountPoints2"
                )
                try:
                    reg_key = actual_unc.replace("\\", "#")
                    with winreg.CreateKey(
                        winreg.HKEY_CURRENT_USER, f"{mp_base}\\{reg_key}"
                    ) as k:
                        winreg.SetValueEx(k, "_LabelFromReg", 0, winreg.REG_SZ, name)
                    logger.debug(f"MountPoints2 gesetzt: {reg_key} = {name!r}")
                except Exception as e:
                    logger.debug(f"MountPoints2 Fehler: {e}")

            # Shell benachrichtigen – NUR für diesen Buchstaben
            try:
                path_w = f"{letter}:\\".encode("utf-16le")
                ctypes.windll.shell32.SHChangeNotify(0x00000100, 0x0005, path_w, None)
                ctypes.windll.shell32.SHChangeNotify(0x00008000, 0x0000, None, None)
            except Exception:
                pass

        threading.Thread(target=_apply, daemon=True).start()

    @staticmethod
    def _get_actual_unc(drive_letter: str) -> str | None:
        """Liest UNC-Pfad via WNetGetConnection. Gibt None bei direkten WinFsp-Mounts."""
        try:
            letter = drive_letter.rstrip("\\").rstrip(":").upper() + ":"
            buf = ctypes.create_unicode_buffer(1024)
            buf_size = ctypes.c_ulong(1024)
            ret = ctypes.windll.mpr.WNetGetConnectionW(letter, buf, ctypes.byref(buf_size))
            if ret == 0:
                return buf.value
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Unmount – für direkte WinFsp-Mounts (kein WNetCancelConnection!)
    # ------------------------------------------------------------------

    def unmount(self, drive_letter: str) -> MountResult:
        letter = drive_letter.rstrip("\\")
        if not letter.endswith(":"):
            letter += ":"
        letter_up = letter.upper()
        drive_char = letter_up[0]

        try:
            from src.app_logger import logger
        except Exception:
            logger = None

        def log(msg):
            if logger:
                logger.debug(f"Unmount {letter_up}: {msg}")

        def verify(after_sec=0.5) -> bool:
            time.sleep(after_sec)
            return not _drive_letter_in_use(letter_up)

        log("Start unmount")

        # UNC vor Unmount lesen (für net use Mounts)
        unc_before = self._get_actual_unc(letter_up)
        is_network_mount = unc_before is not None
        log(f"Mount-Typ: {'net use' if is_network_mount else 'WinFsp direkt'} | UNC={unc_before!r}")

        def cleanup():
            self._cleanup_drive_label(letter_up, known_unc=unc_before)

        # ── Strategie A: Direkter WinFsp-Mount ──────────────────────────
        if not is_network_mount:
            # Schritt 1: sshfs.exe Prozess für diesen Buchstaben finden und beenden
            pid = _find_sshfs_pid_for_drive(drive_char)
            log(f"sshfs PID für {drive_char}: = {pid!r}")

            if pid:
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)],
                        capture_output=True, timeout=5,
                        creationflags=0x08000000,
                    )
                    log(f"PID {pid} beendet.")
                except Exception as e:
                    log(f"taskkill PID Fehler: {e}")

                if verify(1.5):
                    cleanup()
                    return MountResult(True, f"Laufwerk {letter_up} getrennt.")
            else:
                log("Kein sshfs-Prozess für diesen Buchstaben gefunden.")

            # Schritt 2: WinFsp launchctl als Fallback
            for winfsp_bin in [
                r"C:\Program Files\WinFsp\bin\launchctl.exe",
                r"C:\Program Files (x86)\WinFsp\bin\launchctl.exe",
            ]:
                if os.path.exists(winfsp_bin):
                    for cls in ["sshfs", "sshfs-win"]:
                        try:
                            subprocess.run(
                                [winfsp_bin, "stop", cls, drive_char],
                                capture_output=True, timeout=5,
                                creationflags=0x08000000,
                            )
                        except Exception:
                            pass

            if verify(1.0):
                cleanup()
                return MountResult(True, f"Laufwerk {letter_up} getrennt (launchctl).")

            # Schritt 3: Alle sshfs.exe Prozesse als letzter Ausweg
            # (nur wenn Schritt 1+2 nicht funktionierten)
            log("Beende alle sshfs-Prozesse als Fallback...")
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "sshfs.exe", "/T"],
                    capture_output=True, timeout=5,
                    creationflags=0x08000000,
                )
            except Exception:
                pass

            if verify(1.5):
                cleanup()
                return MountResult(True, f"Laufwerk {letter_up} getrennt (alle sshfs beendet).")

        # ── Strategie B: net use Mount ───────────────────────────────────
        else:
            mpr = ctypes.WinDLL('mpr.dll')
            for dw_flags in (1, 0):
                res = mpr.WNetCancelConnection2W(wintypes.LPCWSTR(letter_up), dw_flags, 1)
                log(f"WNetCancelConnection2W(flags={dw_flags}) = {res}")
                if res == 0 or verify(0.5):
                    cleanup()
                    return MountResult(True, f"Laufwerk {letter_up} getrennt (Windows API).")

            try:
                subprocess.run(
                    ["net", "use", letter_up, "/delete", "/yes"],
                    capture_output=True, timeout=10,
                    creationflags=0x08000000,
                )
            except Exception:
                pass

            if verify(0.5):
                cleanup()
                return MountResult(True, f"Laufwerk {letter_up} getrennt (net use).")

        return MountResult(
            False,
            f"Laufwerk {letter_up} konnte nicht getrennt werden.\n\n"
            "Alle Programme schließen die auf das Laufwerk zugreifen "
            "und erneut versuchen – oder Windows neu starten.",
        )

    # ------------------------------------------------------------------
    # Label Cleanup
    # ------------------------------------------------------------------

    def _cleanup_drive_label(self, drive_letter: str, known_unc: str | None = None):
        import winreg
        try:
            letter = drive_letter.rstrip("\\").rstrip(":")

            # DriveIcons NUR für diesen Buchstaben entfernen
            di_path = (
                f"Software\\Microsoft\\Windows\\CurrentVersion\\"
                f"Explorer\\DriveIcons\\{letter}"
            )
            self._delete_reg_key_recursive(winreg.HKEY_CURRENT_USER, di_path)

            # MountPoints2 nur wenn net use (UNC bekannt)
            if known_unc:
                mp_base = (
                    "Software\\Microsoft\\Windows\\CurrentVersion\\"
                    "Explorer\\MountPoints2"
                )
                try:
                    reg_key = known_unc.replace("\\", "#")
                    with winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER, mp_base, 0, winreg.KEY_ALL_ACCESS
                    ) as base_key:
                        self._delete_reg_key_recursive(base_key, reg_key)
                except Exception:
                    pass

            # Shell NUR für diesen Buchstaben benachrichtigen
            ctypes.windll.shell32.SHChangeNotify(
                0x00000080, 0x0005, f"{letter}:\\".encode("utf-16le"), None
            )
        except Exception:
            pass

    def _delete_reg_key_recursive(self, root, subkey):
        import winreg
        try:
            with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
                while True:
                    try:
                        child = winreg.EnumKey(key, 0)
                        self._delete_reg_key_recursive(key, child)
                    except OSError:
                        break
            winreg.DeleteKey(root, subkey)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def purge_all_stale_mounts(self):
        import winreg
        from src.app_logger import logger
        logger.info("Starte Registry-Purge für SSHFS...")
        try:
            mp_base = "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\MountPoints2"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, mp_base, 0, winreg.KEY_ALL_ACCESS) as base_key:
                    keys_to_delete = []
                    i = 0
                    while True:
                        try:
                            name = winreg.EnumKey(base_key, i)
                            if "sshfs" in name.lower():
                                keys_to_delete.append(name)
                            i += 1
                        except OSError:
                            break
                    for k in keys_to_delete:
                        self._delete_reg_key_recursive(base_key, k)
            except Exception:
                pass

            subprocess.run(["net", "use", "*", "/delete", "/y"],
                           capture_output=True, creationflags=0x08000000)
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
            logger.info("Purge abgeschlossen.")
            return True
        except Exception as e:
            logger.error(f"Purge Fehler: {e}")
            return False

    @staticmethod
    def restart_explorer():
        from src.app_logger import logger
        try:
            subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"],
                           capture_output=True, creationflags=0x08000000)
            time.sleep(1)
            subprocess.Popen(["explorer.exe"], creationflags=0x08000000)
            return True
        except Exception as e:
            logger.error(f"Explorer Neustart Fehler: {e}")
            return False

    def is_mounted(self, drive_letter: str) -> bool:
        return _drive_letter_in_use(drive_letter)

    def get_mounted_drives(self) -> dict:
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        return {
            f"{ch}:": ""
            for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            if bitmask & (1 << i)
        }
