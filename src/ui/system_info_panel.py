"""
system_info_panel.py – System info panel for right panel.
Displays SSH-gathered stats in a layout matching the app design.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from src.ui.icons import icon as svg_icon

import subprocess
import os
import sys
import shutil
from src.config import Connection
from src.app_logger import logger
from src.i18n import tr

def _is_safe_file_path(path: str) -> bool:
    """
    Validate file path to prevent path traversal and command injection.
    """
    if not path or not isinstance(path, str):
        return False
    
    # Normalize path and check for traversal
    try:
        normalized = os.path.normpath(path)
    except Exception:
        return False
    
    if '..' in normalized or normalized.startswith('/..'):
        return False
    
    # Reject shell metacharacters
    dangerous = set(';|&`$(){}[]<>!\\"\'\n\r\t')
    if any(c in dangerous for c in path):
        return False
    
    return True


class SSHSystemInfoThread(QThread):
    """Fetches system info via SSH in background."""

    info_ready = pyqtSignal(dict)
    error = pyqtSignal(str, str)  # (error_msg, error_type) where error_type can be "key_missing" or "generic"

    def __init__(self, conn: Connection, settings=None):
        super().__init__()
        self._conn = conn
        self._settings = settings
        self._stopped = False

    def run(self):
        try:
            info = self._gather_info()
            if not self._stopped:
                self.info_ready.emit(info)
        except ValueError as e:
            # ValueError from _build_ssh_command when key is missing
            if not self._stopped:
                self.error.emit(str(e), "key_missing")
        except Exception as e:
            if not self._stopped:
                self.error.emit(str(e), "generic")

    def stop(self):
        self._stopped = True

    def _gather_info(self) -> dict:
        info = {
            "hostname": self._conn.host,
            "user": self._conn.user,
            "connected": False,
            "error": None,
        }

        ssh_client, client_type = self._find_ssh_client()
        if not ssh_client:
            info["error"] = "SSH client not found (ssh.exe or plink.exe)"
            return info

        # Build command based on client type
        if client_type == 'plink':
            cmd_base, target = self._build_plink_command(ssh_client)
        else:
            cmd_base, target = self._build_ssh_command(ssh_client)

        run_opts = {}
        if os.name == "nt":
            run_opts["creationflags"] = subprocess.CREATE_NO_WINDOW

        test_cmd = cmd_base + [target, "echo 'SSH_OK'"]
        try:
            result = subprocess.run(
                test_cmd, capture_output=True, text=True, timeout=15,
                env=self._get_ssh_env(), **run_opts
            )
            if "SSH_OK" not in result.stdout:
                info["error"] = result.stderr or result.stdout or "SSH connection failed"
                return info
        except subprocess.TimeoutExpired:
            info["error"] = "SSH connection timed out (15s)"
            return info
        except Exception as e:
            info["error"] = f"SSH error: {e}"
            return info

        info["connected"] = True

        commands = {
            "os": "cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"' || uname -s",
            "hostname": "hostname -f 2>/dev/null || hostname",
            "uptime": "uptime -p 2>/dev/null || uptime | awk '{print $3,$4}' | sed 's/,//g'",
            "uptime_seconds": "cat /proc/uptime 2>/dev/null | awk '{print $1}'",
            "last_seen": "who -b 2>/dev/null | awk '{print $3,$4}' | head -1",
            "cpu_model": "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2 | sed 's/^ //'",
            "cpu_cores": "nproc",
            "cpu_percent": "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//' 2>/dev/null || grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$3+$4+$5)} END {printf \"%.1f\", usage}'",
            "load": "cat /proc/loadavg | awk '{print $1}'",
            "memory": "free -h | grep Mem",
            "memory_percent": "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'",
            "disk": "df -h / | tail -1",
            "disk_use_percent": "df / | tail -1 | awk '{print $5}' | sed 's/%//g'",
            "processes": "ps aux | wc -l",
            "users": "who | wc -l",
            "ip": "hostname -I 2>/dev/null | awk '{print $1}' || ip addr show | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | cut -d/ -f1",
            "temperature": "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf \"%.1f°C\", $1/1000}'",
        }

        for key, shell_cmd in commands.items():
            try:
                full_cmd = cmd_base + [target, shell_cmd]
                result = subprocess.run(
                    full_cmd, capture_output=True, text=True, timeout=10,
                    env=self._get_ssh_env(), **run_opts
                )
                output = result.stdout.strip()
                if output:
                    info[key] = output
            except Exception:
                pass

        # Parse memory
        if "memory" in info:
            parts = info["memory"].split()
            if len(parts) >= 3:
                info["memory_total"] = parts[1]
                info["memory_used"] = parts[2]

        # Parse disk
        if "disk" in info:
            parts = info["disk"].split()
            if len(parts) >= 4:
                info["disk_total"] = parts[1]
                info["disk_used"] = parts[2]
                info["disk_avail"] = parts[3]
                if len(parts) >= 5:
                    info["disk_use_percent"] = parts[4].replace("%", "")

        return info

    def _find_plink(self) -> str | None:
        """Find plink.exe for PuTTY-based system info."""
        candidates = [
            r"C:\Program Files\PuTTY\plink.exe",
            r"C:\Program Files (x86)\PuTTY\plink.exe",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return shutil.which("plink")

    def _find_ssh_client(self) -> tuple[str | None, str]:
        """Find SSH client (ssh.exe or plink.exe) based on settings.
        Returns (executable_path, client_type) where client_type is 'ssh' or 'plink'."""
        use_putty = getattr(self._settings, 'use_putty', False) if self._settings else False
        
        if use_putty:
            # Use putty_key_path if available, otherwise fall back to key_path
            key_to_use = self._conn.putty_key_path or self._conn.key_path
            
            # Check if key is .ppk format (required by plink)
            if key_to_use and not key_to_use.lower().endswith('.ppk'):
                logger.warning(f"plink requires .ppk format keys, but '{key_to_use}' is not .ppk. Falling back to ssh.exe.")
                # Fallback to ssh.exe for non-.ppk keys
            else:
                plink_exe = self._find_plink()
                if plink_exe:
                    return plink_exe, 'plink'
                # Fallback to ssh.exe if plink not found
        
        ssh_exe = self._find_ssh()
        if ssh_exe:
            return ssh_exe, 'ssh'
        
        return None, 'none'

    def _find_ssh(self) -> str | None:
        candidates = [
            r"C:\Windows\System32\OpenSSH\ssh.exe",
            r"C:\Windows\SysWOW64\OpenSSH\ssh.exe",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    def _build_ssh_command(self, ssh_exe: str) -> tuple[list, str]:
        """Build SSH command for native ssh.exe."""
        # SECURITY FIX: System info panel requires an SSH key to be configured
        # This works regardless of whether password or key auth is set as primary method
        if not self._conn.key_path:
            raise ValueError(tr("sysinfo.key_required"))
        
        # SECURITY FIX: Use absolute path for known_hosts instead of %USERPROFILE%
        known_hosts_path = os.path.expanduser("~\\.ssh\\known_hosts")
        
        cmd_base = [
            ssh_exe,
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", f"UserKnownHostsFile={known_hosts_path}",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes",
            "-o", "PreferredAuthentications=publickey",
            "-p", str(self._conn.port),
        ]

        if self._conn.key_path:
            cmd_base.extend(["-i", self._conn.key_path])

        target = f"{self._conn.user}@{self._conn.host}"
        return cmd_base, target

    def _build_plink_command(self, plink_exe: str) -> tuple[list, str]:
        """Build plink command for PuTTY-based system info."""
        # SECURITY: Validate plink path to prevent command injection
        if not _is_safe_file_path(plink_exe):
            raise ValueError(f"Ungültiger plink.exe Pfad: {plink_exe}")
        
        cmd_base = [
            plink_exe,
            "-batch",  # Non-interactive mode
            "-sshlog", os.devnull,  # Suppress SSH log
            "-P", str(self._conn.port),
        ]

        # Add key authentication if key is configured
        # Use putty_key_path if available, otherwise fall back to key_path
        key_to_use = self._conn.putty_key_path or self._conn.key_path
        if key_to_use:
            # SECURITY: Validate key path
            if not _is_safe_file_path(key_to_use):
                raise ValueError(f"Ungültiger Key-Pfad: {key_to_use}")
            # plink requires .ppk format
            if not key_to_use.lower().endswith('.ppk'):
                raise ValueError(
                    "plink.exe erfordert .ppk-formatierte Keys. "
                    f"Der Key '{key_to_use}' ist nicht im .ppk Format. "
                    "Bitte konvertieren Sie den Key mit PuTTYgen oder verwenden Sie nativen SSH."
                )
            cmd_base.extend(["-i", key_to_use])
        elif self._conn.auth_method == "password" and self._conn.password:
            # SECURITY WARNING: Password in command line is visible in process list
            # This is a security risk but user has enabled plink for this purpose
            logger.warning("Using password authentication with plink - password visible in process list")
            cmd_base.extend(["-pw", self._conn.password])
        else:
            raise ValueError("Bitte hinterlegen Sie einen SSH-Key oder Passwort für diese Verbindung.")

        target = f"{self._conn.user}@{self._conn.host}"
        return cmd_base, target

    def _get_ssh_env(self) -> dict:
        env = os.environ.copy()
        # SECURITY FIX: Removed SSH_PASSWORD environment variable method
        # Passwords in environment variables can be extracted from process lists
        return env


class SystemInfoPanel(QFrame):
    """System info panel shown in the right panel when a connection is mounted."""

    closed = pyqtSignal()

    def __init__(self, conn: Connection, parent=None, settings=None):
        super().__init__(parent)
        self._conn = conn
        self._settings = settings
        self._info_thread: SSHSystemInfoThread | None = None
        self._loading_anim_timer: QTimer | None = None
        self._loading_anim_phase: int = 0

        self.setObjectName("systemInfoPanel")
        self._build_ui()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(120000)
        self._refresh_timer.timeout.connect(self._fetch_info)
        self._refresh_timer.start()

        self._fetch_info()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        hero = QFrame()
        hero.setObjectName("sysinfoHeroCard")
        hero_l = QVBoxLayout(hero)
        hero_l.setContentsMargins(18, 16, 18, 16)
        hero_l.setSpacing(8)

        hero_top = QHBoxLayout()
        hero_top.setContentsMargins(0, 0, 0, 0)
        hero_top.setSpacing(8)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(4)
        self._hero_title = QLabel(self._conn.name)
        self._hero_title.setObjectName("sysinfoHeroTitle")
        title_col.addWidget(self._hero_title)
        self._hero_meta = QLabel(f"{self._conn.user}@{self._conn.host}:{self._conn.port}")
        self._hero_meta.setObjectName("sysinfoHeroMeta")
        title_col.addWidget(self._hero_meta)
        hero_top.addLayout(title_col)
        hero_top.addStretch()

        self._state_pill = QLabel(tr("panel.status.connected"))
        self._state_pill.setObjectName("sysinfoStatePill")
        self._state_pill.setProperty("connected", "true")
        hero_top.addWidget(self._state_pill, 0, Qt.AlignmentFlag.AlignTop)

        self._refresh_btn = QPushButton()
        self._refresh_btn.setObjectName("rpHeaderBtn")
        self._refresh_btn.setFixedSize(28, 28)
        self._refresh_btn.setIcon(svg_icon("refresh", "#aab4c4", 15))
        self._refresh_btn.setIconSize(QSize(15, 15))
        self._refresh_btn.setToolTip(tr("sysinfo.refresh"))
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._fetch_info)
        hero_top.addWidget(self._refresh_btn, 0, Qt.AlignmentFlag.AlignTop)
        hero_l.addLayout(hero_top)

        self._hero_path = QLabel(f"{self._conn.remote_path}  ->  {self._conn.drive_letter}")
        self._hero_path.setObjectName("dialogLead")
        self._hero_path.setWordWrap(True)
        hero_l.addWidget(self._hero_path)
        root.addWidget(hero)

        self._state_card = QFrame()
        self._state_card.setObjectName("sysinfoStateCard")
        state_l = QVBoxLayout(self._state_card)
        state_l.setContentsMargins(16, 14, 16, 14)
        state_l.setSpacing(6)
        self._loading_lbl = QLabel(tr("sysinfo.loading"))
        self._loading_lbl.setObjectName("sysinfoStateText")
        self._loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_lbl.setWordWrap(True)
        state_l.addWidget(self._loading_lbl)

        self._error_lbl = QLabel()
        self._error_lbl.setObjectName("sysinfoErrorText")
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_lbl.setWordWrap(True)
        self._error_lbl.hide()
        state_l.addWidget(self._error_lbl)
        root.addWidget(self._state_card)

        self._content = QWidget()
        # Content stays visible to avoid layout jumps; values are placeholders while loading.
        content_v = QVBoxLayout(self._content)
        content_v.setContentsMargins(0, 0, 0, 0)
        content_v.setSpacing(12)

        resources_card, resources_l, self._sys_section = self._make_section_card(tr("sysinfo.os"))

        self._cpu_row = self._make_stat_row(tr("sysinfo.cpu"), "0%")
        self._cpu_bar = self._make_progress_bar()
        resources_l.addWidget(self._cpu_row)
        resources_l.addWidget(self._cpu_bar)
        resources_l.addSpacing(10)

        self._ram_row = self._make_stat_row(tr("sysinfo.ram"), "— / —")
        self._ram_bar = self._make_progress_bar()
        resources_l.addWidget(self._ram_row)
        resources_l.addWidget(self._ram_bar)
        resources_l.addSpacing(10)

        self._disk_row = self._make_stat_row(tr("sysinfo.disk"), "— / —")
        self._disk_bar = self._make_progress_bar()
        resources_l.addWidget(self._disk_row)
        resources_l.addWidget(self._disk_bar)
        resources_l.addSpacing(12)

        self._temp_widget = QWidget()
        temp_v = QVBoxLayout(self._temp_widget)
        temp_v.setContentsMargins(0, 0, 0, 10)
        temp_v.setSpacing(0)
        self._temp_row = self._make_stat_row(tr("sysinfo.temperature"), "—")
        temp_v.addWidget(self._temp_row)
        self._temp_widget.hide()
        resources_l.addWidget(self._temp_widget)
        resources_l.addStretch()
        content_v.addWidget(resources_card)

        details_card, details_l, self._uptime_section = self._make_section_card(tr("sysinfo.uptime"))

        self._uptime_row = self._make_stat_row(tr("sysinfo.host"), "—")
        details_l.addWidget(self._uptime_row)
        details_l.addSpacing(4)
        self._load_row = self._make_stat_row(tr("sysinfo.load"), "—")
        details_l.addWidget(self._load_row)
        details_l.addSpacing(4)

        self._detail_section = self._make_section_label(tr("sysinfo.active_users") + " & " + tr("sysinfo.processes"))
        details_l.addWidget(self._make_divider())
        details_l.addSpacing(10)
        details_l.addWidget(self._detail_section)
        details_l.addSpacing(8)

        self._users_row = self._make_stat_row(tr("sysinfo.active_users"), "—")
        details_l.addWidget(self._users_row)
        details_l.addSpacing(4)
        self._proc_row = self._make_stat_row(tr("sysinfo.processes"), "—")
        details_l.addWidget(self._proc_row)
        details_l.addSpacing(4)
        self._ip_row = self._make_stat_row(tr("sysinfo.ip"), "—")
        details_l.addWidget(self._ip_row)
        details_l.addStretch()
        content_v.addWidget(details_card)

        root.addWidget(self._content, stretch=1)

        # Loading overlay (single, styled tile) shown while fetching info
        self._loading_overlay = QWidget(self)
        self._loading_overlay.setObjectName("sysinfoLoadingOverlay")
        self._loading_overlay.hide()

        ov = QVBoxLayout(self._loading_overlay)
        ov.setContentsMargins(0, 0, 0, 0)
        ov.setSpacing(0)
        ov.addStretch(1)

        loading_card = QFrame()
        loading_card.setObjectName("sysinfoLoadingCard")
        loading_l = QVBoxLayout(loading_card)
        loading_l.setContentsMargins(18, 16, 18, 16)
        loading_l.setSpacing(8)

        self._loading_icon = QLabel("⏳")
        self._loading_icon.setObjectName("sysinfoLoadingIcon")
        self._loading_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_l.addWidget(self._loading_icon)

        self._loading_title = QLabel(tr("sysinfo.loading"))
        self._loading_title.setObjectName("sysinfoLoadingTitle")
        self._loading_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_title.setWordWrap(True)
        loading_l.addWidget(self._loading_title)

        self._loading_dots = QLabel("…")
        self._loading_dots.setObjectName("sysinfoLoadingDots")
        self._loading_dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_l.addWidget(self._loading_dots)

        ov.addWidget(loading_card, 0, Qt.AlignmentFlag.AlignHCenter)
        ov.addStretch(1)

        self._loading_anim_timer = QTimer(self)
        self._loading_anim_timer.setInterval(320)
        self._loading_anim_timer.timeout.connect(self._tick_loading_overlay)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "_loading_overlay") and self._loading_overlay is not None:
            self._loading_overlay.setGeometry(self.rect())

    def _tick_loading_overlay(self):
        self._loading_anim_phase = (self._loading_anim_phase + 1) % 4
        dots = "." * self._loading_anim_phase
        self._loading_dots.setText(dots if dots else " ")

    def _set_loading_overlay_visible(self, visible: bool):
        if not hasattr(self, "_loading_overlay"):
            return
        if visible:
            self._loading_icon.setText("⏳")
            self._loading_title.setText(tr("sysinfo.loading"))
            self._loading_dots.setText("…")
            self._loading_dots.show()
        self._loading_overlay.setVisible(visible)
        if self._loading_anim_timer:
            if visible and not self._loading_anim_timer.isActive():
                self._loading_anim_phase = 0
                self._loading_anim_timer.start()
            elif not visible and self._loading_anim_timer.isActive():
                self._loading_anim_timer.stop()

    def _show_overlay_error(self, icon: str, title: str, body: str):
        if not hasattr(self, "_loading_overlay"):
            return
        self._loading_anim_timer.stop()
        self._loading_icon.setText(icon)
        self._loading_title.setText(title)
        self._loading_dots.setText(body)
        self._loading_overlay.show()
        self._content.hide()
        self._loading_dots.show()

    def _make_section_card(self, title: str):
        frame = QFrame()
        frame.setObjectName("sysinfoSectionCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(0)
        section = self._make_section_label(title)
        layout.addWidget(section)
        layout.addSpacing(8)
        return frame, layout, section

    def _make_section_label(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setObjectName("rpSectionLabel")
        return lbl

    def _make_divider(self) -> QFrame:
        f = QFrame()
        f.setObjectName("rpDivider")
        f.setFixedHeight(1)
        return f

    def _make_stat_row(self, label: str, value: str) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)
        lbl = QLabel(label)
        lbl.setObjectName("sysinfoStatLabel")
        val = QLabel(value)
        val.setObjectName("sysinfoStatValue")
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        h.addWidget(lbl)
        h.addStretch()
        h.addWidget(val)
        # store val ref on widget for easy update
        w._value_lbl = val
        return w

    def _make_progress_bar(self) -> QProgressBar:
        bar = QProgressBar()
        bar.setObjectName("sysinfoProgress")
        bar.setMaximum(100)
        bar.setValue(0)
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        return bar

    def _set_bar_color(self, bar: QProgressBar, pct: float):
        if pct > 80:
            level = "error"
        elif pct > 50:
            level = "warn"
        else:
            level = "ok"
        bar.setProperty("level", level)
        bar.style().unpolish(bar)
        bar.style().polish(bar)

    def _fetch_info(self):
        self._loading_lbl.show()
        self._state_card.show()
        self._content.show()
        self._error_lbl.hide()
        self._refresh_btn.setEnabled(False)
        self._set_loading_overlay_visible(True)

        if self._info_thread:
            self._info_thread.stop()
            self._info_thread.wait()

        self._info_thread = SSHSystemInfoThread(self._conn)
        self._info_thread.info_ready.connect(self._on_info_ready)
        self._info_thread.error.connect(self._on_error)
        self._info_thread.start()

    def _on_info_ready(self, info: dict):
        self._loading_lbl.hide()
        self._state_card.hide()
        self._refresh_btn.setEnabled(True)
        self._set_loading_overlay_visible(False)

        if info.get("error") and not info.get("connected"):
            self._on_error(info["error"])
            return

        self._content.show()
        self._state_pill.setText(tr("panel.status.connected"))
        self._state_pill.setProperty("connected", "true")
        self._state_pill.style().unpolish(self._state_pill)
        self._state_pill.style().polish(self._state_pill)
        self._hero_title.setText(self._conn.name)
        self._hero_meta.setText(info.get("os", f"{self._conn.user}@{self._conn.host}:{self._conn.port}"))

        # Section header: "SYSTEM · <hostname>"
        hostname = info.get("hostname", self._conn.host)
        self._sys_section.setText(f"SYSTEM · {hostname}".upper())

        # CPU
        try:
            cpu_pct = float(info.get("cpu_percent", "0").replace("%", ""))
        except Exception:
            cpu_pct = 0.0
        cores = info.get("cpu_cores", "?")
        self._cpu_row._value_lbl.setText(f"{cpu_pct:.0f}%  ({cores} cores)")
        self._cpu_bar.setValue(int(cpu_pct))
        self._set_bar_color(self._cpu_bar, cpu_pct)

        # RAM
        mem_used = info.get("memory_used", "—")
        mem_total = info.get("memory_total", "—")
        self._ram_row._value_lbl.setText(f"{mem_used} / {mem_total}")
        try:
            mem_pct = float(info.get("memory_percent", "0"))
        except Exception:
            mem_pct = 0.0
        self._ram_bar.setValue(int(mem_pct))
        self._set_bar_color(self._ram_bar, mem_pct)

        # Disk
        disk_used = info.get("disk_used", "—")
        disk_total = info.get("disk_total", "—")
        try:
            disk_pct = float(str(info.get("disk_use_percent", "0")).replace("%", ""))
        except Exception:
            disk_pct = 0.0
        self._disk_row._value_lbl.setText(f"{disk_used} / {disk_total}")
        self._disk_bar.setValue(int(disk_pct))
        self._set_bar_color(self._disk_bar, disk_pct)

        # Temperature (optional)
        temp = info.get("temperature", "")
        if temp and temp != "0.0°C":
            self._temp_row._value_lbl.setText(temp)
            self._temp_widget.show()
        else:
            self._temp_widget.hide()

        # Uptime
        uptime = info.get("uptime", "—").replace("up ", "")
        self._uptime_row._value_lbl.setText(uptime)

        # Load
        load = info.get("load", "—")
        self._load_row._value_lbl.setText(load)

        # Active users
        users = info.get("users", "—")
        self._users_row._value_lbl.setText(users)

        # Processes
        procs = info.get("processes", "—")
        try:
            procs = str(int(procs) - 1)  # subtract header line from ps aux
        except Exception:
            pass
        self._proc_row._value_lbl.setText(procs)

        # IP
        ip = info.get("ip", "—")
        self._ip_row._value_lbl.setText(ip)

    def _on_error(self, msg: str, error_type: str = "generic"):
        self._set_loading_overlay_visible(False)
        if error_type == "key_missing":
            self._loading_lbl.hide()
            self._state_card.hide()
            self._show_overlay_error(
                "🤷",
                tr("sysinfo.key_missing.title"),
                tr("sysinfo.key_missing.desc"),
            )
            self._refresh_btn.setEnabled(True)
            return
        self._loading_lbl.hide()
        self._content.hide()
        self._state_card.show()
        self._state_pill.setText(tr("dialog.error"))
        self._state_pill.setProperty("connected", "false")
        self._state_pill.style().unpolish(self._state_pill)
        self._state_pill.style().polish(self._state_pill)
        self._error_lbl.setText(f"{tr('sysinfo.error')} {msg}")
        self._error_lbl.show()
        self._refresh_btn.setEnabled(True)

    def _on_close(self):
        self.closed.emit()

    def closeEvent(self, event):
        if self._refresh_timer:
            self._refresh_timer.stop()
        if self._info_thread:
            self._info_thread.stop()
            self._info_thread.wait()
        if self._loading_anim_timer and self._loading_anim_timer.isActive():
            self._loading_anim_timer.stop()
        event.accept()
