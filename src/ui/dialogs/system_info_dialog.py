"""
system_info_dialog.py – Zeigt Systeminformationen eines Remote-Servers via SSH.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QGridLayout, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont
from src.ui.icons import icon as svg_icon

import subprocess
import re
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
        try:
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=15,
                env=self._get_ssh_env()
            )
            if "SSH_OK" not in result.stdout:
                info["error"] = f"SSH-Verbindung fehlgeschlagen: {result.stderr or 'Unbekannter Fehler'}"
                return info
        except subprocess.TimeoutExpired:
            info["error"] = "SSH-Verbindung Timeout (10s)"
            return info
        except Exception as e:
            info["error"] = f"SSH-Fehler: {e}"
            return info
        
        info["connected"] = True
        
        # Sammle Systeminformationen
        commands = {
            "os": "uname -a || cat /etc/os-release | head -1",
            "hostname": "hostname -f 2>/dev/null || hostname",
            "uptime": "uptime -p 2>/dev/null || uptime | awk '{print $3,$4}' | sed 's/,//g'",
            "cpu_model": "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2 | sed 's/^ *//'",
            "cpu_cores": "nproc",
            "cpu_usage": "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1",
            "memory": "free -h | grep Mem",
            "memory_percent": "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'",
            "disk": "df -h / | tail -1",
            "disk_percent": "df / | tail -1 | awk '{print $5}' | sed 's/%//g'",
            "load": "cat /proc/loadavg | awk '{print $1, $2, $3}'",
            "processes": "ps aux | wc -l",
            "users": "who | wc -l",
            "ip": "hostname -I 2>/dev/null || ip addr show | grep 'inet ' | head -1 | awk '{print $2}' | cut -d/ -f1",
            "temperature": "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1 | awk '{print $1/1000 \"°C\"}'",
        }
        
        for key, shell_cmd in commands.items():
            try:
                full_cmd = cmd_base + [target, shell_cmd]
                result = subprocess.run(
                    full_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=self._get_ssh_env()
                )
                output = result.stdout.strip()
                if output and not result.stderr:
                    info[key] = output
            except Exception:
                pass
        
        # Parse Speicher-Info
        if "memory" in info:
            # Format: Mem: total used free shared buff/cache available
            parts = info["memory"].split()
            if len(parts) >= 4:
                info["memory_total"] = parts[1]
                info["memory_used"] = parts[2]
                info["memory_free"] = parts[3]
        
        # Parse Disk-Info
        if "disk" in info:
            # Format: Filesystem Size Used Avail Use% Mounted on
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


class SystemInfoDialog(QDialog):
    """Dialog der Systeminformationen eines SSH-Servers anzeigt."""
    
    def __init__(self, conn: Connection, parent=None):
        super().__init__(parent)
        self._conn = conn
        self._info_thread: SSHSystemInfoThread | None = None
        
        self.setWindowTitle(tr("sysinfo.title", name=conn.name))
        self.setMinimumSize(520, 480)
        self.setModal(True)
        
        self._build_ui()
        self._fetch_info()
    
    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #e6edf3;
            }
            QLabel {
                color: #e6edf3;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#sectionTitle {
                color: #58a6ff;
                font-size: 12px;
                font-weight: bold;
                margin-top: 16px;
            }
            QLabel#infoLabel {
                color: #8b949e;
                font-size: 11px;
            }
            QLabel#valueLabel {
                color: #e6edf3;
                font-size: 12px;
                font-weight: 500;
            }
            QLabel#bigValue {
                color: #e6edf3;
                font-size: 20px;
                font-weight: bold;
            }
            QFrame#sectionFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 12px;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #21262d;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 4px;
            }
            QPushButton {
                background-color: #238636;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
            QPushButton:disabled {
                background-color: #484f58;
                color: #8b949e;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QLabel(f"📊 {tr('sysinfo.title', name=self._conn.name)}")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #e6edf3;")
        layout.addWidget(header)
        
        self._subtitle = QLabel(f"{self._conn.user}@{self._conn.host}:{self._conn.port}")
        self._subtitle.setStyleSheet("color: #8b949e; font-size: 12px;")
        layout.addWidget(self._subtitle)
        
        # Loading
        self._loading_frame = QFrame()
        loading_layout = QVBoxLayout(self._loading_frame)
        self._loading_label = QLabel(tr("sysinfo.loading"))
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self._loading_label)
        
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # Indeterminate
        loading_layout.addWidget(self._progress)
        layout.addWidget(self._loading_frame)
        
        # Content (initially hidden)
        self._content = QWidget()
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        
        # OS Info
        self._os_frame = self._create_section(tr("sysinfo.os"))
        self._os_label = QLabel("-")
        self._os_label.setObjectName("valueLabel")
        self._add_to_section(self._os_frame, self._os_label)
        content_layout.addWidget(self._os_frame)
        
        # Uptime & Hostname
        row = QHBoxLayout()
        self._uptime_frame = self._create_section(tr("sysinfo.host"))
        self._uptime_label = QLabel("-")
        self._uptime_label.setObjectName("valueLabel")
        self._add_to_section(self._uptime_frame, self._uptime_label)
        row.addWidget(self._uptime_frame)
        
        self._hostname_frame = self._create_section("Hostname")
        self._hostname_label = QLabel("-")
        self._hostname_label.setObjectName("valueLabel")
        self._add_to_section(self._hostname_frame, self._hostname_label)
        row.addWidget(self._hostname_frame)
        content_layout.addLayout(row)
        
        # CPU
        self._cpu_frame = self._create_section("CPU")
        cpu_layout = QGridLayout()
        cpu_layout.setSpacing(8)
        
        self._cpu_model = QLabel("-")
        self._cpu_model.setObjectName("valueLabel")
        cpu_layout.addWidget(QLabel(tr("sysinfo.model")), 0, 0)
        cpu_layout.addWidget(self._cpu_model, 0, 1)
        
        self._cpu_cores = QLabel("-")
        self._cpu_cores.setObjectName("valueLabel")
        cpu_layout.addWidget(QLabel(tr("sysinfo.cores_label")), 1, 0)
        cpu_layout.addWidget(self._cpu_cores, 1, 1)
        
        self._load_label = QLabel("-")
        self._load_label.setObjectName("valueLabel")
        cpu_layout.addWidget(QLabel(tr("sysinfo.load") + ":"), 2, 0)
        cpu_layout.addWidget(self._load_label, 2, 1)
        
        self._add_grid_to_section(self._cpu_frame, cpu_layout)
        content_layout.addWidget(self._cpu_frame)
        
        # Memory
        self._mem_frame = self._create_section(tr("sysinfo.ram"))
        mem_layout = QVBoxLayout()
        mem_layout.setSpacing(6)
        
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
        self._add_to_section(self._mem_frame, mem_layout)
        content_layout.addWidget(self._mem_frame)
        
        # Disk
        self._disk_frame = self._create_section(tr("sysinfo.disk"))
        disk_layout = QVBoxLayout()
        disk_layout.setSpacing(6)
        
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
        self._add_to_section(self._disk_frame, disk_layout)
        content_layout.addWidget(self._disk_frame)
        
        # Extra Info
        row2 = QHBoxLayout()
        self._temp_frame = self._create_section(tr("sysinfo.temperature"))
        self._temp_label = QLabel("-")
        self._temp_label.setObjectName("valueLabel")
        self._add_to_section(self._temp_frame, self._temp_label)
        row2.addWidget(self._temp_frame)
        
        self._users_frame = self._create_section(tr("sysinfo.active_users"))
        self._users_label = QLabel("-")
        self._users_label.setObjectName("valueLabel")
        self._add_to_section(self._users_frame, self._users_label)
        row2.addWidget(self._users_frame)
        
        self._proc_frame = self._create_section(tr("sysinfo.processes"))
        self._proc_label = QLabel("-")
        self._proc_label.setObjectName("valueLabel")
        self._add_to_section(self._proc_frame, self._proc_label)
        row2.addWidget(self._proc_frame)
        content_layout.addLayout(row2)
        
        # IP
        self._ip_frame = self._create_section(tr("sysinfo.ip"))
        self._ip_label = QLabel("-")
        self._ip_label.setObjectName("valueLabel")
        self._add_to_section(self._ip_frame, self._ip_label)
        content_layout.addWidget(self._ip_frame)
        
        content_layout.addStretch()
        layout.addWidget(self._content)
        self._content.hide()
        
        # Error label
        self._error_label = QLabel()
        self._error_label.setStyleSheet("color: #f85149; padding: 20px;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.hide()
        layout.addWidget(self._error_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self._refresh_btn = QPushButton(" " + tr("sysinfo.refresh"))
        self._refresh_btn.setIcon(svg_icon("refresh", "#aab4c4", 16))
        self._refresh_btn.setIconSize(QSize(16, 16))
        self._refresh_btn.clicked.connect(self._fetch_info)
        btn_layout.addWidget(self._refresh_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton(tr("dialog.close"))
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_section(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("sectionFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        lbl = QLabel(title)
        lbl.setObjectName("sectionTitle")
        layout.addWidget(lbl)
        return frame
    
    def _add_to_section(self, frame: QFrame, widget):
        frame.layout().addWidget(widget)
    
    def _add_grid_to_section(self, frame: QFrame, grid: QGridLayout):
        frame.layout().addLayout(grid)
    
    def _fetch_info(self):
        """Startet den SSH-Info-Thread."""
        self._loading_frame.show()
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
        """Zeigt die empfangenen Informationen an."""
        self._loading_frame.hide()
        self._content.show()
        self._refresh_btn.setEnabled(True)
        
        # OS
        os_text = info.get("os", tr("sysinfo.unknown"))
        if "PRETTY_NAME" in os_text:
            os_text = os_text.replace('PRETTY_NAME="', '').replace('"', '')
        self._os_label.setText(os_text)
        
        # Hostname
        self._hostname_label.setText(info.get("hostname", "-"))
        
        # Uptime
        uptime = info.get("uptime", "-")
        if uptime and uptime != "-":
            uptime = uptime.replace("up ", "")
        self._uptime_label.setText(uptime)
        
        # CPU
        cpu_model = info.get("cpu_model", "-")
        if cpu_model and len(cpu_model) > 40:
            cpu_model = cpu_model[:40] + "..."
        self._cpu_model.setText(cpu_model)
        self._cpu_cores.setText(tr("sysinfo.cores_suffix", n=info.get('cpu_cores', '-')))
        self._load_label.setText(info.get("load", "-"))
        
        # Memory
        mem_used = info.get("memory_used", "-")
        mem_total = info.get("memory_total", "-")
        self._mem_used.setText(mem_used)
        self._mem_total.setText(f"/ {mem_total}")
        
        mem_pct = info.get("memory_percent", "0")
        try:
            self._mem_bar.setValue(int(float(mem_pct)))
            # Farbe basierend auf Auslastung
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
        
        # Temperatur
        temp = info.get("temperature", "N/A")
        if temp == "N/A" or not temp:
            self._temp_frame.hide()
        else:
            self._temp_frame.show()
            self._temp_label.setText(temp)
        
        # Nutzer & Prozesse
        self._users_label.setText(info.get("users", "-"))
        self._proc_label.setText(info.get("processes", "-"))
        
        # IP
        ip = info.get("ip", "-")
        if ip and ip != "127.0.0.1":
            self._ip_label.setText(ip)
        else:
            self._ip_frame.hide()
    
    def _on_error(self, error_msg: str):
        """Zeigt einen Fehler an."""
        self._loading_frame.hide()
        self._content.hide()
        self._error_label.setText(f"❌ {tr('sysinfo.error')}\n{error_msg}")
        self._error_label.show()
        self._refresh_btn.setEnabled(True)
    
    def closeEvent(self, event):
        """Clean up beim Schließen."""
        if self._info_thread:
            self._info_thread.stop()
            self._info_thread.wait()
        event.accept()
