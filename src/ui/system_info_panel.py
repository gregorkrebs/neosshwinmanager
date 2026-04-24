"""
system_info_panel.py – Expandierbares System Info Panel für ConnectionCard.
Wird direkt unter der ConnectionCard angezeigt.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGridLayout, QWidget
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
    """Holt Systeminformationen via SSH im Hintergrund."""
    
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
        """Führt SSH-Befehle aus und sammelt Systeminformationen."""
        info = {
            "hostname": self._conn.host,
            "user": self._conn.user,
            "connected": False,
            "error": None,
        }
        
        # Teste SSH-Verbindung und hole Basis-Info
        ssh_exe = self._find_ssh()
        if not ssh_exe:
            info["error"] = "ssh.exe nicht gefunden"
            return info
        
        # Baue SSH-Befehl
        cmd_base = [
            ssh_exe,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes" if self._conn.auth_method == "key" else "PreferredAuthentications=password,keyboard-interactive",
            "-p", str(self._conn.port),
        ]
        
        if self._conn.auth_method == "key" and self._conn.key_path:
            cmd_base.extend(["-i", self._conn.key_path])
        
        target = f"{self._conn.user}@{self._conn.host}"
        
        # Teste Verbindung
        test_cmd = cmd_base + [target, "echo 'SSH_OK'"]
        logger.info(f"SSH System Info: Teste Verbindung zu {target} mit {self._conn.auth_method}")
        try:
            # Silently run SSH on Windows
            run_opts = {}
            if os.name == "nt":
                import subprocess
                run_opts["creationflags"] = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=15,
                env=self._get_ssh_env(),
                **run_opts
            )
            logger.debug(f"SSH Test stdout: {result.stdout[:200]}")
            logger.debug(f"SSH Test stderr: {result.stderr[:200]}")
            if "SSH_OK" not in result.stdout:
                info["error"] = f"SSH-Verbindung fehlgeschlagen: {result.stderr or result.stdout or 'Unbekannter Fehler'}"
                logger.error(f"SSH System Info: Verbindung fehlgeschlagen - {info['error']}")
                return info
        except subprocess.TimeoutExpired:
            info["error"] = "SSH-Verbindung Timeout (15s)"
            logger.error("SSH System Info: Timeout")
            return info
        except Exception as e:
            info["error"] = f"SSH-Fehler: {e}"
            logger.error(f"SSH System Info: Exception - {e}")
            return info
        
        info["connected"] = True
        
        # Sammle Systeminformationen
        commands = {
            "os": "uname -a || cat /etc/os-release | head -1",
            "hostname": "hostname -f 2>/dev/null || hostname",
            "uptime": "uptime -p 2>/dev/null || uptime | awk '{print $3,$4}' | sed 's/,//g'",
            "cpu_model": "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2 | sed 's/^ *//'",
            "cpu_cores": "nproc",
            "load": "cat /proc/loadavg | awk '{print $1, $2, $3}'",
            "memory": "free -h | grep Mem",
            "memory_percent": "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'",
            "disk": "df -h / | tail -1",
            "disk_use_percent": "df / | tail -1 | awk '{print $5}' | sed 's/%//g'",
            "processes": "ps aux | wc -l",
            "users": "who | wc -l",
            "ip": "hostname -I 2>/dev/null || ip addr show | grep 'inet ' | head -1 | awk '{print $2}' | cut -d/ -f1",
            "temperature": "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1 | awk '{print $1/1000 \"°C\"}'",
        }
        
        for key, shell_cmd in commands.items():
            try:
                full_cmd = cmd_base + [target, shell_cmd]
                # Silently run SSH on Windows
                run_opts = {}
                if os.name == "nt":
                    import subprocess
                    run_opts["creationflags"] = subprocess.CREATE_NO_WINDOW

                result = subprocess.run(
                    full_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=self._get_ssh_env(),
                    **run_opts
                )
                output = result.stdout.strip()
                # Akzeptiere Output auch wenn stderr nicht leer ist (viele Befehle schreiben Warnungen)
                if output:
                    info[key] = output
                    logger.debug(f"SSH info [{key}]: {output[:50]}...")
                elif result.stderr:
                    logger.debug(f"SSH info [{key}] stderr: {result.stderr[:100]}...")
            except Exception as e:
                logger.debug(f"SSH info [{key}] error: {e}")
                pass
        
        # Parse Speicher-Info
        if "memory" in info:
            parts = info["memory"].split()
            if len(parts) >= 4:
                info["memory_total"] = parts[1]
                info["memory_used"] = parts[2]
                info["memory_free"] = parts[3]
        
        # Parse Disk-Info
        if "disk" in info:
            parts = info["disk"].split()
            if len(parts) >= 6:
                info["disk_total"] = parts[1]
                info["disk_used"] = parts[2]
                info["disk_avail"] = parts[3]
                info["disk_use_percent"] = parts[4]
        
        return info
    
    def _find_ssh(self) -> str | None:
        """Findet ssh.exe auf Windows."""
        candidates = [
            r"C:\Windows\System32\OpenSSH\ssh.exe",
            r"C:\Windows\SysWOW64\OpenSSH\ssh.exe",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None
    
    def _get_ssh_env(self) -> dict:
        """Erstellt Umgebung mit Passwort für SSH."""
        env = os.environ.copy()
        if self._conn.auth_method == "password" and self._conn.password:
            is_frozen = getattr(sys, "frozen", False)
            if is_frozen:
                askpass_cmd = f'"{sys.executable}" --pass-helper'
            else:
                askpass_cmd = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}" --pass-helper'
            env["SSH_PASSWORD"] = self._conn.password
            env["SSH_ASKPASS"] = askpass_cmd
            env["SSH_ASKPASS_REQUIRE"] = "force"
            env["DISPLAY"] = "dummy:0"
        return env


class SystemInfoPanel(QFrame):
    """Expandierbares Panel das direkt unter der Connection angezeigt wird."""
    
    closed = pyqtSignal()  # Wenn Panel geschlossen wird
    
    def __init__(self, conn: Connection, parent=None):
        super().__init__(parent)
        self._conn = conn
        self._info_thread: SSHSystemInfoThread | None = None
        
        self.setObjectName("systemInfoPanel")
        self._build_ui()
        
        # Auto-refresh timer (2 minutes)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(120000) # 120 seconds
        self._refresh_timer.timeout.connect(self._fetch_info)
        self._refresh_timer.start()
        
        self._fetch_info()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header mit Titel und Close-Button
        header = QHBoxLayout()
        
        title = QLabel(f"📊 {tr('sysinfo.title', name=self._conn.name)}")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        
        header.addStretch()
        
        self._refresh_btn = QPushButton()
        self._refresh_btn.setFixedSize(28, 28)
        self._refresh_btn.setIcon(svg_icon("refresh", "#aab4c4", 15))
        self._refresh_btn.setIconSize(QSize(15, 15))
        self._refresh_btn.setToolTip(tr("sysinfo.refresh"))
        self._refresh_btn.clicked.connect(self._fetch_info)
        header.addWidget(self._refresh_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setToolTip(tr("dialog.close"))
        close_btn.setProperty("btn_type", "danger")
        close_btn.clicked.connect(self._on_close)
        header.addWidget(close_btn)
        
        layout.addLayout(header)
        
        # Loading
        self._loading = QLabel(tr("sysinfo.loading"))
        self._loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading.setStyleSheet("color: #8b949e; padding: 20px;")
        layout.addWidget(self._loading)
        
        # Content Grid
        self._content = QWidget()
        content_layout = QGridLayout(self._content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        
        # Row 0: OS & Hostname
        self._os_frame = self._create_section(tr("sysinfo.os"))
        self._os_label = QLabel("-")
        self._os_label.setObjectName("valueLabel")
        self._os_frame.layout().addWidget(self._os_label)
        content_layout.addWidget(self._os_frame, 0, 0)
        
        self._host_frame = self._create_section(tr("sysinfo.host"))
        self._host_label = QLabel("-")
        self._host_label.setObjectName("valueLabel")
        self._host_frame.layout().addWidget(self._host_label)
        content_layout.addWidget(self._host_frame, 0, 1)
        
        # Row 1: CPU
        self._cpu_frame = self._create_section("CPU")
        cpu_layout = QHBoxLayout()
        cpu_layout.setSpacing(10)
        self._cpu_info = QLabel("-")
        self._cpu_info.setObjectName("valueLabel")
        cpu_layout.addWidget(self._cpu_info)
        cpu_layout.addStretch()
        self._cpu_frame.layout().addLayout(cpu_layout)
        content_layout.addWidget(self._cpu_frame, 1, 0, 1, 2)
        
        # Row 2: Memory & Disk
        self._mem_frame = self._create_section(tr("sysinfo.ram"))
        mem_layout = QVBoxLayout()
        mem_layout.setSpacing(4)
        mem_row = QHBoxLayout()
        self._mem_used = QLabel("-")
        self._mem_used.setObjectName("bigValue")
        self._mem_total = QLabel("/ -")
        self._mem_total.setObjectName("infoLabel")
        mem_row.addWidget(self._mem_used)
        mem_row.addWidget(self._mem_total)
        mem_row.addStretch()
        mem_layout.addLayout(mem_row)
        self._mem_bar = QProgressBar()
        self._mem_bar.setMaximum(100)
        mem_layout.addWidget(self._mem_bar)
        self._mem_frame.layout().addLayout(mem_layout)
        content_layout.addWidget(self._mem_frame, 2, 0)
        
        self._disk_frame = self._create_section(tr("sysinfo.disk"))
        disk_layout = QVBoxLayout()
        disk_layout.setSpacing(4)
        disk_row = QHBoxLayout()
        self._disk_used = QLabel("-")
        self._disk_used.setObjectName("bigValue")
        self._disk_total = QLabel("/ -")
        self._disk_total.setObjectName("infoLabel")
        disk_row.addWidget(self._disk_used)
        disk_row.addWidget(self._disk_total)
        disk_row.addStretch()
        disk_layout.addLayout(disk_row)
        self._disk_bar = QProgressBar()
        self._disk_bar.setMaximum(100)
        disk_layout.addWidget(self._disk_bar)
        self._disk_frame.layout().addLayout(disk_layout)
        content_layout.addWidget(self._disk_frame, 2, 1)
        
        # Row 3: Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(8)
        
        self._temp_frame = self._create_section(f"🌡 {tr('sysinfo.temp')}")
        self._temp_label = QLabel("-")
        self._temp_label.setObjectName("valueLabel")
        self._add_to_section(self._temp_frame, self._temp_label)
        stats_layout.addWidget(self._temp_frame)
        
        self._users_frame = self._create_section(f"👤 {tr('sysinfo.users')}")
        self._users_label = QLabel("-")
        self._users_label.setObjectName("valueLabel")
        self._add_to_section(self._users_frame, self._users_label)
        stats_layout.addWidget(self._users_frame)
        
        self._proc_frame = self._create_section(tr("sysinfo.processes"))
        self._proc_label = QLabel("-")
        self._proc_label.setObjectName("valueLabel")
        self._add_to_section(self._proc_frame, self._proc_label)
        stats_layout.addWidget(self._proc_frame)
        
        self._load_frame = self._create_section(f"📈 {tr('sysinfo.load')}")
        self._load_label = QLabel("-")
        self._load_label.setObjectName("valueLabel")
        self._add_to_section(self._load_frame, self._load_label)
        stats_layout.addWidget(self._load_frame)
        
        content_layout.addLayout(stats_layout, 3, 0, 1, 2)
        
        # Row 4: IP
        self._ip_frame = self._create_section(f"🌐 {tr('sysinfo.ip')}")
        self._ip_label = QLabel("-")
        self._ip_label.setObjectName("valueLabel")
        self._add_to_section(self._ip_frame, self._ip_label)
        content_layout.addWidget(self._ip_frame, 4, 0, 1, 2)
        
        layout.addWidget(self._content)
        self._content.hide()
        
        # Error
        self._error_label = QLabel()
        self._error_label.setStyleSheet("color: #f85149; padding: 15px;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.hide()
        layout.addWidget(self._error_label)
        
        layout.addStretch()
    
    def _create_section(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("sectionFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        lbl = QLabel(title)
        lbl.setObjectName("sectionTitle")
        layout.addWidget(lbl)
        return frame
    
    def _add_to_section(self, frame: QFrame, widget):
        frame.layout().addWidget(widget)
    
    def _fetch_info(self):
        self._loading.show()
        self._content.hide()
        self._error_label.hide()
        self._refresh_btn.setEnabled(False)
        
        if self._info_thread:
            self._info_thread.stop()
            self._info_thread.wait()
        
        self._info_thread = SSHSystemInfoThread(self._conn)
        self._info_thread.info_ready.connect(self._on_info_ready)
        self._info_thread.error.connect(self._on_error)
        self._info_thread.start()
    
    def _on_info_ready(self, info: dict):
        self._loading.hide()
        self._content.show()
        self._refresh_btn.setEnabled(True)
        
        # Debug: Zeige an wie viele Daten empfangen wurden
        data_count = len([k for k in info.keys() if k not in ["hostname", "user", "connected", "error"]])
        logger.info(f"SSH System Info: {data_count} Datenfelder empfangen")
        
        # Wenn keine Daten außer Fehler, zeige Fehler an
        if data_count == 0 and info.get("error"):
            self._on_error(info["error"])
            return
        elif data_count == 0:
            self._on_error(tr("sysinfo.no_data"))
            return
        
        # OS
        os_text = info.get("os", tr("sysinfo.unknown"))
        if "PRETTY_NAME" in os_text:
            os_text = os_text.replace('PRETTY_NAME="', '').replace('"', '')
        if len(os_text) > 50:
            os_text = os_text[:50] + "..."
        self._os_label.setText(os_text)
        
        # Hostname/Uptime
        host = info.get("hostname", "-")
        uptime = info.get("uptime", "-").replace("up ", "")
        self._host_label.setText(f"{host}\n⏱ {uptime}")
        
        # CPU
        cpu = info.get("cpu_model", "-")
        if cpu and len(cpu) > 35:
            cpu = cpu[:35] + "..."
        cores = info.get("cpu_cores", "-")
        self._cpu_info.setText(f"{cpu} ({tr('sysinfo.cores', cores=cores)})")
        
        # Memory
        mem_used = info.get("memory_used", "-")
        mem_total = info.get("memory_total", "-")
        self._mem_used.setText(mem_used)
        self._mem_total.setText(f"/ {mem_total}")
        
        mem_pct = info.get("memory_percent", "0")
        try:
            self._mem_bar.setValue(int(float(mem_pct)))
            if float(mem_pct) > 80:
                self._mem_bar.setStyleSheet("QProgressBar::chunk { background-color: #f85149; }")
            elif float(mem_pct) > 50:
                self._mem_bar.setStyleSheet("QProgressBar::chunk { background-color: #f0883e; }")
            else:
                self._mem_bar.setStyleSheet("QProgressBar::chunk { background-color: #3fb950; }")
        except:
            self._mem_bar.setValue(0)
        
        # Disk
        disk_used = info.get("disk_used", "-")
        disk_total = info.get("disk_total", "-")
        self._disk_used.setText(disk_used)
        self._disk_total.setText(f"/ {disk_total}")
        
        disk_pct = info.get("disk_use_percent", "0%").replace("%", "")
        try:
            self._disk_bar.setValue(int(disk_pct))
            if int(disk_pct) > 80:
                self._disk_bar.setStyleSheet("QProgressBar::chunk { background-color: #f85149; }")
            elif int(disk_pct) > 50:
                self._disk_bar.setStyleSheet("QProgressBar::chunk { background-color: #f0883e; }")
            else:
                self._disk_bar.setStyleSheet("QProgressBar::chunk { background-color: #3fb950; }")
        except:
            self._disk_bar.setValue(0)
        
        # Stats
        temp = info.get("temperature", "N/A")
        if temp == "N/A" or not temp:
            self._temp_frame.hide()
        else:
            self._temp_frame.show()
            self._temp_label.setText(temp)
        
        self._users_label.setText(info.get("users", "-"))
        self._proc_label.setText(info.get("processes", "-"))
        self._load_label.setText(info.get("load", "-"))
        
        # IP
        ip = info.get("ip", "-")
        if ip and ip != "127.0.0.1":
            self._ip_label.setText(ip)
        else:
            self._ip_frame.hide()
    
    def _on_error(self, error_msg: str):
        self._loading.hide()
        self._content.hide()
        self._error_label.setText(f"❌ {error_msg}")
        self._error_label.show()
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
