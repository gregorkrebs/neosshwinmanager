"""
main_window.py – The primary application window for NEO SSH-Win Manager.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QSizePolicy,
    QMessageBox, QApplication, QSystemTrayIcon, QDialog
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
import os
import ctypes
import ctypes.wintypes
import json

from src.auth_manager import Session, UserConnectionManager
from src.sshfs_controller import SSHFSController
from src.config import Connection
from src.ui.connection_card import ConnectionCard
from src.ui.system_tray import SystemTray
from src.ui.dialogs.add_edit_dialog import AddEditDialog
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.dialogs.about_dialog import AboutDialog
from src.ui.dialogs.login_dialog import UserManagementDialog
from src.ui.debug_window import DebugWindow
from src.app_logger import logger
from src.ui.worker import MountWorker, UnmountWorker
from src.ui.icons import icon as svg_icon
from src.i18n import tr
from PyQt6.QtCore import QThread, QSize


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # UserConnectionManager für den eingeloggten Benutzer
        self._user = Session.current()
        self._mgr = UserConnectionManager(self._user)
        self._controller = SSHFSController()
        self._cards: dict[str, ConnectionCard] = {}
        self._selected_id: str | None = None
        self._workers: dict[str, QThread] = {}  # Tracking active workers

        self.setObjectName("MainWindow")
        self.setWindowTitle("NEO SSH-Win Manager v1.1.0")
        # Mindestbreite so gewählt, dass die Connection-Card (Cloud + Info + Drive-Badge
        # + SSH-Button + Mount-Toggle) plus Action-Panel ohne Abschneiden passt.
        self.setMinimumSize(820, 420)
        self.resize(1100, 640)

        def get_resource_path(relative_path):
            import sys
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                relative_path
            )

        icon_path = get_resource_path(os.path.join("assets", "app_icon.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._build_ui()
        self._setup_tray()
        self._refresh_list()
        self._apply_debug_mode()
        
        # Für IPC (CLI-Access)
        self._setup_ipc()

        # Nur Mount-Status prüfen – kein Auto-Reconnect
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_mount_states)
        self._poll_timer.start(self._mgr.get_settings().check_interval_seconds * 1000)

        self._check_prerequisites()
        
        # Auto-Reconnect zuletzt aktiver Verbindungen (mit Verzögerung)
        QTimer.singleShot(2000, self._auto_reconnect_mounts)
        
        logger.info("NEO SSH-Win Manager gestartet.")

    # ------------------------------------------------------------------
    # CLI Access / IPC
    # ------------------------------------------------------------------

    def _setup_ipc(self):
        """Bereite IPC vor – Named Pipe Listener statt nativeEvent."""
        import threading
        self._ipc_pipe_name = r"\\.\pipe\SSHWinManager_IPC_v1"
        self._ipc_running = True
        self._ipc_thread = threading.Thread(target=self._ipc_listener, daemon=True)
        self._ipc_thread.start()
        logger.info("IPC Pipe Listener gestartet.")

    def _ipc_listener(self):
        """Hört auf Named Pipe für CLI-Anfragen (läuft in eigenem Thread)."""
        import time
        PIPE_ACCESS_DUPLEX = 0x00000003
        PIPE_TYPE_MESSAGE = 0x00000004
        PIPE_READMODE_MESSAGE = 0x00000002
        PIPE_WAIT = 0x00000000
        
        while self._ipc_running:
            try:
                pipe = ctypes.windll.kernel32.CreateNamedPipeW(
                    self._ipc_pipe_name,
                    PIPE_ACCESS_DUPLEX,
                    PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
                    5,       # max instances (allow multiple CLI clients)
                    65536, 65536,
                    5000,    # default timeout 5s
                    None
                )
                if pipe == -1:
                    time.sleep(1)
                    continue

                # Warte auf Verbindung (blockiert)
                ctypes.windll.kernel32.ConnectNamedPipe(pipe, None)
                if not self._ipc_running:
                    ctypes.windll.kernel32.CloseHandle(pipe)
                    break

                # Daten lesen (Message-Mode: ein ReadFile = eine komplette Nachricht)
                buf = ctypes.create_string_buffer(65536)
                read = ctypes.wintypes.DWORD()
                if ctypes.windll.kernel32.ReadFile(pipe, buf, 65536, ctypes.byref(read), None):
                    try:
                        data_json = buf.value[:read.value].decode('utf-8')
                        request = json.loads(data_json)
                        logger.info(f"IPC Request empfangen: {request.get('action')}")
                        
                        if request.get("action") == "cli_connect":
                            conn = self._mgr.get_by_cli_key(request.get("key", ""))
                            response = {"success": False}
                            if conn:
                                logger.info(f"CLI-Zugriff autorisiert für: {conn.name}")
                                response = {
                                    "success": True,
                                    "connection": {
                                        "id": conn.id, "name": conn.name,
                                        "host": conn.host, "user": conn.user,
                                        "port": conn.port, "remote_path": conn.remote_path,
                                        "auth_method": conn.auth_method,
                                        "password": conn.password,
                                        "key_path": conn.key_path
                                    }
                                }
                            else:
                                logger.warning(f"CLI-Zugriff verweigert: ungültiger Key")
                                response["error"] = "Ungültiger Access Key oder Zugriff deaktiviert."

                            # Antwort zurückschreiben
                            res_bytes = json.dumps(response).encode('utf-8')
                            written = ctypes.wintypes.DWORD()
                            ctypes.windll.kernel32.WriteFile(pipe, res_bytes, len(res_bytes), ctypes.byref(written), None)
                            ctypes.windll.kernel32.FlushFileBuffers(pipe)
                    except Exception as e:
                        logger.error(f"IPC Request Fehler: {e}")

                ctypes.windll.kernel32.DisconnectNamedPipe(pipe)
                ctypes.windll.kernel32.CloseHandle(pipe)
            except Exception as e:
                logger.error(f"IPC Listener Fehler: {e}")
                time.sleep(1)

    def _stop_ipc(self):
        """Stoppt den IPC Listener."""
        self._ipc_running = False

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_list_panel(), stretch=1)
        body.addWidget(self._build_action_panel())
        root.addLayout(body, stretch=1)
        root.addWidget(self._build_status_bar())

    def _build_list_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("sidePanel")
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 8, 0, 8)
        v.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("connectionScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._list_container = QWidget()
        self._list_container.setObjectName("connectionList")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        v.addWidget(scroll)
        return panel

    def _build_action_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("actionPanel")
        v = QVBoxLayout(panel)
        v.setContentsMargins(12, 16, 12, 16)
        v.setSpacing(6)

        self._add_btn = self._action_btn(tr("main.add_connection"), "addBtn", self._on_add, icon_name="plus")
        self._delete_btn = self._action_btn(tr("main.delete"), "deleteBtn", self._on_delete, icon_name="trash")

        for btn in (self._add_btn, self._delete_btn):
            v.addWidget(btn)

        div = QFrame()
        div.setObjectName("divider")
        v.addWidget(div)
        # Active Mounts Tracking
        self._active_mounts: set[str] = set()
        self._load_active_mounts()
        
        # Container für Card + Panel
        self._containers: dict[str, any] = {}
        self._panels: set[str] = set()
        self._settings_btn = self._action_btn(tr("main.settings"), "settingsBtn", self._on_settings, icon_name="settings")
        self._about_btn = self._action_btn(tr("main.about"), "aboutBtn", self._on_about, icon_name="info")
        v.addWidget(self._settings_btn)
        v.addWidget(self._about_btn)

        # Eigenes Passwort ändern – für alle User
        self._chgpw_btn = self._action_btn(tr("main.password"), "settingsBtn", self._on_change_own_password, icon_name="key")
        v.addWidget(self._chgpw_btn)

        # Benutzerverwaltung (nur für Admins sichtbar)
        if Session.is_admin():
            self._users_btn = self._action_btn(tr("main.users"), "settingsBtn", self._on_user_management, icon_name="users")
            v.addWidget(self._users_btn)

        # Elastischer Raum: hält die Buttons als kompakten Block oben,
        # schiebt Logout/Debug nach unten. Ohne diesen Stretch verteilt
        # das Layout zusätzliche Höhe als Abstand zwischen den Buttons.
        v.addStretch(1)

        # Logout
        self._logout_btn = QPushButton(tr("main.logout"))
        self._logout_btn.setObjectName("actionBtn")
        self._logout_btn.setProperty("btn_type", "danger")
        self._logout_btn.setMinimumHeight(38)
        self._logout_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._logout_btn.setIcon(svg_icon("logout", "#ff6b7a", 18))
        self._logout_btn.setIconSize(QSize(18, 18))
        self._logout_btn.clicked.connect(self._on_logout)
        v.addWidget(self._logout_btn)

        self._debug_btn = QPushButton(tr("main.debug"))
        self._debug_btn.setObjectName("actionBtn")
        self._debug_btn.setProperty("btn_type", "warning")
        self._debug_btn.setMinimumHeight(38)
        self._debug_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._debug_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._debug_btn.setIcon(svg_icon("bug", "#ffb347", 18))
        self._debug_btn.setIconSize(QSize(18, 18))
        self._debug_btn.setVisible(False)
        self._debug_btn.clicked.connect(self._on_debug)
        v.addSpacing(4)
        v.addWidget(self._debug_btn)
        return panel

    def _action_btn(self, label: str, name: str, slot, icon_name: str | None = None) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("actionBtn")
        btn.setProperty("name_id", name)
        btn.setMinimumHeight(38)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(slot)
        if name == "addBtn":
            btn.setProperty("btn_type", "primary")
            icon_color = "#5ee7a0"
        elif name == "deleteBtn":
            btn.setProperty("btn_type", "danger")
            icon_color = "#ff6b7a"
        else:
            icon_color = "#aab4c4"
        if icon_name:
            btn.setIcon(svg_icon(icon_name, icon_color, 18))
            btn.setIconSize(QSize(18, 18))
        return btn

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("statusBar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(12, 0, 12, 0)

        self._status_dot = QLabel("●")
        self._status_dot.setObjectName("statusDot")
        h.addWidget(self._status_dot)

        self._status_lbl = QLabel(tr("app.ready"))
        self._status_lbl.setObjectName("statusBar")
        h.addWidget(self._status_lbl)
        h.addStretch()

        self._mount_count_lbl = QLabel("")
        self._mount_count_lbl.setObjectName("statusBar")
        h.addWidget(self._mount_count_lbl)
        return bar

    # ------------------------------------------------------------------
    # Tray
    # ------------------------------------------------------------------

    def _setup_tray(self):
        self._tray = SystemTray(self, parent=self)
        self._tray.show()

    # ------------------------------------------------------------------
    # Connection list
    # ------------------------------------------------------------------

    def _refresh_list(self):
        # Lösche alle vorhandenen Widgets
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
        self._containers.clear()  # Container mit Card + Panel
        self._panels.clear()  # Aktive Panels
        self._selected_id = None

        connections = self._mgr.get_all()
        mounted_map = self._controller.get_mounted_drives()

        for conn in connections:
            mounted = conn.drive_letter.upper().rstrip("\\") in {
                k.upper().rstrip("\\") for k in mounted_map.keys()
            }
            
            # Erstelle Container mit Card + Panel
            container = self._create_connection_container(conn, mounted)
            self._list_layout.insertWidget(self._list_layout.count() - 1, container)
            self._containers[conn.id] = container
            self._cards[conn.id] = container._card

        self._update_status()
        self._tray.update_connections_menu(connections, set(mounted_map.keys()))
    
    def _create_connection_container(self, conn, mounted):
        """Erstellt ein Container-Widget mit Card und expandable Panel."""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout
        
        container = QWidget()
        container.setObjectName("connectionContainer")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Die ConnectionCard
        card = ConnectionCard(conn, mounted=mounted)
        card.mount_requested.connect(self._on_mount)
        card.unmount_requested.connect(self._on_unmount)
        card.ssh_requested.connect(self._on_ssh_terminal)
        card.open_path_requested.connect(self._on_open_mounted_path)
        card.info_requested.connect(self._on_show_system_info)
        card.edit_requested.connect(self._on_edit_card)
        card.mousePressEvent = lambda ev, cid=conn.id: self._select_card(cid)
        
        layout.addWidget(card)
        container._card = card
        container._panel = None
        container._conn_id = conn.id
        
        return container

    @pyqtSlot(str)
    def _on_show_system_info(self, conn_id: str):
        """Öffnet die Systeminformationen als Popup-Dialog."""
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return
        from src.ui.system_info_panel import SystemInfoPanel
        from src.ui.dialog_utils import match_parent_height, make_maximize_button

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("sysinfo.title", name=conn.name))
        dlg.setObjectName("systemInfoDialog")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        panel = SystemInfoPanel(conn, parent=dlg)
        panel.closed.connect(dlg.accept)
        lay.addWidget(panel, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addWidget(make_maximize_button(dlg))
        btn_row.addStretch()
        close_btn = QPushButton(tr("dialog.close"))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)
        lay.addLayout(btn_row)

        dlg.resize(560, 520)
        match_parent_height(dlg, self)
        dlg.exec()

    @pyqtSlot(str)
    def _on_edit_card(self, conn_id: str):
        """Bearbeiten einer Verbindung via Edit-Button auf der Card."""
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return
        card = self._cards.get(conn_id)
        if card and card.is_mounted:
            QMessageBox.information(
                self, tr("edit.locked.title"), tr("edit.locked.msg")
            )
            return
        used = [c.drive_letter for c in self._mgr.get_all() if c.id != conn_id]
        dlg = AddEditDialog(self, connection=conn, used_letters=used)
        if dlg.exec():
            updated = dlg.get_connection()
            self._mgr.update(updated)
            self._refresh_list()
            self._set_status(tr("status.connection_updated", name=updated.name))

    @pyqtSlot(str)
    def _on_ssh_terminal(self, conn_id: str):
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return
        from src.ssh_launcher import launch_ssh_terminal
        success, error = launch_ssh_terminal(conn, self._mgr.get_settings())
        if success:
            backend = "PuTTY" if self._mgr.get_settings().use_putty else "SSH"
            self._set_status(tr("status.ssh_started", backend=backend, name=conn.name))
            logger.info(f"SSH-Terminal gestartet: {conn.name} ({backend})")
        else:
            logger.error(f"SSH-Terminal Fehler: {error}")
            QMessageBox.critical(self, "SSH-Terminal", error)


    def _on_open_mounted_path(self, conn_id: str):
        import os, ctypes, subprocess
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return
        path = conn.drive_letter
        if not path.endswith("\\"):
            path += "\\"

        # Wenn die App elevated läuft, ist der Mount nur im Admin-Namespace
        # sichtbar. Der normale Shell-Explorer kommt dann nicht dran (UAC-Prompt,
        # der nicht durchläuft). Wir starten stattdessen explorer.exe direkt als
        # Child dieses Prozesses, damit er im selben Security-Context läuft.
        try:
            is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            is_admin = False

        try:
            if is_admin:
                subprocess.Popen(
                    ["explorer.exe", path],
                    creationflags=0x00000010,  # CREATE_NEW_CONSOLE (detach)
                )
            else:
                os.startfile(path)
            self._set_status(tr("status.opening_explorer", path=path))
        except Exception as e:
            logger.error(f"Konnte {path} nicht öffnen: {e}")
            QMessageBox.warning(self, tr("dialog.error"), str(e))

    def _select_card(self, conn_id: str):
        if self._selected_id and self._selected_id in self._cards:
            prev = self._cards[self._selected_id]
            prev.setProperty("selected", False)
            prev.style().unpolish(prev)
            prev.style().polish(prev)
            
        self._selected_id = conn_id
        if conn_id in self._cards:
            card = self._cards[conn_id]
            card.setProperty("selected", True)
            card.style().unpolish(card)
            card.style().polish(card)

    def _update_status(self):
        connections = self._mgr.get_all()
        mounted = sum(1 for c in self._cards.values() if c.is_mounted)
        total = len(connections)
        self._mount_count_lbl.setText(
            tr("app.mounted_count", mounted=mounted, total=total) if total else tr("app.no_connections")
        )

    # ------------------------------------------------------------------
    # Mount state polling (nur Status-Check, kein Auto-Reconnect)
    # ------------------------------------------------------------------

    def _poll_mount_states(self):
        mounted_map = self._controller.get_mounted_drives()
        mounted_set = {k.upper().rstrip("\\") for k in mounted_map.keys()}

        for conn_id, card in self._cards.items():
            conn = card.connection
            letter_key = conn.drive_letter.upper().rstrip("\\")
            if not letter_key.endswith(":"):
                letter_key += ":"
            is_mounted_now = letter_key in mounted_set
            if is_mounted_now != card.is_mounted:
                card.update_mount_state(is_mounted_now)

        self._update_status()

    # ------------------------------------------------------------------
    # Action slots
    # ------------------------------------------------------------------

    def _on_add(self):
        used = [c.drive_letter for c in self._mgr.get_all()]
        existing = self._mgr.get_all()  # für Template-Dropdown
        dlg = AddEditDialog(self, used_letters=used, existing_connections=existing)
        if dlg.exec():
            conn = dlg.get_connection()
            self._mgr.add(conn)
            self._refresh_list()
            self._set_status(tr("status.connection_added", name=conn.name))

    def _on_delete(self):
        conn_id = self._selected_id
        if not conn_id:
            QMessageBox.information(self, tr("delete.title"), tr("delete.select_one"))
            return
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return
        card = self._cards.get(conn_id)
        if card and card.is_mounted:
            reply = QMessageBox.question(
                self, tr("delete.title"),
                tr("delete.mounted_confirm", name=conn.name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._controller.unmount(conn.drive_letter)
        else:
            reply = QMessageBox.question(
                self, tr("delete.title"),
                tr("delete.confirm", name=conn.name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._mgr.delete(conn_id)
        self._selected_id = None
        self._refresh_list()
        self._set_status(tr("status.connection_deleted", name=conn.name))

    @pyqtSlot(str)
    def _on_mount(self, conn_id: str):
        if conn_id in self._workers:
            logger.debug(f"Mount bereits aktiv für {conn_id}")
            return
            
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return

        self._set_status(tr("status.connecting", name=conn.name, drive=conn.drive_letter))
        logger.info(f"Mount gestartet (async): {conn.name} ({conn.host})")

        # Ensure card shows loading state
        card = self._cards.get(conn_id)
        if card:
            card.show_loading(tr("card.loading.connect"))

        worker = MountWorker(conn, self._controller)
        worker.finished.connect(self._on_mount_finished)
        self._workers[conn_id] = worker
        worker.start()

    def _on_mount_finished(self, conn_id: str, result):
        if conn_id in self._workers:
            self._workers[conn_id].deleteLater()
            del self._workers[conn_id]
            
        conn = self._mgr.get_by_id(conn_id)
        card = self._cards.get(conn_id)
        if card:
            card.hide_loading()

        if result.success:
            if card:
                card.update_mount_state(True)
            self._save_active_mount(conn_id, True)
            if conn:
                self._set_status(tr("status.connected", name=conn.name, drive=conn.drive_letter))
                logger.info(f"Mount erfolgreich: {conn.drive_letter} ← {conn.name}")
        else:
            name = conn.name if conn else "?"
            logger.error(f"Mount fehlgeschlagen: {name} — {result.message}")

            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Critical)
            box.setWindowTitle(tr("mount.failed.title"))

            main_msg = tr("mount.failed.main", name=name)
            troubleshoot = tr(
                "mount.failed.troubleshoot",
                host=conn.host if conn else "?",
                port=conn.port if conn else "?",
            )
            detail_msg = tr("mount.failed.details", msg=result.message)

            box.setText(main_msg + troubleshoot)
            box.setInformativeText(detail_msg)

            retry_btn = box.addButton(tr("mount.failed.retry"), QMessageBox.ButtonRole.ActionRole)
            box.addButton(QMessageBox.StandardButton.Ok)
            box.exec()

            if box.clickedButton() == retry_btn:
                QTimer.singleShot(500, lambda: self._on_mount(conn_id))
                return
            self._set_status(tr("status.connect_failed", name=name))
        self._update_status()

    @pyqtSlot(str)
    def _on_unmount(self, conn_id: str):
        if conn_id in self._workers:
            logger.debug(f"Operation bereits aktiv für {conn_id}")
            return
            
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return

        self._set_status(tr("status.disconnecting", drive=conn.drive_letter))
        logger.info(f"Unmount gestartet (async): {conn.name} ({conn.drive_letter})")

        # Ensure card shows loading state
        card = self._cards.get(conn_id)
        if card:
            card.show_loading(tr("card.loading.disconnect"))

        worker = UnmountWorker(conn_id, conn.drive_letter, self._controller)
        worker.finished.connect(self._on_unmount_finished)
        self._workers[conn_id] = worker
        worker.start()

    def _on_unmount_finished(self, conn_id: str, result):
        if conn_id in self._workers:
            self._workers[conn_id].deleteLater()
            del self._workers[conn_id]
            
        conn = self._mgr.get_by_id(conn_id)
        card = self._cards.get(conn_id)
        if card:
            card.hide_loading()

        if result.success:
            if card:
                card.update_mount_state(False)
            self._save_active_mount(conn_id, False)
            name = conn.name if conn else "?"
            self._set_status(tr("status.disconnected", name=name))
            logger.info(f"Unmount erfolgreich: {conn.drive_letter if conn else '???'}")
        else:
            letter = conn.drive_letter if conn else "???"
            logger.error(f"Unmount fehlgeschlagen: {letter} — {result.message}")
            QMessageBox.critical(self, tr("unmount.failed.title"), result.message)
            if conn:
                self._set_status(tr("status.disconnect_failed", name=conn.name))
        self._update_status()

    def _on_settings(self):
        dlg = SettingsDialog(self, self._mgr.get_settings())
        if dlg.exec():
            self._mgr.save_settings(dlg.get_settings())
            self._apply_settings()
            self._set_status(tr("status.settings_saved"))
            logger.info("Einstellungen gespeichert.")

    def _apply_settings(self):
        interval = self._mgr.get_settings().check_interval_seconds * 1000
        if self._poll_timer.interval() != interval:
            self._poll_timer.setInterval(interval)
        self._apply_debug_mode()

    def _apply_debug_mode(self):
        enabled = self._mgr.get_settings().debug_mode
        self._debug_btn.setVisible(enabled)
        if enabled:
            logger.debug("Debug-Modus aktiviert.")

    def _on_debug(self):
        if not hasattr(self, '_debug_window') or self._debug_window is None:
            self._debug_window = DebugWindow(self)
        self._debug_window.show()
        self._debug_window.raise_()
        self._debug_window.activateWindow()

    def _on_user_management(self):
        if not Session.is_admin():
            return
        UserManagementDialog(self).exec()

    def _on_change_own_password(self):
        user = Session.current()
        if not user:
            return
        from src.ui.dialogs.login_dialog import ChangePasswordDialog
        ChangePasswordDialog(user.id, self).exec()

    def _on_logout(self):
        reply = QMessageBox.question(
            self, tr("logout.title"),
            tr("logout.confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Alle Mounts trennen
        self._unmount_all()

        Session.logout()

        # Hauptfenster verstecken während Login läuft
        self.hide()

        # Login-Dialog ohne Parent anzeigen (eigenes Fenster)
        from src.ui.dialogs.login_dialog import LoginDialog
        login = LoginDialog(parent=None)
        result = login.exec()

        if result == QDialog.DialogCode.Accepted and Session.is_logged_in():
            # Neuen Manager für eingeloggten Benutzer
            self._user = Session.current()
            self._mgr = UserConnectionManager(self._user)
            self._refresh_list()
            self._apply_settings()
            self.setWindowTitle(
                f"NEO SSH-Win Manager v1.1.0 – {Session.current().username}"
            )
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            # Kein Login → App wirklich beenden
            QApplication.quit()

    def _on_about(self):
        AboutDialog(self).exec()

    # ------------------------------------------------------------------
    # Window close – Mounts bleiben aktiv!
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        """
        Fenster schließen:
          - minimize_to_tray=True  → Fenster verstecken, im Tray weiter
          - minimize_to_tray=False → App beenden, Mounts trennen, SSHFS-Prozesse killen
        """
        settings = self._mgr.get_settings()
        if settings.minimize_to_tray:
            event.ignore()
            self.hide()
            self._tray.showMessage(
                "NEO SSH-Win Manager",
                tr("tray.running"),
                self._tray.MessageIcon.Information,
                2000,
            )
        else:
            # Alle Mounts trennen und SSHFS-Prozesse beenden
            self._unmount_all()
            self._kill_sshfs_processes()
            event.accept()
            QApplication.quit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, msg: str):
        self._status_lbl.setText(msg)

    def _check_prerequisites(self):
        status = SSHFSController.get_install_status()
        if not status["winfsp"] and not status["sshfs_win"]:
            self._set_status(tr("prereq.missing_both"))
        elif not status["winfsp"]:
            self._set_status(tr("prereq.missing_winfsp"))
        elif not status["sshfs_win"]:
            self._set_status(tr("prereq.missing_sshfs"))
        else:
            self._set_status(tr("prereq.ok", path=status['sshfs_exe']))

    # ------------------------------------------------------------------
    # Active Mounts Tracking
    # ------------------------------------------------------------------

    def _load_active_mounts(self):
        """Lädt die zuletzt aktiven Mounts aus der Datenbank."""
        try:
            self._active_mounts = set(self._mgr.get_active_mounts())
            logger.info(f"Aktive Mounts geladen: {len(self._active_mounts)}")
        except Exception as e:
            logger.warning(f"Konnte aktive Mounts nicht laden: {e}")
            self._active_mounts = set()

    def _save_active_mount(self, conn_id: str, mounted: bool):
        """Speichert den Mount-Status in der Datenbank."""
        try:
            if mounted:
                self._mgr.add_active_mount(conn_id)
                self._active_mounts.add(conn_id)
            else:
                self._mgr.remove_active_mount(conn_id)
                self._active_mounts.discard(conn_id)
        except Exception as e:
            logger.warning(f"Konnte Mount-Status nicht speichern: {e}")

    def _auto_reconnect_mounts(self):
        """Stellt zuletzt aktive Verbindungen wieder her (nur beim Start)."""
        if not self._mgr.get_settings().auto_reconnect_mounts:
            return
        
        active_ids = self._mgr.get_active_mounts()
        if not active_ids:
            return
        
        logger.info(f"Auto-Reconnect: {len(active_ids)} Verbindungen werden wiederhergestellt...")
        self._set_status(f"Wiederherstellen von {len(active_ids)} Verbindungen...")
        
        for conn_id in active_ids:
            conn = self._mgr.get_by_id(conn_id)
            if conn:
                # Nur reconnecten wenn nicht schon gemountet
                if not self._controller.is_mounted(conn.drive_letter):
                    logger.info(f"Auto-Reconnect: {conn.name} ({conn.drive_letter})")
                    QTimer.singleShot(1000, lambda cid=conn_id: self._on_mount(cid))

    def _unmount_all(self):
        """Trennt alle aktiven Mounts (beim Logout/Schließen)."""
        mounted_map = self._controller.get_mounted_drives()
        if not mounted_map:
            return
        
        logger.info(f"Unmount all: {len(mounted_map)} Laufwerke werden getrennt...")
        for letter in mounted_map.keys():
            try:
                self._controller.unmount(letter)
            except Exception as e:
                logger.warning(f"Unmount {letter} fehlgeschlagen: {e}")

    def _kill_sshfs_processes(self):
        """Beendet alle SSHFS-Prozesse beim Schließen der App."""
        import subprocess
        for proc_name in ["sshfs.exe", "sshfs-win.exe", "sshfs-win-broker.exe"]:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", proc_name],
                    capture_output=True,
                    creationflags=0x08000000,
                )
            except Exception:
                pass
