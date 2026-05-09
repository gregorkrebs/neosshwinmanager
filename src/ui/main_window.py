"""
main_window.py – The primary application window for NEO SSH-Win Manager.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QScrollArea,
    QMessageBox, QApplication, QSystemTrayIcon, QDialog,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QFrame,
    QFileDialog, QRadioButton, QDialogButtonBox,
    QInputDialog, QSplitter, QSplitterHandle, QSizePolicy, QStackedWidget
)
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor, QPen, QBrush, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QSize
import os
from PyQt6 import sip
import ctypes
import ctypes.wintypes
import json

from src.auth_manager import Session, UserConnectionManager
from src.sshfs_controller import SSHFSController, _is_safe_label
from src.config import Connection, AppSettings
from src.ui.connection_card import ConnectionCard
from src.ui.system_tray import SystemTray
from src.ui.debug_window import DebugWindow
from src.app_logger import logger
from src.ui.worker import MountWorker, UnmountWorker
from src.ui.icons import icon as svg_icon
from src.ui.widgets.no_wheel import NoWheelComboBox, NoWheelSpinBox
from src.i18n import tr, current_language, available_languages
from PyQt6.QtCore import QThread


_LANG_LABELS = {"en": "English", "de": "Deutsch"}

# Right-panel mode constants
_PANEL_NONE     = "none"
_PANEL_INFO     = "info"
_PANEL_SYSINFO  = "sysinfo"
_PANEL_EDIT     = "edit"
_PANEL_SETTINGS = "settings"
_PANEL_ADD      = "add"
_PANEL_USERS    = "users"


class _PillHandle(QSplitterHandle):
    """Splitter handle that paints a centred pill indicator."""
    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pill_w, pill_h = 4, 36
        x = (w - pill_w) // 2
        y = (h - pill_h) // 2
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(QColor(0, 180, 216, 55)))
        painter.drawRoundedRect(x, y, pill_w, pill_h, pill_w, pill_w)
        painter.end()


class _PillSplitter(QSplitter):
    """QSplitter that uses _PillHandle for its divider."""
    def createHandle(self) -> QSplitterHandle:  # noqa: N802
        return _PillHandle(self.orientation(), self)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._user = Session.current()
        self._mgr = UserConnectionManager(self._user)
        self._controller = SSHFSController()
        self._cards: dict[str, ConnectionCard] = {}
        self._selected_id: str | None = None
        self._workers: dict[str, QThread] = {}
        self._panel_mode: str = _PANEL_NONE
        self._panel_conn_id: str | None = None   # which connection the panel belongs to
        self._ef_initial_snapshot: dict | None = None
        self._saving_in_progress = False
        self._shortcuts: list[QShortcut] = []
        
        # Debug mode settings
        self._debug_mode = False  # Can be toggled via F2

        self.setObjectName("MainWindow")
        self.setWindowTitle("NEO SSH-Win Manager v1.4.0")
        self.setMinimumSize(820, 520)
        self.resize(1100, 640)

        def get_resource_path(relative_path):
            import sys
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                relative_path
            )

        for icon_file in ("app_icon.ico", "app_icon.png"):
            icon_path = get_resource_path(os.path.join("assets", icon_file))
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break

        self._build_ui()
        self._setup_tray()
        self._refresh_list()
        self._apply_debug_mode()
        self._setup_ipc()

        # Setup keyboard shortcut for debug mode toggle (F2)
        debug_shortcut = QShortcut(QKeySequence("F2"), self)
        debug_shortcut.activated.connect(self._debug_widget_under_mouse)
        self._shortcuts.append(debug_shortcut)
        self._install_shortcuts()

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_mount_states)
        self._poll_timer.start(self._mgr.get_settings().check_interval_seconds * 1000)

        self._check_prerequisites()
        QTimer.singleShot(2000, self._auto_reconnect_mounts)
        QTimer.singleShot(0, self._apply_titlebar_color)

        import src.app_logger as _log_mod
        _em = _log_mod.log_emitter
        if _em is not None:
            _em.new_record.connect(self._on_log_record_for_status)

        logger.info("NEO SSH-Win Manager gestartet.")

    # ------------------------------------------------------------------
    # CLI Access / IPC
    # ------------------------------------------------------------------

    def _setup_ipc(self):
        import threading
        self._ipc_pipe_name = r"\\.\pipe\SSHWinManager_IPC_v1"
        self._ipc_running = True
        self._ipc_thread = threading.Thread(target=self._ipc_listener, daemon=True)
        self._ipc_thread.start()

    def _ipc_listener(self):
        import time
        PIPE_ACCESS_DUPLEX    = 0x00000003
        PIPE_TYPE_MESSAGE     = 0x00000004
        PIPE_READMODE_MESSAGE = 0x00000002
        PIPE_WAIT             = 0x00000000

        while self._ipc_running:
            try:
                pipe = ctypes.windll.kernel32.CreateNamedPipeW(
                    self._ipc_pipe_name, PIPE_ACCESS_DUPLEX,
                    PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
                    5, 65536, 65536, 5000, None
                )
                if pipe == -1:
                    time.sleep(1)
                    continue
                ctypes.windll.kernel32.ConnectNamedPipe(pipe, None)
                if not self._ipc_running:
                    ctypes.windll.kernel32.CloseHandle(pipe)
                    break
                buf  = ctypes.create_string_buffer(65536)
                read = ctypes.wintypes.DWORD()
                if ctypes.windll.kernel32.ReadFile(pipe, buf, 65536, ctypes.byref(read), None):
                    try:
                        request = json.loads(buf.value[:read.value].decode('utf-8'))
                        if request.get("action") == "cli_connect":
                            conn = self._mgr.get_by_cli_key(request.get("key", ""))
                            if conn:
                                response = {"success": True, "connection": {
                                    "id": conn.id, "name": conn.name,
                                    "host": conn.host, "user": conn.user,
                                    "port": conn.port, "remote_path": conn.remote_path,
                                    "auth_method": conn.auth_method,
                                    "password": conn.password, "key_path": conn.key_path,
                                }}
                            else:
                                response = {"success": False, "error": "Ungültiger Access Key."}
                            res = json.dumps(response).encode('utf-8')
                            written = ctypes.wintypes.DWORD()
                            ctypes.windll.kernel32.WriteFile(pipe, res, len(res), ctypes.byref(written), None)
                            ctypes.windll.kernel32.FlushFileBuffers(pipe)
                    except Exception as e:
                        logger.error(f"IPC Request Fehler: {e}")
                ctypes.windll.kernel32.DisconnectNamedPipe(pipe)
                ctypes.windll.kernel32.CloseHandle(pipe)
            except Exception as e:
                logger.error(f"IPC Listener Fehler: {e}")
                time.sleep(1)

    def _stop_ipc(self):
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

        self._active_mounts: set[str] = set()
        self._load_active_mounts()
        self._containers: dict[str, object] = {}

        # Outer body: sidebar (always visible) + main content stack
        body = QWidget()
        body_h = QHBoxLayout(body)
        body_h.setContentsMargins(0, 0, 0, 0)
        body_h.setSpacing(0)
        body_h.addWidget(self._build_sidebar())

        # Stack page 0: connections list + resizable right panel
        self._right_panel_widget = self._build_right_panel()
        self._body_splitter = _PillSplitter(Qt.Orientation.Horizontal)
        self._body_splitter.setObjectName("bodySplitter")
        self._body_splitter.setHandleWidth(14)
        self._body_splitter.addWidget(self._build_connections_panel())
        self._body_splitter.addWidget(self._right_panel_widget)
        self._body_splitter.setCollapsible(0, False)
        self._body_splitter.setCollapsible(1, False)
        self._body_splitter.setSizes([420, 620])
        self._body_splitter.splitterMoved.connect(self._clamp_splitter_40)

        # Stack page 1: full-screen panel (settings, users)
        self._fullscreen_widget = self._build_fullscreen_panel()

        self._main_stack = QStackedWidget()
        self._main_stack.addWidget(self._body_splitter)   # index 0
        self._main_stack.addWidget(self._fullscreen_widget)  # index 1

        body_h.addWidget(self._main_stack, stretch=1)

        root.addWidget(body, stretch=1)
        root.addWidget(self._build_status_bar())
        self._show_right_panel_placeholder()

    def _sidebar_btn(self, icon_name: str, slot=None, *, active: bool = False, btn_type: str = "") -> QPushButton:
        btn = QPushButton()
        btn.setObjectName("sidebarBtn")
        btn.setFixedSize(QSize(42, 42))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if active:
            btn.setProperty("active", "true")
        if btn_type:
            btn.setProperty("btn_type", btn_type)
        color = "#ef4444" if btn_type == "danger" else ("#f59e0b" if btn_type == "warning" else "#aab4c4")
        if active:
            color = "#00b4d8"
        btn.setIcon(svg_icon(icon_name, color, 18))
        btn.setIconSize(QSize(18, 18))
        if slot:
            btn.clicked.connect(slot)
        return btn

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(60)
        v = QVBoxLayout(sidebar)
        v.setContentsMargins(8, 10, 8, 10)
        v.setSpacing(8)
        v.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._sb_home_btn = self._sidebar_btn("cloud", active=True)
        self._sb_home_btn.clicked.connect(self._nav_home)
        v.addWidget(self._sb_home_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        self._sb_settings_btn = self._sidebar_btn("settings", self._on_settings)
        v.addWidget(self._sb_settings_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        self._sb_users_btn = None
        if Session.is_admin():
            self._sb_users_btn = self._sidebar_btn("users", self._on_user_management)
            v.addWidget(self._sb_users_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        v.addStretch()

        self._debug_btn = self._sidebar_btn("bug", self._on_debug, btn_type="warning")
        self._debug_btn.setVisible(False)
        v.addWidget(self._debug_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        self._about_btn = self._sidebar_btn("info", self._on_about)
        v.addWidget(self._about_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        logout_btn = self._sidebar_btn("logout", self._on_logout, btn_type="danger")
        v.addWidget(logout_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        return sidebar

    def _set_sidebar_active(self, name: str):
        """Set active state on tracked sidebar buttons. name: 'home'|'settings'|'users'"""
        candidates = [
            ("home",     "cloud",    self._sb_home_btn),
            ("settings", "settings", self._sb_settings_btn),
            ("users",    "users",    self._sb_users_btn),
        ]
        for key, icon_name, btn in candidates:
            if btn is None:
                continue
            is_active = key == name
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.setIcon(svg_icon(icon_name, "#00b4d8" if is_active else "#aab4c4", 18))
            btn.setIconSize(QSize(18, 18))

    def _build_connections_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("connectionsPanel")
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        header = QWidget()
        header.setObjectName("connectionsHeader")
        header_h = QHBoxLayout(header)
        header_h.setContentsMargins(18, 12, 18, 12)
        header_h.setSpacing(8)

        title_wrap = QWidget()
        title_wrap.setObjectName("connectionsTitleWrap")
        title_layout = QVBoxLayout(title_wrap)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title_lbl = QLabel(tr("header.connections"))
        title_lbl.setObjectName("connectionsTitle")
        title_layout.addWidget(title_lbl)

        header_h.addWidget(title_wrap)
        header_h.addStretch()

        self._add_btn = QPushButton()
        self._add_btn.setObjectName("headerAddBtn")
        self._add_btn.setFixedSize(QSize(32, 32))
        self._add_btn.setIcon(svg_icon("plus", "#aab4c4", 16))
        self._add_btn.setIconSize(QSize(16, 16))
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setToolTip(tr("main.add_connection"))
        self._add_btn.clicked.connect(self._on_add)
        header_h.addWidget(self._add_btn)

        self._badge_lbl = QLabel("")
        self._badge_lbl.setObjectName("connectionsBadge")
        self._badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge_lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        header_h.addWidget(self._badge_lbl)

        v.addWidget(header)

        scroll = QScrollArea()
        scroll.setObjectName("connectionScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._list_container = QWidget()
        self._list_container.setObjectName("connectionList")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(12, 12, 12, 12)
        self._list_layout.setSpacing(10)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        v.addWidget(scroll)
        return panel

    def _build_right_panel(self) -> QWidget:
        """Container for the right panel — content is swapped dynamically."""
        panel = QWidget()
        panel.setObjectName("rightPanel")
        panel.setMinimumWidth(10)
        panel.setMaximumWidth(16777215)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Header row (title + action buttons)
        header = QWidget()
        header.setObjectName("rightPanelHeader")
        hh = QHBoxLayout(header)
        hh.setContentsMargins(18, 12, 18, 12)
        hh.setSpacing(8)

        title_wrap = QWidget()
        title_wrap.setObjectName("rightPanelTitleWrap")
        title_layout = QVBoxLayout(title_wrap)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._right_panel_title = QLabel("")
        self._right_panel_title.setObjectName("rightPanelTitle")
        title_layout.addWidget(self._right_panel_title)

        hh.addWidget(title_wrap)
        hh.addStretch()

        # Info button (shown in info mode - opens system info panel)
        self._rp_info_btn = QPushButton("i")
        self._rp_info_btn.setObjectName("cardInfoBtn")
        self._rp_info_btn.setFixedSize(QSize(32, 32))
        self._rp_info_btn.setIconSize(QSize(14, 14))
        self._rp_info_btn.setToolTip(tr("card.tooltip.info"))
        self._rp_info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rp_info_btn.clicked.connect(self._on_rp_info_clicked)
        self._rp_info_btn.setVisible(False)
        self._rp_info_btn.setAccessibleName(tr("card.tooltip.info"))
        hh.addWidget(self._rp_info_btn)

        # Edit button (shown in info mode)
        self._rp_edit_btn = QPushButton()
        self._rp_edit_btn.setObjectName("rpHeaderBtn")
        self._rp_edit_btn.setFixedSize(QSize(32, 32))
        self._rp_edit_btn.setIcon(svg_icon("edit", "#aab4c4", 15))
        self._rp_edit_btn.setIconSize(QSize(15, 15))
        self._rp_edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rp_edit_btn.setToolTip(tr("card.tooltip.edit"))
        self._rp_edit_btn.clicked.connect(self._on_rp_edit_clicked)
        self._rp_edit_btn.setVisible(False)
        self._rp_edit_btn.setAccessibleName(tr("card.tooltip.edit"))
        hh.addWidget(self._rp_edit_btn)

        # Terminal button (shown in info/sysinfo mode)
        self._rp_terminal_btn = QPushButton()
        self._rp_terminal_btn.setObjectName("rpHeaderBtn")
        self._rp_terminal_btn.setFixedSize(QSize(32, 32))
        self._rp_terminal_btn.setIcon(svg_icon("terminal", "#aab4c4", 15))
        self._rp_terminal_btn.setIconSize(QSize(15, 15))
        self._rp_terminal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rp_terminal_btn.setToolTip(tr("card.tooltip.ssh"))
        self._rp_terminal_btn.clicked.connect(self._on_rp_terminal_clicked)
        self._rp_terminal_btn.setVisible(False)
        self._rp_terminal_btn.setAccessibleName(tr("card.tooltip.ssh"))
        hh.addWidget(self._rp_terminal_btn)

        # Mount/Unmount button (shown in info/sysinfo mode)
        self._rp_mount_btn = QPushButton()
        self._rp_mount_btn.setObjectName("rpHeaderBtn")
        self._rp_mount_btn.setFixedSize(QSize(32, 32))
        self._rp_mount_btn.setIconSize(QSize(15, 15))
        self._rp_mount_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rp_mount_btn.clicked.connect(self._on_rp_mount_clicked)
        self._rp_mount_btn.setVisible(False)
        hh.addWidget(self._rp_mount_btn)

        # Delete button (shown in info/edit mode)
        self._rp_del_btn = QPushButton()
        self._rp_del_btn.setObjectName("rpHeaderBtn")
        self._rp_del_btn.setProperty("btn_type", "danger")
        self._rp_del_btn.setFixedSize(QSize(32, 32))
        # Icon is white on danger background
        self._rp_del_btn.setIcon(svg_icon("trash", "#ffffff", 15))
        self._rp_del_btn.setIconSize(QSize(15, 15))
        self._rp_del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rp_del_btn.setToolTip(tr("main.delete"))
        self._rp_del_btn.clicked.connect(self._on_delete)
        self._rp_del_btn.setVisible(False)
        self._rp_del_btn.setAccessibleName(tr("main.delete"))
        hh.addWidget(self._rp_del_btn)

        self._rp_save_top_btn = QPushButton()
        self._rp_save_top_btn.setObjectName("rpHeaderSaveBtn")
        self._rp_save_top_btn.setFixedSize(QSize(32, 32))
        self._rp_save_top_btn.setIcon(svg_icon("check", "#deebf7", 15))
        self._rp_save_top_btn.setIconSize(QSize(15, 15))
        self._rp_save_top_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rp_save_top_btn.setToolTip(tr("card.tooltip.save_top"))
        self._rp_save_top_btn.clicked.connect(self._on_rp_save)
        self._rp_save_top_btn.setVisible(False)
        self._rp_save_top_btn.setAccessibleName(tr("card.tooltip.save_top"))
        hh.addWidget(self._rp_save_top_btn)

        self._rp_cancel_top_btn = QPushButton()
        self._rp_cancel_top_btn.setObjectName("rpHeaderBtn")
        self._rp_cancel_top_btn.setFixedSize(QSize(32, 32))
        self._rp_cancel_top_btn.setIcon(svg_icon("x", "#aab4c4", 15))
        self._rp_cancel_top_btn.setIconSize(QSize(15, 15))
        self._rp_cancel_top_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rp_cancel_top_btn.setToolTip(tr("card.tooltip.cancel_top"))
        self._rp_cancel_top_btn.clicked.connect(self._on_rp_cancel)
        self._rp_cancel_top_btn.setVisible(False)
        self._rp_cancel_top_btn.setAccessibleName(tr("card.tooltip.cancel_top"))
        hh.addWidget(self._rp_cancel_top_btn)

        # Close button
        self._rp_close_btn = QPushButton()
        self._rp_close_btn.setObjectName("rpHeaderBtn")
        self._rp_close_btn.setFixedSize(QSize(32, 32))
        self._rp_close_btn.setIcon(svg_icon("x", "#6a7a8a", 15))
        self._rp_close_btn.setIconSize(QSize(15, 15))
        self._rp_close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rp_close_btn.setToolTip(tr("dialog.close"))
        self._rp_close_btn.clicked.connect(self._close_right_panel)
        self._rp_close_btn.setAccessibleName(tr("dialog.close"))
        hh.addWidget(self._rp_close_btn)

        v.addWidget(header)

        # Scrollable content area
        self._rp_scroll = QScrollArea()
        self._rp_scroll.setObjectName("rightPanelScroll")
        self._rp_scroll.setWidgetResizable(True)
        self._rp_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._rp_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._rp_content = QWidget()
        self._rp_content.setObjectName("rightPanelContent")
        self._rp_layout = QVBoxLayout(self._rp_content)
        self._rp_layout.setContentsMargins(0, 0, 0, 0)
        self._rp_layout.setSpacing(0)
        self._rp_scroll.setWidget(self._rp_content)
        v.addWidget(self._rp_scroll, stretch=1)

        # Save/Cancel button bar (only visible in edit/add mode)
        self._rp_btn_bar = QWidget()
        self._rp_btn_bar.setObjectName("rpBtnBar")
        bb = QHBoxLayout(self._rp_btn_bar)
        bb.setContentsMargins(12, 8, 12, 12)
        bb.setSpacing(8)
        bb.addStretch()
        self._rp_cancel_btn = QPushButton(tr("dialog.cancel"))
        self._rp_cancel_btn.setObjectName("secondaryBtn")
        self._rp_cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rp_cancel_btn.setToolTip(tr("card.tooltip.cancel_top"))
        self._rp_cancel_btn.clicked.connect(self._on_rp_cancel)
        bb.addWidget(self._rp_cancel_btn)
        self._rp_save_btn = QPushButton(tr("dialog.save"))
        self._rp_save_btn.setObjectName("primaryBtn")
        self._rp_save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rp_save_btn.setToolTip(tr("card.tooltip.save_top"))
        self._rp_save_btn.clicked.connect(self._on_rp_save)
        bb.addWidget(self._rp_save_btn)
        self._rp_btn_bar.setVisible(False)
        v.addWidget(self._rp_btn_bar)

        return panel

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("statusBar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 10, 14, 10)
        h.setSpacing(8)

        self._status_dot = QLabel("●")
        self._status_dot.setObjectName("statusDot")
        h.addWidget(self._status_dot)

        self._status_lbl = QLabel(tr("app.ready"))
        self._status_lbl.setObjectName("statusText")
        h.addWidget(self._status_lbl)

        h.addStretch()

        self._mount_count_lbl = QLabel("")
        self._mount_count_lbl.setObjectName("versionLabel")
        h.addWidget(self._mount_count_lbl)

        ver_lbl = QLabel("  v1.3.2")
        ver_lbl.setObjectName("versionLabel")
        h.addWidget(ver_lbl)

        return bar

    def _build_fullscreen_panel(self) -> QWidget:
        """Full-screen content panel used for settings and user management."""
        panel = QWidget()
        panel.setObjectName("fullscreenPanel")
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self._fs_header = QWidget()
        self._fs_header.setObjectName("rightPanelHeader")
        fh = QHBoxLayout(self._fs_header)
        fh.setContentsMargins(16, 0, 16, 0)
        fh.setSpacing(12)

        fs_title_wrap = QWidget()
        fs_title_wrap.setObjectName("rightPanelTitleWrap")
        fs_title_layout = QVBoxLayout(fs_title_wrap)
        fs_title_layout.setContentsMargins(0, 0, 0, 0)
        fs_title_layout.setSpacing(0)
        fs_title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._fs_title = QLabel()
        self._fs_title.setObjectName("rightPanelTitle")
        fs_title_layout.addWidget(self._fs_title)

        fh.addWidget(fs_title_wrap, 1)

        self._fs_close_btn = QPushButton()
        self._fs_close_btn.setObjectName("rpHeaderBtn")
        self._fs_close_btn.setFixedSize(QSize(32, 32))
        self._fs_close_btn.setIcon(svg_icon("x", "#aab4c4", 15))
        self._fs_close_btn.setIconSize(QSize(15, 15))
        self._fs_close_btn.setToolTip(tr("dialog.close"))
        self._fs_close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fs_close_btn.clicked.connect(self._nav_home)
        fh.addWidget(self._fs_close_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self._fs_header.setVisible(False)
        v.addWidget(self._fs_header)

        self._fs_scroll = QScrollArea()
        self._fs_scroll.setObjectName("rightPanelScroll")
        self._fs_scroll.setWidgetResizable(True)
        self._fs_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._fs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._fs_content = QWidget()
        self._fs_content.setObjectName("fullscreenContent")
        self._fs_layout = QVBoxLayout(self._fs_content)
        self._fs_layout.setContentsMargins(0, 0, 0, 0)
        self._fs_layout.setSpacing(0)
        self._fs_scroll.setWidget(self._fs_content)
        v.addWidget(self._fs_scroll, stretch=1)

        self._fs_btn_bar = QWidget()
        self._fs_btn_bar.setObjectName("rpBtnBar")
        bb = QHBoxLayout(self._fs_btn_bar)
        bb.setContentsMargins(24, 8, 24, 12)
        bb.setSpacing(8)
        bb.addStretch()
        self._fs_cancel_btn = QPushButton(tr("dialog.cancel"))
        self._fs_cancel_btn.setObjectName("secondaryBtn")
        self._fs_cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fs_cancel_btn.clicked.connect(self._nav_home)
        bb.addWidget(self._fs_cancel_btn)
        self._fs_save_btn = QPushButton(tr("dialog.save"))
        self._fs_save_btn.setObjectName("primaryBtn")
        self._fs_save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fs_save_btn.clicked.connect(self._on_fs_save)
        bb.addWidget(self._fs_save_btn)
        self._fs_btn_bar.setVisible(False)
        v.addWidget(self._fs_btn_bar)

        return panel

    def _clear_fs_content(self):
        while self._fs_layout.count():
            item = self._fs_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _set_fullscreen_header(self, kicker: str = "", title: str = "", show_close: bool = True):
        self._fs_title.setText(title)
        self._fs_title.setVisible(bool(title))
        self._fs_close_btn.setVisible(show_close)
        self._fs_header.setVisible(bool(title or show_close))

    def _nav_home(self):
        """Return to connections view and reset sidebar to home."""
        if not self._guard_leave_form():
            return
        self._clear_fs_content()
        self._set_fullscreen_header("", "", False)
        self._main_stack.setCurrentIndex(0)
        self._panel_mode = _PANEL_NONE
        self._panel_conn_id = None
        self._set_sidebar_active("home")
        self._close_right_panel_force()

    def _on_fs_save(self):
        if self._panel_mode == _PANEL_SETTINGS:
            self._save_settings_form()

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
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
        self._containers.clear()
        self._selected_id = None

        connections = self._mgr.get_all()
        mounted_map = self._controller.get_mounted_drives()

        for conn in connections:
            mounted = conn.drive_letter.upper().rstrip("\\") in {
                k.upper().rstrip("\\") for k in mounted_map.keys()
            }
            container = self._create_connection_container(conn, mounted)
            self._list_layout.insertWidget(self._list_layout.count() - 1, container)
            self._containers[conn.id] = container
            self._cards[conn.id] = container._card

        self._update_status()
        self._tray.update_connections_menu(connections, set(mounted_map.keys()))

    def _create_connection_container(self, conn, mounted):
        container = QWidget()
        container.setObjectName("connectionContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card = ConnectionCard(conn, mounted=mounted)
        card.mount_requested.connect(self._on_mount)
        card.unmount_requested.connect(self._on_unmount)
        card.ssh_requested.connect(self._on_ssh_terminal)
        card.open_path_requested.connect(self._on_open_mounted_path)
        card.info_requested.connect(self._on_info_requested)
        card.edit_requested.connect(self._open_edit_panel)
        card.mousePressEvent = lambda ev, cid=conn.id: self._select_card(cid)

        layout.addWidget(card)
        container._card = card
        container._conn_id = conn.id
        return container

    # ------------------------------------------------------------------
    # Right panel management
    # ------------------------------------------------------------------

    def _clear_right_panel_content(self):
        """Remove all widgets from the scrollable content area."""
        while self._rp_layout.count():
            item = self._rp_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        # Prevent stale references to deleted Qt widgets from later save/click handlers.
        self._reset_edit_form_refs()

    def _reset_edit_form_refs(self):
        """Clear edit/add form widget references after panel content gets rebuilt."""
        for attr in (
            "_ef_conn", "_ef_name", "_ef_host", "_ef_user", "_ef_path", "_ef_port",
            "_ef_drive", "_ef_auth", "_ef_pw", "_ef_key", "_ef_cli_cb",
            "_ef_cli_widget", "_ef_cli_key", "_ef_cli_copy_btn", "_ef_cli_gen_btn",
            "_ef_putty_key"
        ):
            setattr(self, attr, None)
        self._ef_initial_snapshot = None

    def _ensure_panel_sized(self):
        """Give the right panel a visible size the first time it opens."""
        sizes = self._body_splitter.sizes()
        # If right panel currently has no width, give it a comfortable docked size.
        if len(sizes) == 2 and sizes[1] < 420:
            total = sizes[0] + sizes[1]
            self._body_splitter.setSizes([max(total - 420, 260), 420])

    def _clamp_splitter_40(self, pos: int = 0, index: int = 0) -> None:
        sp = self._body_splitter
        total = sp.widget(0).width() + sp.widget(1).width() + sp.handleWidth()
        if total <= 0:
            return
        min_w = total * 2 // 5
        sizes = sp.sizes()
        if sizes[0] < min_w:
            sp.setSizes([min_w, total - min_w])
        elif sizes[1] < min_w:
            sp.setSizes([total - min_w, min_w])

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_body_splitter"):
            self._clamp_splitter_40()

    def _set_right_panel_header(self, kicker: str = "", title: str = ""):
        self._right_panel_title.setText(title)
        self._right_panel_title.setVisible(bool(title))

    def _show_right_panel_placeholder(self):
        """Render the default empty-state panel instead of collapsing the area."""
        self._clear_right_panel_content()
        self._set_right_panel_header()
        self._rp_info_btn.setVisible(False)
        self._rp_edit_btn.setVisible(False)
        self._rp_terminal_btn.setVisible(False)
        self._rp_mount_btn.setVisible(False)
        self._rp_del_btn.setVisible(False)
        self._rp_save_top_btn.setVisible(False)
        self._rp_cancel_top_btn.setVisible(False)
        self._rp_close_btn.setVisible(False)
        self._rp_btn_bar.setVisible(False)

        body = QWidget()
        body.setObjectName("rightPanelPlaceholder")
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        v = QVBoxLayout(body)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(12)
        v.addStretch()

        copy = QWidget()
        copy.setObjectName("rightPanelPlaceholderCopy")
        copy.setFixedWidth(360)
        copy_layout = QVBoxLayout(copy)
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(10)

        title = QLabel(tr("panel.placeholder.title"))
        title.setObjectName("rightPanelPlaceholderTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        copy_layout.addWidget(title)

        msg = QLabel(tr("panel.placeholder.body"))
        msg.setObjectName("rightPanelPlaceholderBody")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        copy_layout.addWidget(msg)

        v.addWidget(copy, 0, Qt.AlignmentFlag.AlignHCenter)

        v.addStretch()
        self._rp_layout.addWidget(body, stretch=1)
        self._right_panel_widget.setVisible(True)
        self._ensure_panel_sized()

    def _close_right_panel(self):
        """Reset the right panel to its placeholder state and deselect."""
        if not self._guard_leave_form():
            return
        self._close_right_panel_force()

    def _close_right_panel_force(self):
        """Close right panel without dirty-check prompt."""
        # Deactivate info btn on previously active card
        if self._panel_conn_id and self._panel_conn_id in self._cards:
            self._cards[self._panel_conn_id].set_info_active(False)
        self._panel_mode = _PANEL_NONE
        self._panel_conn_id = None
        # Also deselect card highlight
        if self._selected_id and self._selected_id in self._cards:
            card = self._cards[self._selected_id]
            card.setProperty("selected", False)
            card.style().unpolish(card)
            card.style().polish(card)
        self._selected_id = None
        self._show_right_panel_placeholder()

    def _open_info_panel(self, conn_id: str):
        """Show connection details (host data / credentials) for the given connection."""
        if (self._panel_mode in (_PANEL_EDIT, _PANEL_ADD)) and (conn_id != self._panel_conn_id):
            if not self._guard_leave_form():
                return
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return

        if self._panel_conn_id and self._panel_conn_id in self._cards:
            self._cards[self._panel_conn_id].set_info_active(False)

        self._panel_mode = _PANEL_INFO
        self._panel_conn_id = conn_id

        card = self._cards.get(conn_id)
        is_mounted = card and card.is_mounted

        self._set_right_panel_header(tr("panel.header.details"), conn.name.upper())
        # Info button - always visible in info mode
        self._rp_info_btn.setVisible(True)
        # Edit button: enabled=accent color, disabled=muted (theme-aware)
        theme = self._mgr.get_settings().theme or "dark"
        if is_mounted:
            edit_icon_color = "#aab4c4" if theme == "light" else "#2a3a4a"
        else:
            edit_icon_color = "#0077b6" if theme == "light" else "#aab4c4"
        self._rp_edit_btn.setIcon(svg_icon("edit", edit_icon_color, 15))
        self._rp_edit_btn.setVisible(True)
        self._rp_edit_btn.setEnabled(not is_mounted)
        self._rp_edit_btn.setToolTip(
            tr("card.tooltip.edit_locked") if is_mounted else tr("card.tooltip.edit")
        )
        # Header actions (overview): Sysinfo → Edit → Terminal → Mount → Close
        self._rp_terminal_btn.setVisible(True)
        self._rp_mount_btn.setVisible(True)
        self._sync_rp_mount_button(conn_id)

        self._rp_del_btn.setVisible(False)
        self._rp_save_top_btn.setVisible(False)
        self._rp_cancel_top_btn.setVisible(False)
        self._rp_close_btn.setVisible(True)
        self._rp_btn_bar.setVisible(False)

        self._clear_right_panel_content()
        self._build_info_content(conn)
        self._right_panel_widget.setVisible(True)
        self._ensure_panel_sized()

    def _open_sysinfo_panel(self, conn_id: str):
        """Show system info (SSH stats) for the given connection — always, regardless of mount."""
        if self._panel_mode in (_PANEL_EDIT, _PANEL_ADD):
            if not self._guard_leave_form():
                return
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return

        if self._panel_conn_id and self._panel_conn_id in self._cards:
            self._cards[self._panel_conn_id].set_info_active(False)

        self._panel_mode = _PANEL_SYSINFO
        self._panel_conn_id = conn_id

        card = self._cards.get(conn_id)
        if card:
            card.set_info_active(True)

        self._set_right_panel_header(tr("panel.header.sysinfo"), conn.name.upper())
        self._rp_info_btn.setVisible(False)
        self._rp_edit_btn.setVisible(False)
        self._rp_terminal_btn.setVisible(True)
        self._rp_mount_btn.setVisible(True)
        self._sync_rp_mount_button(conn_id)
        self._rp_del_btn.setVisible(False)
        self._rp_save_top_btn.setVisible(False)
        self._rp_cancel_top_btn.setVisible(False)
        self._rp_close_btn.setVisible(True)
        self._rp_btn_bar.setVisible(False)

        self._clear_right_panel_content()
        self._build_sysinfo_fullpanel(conn)
        self._right_panel_widget.setVisible(True)
        self._ensure_panel_sized()

    def _build_info_content(self, conn: Connection):
        """Build the read-only info view for the right panel."""
        is_mounted = (conn.id in self._cards and self._cards[conn.id].is_mounted)

        _theme = (self._mgr.get_settings().theme or "dark")
        _val_color = "#ffffff" if _theme == "dark" else "#1a2332"

        body = QWidget()
        body.setObjectName("rpInfoBody")
        v = QVBoxLayout(body)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(14)

        def _section(title):
            lbl = QLabel(title.upper())
            lbl.setObjectName("rpSectionLabel")
            lbl.setStyleSheet("color: #00b4d8; font-size: 11px; font-weight: 600; letter-spacing: 2px;")
            return lbl

        def _row(label, value, value_obj_name="rpValue"):
            container = QFrame()
            container.setObjectName("rpInfoField")
            container.setFixedHeight(54)  # Match height of input fields in edit mode

            
            vl = QVBoxLayout(container)
            vl.setContentsMargins(16, 8, 16, 8)
            vl.setSpacing(4)
            
            # Label at top in caps, muted grey
            lbl = QLabel(label.upper())
            lbl.setObjectName("rpFieldLabelCaps")
            lbl.setStyleSheet("color: #6a7685; font-size: 11px; font-weight: 500;")
            
            val = QLabel(str(value) if value else "—")
            val.setObjectName(value_obj_name)
            val.setStyleSheet(f"color: {_val_color}; font-size: 14px; font-weight: 400; padding: 0; background: transparent; border: none;")
    
            vl.addWidget(lbl)
            vl.addWidget(val)
            
            return container

        # Status badge row
        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        
        # Pill-shaped status label (not button) with dot
        status_container = QFrame()
        status_container.setObjectName("rpStatusContainer")
        if is_mounted:
            status_container.setStyleSheet("""
                QFrame#rpStatusContainer {
                    background-color: rgba(0, 212, 100, 0.15);
                    border: 1px solid rgba(0, 212, 100, 0.3);
                    border-radius: 16px;
                }
            """)
        else:
            status_container.setStyleSheet("""
                QFrame#rpStatusContainer {
                    background-color: rgba(106, 122, 138, 0.15);
                    border: 1px solid rgba(106, 122, 138, 0.3);
                    border-radius: 16px;
                }
            """)
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(12, 6, 16, 6)
        status_layout.setSpacing(6)
        
        # Small status dot
        dot_container = QWidget()
        dot_container.setFixedSize(6, 6)
        dot_container.setStyleSheet(f"""
            background-color: {'#00d464' if is_mounted else '#8a9aa8'};
            border-radius: 3px;
        """)
        status_layout.addWidget(dot_container)
        
        # Status text
        status_text = QLabel(tr("panel.status.connected") if is_mounted else tr("panel.status.disconnected"))
        status_text.setStyleSheet(f"color: {'#00d464' if is_mounted else '#8a9aa8'}; font-weight: 600; font-size: 13px;")
        status_layout.addWidget(status_text)
        status_row.addWidget(status_container)
        status_row.addStretch()
        
        # Drive badge - same style as connection card
        drive_badge = QLabel(conn.drive_letter)
        drive_badge.setObjectName("driveBadge")
        drive_badge.setProperty("mounted", "true" if is_mounted else "false")
        drive_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drive_badge.setFixedSize(QSize(42, 30))
        status_row.addWidget(drive_badge)
        
        v.addLayout(status_row)
        
        # Spacer before section
        v.addSpacing(8)

        v.addWidget(_section(tr("addedit.section.general")))
        v.addWidget(_row(tr("addedit.label.name"), conn.name))
        v.addWidget(_row(tr("addedit.label.host"), conn.host))
        v.addWidget(_row(tr("addedit.label.user"), conn.user))
        v.addWidget(_row(tr("addedit.label.port"), str(conn.port)))

        v.addSpacing(8)
        v.addWidget(_section(tr("addedit.section.path")))
        v.addWidget(_row(tr("addedit.label.path"), conn.remote_path))
        v.addWidget(_row(tr("addedit.label.drive"), conn.drive_letter))

        v.addSpacing(8)
        v.addWidget(_section(tr("addedit.section.auth")))
        auth_map = {"password": tr("addedit.auth.password"), "key": tr("addedit.auth.key"), "ask": tr("addedit.auth.ask")}
        v.addWidget(_row(tr("addedit.label.method"), auth_map.get(conn.auth_method, conn.auth_method)))
        if conn.auth_method in ("password", "ask") and conn.password:
            v.addWidget(_row(tr("addedit.label.password"), "••••••••"))
        if conn.key_path:
            v.addWidget(_row(tr("addedit.label.key"), conn.key_path))

        if conn.cli_access_enabled:
            v.addSpacing(8)
            v.addWidget(_section(tr("addedit.section.cli")))
            v.addWidget(_row(tr("addedit.cli.label"), tr("addedit.cli.enable") + " ✓"))

        v.addStretch()

        self._rp_layout.addWidget(body)

    def _build_sysinfo_fullpanel(self, conn: Connection):
        """Fill the right panel content area with SystemInfoPanel (mounted state)."""
        from src.ui.system_info_panel import SystemInfoPanel
        try:
            sip = SystemInfoPanel(conn, parent=self._rp_content, settings=self._mgr.get_settings())
        except AttributeError:
            sip = SystemInfoPanel(conn, parent=self._rp_content)
        sip.setObjectName("sysinfoFullPanel")
        self._rp_layout.addWidget(sip)
        self._current_info_panel = sip

    def _open_edit_panel(self, conn_id: str):
        """Show the inline edit form for the given connection."""
        if not self._guard_leave_form():
            return
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return

        card = self._cards.get(conn_id)
        if card and card.is_mounted:
            self._show_inline_message(
                tr("edit.locked.title"),
                tr("edit.locked.msg"),
                is_error=True
            )
            return

        if self._panel_conn_id and self._panel_conn_id in self._cards:
            self._cards[self._panel_conn_id].set_info_active(False)

        self._panel_mode = _PANEL_EDIT
        self._panel_conn_id = conn_id

        if card:
            card.set_info_active(True)

        self._set_right_panel_header(tr("addedit.edit_title"), tr("addedit.edit_title").upper())
        # Edit-Mode: only destructive/save/discard actions in header
        self._rp_info_btn.setVisible(False)
        self._rp_edit_btn.setVisible(False)
        self._rp_terminal_btn.setVisible(False)
        self._rp_mount_btn.setVisible(False)
        self._rp_del_btn.setVisible(True)
        self._rp_del_btn.setEnabled(True)
        self._rp_save_top_btn.setVisible(True)
        self._rp_cancel_top_btn.setVisible(True)
        # Avoid duplicate close/discard UX (and double dirty-prompts)
        self._rp_close_btn.setVisible(False)
        self._rp_btn_bar.setVisible(False)

        self._clear_right_panel_content()
        self._build_edit_form(conn)
        self._right_panel_widget.setVisible(True)
        self._ensure_panel_sized()

    def _open_add_panel(self):
        """Show the inline add-connection form."""
        if not self._guard_leave_form():
            return
        if self._panel_conn_id and self._panel_conn_id in self._cards:
            self._cards[self._panel_conn_id].set_info_active(False)
        if self._selected_id and self._selected_id in self._cards:
            card = self._cards[self._selected_id]
            card.setProperty("selected", False)
            card.style().unpolish(card)
            card.style().polish(card)
        self._selected_id = None
        self._panel_mode = _PANEL_ADD
        self._panel_conn_id = None

        self._set_right_panel_header(tr("addedit.add_title"), tr("addedit.add_title").upper())
        self._rp_info_btn.setVisible(False)
        self._rp_edit_btn.setVisible(False)
        self._rp_terminal_btn.setVisible(False)
        self._rp_mount_btn.setVisible(False)
        self._rp_del_btn.setVisible(False)
        self._rp_save_top_btn.setVisible(False)
        self._rp_cancel_top_btn.setVisible(False)
        self._rp_close_btn.setVisible(True)
        self._rp_btn_bar.setVisible(True)

        self._clear_right_panel_content()
        self._build_edit_form(None)
        self._right_panel_widget.setVisible(True)
        self._ensure_panel_sized()

    def _open_settings_panel(self):
        """Show the settings form full-screen. Toggle off if already open."""
        if not self._guard_leave_form():
            return
        if self._panel_mode == _PANEL_SETTINGS:
            self._nav_home()
            return
        if self._panel_conn_id and self._panel_conn_id in self._cards:
            self._cards[self._panel_conn_id].set_info_active(False)
        self._panel_mode = _PANEL_SETTINGS
        self._panel_conn_id = None

        self._clear_fs_content()
        self._set_fullscreen_header(tr("main.settings"), tr("settings.title"), True)
        self._build_settings_form()
        self._fs_btn_bar.setVisible(True)
        self._main_stack.setCurrentIndex(1)
        self._set_sidebar_active("settings")

    def _open_users_panel(self):
        """Show user management full-screen. Toggle off if already open."""
        if not self._guard_leave_form():
            return
        if self._panel_mode == _PANEL_USERS:
            self._nav_home()
            return
        if self._panel_conn_id and self._panel_conn_id in self._cards:
            self._cards[self._panel_conn_id].set_info_active(False)
        self._panel_mode = _PANEL_USERS
        self._panel_conn_id = None

        self._clear_fs_content()
        self._set_fullscreen_header(tr("main.users"), tr("users.title"), True)
        self._build_users_form()
        self._fs_btn_bar.setVisible(False)
        self._main_stack.setCurrentIndex(1)
        self._set_sidebar_active("users")

    def _build_users_form(self):
        from src.auth_manager import AuthManager
        from src.database import get_connection

        users = AuthManager.list_users()
        current_user = Session.current()
        current_id = current_user.id if current_user else None
        current_username = current_user.username if current_user else ""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT user_id, COUNT(*) AS count FROM connections GROUP BY user_id"
            ).fetchall()
        connection_counts = {row["user_id"]: row["count"] for row in rows}

        body = QWidget()
        body.setObjectName("fullscreenForm")
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        body.setMinimumWidth(320)
        v = QVBoxLayout(body)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(16)

        def _section_card(title: str, pill_text: str = ""):
            frame = QFrame()
            frame.setObjectName("fullscreenSectionCard")
            frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(18, 16, 18, 16)
            layout.setSpacing(12)

            head = QWidget()
            head_layout = QHBoxLayout(head)
            head_layout.setContentsMargins(0, 0, 0, 0)
            head_layout.setSpacing(10)

            head_title = QLabel(title)
            head_title.setObjectName("connectionsTitle")
            head_layout.addWidget(head_title)
            head_layout.addStretch(1)
            if pill_text:
                head_layout.addWidget(self._pill_label(pill_text), 0, Qt.AlignmentFlag.AlignVCenter)

            layout.addWidget(head)
            return frame, layout

        hero = QFrame()
        hero.setObjectName("dialogHeroCard")
        hero_l = QHBoxLayout(hero)
        hero_l.setContentsMargins(22, 18, 22, 18)
        hero_l.setSpacing(14)

        hero_copy = QWidget()
        hero_copy_layout = QVBoxLayout(hero_copy)
        hero_copy_layout.setContentsMargins(0, 0, 0, 0)
        hero_copy_layout.setSpacing(6)
        hero_copy_layout.addWidget(self._section_label(tr("users.section.users")))

        lead = QLabel(tr("dialog.lead.users"))
        lead.setObjectName("connectionsTitle")
        lead.setWordWrap(True)
        hero_copy_layout.addWidget(lead)

        hero_l.addWidget(hero_copy, 1)

        summary = self._pill_label(
            tr("users.summary", users=len(users), admins=sum(1 for user in users if user["is_admin"]))
        )
        hero_l.addWidget(summary, 0, Qt.AlignmentFlag.AlignTop)
        v.addWidget(hero)

        columns = QHBoxLayout()
        columns.setSpacing(16)

        list_card, list_layout = _section_card(tr("users.section.users"), current_username)

        for u in users:
            uid = u["id"]
            name = u["username"]
            is_me = uid == current_id
            connection_count = int(connection_counts.get(uid, 0))
            count_text = tr("users.connections.one", n=connection_count) if connection_count == 1 else tr("users.connections.many", n=connection_count)

            row = QFrame()
            row.setObjectName("userBox")
            row.setProperty("current", "true" if is_me else "false")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(14, 12, 14, 12)
            rl.setSpacing(10)

            avatar = QLabel(name[:2].upper())
            avatar.setObjectName("userAvatar")
            avatar.setProperty("admin", "true" if u["is_admin"] else "false")
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar.setFixedSize(QSize(46, 46))
            rl.addWidget(avatar)

            meta = QWidget()
            meta_l = QVBoxLayout(meta)
            meta_l.setContentsMargins(0, 0, 0, 0)
            meta_l.setSpacing(4)

            header_row = QHBoxLayout()
            header_row.setContentsMargins(0, 0, 0, 0)
            header_row.setSpacing(8)

            name_lbl = QLabel(name)
            name_lbl.setObjectName("userRowName")
            header_row.addWidget(name_lbl)

            role_badge = QLabel(tr("users.admin") if u["is_admin"] else tr("users.role.member"))
            role_badge.setObjectName("userRoleBadge")
            if u["is_admin"]:
                role_badge.setProperty("variant", "accent")
            header_row.addWidget(role_badge)

            if is_me:
                you_badge = QLabel(tr("users.badge.you"))
                you_badge.setObjectName("userRoleBadge")
                you_badge.setProperty("variant", "accent")
                header_row.addWidget(you_badge)

            header_row.addStretch(1)
            meta_l.addLayout(header_row)

            sub_lbl = QLabel(count_text)
            sub_lbl.setObjectName("userMetaSub")
            meta_l.addWidget(sub_lbl)

            rl.addWidget(meta, stretch=1)

            if is_me:
                chg_btn = QPushButton()
                chg_btn.setObjectName("rpHeaderBtn")
                chg_btn.setFixedSize(QSize(32, 32))
                chg_btn.setIcon(svg_icon("key", "#aab4c4", 15))
                chg_btn.setIconSize(QSize(15, 15))
                chg_btn.setToolTip(tr("users.tooltip.change_pw"))
                chg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                chg_btn.clicked.connect(self._uf_focus_change_password)
                rl.addWidget(chg_btn)
            else:
                if Session.is_admin():
                    rst_btn = QPushButton()
                    rst_btn.setObjectName("rpHeaderBtn")
                    rst_btn.setFixedSize(QSize(32, 32))
                    rst_btn.setIcon(svg_icon("rotate-cw", "#aab4c4", 15))
                    rst_btn.setIconSize(QSize(15, 15))
                    rst_btn.setToolTip(tr("users.tooltip.reset_pw", name=name))
                    rst_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    rst_btn.clicked.connect(lambda _, i=uid, n=name: self._uf_reset_password(i, n))
                    rl.addWidget(rst_btn)

                del_btn = QPushButton()
                del_btn.setObjectName("rpHeaderBtn")
                del_btn.setFixedSize(QSize(32, 32))
                del_btn.setIcon(svg_icon("trash", "#ef4444", 15))
                del_btn.setIconSize(QSize(15, 15))
                del_btn.setToolTip(tr("users.tooltip.delete", name=name))
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.clicked.connect(lambda _, i=uid, n=name: self._uf_delete_user(i, n))
                rl.addWidget(del_btn)

            list_layout.addWidget(row)

        create_card, create_layout = _section_card(tr("users.section.new"))

        create_layout.addWidget(self._field_label(tr("users.placeholder.username")))
        self._uf_username = QLineEdit()
        self._uf_username.setPlaceholderText(tr("users.placeholder.username"))
        create_layout.addWidget(self._uf_username)

        create_layout.addWidget(self._field_label(tr("users.placeholder.password")))
        self._uf_password = QLineEdit()
        self._uf_password.setPlaceholderText(tr("users.placeholder.password"))
        self._uf_password.setEchoMode(QLineEdit.EchoMode.Password)
        create_layout.addWidget(self._uf_password)

        self._uf_is_admin = QCheckBox(tr("users.admin"))
        create_layout.addWidget(self._uf_is_admin)

        create_btn = QPushButton(tr("users.create"))
        create_btn.setObjectName("primaryBtn")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._uf_add_user)
        create_layout.addWidget(create_btn)

        password_card, password_layout = _section_card(tr("users.section.password"), current_username)
        password_layout.addWidget(self._field_label(tr("chgpw.current")))
        self._uf_pw_current = QLineEdit()
        self._uf_pw_current.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self._uf_pw_current)

        password_layout.addWidget(self._field_label(tr("chgpw.new")))
        self._uf_pw_new = QLineEdit()
        self._uf_pw_new.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self._uf_pw_new)

        password_layout.addWidget(self._field_label(tr("chgpw.confirm")))
        self._uf_pw_confirm = QLineEdit()
        self._uf_pw_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self._uf_pw_confirm)

        password_btn = QPushButton(tr("dialog.save"))
        password_btn.setObjectName("primaryBtn")
        password_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        password_btn.clicked.connect(self._uf_change_password)
        password_layout.addWidget(password_btn)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.addWidget(list_card, 0, Qt.AlignmentFlag.AlignTop)

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(16)
        right_col.addWidget(create_card, 0, Qt.AlignmentFlag.AlignTop)
        right_col.addWidget(password_card, 0, Qt.AlignmentFlag.AlignTop)
        right_col.addStretch(1)

        columns.addLayout(left_col, 6)
        columns.addLayout(right_col, 5)
        v.addLayout(columns)

        v.addStretch()
        self._fs_layout.addWidget(body, stretch=1)

    def _uf_add_user(self):
        from src.auth_manager import AuthManager
        username = self._uf_username.text().strip()
        pw = self._uf_password.text()
        if not username or len(username) < 3:
            self._set_status(tr("users.username_min"))
            return
        if len(pw) < 6:
            self._set_status(tr("users.password_min"))
            return
        try:
            AuthManager.register(username, pw, is_admin=self._uf_is_admin.isChecked())
            self._open_users_panel()
        except Exception as e:
            self._set_status(str(e))

    def _uf_delete_user(self, user_id: str, username: str):
        from src.auth_manager import AuthManager
        reply = QMessageBox.question(
            self, tr("users.delete.title"),
            tr("users.delete.confirm", name=username),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            AuthManager.delete_user(user_id)
            self._open_users_panel()

    def _uf_reset_password(self, user_id: str, username: str):
        from src.auth_manager import AuthManager
        reply = QMessageBox.question(
            self, tr("users.reset.title"),
            tr("users.reset.confirm", name=username),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        new_pw = AuthManager.admin_reset_password(user_id)
        if not new_pw:
            self._set_status(tr("users.not_found"))
            return
        box = QMessageBox(self)
        box.setWindowTitle(tr("users.reset.new_title"))
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(tr("users.reset.new_msg", name=username, pw=new_pw))
        box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.exec()

    def _uf_focus_change_password(self):
        if hasattr(self, "_uf_pw_current"):
            self._uf_pw_current.setFocus()
            self._uf_pw_current.selectAll()

    def _uf_change_password(self):
        from src.auth_manager import AuthManager

        user = Session.current()
        if not user:
            return

        current_pw = self._uf_pw_current.text()
        new_pw = self._uf_pw_new.text()
        confirm_pw = self._uf_pw_confirm.text()

        if len(new_pw) < 6:
            self._set_status(tr("chgpw.new_min"))
            return
        if new_pw != confirm_pw:
            self._set_status(tr("chgpw.mismatch"))
            return
        if not AuthManager.change_password(user.id, current_pw, new_pw):
            self._set_status(tr("chgpw.wrong_old"))
            self._uf_pw_current.setFocus()
            self._uf_pw_current.selectAll()
            return

        self._uf_pw_current.clear()
        self._uf_pw_new.clear()
        self._uf_pw_confirm.clear()
        self._set_status(tr("chgpw.success"))

    # ------------------------------------------------------------------
    # Edit form (add + edit)
    # ------------------------------------------------------------------

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionLabel")
        return lbl

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("fieldLabel")
        return lbl

    def _pill_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("connectionsBadge")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        return lbl

    def _divider(self) -> QFrame:
        f = QFrame()
        f.setObjectName("divider")
        f.setFixedHeight(1)
        return f

    def _build_edit_form(self, conn):
        """Build add/edit form inside right panel content area."""
        from src.drive_utils import get_available_drives
        import secrets as _secrets

        is_edit = conn is not None

        body = QWidget()
        body.setMinimumWidth(268)
        v = QVBoxLayout(body)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(8)

        # General
        v.addWidget(self._section_label(tr("addedit.section.general")))
        v.addWidget(self._field_label(tr("addedit.label.name")))
        self._ef_name = QLineEdit(conn.name if is_edit else "")
        self._ef_name.setPlaceholderText(tr("addedit.placeholder.name"))
        v.addWidget(self._ef_name)

        v.addWidget(self._field_label(tr("addedit.label.host")))
        self._ef_host = QLineEdit(conn.host if is_edit else "")
        self._ef_host.setPlaceholderText("192.168.1.1")
        v.addWidget(self._ef_host)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        uc = QVBoxLayout()
        uc.setSpacing(4)
        uc.addWidget(self._field_label(tr("addedit.label.user")))
        self._ef_user = QLineEdit(conn.user if is_edit else "")
        self._ef_user.setPlaceholderText("root")
        uc.addWidget(self._ef_user)
        row1.addLayout(uc, stretch=2)
        pc = QVBoxLayout()
        pc.setSpacing(4)
        pc.addWidget(self._field_label(tr("addedit.label.port")))
        self._ef_port = NoWheelSpinBox()
        self._ef_port.setRange(1, 65535)
        self._ef_port.setValue(conn.port if is_edit else 22)
        pc.addWidget(self._ef_port)
        row1.addLayout(pc, stretch=1)
        v.addLayout(row1)

        v.addWidget(self._divider())
        v.addWidget(self._section_label(tr("addedit.section.path")))
        v.addWidget(self._field_label(tr("addedit.label.path")))
        self._ef_path = QLineEdit(conn.remote_path if is_edit else "/")
        self._ef_path.setPlaceholderText("/home/user")
        v.addWidget(self._ef_path)

        v.addWidget(self._field_label(tr("addedit.label.drive")))
        self._ef_drive = NoWheelComboBox()
        used = [c.drive_letter for c in self._mgr.get_all() if (not is_edit or c.id != conn.id)]
        available = get_available_drives(exclude=used)
        if is_edit:
            curr = conn.drive_letter.upper().rstrip("\\") + ":"
            if curr not in available:
                available.insert(0, curr)
        for letter in sorted(set(available)):
            self._ef_drive.addItem(letter, letter)
        if is_edit:
            idx = self._ef_drive.findData(conn.drive_letter)
            if idx >= 0:
                self._ef_drive.setCurrentIndex(idx)
        v.addWidget(self._ef_drive)

        v.addWidget(self._divider())
        v.addWidget(self._section_label(tr("addedit.section.auth")))
        v.addWidget(self._field_label(tr("addedit.label.method")))
        self._ef_auth = NoWheelComboBox()
        self._ef_auth.addItem(tr("addedit.auth.password"), "password")
        self._ef_auth.addItem(tr("addedit.auth.key"), "key")
        self._ef_auth.addItem(tr("addedit.auth.ask"), "ask")
        if is_edit:
            idx = self._ef_auth.findData(conn.auth_method)
            if idx >= 0:
                self._ef_auth.setCurrentIndex(idx)
        v.addWidget(self._ef_auth)

        v.addWidget(self._field_label(tr("addedit.label.password")))
        self._ef_pw = QLineEdit(conn.password if is_edit else "")
        self._ef_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._ef_pw.setPlaceholderText("••••••••")
        v.addWidget(self._ef_pw)

        v.addWidget(self._field_label(tr("addedit.label.key")))
        key_row = QHBoxLayout()
        key_row.setSpacing(6)
        self._ef_key = QLineEdit(conn.key_path if is_edit else "")
        self._ef_key.setPlaceholderText("C:/Users/user/.ssh/id_rsa")
        key_row.addWidget(self._ef_key, stretch=1)
        browse_btn = QPushButton("…")
        browse_btn.setFixedWidth(32)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._ef_browse_key)
        key_row.addWidget(browse_btn)
        v.addLayout(key_row)

        v.addWidget(self._divider())
        v.addWidget(self._section_label(tr("addedit.section.cli")))
        self._ef_cli_cb = QCheckBox(tr("addedit.cli.enable"))
        self._ef_cli_cb.setChecked(conn.cli_access_enabled if is_edit else False)
        self._ef_cli_cb.toggled.connect(self._ef_cli_toggle)
        v.addWidget(self._ef_cli_cb)

        self._ef_cli_widget = QWidget()
        cli_inner = QVBoxLayout(self._ef_cli_widget)
        cli_inner.setContentsMargins(0, 4, 0, 0)
        cli_inner.setSpacing(4)
        cli_inner.addWidget(self._field_label(tr("addedit.cli.label")))
        cli_key_row = QHBoxLayout()
        cli_key_row.setSpacing(4)
        self._ef_cli_key = QLineEdit(conn.cli_access_key or "" if is_edit else "")
        self._ef_cli_key.setReadOnly(True)
        self._ef_cli_key.setPlaceholderText(tr("addedit.cli.none"))
        cli_key_row.addWidget(self._ef_cli_key, stretch=1)

        self._ef_cli_copy_btn = QPushButton()
        self._ef_cli_copy_btn.setObjectName("rpHeaderBtn")
        self._ef_cli_copy_btn.setFixedSize(32, 32)
        self._ef_cli_copy_btn.setIcon(svg_icon("copy", "#aab4c4", 15))
        self._ef_cli_copy_btn.setIconSize(QSize(15, 15))
        self._ef_cli_copy_btn.setToolTip(tr("addedit.cli.copy"))
        self._ef_cli_copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ef_cli_copy_btn.clicked.connect(self._ef_copy_cli_key)
        cli_key_row.addWidget(self._ef_cli_copy_btn)

        self._ef_cli_gen_btn = QPushButton()
        self._ef_cli_gen_btn.setObjectName("rpHeaderBtn")
        self._ef_cli_gen_btn.setFixedSize(32, 32)
        self._ef_cli_gen_btn.setIcon(svg_icon("refresh", "#aab4c4", 15))
        self._ef_cli_gen_btn.setIconSize(QSize(15, 15))
        self._ef_cli_gen_btn.setToolTip(tr("addedit.cli.generate"))
        self._ef_cli_gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ef_cli_gen_btn.clicked.connect(self._ef_generate_new_cli_key)
        cli_key_row.addWidget(self._ef_cli_gen_btn)

        cli_inner.addLayout(cli_key_row)
        self._ef_cli_widget.setVisible(conn.cli_access_enabled if is_edit else False)
        v.addWidget(self._ef_cli_widget)

        if is_edit and conn.cli_access_enabled and not conn.cli_access_key:
            self._ef_generate_new_cli_key()

        # ── PUTTY KEY ───────────────────────────────────────────────
        # Only visible when PuTTY is enabled globally
        s = self._mgr.get_settings()
        if s.use_putty:
            v.addWidget(self._divider())
            v.addWidget(self._section_label("PuTTY"))
            v.addWidget(self._field_label(tr("addedit.putty_key.label")))
            putty_row = QHBoxLayout()
            putty_row.setSpacing(6)
            self._ef_putty_key = QLineEdit(conn.putty_key_path if is_edit else "")
            self._ef_putty_key.setPlaceholderText("C:/Users/user/.ssh/id_rsa.ppk")
            putty_row.addWidget(self._ef_putty_key, stretch=1)
            putty_browse_btn = QPushButton("…")
            putty_browse_btn.setFixedWidth(32)
            putty_browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            putty_browse_btn.clicked.connect(self._ef_browse_putty_key)
            putty_row.addWidget(putty_browse_btn)
            v.addLayout(putty_row)
            v.addWidget(self._field_label(tr("addedit.putty_key.hint")))

        v.addStretch()
        self._rp_layout.addWidget(body)
        # Store edit connection reference
        self._ef_conn = conn
        for w in (self._ef_name, self._ef_host, self._ef_user):
            w.textChanged.connect(self._validate_edit_form)
        self._ef_initial_snapshot = self._snapshot_form()
        self._validate_edit_form()
        self._setup_edit_tab_order()
        QTimer.singleShot(0, self._ef_name.setFocus)

    def _setup_edit_tab_order(self):
        chain = [
            self._ef_name, self._ef_host, self._ef_user, self._ef_port, self._ef_path,
            self._ef_drive, self._ef_auth, self._ef_pw, self._ef_key,
            self._ef_cli_cb, self._ef_cli_key
        ]
        if getattr(self, "_ef_putty_key", None) is not None:
            chain.append(self._ef_putty_key)
        for i in range(len(chain) - 1):
            self.setTabOrder(chain[i], chain[i + 1])

    def _ef_browse_key(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("addedit.select_key"), "", "All Files (*)"
        )
        if path and getattr(self, "_ef_key", None) is not None:
            try:
                self._ef_key.setText(path)
            except RuntimeError:
                pass

    def _ef_browse_putty_key(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("addedit.putty_key.select"), "", "PuTTY Private Key (*.ppk)"
        )
        if path and getattr(self, "_ef_putty_key", None) is not None:
            try:
                self._ef_putty_key.setText(path)
            except RuntimeError:
                pass

    def _ef_cli_toggle(self, checked: bool):
        if getattr(self, "_ef_cli_widget", None) is None or getattr(self, "_ef_cli_key", None) is None:
            return
        try:
            self._ef_cli_widget.setVisible(checked)
            is_empty = not self._ef_cli_key.text()
        except RuntimeError:
            return
        if checked and is_empty:
            self._ef_generate_new_cli_key()

    def _ef_generate_new_cli_key(self):
        import secrets as _secrets
        if getattr(self, "_ef_cli_key", None) is None:
            return
        try:
            self._ef_cli_key.setText(_secrets.token_hex(64))
        except RuntimeError:
            pass

    def _ef_copy_cli_key(self):
        if getattr(self, "_ef_cli_key", None) is None:
            return
        try:
            key = self._ef_cli_key.text()
        except RuntimeError:
            return
        if not key:
            return

        QApplication.clipboard().setText(key)
        if getattr(self, "_ef_cli_copy_btn", None) is None:
            return
        try:
            self._ef_cli_copy_btn.setIcon(svg_icon("check", "#00d464", 15))
        except RuntimeError:
            return
        QTimer.singleShot(
            1500,
            self._ef_restore_copy_icon
        )

    def _ef_restore_copy_icon(self):
        btn = getattr(self, "_ef_cli_copy_btn", None)
        if btn is None:
            return
        try:
            btn.setIcon(svg_icon("copy", "#aab4c4", 15))
        except RuntimeError:
            pass

    def _install_shortcuts(self):
        mapping = [
            ("Ctrl+S", self._shortcut_save),
            ("Esc", self._shortcut_escape),
            ("Ctrl+N", self._shortcut_add),
            ("Ctrl+E", self._shortcut_edit),
            ("Delete", self._shortcut_delete),
        ]
        for key, slot in mapping:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(slot)
            self._shortcuts.append(sc)

    def _shortcut_save(self):
        if self._panel_mode in (_PANEL_EDIT, _PANEL_ADD):
            self._on_rp_save()

    def _shortcut_escape(self):
        if self._panel_mode in (_PANEL_EDIT, _PANEL_ADD):
            self._on_rp_cancel()
        elif self._panel_mode in (_PANEL_INFO, _PANEL_SYSINFO):
            self._close_right_panel()

    def _shortcut_add(self):
        self._open_add_panel()

    def _shortcut_edit(self):
        target_id = self._panel_conn_id or self._selected_id
        if target_id:
            self._open_edit_panel(target_id)

    def _shortcut_delete(self):
        if self._panel_mode == _PANEL_EDIT and self._panel_conn_id:
            self._on_delete()

    # ------------------------------------------------------------------
    # Settings form
    # ------------------------------------------------------------------

    def _build_settings_form(self):
        """Build the settings form inside the fullscreen panel."""
        s = self._mgr.get_settings()

        body = QWidget()
        body.setObjectName("fullscreenForm")
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        v = QVBoxLayout(body)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(10)

        # Language
        v.addWidget(self._section_label(tr("settings.section.language")))
        lang_theme_row = QHBoxLayout()
        lang_theme_row.setSpacing(12)

        lang_col = QVBoxLayout()
        lang_col.setContentsMargins(0, 0, 0, 0)
        lang_col.setSpacing(6)
        lang_col.addWidget(self._field_label(tr("settings.language.label")))
        self._sf_lang = NoWheelComboBox()
        for code in available_languages():
            self._sf_lang.addItem(_LANG_LABELS.get(code, code), code)
        idx = self._sf_lang.findData(getattr(s, 'language', 'en') or 'en')
        if idx >= 0:
            self._sf_lang.setCurrentIndex(idx)
        self._sf_lang.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lang_col.addWidget(self._sf_lang)
        lang_theme_row.addLayout(lang_col, 1)

        # Theme
        theme_col = QVBoxLayout()
        theme_col.setContentsMargins(0, 0, 0, 0)
        theme_col.setSpacing(6)
        theme_col.addWidget(self._field_label(tr("settings.theme.label")))
        self._sf_theme = NoWheelComboBox()
        self._sf_theme.addItem(tr("settings.theme.dark"), "dark")
        self._sf_theme.addItem(tr("settings.theme.light"), "light")
        idx = self._sf_theme.findData(getattr(s, 'theme', 'dark') or 'dark')
        if idx >= 0:
            self._sf_theme.setCurrentIndex(idx)
        self._sf_theme.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        theme_col.addWidget(self._sf_theme)
        lang_theme_row.addLayout(theme_col, 1)
        v.addLayout(lang_theme_row)

        hint = QLabel(tr("settings.language.restart"))
        hint.setObjectName("fieldLabel")
        hint.setWordWrap(True)
        v.addWidget(hint)

        # General
        v.addWidget(self._section_label(tr("settings.section.general")))
        self._sf_start = QCheckBox(tr("settings.start_with_windows"))
        self._sf_start.setChecked(s.start_with_windows)
        v.addWidget(self._sf_start)
        self._sf_tray = QCheckBox(tr("settings.minimize_to_tray"))
        self._sf_tray.setChecked(s.minimize_to_tray)
        v.addWidget(self._sf_tray)
        self._sf_admin = QCheckBox(tr("settings.require_admin"))
        self._sf_admin.setChecked(s.require_admin)
        v.addWidget(self._sf_admin)

        # Mount status
        v.addWidget(self._section_label(tr("settings.section.mount")))
        interval_row = QHBoxLayout()
        interval_row.addWidget(self._field_label(tr("settings.check_interval")))
        interval_row.addStretch()
        self._sf_interval = NoWheelSpinBox()
        self._sf_interval.setRange(5, 300)
        self._sf_interval.setValue(s.check_interval_seconds)
        self._sf_interval.setFixedWidth(80)
        interval_row.addWidget(self._sf_interval)
        v.addLayout(interval_row)
        self._sf_auto_reconnect = QCheckBox(tr("settings.auto_reconnect"))
        self._sf_auto_reconnect.setChecked(s.auto_reconnect)
        v.addWidget(self._sf_auto_reconnect)
        self._sf_auto_remount = QCheckBox(tr("settings.auto_remount"))
        self._sf_auto_remount.setChecked(s.auto_remount_on_lost)
        v.addWidget(self._sf_auto_remount)

        # Security Level
        v.addWidget(self._section_label(tr("settings.section.security")))
        sec_row = QHBoxLayout()
        sec_row.addWidget(self._field_label(tr("settings.security.level.label")))
        sec_row.addStretch()
        self._sf_security_level = NoWheelComboBox()
        self._sf_security_level.addItem(tr("settings.security.level.strict"), 0)
        self._sf_security_level.addItem(tr("settings.security.level.key_no_passphrase"), 1)
        self._sf_security_level.addItem(tr("settings.security.level.password_arg"), 2)
        _cur_level = getattr(s, 'security_level', 0)
        self._sf_security_level.setCurrentIndex(min(_cur_level, 2))
        self._sf_security_level.setFixedWidth(230)
        sec_row.addWidget(self._sf_security_level)
        v.addLayout(sec_row)
        self._sf_sec_warning = QLabel()
        self._sf_sec_warning.setObjectName("errorLabel")
        self._sf_sec_warning.setWordWrap(True)
        v.addWidget(self._sf_sec_warning)
        self._sf_security_level.currentIndexChanged.connect(self._on_sf_security_changed)
        self._on_sf_security_changed(_cur_level)

        # SSH Terminal
        v.addWidget(self._section_label(tr("settings.section.terminal")))
        self._sf_putty = QCheckBox(tr("settings.use_putty"))
        self._sf_putty.setChecked(getattr(s, 'use_putty', False))
        self._sf_putty.toggled.connect(self._sf_putty_toggled)
        v.addWidget(self._sf_putty)

        self._sf_putty_widget = QWidget()
        pw_inner = QVBoxLayout(self._sf_putty_widget)
        pw_inner.setContentsMargins(0, 4, 0, 0)
        pw_inner.setSpacing(4)
        pw_inner.addWidget(self._field_label(tr("settings.putty_path")))
        putty_row = QHBoxLayout()
        putty_row.setSpacing(6)
        self._sf_putty_path = QLineEdit(getattr(s, 'putty_path', r"C:\Program Files\PuTTY\putty.exe"))
        self._sf_putty_path.setPlaceholderText(r"C:\Program Files\PuTTY\putty.exe")
        putty_row.addWidget(self._sf_putty_path, stretch=1)
        browse_p = QPushButton("…")
        browse_p.setFixedWidth(32)
        browse_p.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_p.clicked.connect(self._sf_browse_putty)
        putty_row.addWidget(browse_p)
        pw_inner.addLayout(putty_row)
        hint2 = QLabel(tr("settings.putty_hint"))
        hint2.setObjectName("fieldLabel")
        hint2.setWordWrap(True)
        pw_inner.addWidget(hint2)
        self._sf_putty_widget.setVisible(getattr(s, 'use_putty', False))
        v.addWidget(self._sf_putty_widget)

        # Developer
        v.addWidget(self._section_label(tr("settings.section.developer")))
        self._sf_debug = QCheckBox(tr("settings.debug_mode"))
        self._sf_debug.setChecked(s.debug_mode)
        self._sf_debug.toggled.connect(self._sf_debug_toggled)
        v.addWidget(self._sf_debug)

        # Tools (only when debug is on)
        self._sf_tools_widget = QWidget()
        tw_inner = QVBoxLayout(self._sf_tools_widget)
        tw_inner.setContentsMargins(0, 0, 0, 0)
        tw_inner.setSpacing(8)
        tw_inner.addWidget(self._section_label(tr("settings.section.tools")))
        fix_btn = QPushButton(tr("settings.fix_ghosts"))
        fix_btn.setObjectName("actionBtn")
        fix_btn.setProperty("btn_type", "primary")
        fix_btn.setMinimumHeight(34)
        fix_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fix_btn.clicked.connect(self._sf_fix_ghosts)
        tw_inner.addWidget(fix_btn)
        rst_btn = QPushButton(tr("settings.restart_explorer"))
        rst_btn.setObjectName("actionBtn")
        rst_btn.setMinimumHeight(34)
        rst_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rst_btn.clicked.connect(self._sf_restart_explorer)
        tw_inner.addWidget(rst_btn)
        self._sf_tools_widget.setVisible(s.debug_mode)
        v.addWidget(self._sf_tools_widget)

        v.addStretch()
        self._fs_layout.addWidget(body)

    def _on_sf_security_changed(self, index: int):
        _WARNINGS = [
            "",
            tr("settings.security.warning.level1"),
            tr("settings.security.warning.level2"),
        ]
        txt = _WARNINGS[index] if index < len(_WARNINGS) else ""
        self._sf_sec_warning.setText(txt)
        self._sf_sec_warning.setVisible(bool(txt))

    def _sf_putty_toggled(self, checked: bool):
        self._sf_putty_widget.setVisible(checked)

    def _sf_debug_toggled(self, checked: bool):
        self._sf_tools_widget.setVisible(checked)

    def _sf_browse_putty(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("settings.select_putty"),
            r"C:\Program Files\PuTTY", "Executables (*.exe)"
        )
        if path:
            self._sf_putty_path.setText(path)

    def _sf_fix_ghosts(self):
        ok = self._controller.purge_all_stale_mounts()
        msg = tr("settings.ghosts_ok") if ok else tr("settings.ghosts_failed")
        self._show_inline_message("", msg, is_error=not ok)
        if ok:
            SSHFSController.restart_explorer()

    def _sf_restart_explorer(self):
        SSHFSController.restart_explorer()
        self._show_inline_message("", tr("settings.explorer_restarted"))

    # ------------------------------------------------------------------
    # Right panel save / cancel
    # ------------------------------------------------------------------

    def _on_rp_save(self):
        if self._saving_in_progress:
            return
        self._set_saving_state(True)
        try:
            if self._panel_mode == _PANEL_EDIT:
                self._save_edit_form()
            elif self._panel_mode == _PANEL_ADD:
                self._save_add_form()
        except RuntimeError:
            self._err_popup(
                tr("dialog.error"),
                tr("sysinfo.error") + " Formular wurde neu geladen. Bitte Eingaben prüfen und erneut speichern."
            )
            if self._panel_conn_id:
                self._open_edit_panel(self._panel_conn_id)
            else:
                self._open_add_panel()
        except Exception as e:
            self._err_popup(tr("dialog.error"), str(e))
        finally:
            self._set_saving_state(False)
            if self._panel_mode in (_PANEL_EDIT, _PANEL_ADD):
                self._validate_edit_form()

    def _on_rp_cancel(self):
        if self._panel_mode in (_PANEL_EDIT, _PANEL_ADD):
            if not self._guard_leave_form():
                return
            if self._panel_conn_id:
                self._open_info_panel(self._panel_conn_id)
            else:
                self._close_right_panel_force()

    def _on_rp_terminal_clicked(self):
        """Header terminal button for the currently open connection panel."""
        conn_id = self._panel_conn_id
        if not conn_id:
            return
        self._on_ssh_terminal(conn_id)

    def _sync_rp_mount_button(self, conn_id: str):
        """Update mount/unmount header button state based on card mount state."""
        btn = getattr(self, "_rp_mount_btn", None)
        if btn is None:
            return
        card = self._cards.get(conn_id)
        is_mounted = bool(card and card.is_mounted)
        if is_mounted:
            # Match ConnectionCard.update_mount_state()
            btn.setIcon(svg_icon("minus", "#00d464", 16))
            btn.setToolTip(tr("card.tooltip.mount_on"))
            btn.setEnabled(True)
        else:
            # Match ConnectionCard.update_mount_state()
            btn.setIcon(svg_icon("arrow-right", "#aab4c4", 16))
            btn.setToolTip(tr("card.tooltip.mount_off"))
            btn.setEnabled(True)
        btn.setAccessibleName(btn.toolTip())

    def _on_rp_mount_clicked(self):
        """Header mount/unmount button for the currently open connection panel."""
        conn_id = self._panel_conn_id
        if not conn_id:
            return
        card = self._cards.get(conn_id)
        if not card:
            return
        if card.is_mounted:
            self._on_unmount(conn_id)
        else:
            self._on_mount(conn_id)

    def _safe_lineedit_text(self, attr_name: str) -> str:
        """
        Return text from a potentially stale QLineEdit attribute.
        If the wrapped Qt object was already deleted, return empty string.
        """
        widget = getattr(self, attr_name, None)
        if widget is None:
            return ""
        try:
            return widget.text().strip()
        except RuntimeError:
            return ""

    def _safe_current_data(self, attr_name: str, default=None):
        widget = getattr(self, attr_name, None)
        if widget is None:
            return default
        try:
            value = widget.currentData()
            return default if value is None else value
        except RuntimeError:
            return default

    def _safe_bool_checked(self, attr_name: str, default: bool = False) -> bool:
        widget = getattr(self, attr_name, None)
        if widget is None:
            return default
        try:
            return bool(widget.isChecked())
        except RuntimeError:
            return default

    def _safe_spin_value(self, attr_name: str, default: int = 22) -> int:
        widget = getattr(self, attr_name, None)
        if widget is None:
            return default
        try:
            return int(widget.value())
        except RuntimeError:
            return default

    def _set_saving_state(self, saving: bool):
        self._saving_in_progress = saving
        for btn_name in ("_rp_save_top_btn", "_rp_save_btn", "_rp_cancel_top_btn", "_rp_cancel_btn"):
            btn = getattr(self, btn_name, None)
            if btn is None:
                continue
            try:
                btn.setEnabled(not saving)
            except RuntimeError:
                pass
        if saving:
            self._set_status(tr("card.loading.saving"))

    def _snapshot_form(self) -> dict:
        return {
            "name": self._safe_lineedit_text("_ef_name"),
            "host": self._safe_lineedit_text("_ef_host"),
            "user": self._safe_lineedit_text("_ef_user"),
            "path": self._safe_lineedit_text("_ef_path"),
            "port": self._safe_spin_value("_ef_port", 22),
            "auth": self._safe_current_data("_ef_auth", "password"),
            "password": self._safe_lineedit_text("_ef_pw"),
            "key": self._safe_lineedit_text("_ef_key"),
            "putty_key": self._safe_lineedit_text("_ef_putty_key"),
            "drive": self._safe_current_data("_ef_drive", "Z:"),
            "cli_enabled": self._safe_bool_checked("_ef_cli_cb", False),
            "cli_key": self._safe_lineedit_text("_ef_cli_key"),
        }

    def _form_is_dirty(self) -> bool:
        if self._panel_mode not in (_PANEL_EDIT, _PANEL_ADD):
            return False
        if self._ef_initial_snapshot is None:
            return False
        return self._snapshot_form() != self._ef_initial_snapshot

    def _guard_leave_form(self) -> bool:
        if not self._form_is_dirty():
            return True
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(tr("dirty.title"))
        box.setText(tr("dirty.body"))
        discard_btn = box.addButton(tr("dirty.discard"), QMessageBox.ButtonRole.DestructiveRole)
        keep_btn = box.addButton(tr("dirty.keep"), QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(keep_btn)
        box.exec()
        return box.clickedButton() == discard_btn

    def _validate_edit_form(self):
        required = ("_ef_name", "_ef_host", "_ef_user")
        is_valid = True
        for attr in required:
            widget = getattr(self, attr, None)
            if widget is None:
                continue
            try:
                text = widget.text().strip()
                invalid = not text
                if attr == "_ef_name" and text and not _is_safe_label(text):
                    invalid = True
                widget.setProperty("invalid", "true" if invalid else "false")
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                is_valid = is_valid and (not invalid)
            except RuntimeError:
                is_valid = False

        for btn_name in ("_rp_save_top_btn", "_rp_save_btn"):
            btn = getattr(self, btn_name, None)
            if btn is None:
                continue
            try:
                btn.setEnabled(is_valid and not self._saving_in_progress)
            except RuntimeError:
                pass

    def _save_edit_form(self):
        if not getattr(self, "_ef_conn", None):
            self._show_inline_message(tr("dialog.error"), "Formular ist nicht verfügbar. Bitte erneut öffnen.", is_error=True)
            return
        name = self._safe_lineedit_text("_ef_name")
        host = self._safe_lineedit_text("_ef_host")
        user = self._safe_lineedit_text("_ef_user")
        errors = []
        if not name: errors.append(tr("addedit.required.name"))
        elif not _is_safe_label(name): errors.append(tr("addedit.name.invalid"))
        if not host: errors.append(tr("addedit.required.host"))
        if not user: errors.append(tr("addedit.required.user"))
        if errors:
            self._show_inline_message(tr("addedit.required.title"), "\n".join(errors), is_error=True)
            return

        conn = self._ef_conn
        putty_key_path = self._safe_lineedit_text("_ef_putty_key")
        cli_enabled = self._safe_bool_checked("_ef_cli_cb", False)
        
        updated = Connection(
            id=conn.id,
            name=name, host=host, user=user,
            remote_path=self._safe_lineedit_text("_ef_path") or "/",
            port=self._safe_spin_value("_ef_port", 22),
            auth_method=self._safe_current_data("_ef_auth", "password"),
            password=self._safe_lineedit_text("_ef_pw"),
            key_path=self._safe_lineedit_text("_ef_key"),
            putty_key_path=putty_key_path,
            drive_letter=self._safe_current_data("_ef_drive", "Z:"),
            cli_access_enabled=cli_enabled,
            cli_access_key=self._safe_lineedit_text("_ef_cli_key") if cli_enabled else None,
        )
        self._mgr.update(updated)
        self._refresh_list()
        self._set_status(tr("status.saved"))
        # Reopen info panel for the updated connection
        self._open_info_panel(conn.id)

    def _save_add_form(self):
        name = self._safe_lineedit_text("_ef_name")
        host = self._safe_lineedit_text("_ef_host")
        user = self._safe_lineedit_text("_ef_user")
        errors = []
        if not name: errors.append(tr("addedit.required.name"))
        elif not _is_safe_label(name): errors.append(tr("addedit.name.invalid"))
        if not host: errors.append(tr("addedit.required.host"))
        if not user: errors.append(tr("addedit.required.user"))
        if errors:
            self._show_inline_message(tr("addedit.required.title"), "\n".join(errors), is_error=True)
            return

        putty_key_path = self._safe_lineedit_text("_ef_putty_key")
        cli_enabled = self._safe_bool_checked("_ef_cli_cb", False)
        
        new_conn = Connection(
            name=name, host=host, user=user,
            remote_path=self._safe_lineedit_text("_ef_path") or "/",
            port=self._safe_spin_value("_ef_port", 22),
            auth_method=self._safe_current_data("_ef_auth", "password"),
            password=self._safe_lineedit_text("_ef_pw"),
            key_path=self._safe_lineedit_text("_ef_key"),
            putty_key_path=putty_key_path,
            drive_letter=self._safe_current_data("_ef_drive", "Z:"),
            cli_access_enabled=cli_enabled,
            cli_access_key=self._safe_lineedit_text("_ef_cli_key") if cli_enabled else None,
        )
        self._mgr.add(new_conn)
        self._refresh_list()
        self._set_status(tr("status.saved"))
        self._open_info_panel(new_conn.id)

    def _save_settings_form(self):
        if self._sf_putty.isChecked():
            import os as _os
            path = self._sf_putty_path.text().strip()
            if not path:
                self._show_inline_message("PuTTY", tr("settings.putty_missing"), is_error=True)
                return
            if not _os.path.exists(path):
                # Ask inline
                self._show_inline_message(
                    tr("settings.putty_not_found_title"),
                    tr("settings.putty_not_found", path=path),
                    is_error=True
                )
                return

        old_lang = current_language()
        _sec = self._sf_security_level.currentIndex()
        new_settings = AppSettings(
            start_with_windows=self._sf_start.isChecked(),
            minimize_to_tray=self._sf_tray.isChecked(),
            require_admin=self._sf_admin.isChecked(),
            check_interval_seconds=self._sf_interval.value(),
            auto_reconnect=self._sf_auto_reconnect.isChecked(),
            auto_remount_on_lost=self._sf_auto_remount.isChecked(),
            debug_mode=self._sf_debug.isChecked(),
            use_putty=self._sf_putty.isChecked(),
            putty_path=self._sf_putty_path.text().strip(),
            language=self._sf_lang.currentData() or "en",
            theme=self._sf_theme.currentData() or "dark",
            security_level=_sec,
            allow_passwordless_key_auth=_sec >= 1,
            allow_insecure_password_auth=_sec >= 2,
        )
        self._mgr.save_settings(new_settings)
        self._apply_settings_object(new_settings)
        self._set_status(tr("status.settings_saved"))
        self._nav_home()
        if new_settings.language != old_lang:
            self._show_inline_message("Info", tr("settings.language.restart"))

    # ------------------------------------------------------------------
    # Inline message helper
    # ------------------------------------------------------------------

    def _show_inline_message(self, title: str, msg: str, is_error: bool = False):
        """Show a brief status message in the status bar."""
        self._set_status(f"{'⚠ ' if is_error else ''}{title + ': ' if title else ''}{msg.splitlines()[0]}")

    def _err_popup(self, title: str, message: str) -> None:
        """Error dialog with a copy-to-clipboard button. Also persists title+first line in status bar."""
        self._set_error_status(f"⚠ {title}: {message.splitlines()[0]}")

        dlg = QDialog(self)
        dlg.setObjectName("dialogSurface")
        dlg.setWindowTitle(title)
        dlg.setModal(True)
        dlg.setMinimumWidth(420)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("dialogTitle")
        layout.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("errorLabel")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        copy_btn = QPushButton()
        copy_btn.setObjectName("rpHeaderBtn")
        copy_btn.setFixedSize(32, 32)
        copy_btn.setIcon(svg_icon("copy", "#aab4c4", 16))
        copy_btn.setIconSize(QSize(16, 16))
        copy_btn.setToolTip("Fehlermeldung kopieren")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _clip_text = f"{title}\n\n{message}"
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(_clip_text))
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primaryBtn")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(dlg.accept)
        ok_btn.setDefault(True)
        btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)
        dlg.exec()

    def _set_error_status(self, msg: str) -> None:
        """Set a persistent error message in the status bar (no timeout)."""
        self._set_status(msg)

    def _show_mount_failure_dialog(self, conn: Connection | None, message: str) -> bool:
        """Show a richer failure dialog that mirrors the website demo's guidance blocks."""
        dialog = QDialog(self)
        dialog.setObjectName("mountErrorDialog")
        dialog.setWindowTitle(tr("mount.failed.title"))
        dialog.setModal(True)
        dialog.setMinimumWidth(540)

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(12)

        title = QLabel(tr("mount.failed.title"))
        title.setObjectName("dialogTitle")
        outer.addWidget(title)

        lead = QLabel(tr("mount.failed.main", name=conn.name if conn else "?"))
        lead.setObjectName("mountErrorLead")
        lead.setWordWrap(True)
        outer.addWidget(lead)

        checks_frame = QFrame()
        checks_frame.setObjectName("mountErrorBlock")
        checks_layout = QVBoxLayout(checks_frame)
        checks_layout.setContentsMargins(14, 12, 14, 12)
        checks_layout.setSpacing(0)
        checks = QLabel(
            tr(
                "mount.failed.troubleshoot",
                host=conn.host if conn else "?",
                port=conn.port if conn else "?",
            ).strip()
        )
        checks.setObjectName("mountErrorBody")
        checks.setWordWrap(True)
        checks_layout.addWidget(checks)
        outer.addWidget(checks_frame)

        details = QLabel(tr("mount.failed.details", msg=message).strip())
        details.setObjectName("mountErrorDetails")
        details.setWordWrap(True)
        details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        outer.addWidget(details)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        close_btn = QPushButton(tr("dialog.close"))
        close_btn.setObjectName("secondaryBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(close_btn)

        retry_btn = QPushButton(tr("mount.failed.retry"))
        retry_btn.setObjectName("primaryBtn")
        retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        retry_btn.setDefault(True)
        retry_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(retry_btn)

        outer.addLayout(btn_row)
        return dialog.exec() == QDialog.DialogCode.Accepted

    # ------------------------------------------------------------------
    # Info panel helpers
    # ------------------------------------------------------------------

    def _on_rp_edit_clicked(self):
        """Edit button in right panel header."""
        if self._panel_conn_id:
            self._open_edit_panel(self._panel_conn_id)

    def _on_rp_info_clicked(self):
        """Info button in right panel header - opens system info panel with toggle logic."""
        if self._panel_conn_id:
            if self._panel_mode == _PANEL_SYSINFO and self._panel_conn_id == self._panel_conn_id:
                self._close_right_panel()
            else:
                self._open_sysinfo_panel(self._panel_conn_id)

    # ------------------------------------------------------------------
    # Card selection
    # ------------------------------------------------------------------

    def _select_card(self, conn_id: str):
        if conn_id != self._panel_conn_id and not self._guard_leave_form():
            return
        if self._selected_id and self._selected_id in self._cards:
            prev = self._cards[self._selected_id]
            prev.setProperty("selected", False)
            prev.style().unpolish(prev)
            prev.style().polish(prev)

        self._selected_id = conn_id
        if conn_id in self._cards:
            card = self._cards[conn_id]
            if not card.is_mounted:
                card.setProperty("selected", True)
                card.style().unpolish(card)
                card.style().polish(card)

        # Card click always shows connection details (not sysinfo)
        if self._panel_mode not in (_PANEL_INFO, _PANEL_EDIT) or self._panel_conn_id != conn_id:
            self._open_info_panel(conn_id)

    @pyqtSlot(str)
    def _on_info_requested(self, conn_id: str):
        """[i] button clicked — always shows system info, toggles closed on second click."""
        if self._panel_mode == _PANEL_SYSINFO and self._panel_conn_id == conn_id:
            self._close_right_panel()
        else:
            self._open_sysinfo_panel(conn_id)

    def _update_status(self):
        connections = self._mgr.get_all()
        total = len(connections)
        mounted = sum(1 for c in self._cards.values() if c.is_mounted)
        if total:
            active_str = tr("badge.n_active", n=total)
            mount_str  = tr("badge.n_mounted", n=mounted)
            self._badge_lbl.setText(f"{active_str} · {mount_str}")
        else:
            self._badge_lbl.setText("")
        self._mount_count_lbl.setText(
            tr("status.mounted_short", n=mounted) if mounted else tr("status.mounted_none")
        )

    # ------------------------------------------------------------------
    # Mount state polling
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
                # Refresh open panel for this connection on mount state change
                if self._panel_conn_id == conn_id:
                    if self._panel_mode == _PANEL_INFO:
                        self._open_info_panel(conn_id)
                    elif self._panel_mode == _PANEL_SYSINFO:
                        self._open_sysinfo_panel(conn_id)

        self._update_status()

    # ------------------------------------------------------------------
    # Action slots
    # ------------------------------------------------------------------

    def _on_add(self):
        self._open_add_panel()

    def _on_delete(self):
        conn_id = self._panel_conn_id or self._selected_id
        if not conn_id:
            self._set_status(tr("delete.select_one"))
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
        self._close_right_panel()
        self._refresh_list()
        self._set_status(tr("status.connection_deleted", name=conn.name))

    def _prepare_auth(self, conn):
        import copy
        conn = copy.copy(conn)

        if conn.auth_method == "ask":
            dlg = QDialog(self)
            dlg.setWindowTitle(tr("addedit.auth.ask.title"))
            dlg.setModal(True)
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel(tr("addedit.auth.ask.prompt", name=conn.name)))
            rb_pw  = QRadioButton(tr("addedit.auth.password"))
            rb_key = QRadioButton(tr("addedit.auth.key"))
            has_key = bool(conn.key_path)
            rb_key.setEnabled(has_key)
            if has_key and not conn.password:
                rb_key.setChecked(True)
            else:
                rb_pw.setChecked(True)
            layout.addWidget(rb_pw)
            layout.addWidget(rb_key)
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            btns.accepted.connect(dlg.accept)
            btns.rejected.connect(dlg.reject)
            layout.addWidget(btns)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return None
            conn.auth_method = "password" if rb_pw.isChecked() else "key"

        if conn.auth_method == "password" and not conn.password:
            pw, ok = QInputDialog.getText(
                self, tr("auth.enter_password.title"),
                tr("auth.enter_password.prompt", name=conn.name),
                QLineEdit.EchoMode.Password,
            )
            if not ok:
                return None
            conn.password = pw

        return conn

    @pyqtSlot(str)
    def _on_mount(self, conn_id: str):
        if conn_id in self._workers:
            return
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return
        conn = self._prepare_auth(conn)
        if conn is None:
            return
        self._set_status(tr("status.connecting", name=conn.name, drive=conn.drive_letter))
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
            if self._panel_conn_id == conn_id:
                # Keep header mount state and panel content in sync
                if self._panel_mode == _PANEL_INFO:
                    self._open_info_panel(conn_id)
                elif self._panel_mode == _PANEL_SYSINFO:
                    self._open_sysinfo_panel(conn_id)
                else:
                    self._sync_rp_mount_button(conn_id)
        else:
            name = conn.name if conn else "?"
            if self._show_mount_failure_dialog(conn, result.message):
                QTimer.singleShot(500, lambda: self._on_mount(conn_id))
                return
            self._set_status(tr("status.connect_failed", name=name))
        self._update_status()

    @pyqtSlot(str)
    def _on_unmount(self, conn_id: str):
        if conn_id in self._workers:
            return
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return
        self._set_status(tr("status.disconnecting", drive=conn.drive_letter))
        card = self._cards.get(conn_id)
        if card:
            card.show_loading(tr("card.loading.disconnect"))
        worker = UnmountWorker(conn_id, conn.drive_letter, self._controller)
        worker.finished.connect(self._on_unmount_finished)
        self._workers[conn_id] = worker
        worker.start()

    def _on_unmount_finished(self, conn_id: str, result):
        try:
            worker = self._workers.pop(conn_id, None)
            if worker is not None:
                worker.finished.disconnect()
                worker.deleteLater()
        except Exception as e:
            logger.warning(f"Unmount worker cleanup error: {e}")

        try:
            conn = self._mgr.get_by_id(conn_id)
            card = self._cards.get(conn_id)
            if card:
                card.hide_loading()
            if result.success:
                if card:
                    card.update_mount_state(False)
                self._save_active_mount(conn_id, False)
                self._set_status(tr("status.disconnected", name=conn.name if conn else "?"))
                try:
                    if self._panel_conn_id == conn_id:
                        if self._panel_mode == _PANEL_INFO:
                            self._open_info_panel(conn_id)
                        elif self._panel_mode == _PANEL_SYSINFO:
                            self._open_sysinfo_panel(conn_id)
                        else:
                            self._sync_rp_mount_button(conn_id)
                except Exception as e:
                    logger.warning(f"Panel refresh after unmount failed: {e}")
            else:
                self._err_popup(tr("unmount.failed.title"), result.message)
                if conn:
                    self._set_status(tr("status.disconnect_failed", name=conn.name))
        except Exception as e:
            logger.error(f"Unexpected error in unmount callback for {conn_id}: {e}")
        finally:
            try:
                self._update_status()
            except Exception:
                pass

    @pyqtSlot(str)
    def _on_ssh_terminal(self, conn_id: str):
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return
        conn = self._prepare_auth(conn)
        if conn is None:
            return
        from src.ssh_launcher import launch_ssh_terminal
        success, error = launch_ssh_terminal(conn, self._mgr.get_settings())
        if success:
            backend = "PuTTY" if self._mgr.get_settings().use_putty else "SSH"
            self._set_status(tr("status.ssh_started", backend=backend, name=conn.name))
        else:
            self._err_popup("SSH-Terminal", error)

    def _on_open_mounted_path(self, conn_id: str):
        import subprocess
        conn = self._mgr.get_by_id(conn_id)
        if not conn:
            return
        card = self._cards.get(conn_id)
        if not card or not card.is_mounted:
            return
        path = conn.drive_letter
        if not path.endswith("\\"):
            path += "\\"
        try:
            is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            is_admin = False
        # SECURITY FIX: Validate path to prevent command injection
        if not path or not isinstance(path, str):
            return
        # Reject dangerous characters but allow backslash for Windows paths
        dangerous = set(';|&`$(){}[]<>!"\'\n\r\t')
        if any(c in dangerous for c in path):
            logger.warning(f"Rejected potentially dangerous path: {path}")
            return
        
        try:
            if is_admin:
                subprocess.Popen(["explorer.exe", path], creationflags=0x00000010)
            else:
                os.startfile(path)
            self._set_status(tr("status.opening_explorer", path=path))
        except Exception as e:
            self._err_popup(tr("dialog.error"), str(e))

    def _on_settings(self):
        self._open_settings_panel()

    def _apply_settings(self):
        s = self._mgr.get_settings()
        self._apply_settings_object(s)

    def _apply_settings_object(self, s: AppSettings):
        interval = s.check_interval_seconds * 1000
        if self._poll_timer.interval() != interval:
            self._poll_timer.setInterval(interval)
        self._apply_debug_mode()
        from src.ui.theme import get_stylesheet
        theme = s.theme or "dark"
        QApplication.instance().setStyleSheet(get_stylesheet(theme))
        self._apply_titlebar_color(theme)

    def _apply_titlebar_color(self, theme: str = None):
        """Apply Windows title bar color to match the app theme (Windows 11+)."""
        if theme is None:
            theme = (self._mgr.get_settings().theme or "dark")
        if theme == "light":
            bg_hex = "#f0f2f5"
            text_hex = "#1a2332"
        else:
            bg_hex = "#0d0d12"
            text_hex = "#c8d6e5"
        try:
            hwnd = int(self.winId())
            r, g, b = int(bg_hex[1:3], 16), int(bg_hex[3:5], 16), int(bg_hex[5:7], 16)
            colorref = ctypes.c_uint32((b << 16) | (g << 8) | r)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 35, ctypes.byref(colorref), ctypes.sizeof(colorref)
            )
            tr_v, tg_v, tb_v = int(text_hex[1:3], 16), int(text_hex[3:5], 16), int(text_hex[5:7], 16)
            text_colorref = ctypes.c_uint32((tb_v << 16) | (tg_v << 8) | tr_v)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 36, ctypes.byref(text_colorref), ctypes.sizeof(text_colorref)
            )
        except Exception:
            pass

    def _apply_debug_mode(self):
        enabled = self._mgr.get_settings().debug_mode
        self._debug_btn.setVisible(enabled)

    def _on_debug(self):
        if not hasattr(self, '_debug_window') or self._debug_window is None:
            self._debug_window = DebugWindow(self)
        self._debug_window.show()
        self._debug_window.raise_()
        self._debug_window.activateWindow()

    def _on_user_management(self):
        if not Session.is_admin():
            return
        self._open_users_panel()

    def _on_change_own_password(self):
        user = Session.current()
        if not user:
            return
        from src.ui.dialogs.login_dialog import ChangePasswordDialog
        ChangePasswordDialog(user.id, self).exec()

    def _on_logout(self):
        reply = QMessageBox.question(
            self, tr("logout.title"), tr("logout.confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._unmount_all()
        Session.logout()
        QApplication.quit()

    def _on_about(self):
        from src.ui.dialogs.about_dialog import AboutDialog
        AboutDialog(self).exec()

    # ------------------------------------------------------------------
    # Window close
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        settings = self._mgr.get_settings()
        if settings.minimize_to_tray:
            event.ignore()
            self.hide()
            self._tray.showMessage(
                "NEO SSH-Win Manager", tr("tray.running"),
                self._tray.MessageIcon.Information, 2000,
            )
        else:
            self._unmount_all()
            self._kill_sshfs_processes()
            event.accept()
            QApplication.quit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, msg: str):
        self._status_lbl.setText(msg)

    @pyqtSlot(str)
    def _on_log_record_for_status(self, line: str):
        lu = line.upper()
        if "[ERROR" in lu or "[CRITICAL" in lu:
            short = line.split(" — ", 1)[-1] if " — " in line else line
            self._set_status(f"⚠ Fehler: {short[:140]}")

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

    def _load_active_mounts(self):
        try:
            self._active_mounts = set(self._mgr.get_active_mounts())
        except Exception as e:
            logger.warning(f"Konnte aktive Mounts nicht laden: {e}")
            self._active_mounts = set()

    def _save_active_mount(self, conn_id: str, mounted: bool):
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
        if not self._mgr.get_settings().auto_reconnect_mounts:
            return
        active_ids = self._mgr.get_active_mounts()
        if not active_ids:
            return
        for conn_id in active_ids:
            conn = self._mgr.get_by_id(conn_id)
            if conn and not self._controller.is_mounted(conn.drive_letter):
                QTimer.singleShot(1000, lambda cid=conn_id: self._on_mount(cid))

    def _unmount_all(self):
        mounted_map = self._controller.get_mounted_drives()
        for letter in mounted_map.keys():
            try:
                self._controller.unmount(letter)
            except Exception as e:
                logger.warning(f"Unmount {letter} fehlgeschlagen: {e}")

    def _kill_sshfs_processes(self):
        import subprocess
        for proc_name in ["sshfs.exe", "sshfs-win.exe", "sshfs-win-broker.exe"]:
            try:
                subprocess.run(["taskkill", "/F", "/IM", proc_name],
                               capture_output=True, creationflags=0x08000000)
            except Exception:
                pass

    def _debug_widget_under_mouse(self):
        """Debug the widget currently under the mouse cursor (triggered by F2)."""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QCursor
        
        # Get widget under mouse cursor using global cursor position
        cursor_pos = QCursor.pos()
        widget = QApplication.widgetAt(cursor_pos)
        
        if widget:
            self._log_widget_debug_info(widget)
        else:
            msg = "DEBUG: No widget under mouse cursor"
            print(msg)
            logger.debug(msg)
            if hasattr(self, '_debug_window') and self._debug_window and not sip.isdeleted(self._debug_window):
                self._debug_window.append_log(msg + "\n")

    def _log_widget_debug_info(self, widget):
        """Log detailed widget information to debug console, logger, and statusbar."""
        # Collect widget information
        widget_info = {
            'widget_type': type(widget).__name__,
            'object_name': widget.objectName(),
            'text': getattr(widget, 'text', lambda: 'N/A')(),
            'tooltip': getattr(widget, 'toolTip', lambda: 'N/A')(),
            'accessible_name': getattr(widget, 'accessibleName', lambda: 'N/A')(),
            'parent': type(widget.parent()).__name__ if widget.parent() else None,
            'visible': widget.isVisible(),
            'enabled': widget.isEnabled(),
            'geometry': f"{widget.geometry().width()}x{widget.geometry().height()} at ({widget.geometry().x()}, {widget.geometry().y()})",
            'style_sheet': widget.styleSheet()[:100] + '...' if len(widget.styleSheet()) > 100 else widget.styleSheet()
        }
        
        # Format debug message
        debug_msg = "=== DEBUG: Widget Under Mouse ===\n"
        for key, value in widget_info.items():
            debug_msg += f"{key.upper()}: {value}\n"
        debug_msg += "================================\n"
        
        # Log to debug console
        print(debug_msg)
        
        # Log to file logger
        logger.debug(debug_msg)
        
        # Log to debug window if exists
        if hasattr(self, '_debug_window') and self._debug_window and not sip.isdeleted(self._debug_window):
            self._debug_window.append_log(debug_msg)
        
        # Log to statusbar
        status_msg = f"DEBUG: {widget_info['widget_type']} | {widget_info['object_name'] or 'No Name'} | {widget_info['text'][:30] if widget_info['text'] != 'N/A' else 'N/A'}"
        if hasattr(self, 'statusBar') and self.statusBar():
            self.statusBar().showMessage(status_msg, 5000)
