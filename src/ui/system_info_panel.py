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
from src.config import Connection
from src.app_logger import logger
from src.i18n import tr


class SSHSystemInfoThread(QThread):
    """Fetches system info via SSH in background."""

    info_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, conn: Connection):
        super().__init__()
        self._conn = conn
        self._stopped = False

    def run(self):
        try:
            info = self._gather_info()
            if not self._stopped:
                self.info_ready.emit(info)
        except Exception as e:
            if not self._stopped:
                self.error.emit(str(e))

    def stop(self):
        self._stopped = True

    def _gather_info(self) -> dict:
        info = {
            "hostname": self._conn.host,
            "user": self._conn.user,
            "connected": False,
            "error": None,
        }

        ssh_exe = self._find_ssh()
        if not ssh_exe:
            info["error"] = "ssh.exe not found"
            return info

        # SECURITY FIX: Use absolute path for known_hosts instead of %USERPROFILE%
        known_hosts_path = os.path.expanduser("~\\.ssh\\known_hosts")
        
        cmd_base = [
            ssh_exe,
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", f"UserKnownHostsFile={known_hosts_path}",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes" if self._conn.auth_method == "key" else "PreferredAuthentications=password,keyboard-interactive",
            "-p", str(self._conn.port),
        ]

        if self._conn.auth_method == "key" and self._conn.key_path:
            cmd_base.extend(["-i", self._conn.key_path])

        target = f"{self._conn.user}@{self._conn.host}"

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

    def _find_ssh(self) -> str | None:
        candidates = [
            r"C:\Windows\System32\OpenSSH\ssh.exe",
            r"C:\Windows\SysWOW64\OpenSSH\ssh.exe",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    def _get_ssh_env(self) -> dict:
        env = os.environ.copy()
        # SECURITY FIX: Removed SSH_PASSWORD environment variable method
        # Passwords in environment variables can be extracted from process lists
        # System info panel should only work with key authentication
        if self._conn.auth_method == "password" and self._conn.password:
            logger.warning(
                "System info panel does not support password authentication for security reasons. "
                "Please use SSH key authentication."
            )
        return env


class SystemInfoPanel(QFrame):
    """System info panel shown in the right panel when a connection is mounted."""

    closed = pyqtSignal()

    def __init__(self, conn: Connection, parent=None):
        super().__init__(parent)
        self._conn = conn
        self._info_thread: SSHSystemInfoThread | None = None

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
        self._content.hide()
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
        self._content.hide()
        self._error_lbl.hide()
        self._refresh_btn.setEnabled(False)

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

    def _on_error(self, msg: str):
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
        event.accept()
