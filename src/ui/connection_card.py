"""
connection_card.py – Widget representing a single SSH connection in the list.
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
from src.config import Connection
from src.ui.loading_overlay import LoadingOverlay
from src.ui.icons import icon as svg_icon, pixmap as svg_pixmap
from src.i18n import tr


class ConnectionCard(QFrame):
    """A row widget displaying one SSH connection with mount/unmount toggle."""

    mount_requested = pyqtSignal(str)    # emits connection id
    unmount_requested = pyqtSignal(str)  # emits connection id
    edit_requested = pyqtSignal(str)     # emits connection id
    delete_requested = pyqtSignal(str)   # emits connection id
    ssh_requested = pyqtSignal(str)      # emits connection id
    open_path_requested = pyqtSignal(str) # emits connection id (open mounted drive in explorer)
    info_requested = pyqtSignal(str)     # emits connection id (system info popup)

    def __init__(self, conn: Connection, mounted: bool = False, parent=None):
        super().__init__(parent)
        self._conn = conn
        self._mounted = mounted
        self.setObjectName("connectionCard")
        self._build_ui()
        self.update_mount_state(mounted)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        # --- Connection icon (folder when mounted, cloud when not)
        self._cloud_lbl = QLabel()
        self._cloud_lbl.setObjectName("cloudIcon")
        self._cloud_lbl.setFixedSize(QSize(34, 34))
        self._cloud_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cloud_lbl.mousePressEvent = self._on_icon_clicked
        layout.addWidget(self._cloud_lbl)

        # --- Info column
        info_col = QVBoxLayout()
        info_col.setSpacing(3)
        info_col.setContentsMargins(0, 0, 0, 0)

        self._name_lbl = QLabel(self._conn.name)
        self._name_lbl.setObjectName("connName")

        detail = f"{self._conn.host}  •  {self._conn.remote_path}"
        self._detail_lbl = QLabel(detail)
        self._detail_lbl.setObjectName("connDetail")
        self._detail_lbl.setWordWrap(False)

        info_col.addWidget(self._name_lbl)
        info_col.addWidget(self._detail_lbl)
        layout.addLayout(info_col, stretch=1)

        # --- Drive badge
        self._drive_badge = QLabel(self._conn.drive_letter)
        self._drive_badge.setObjectName("driveBadge")
        self._drive_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drive_badge.setFixedSize(QSize(38, 28))
        layout.addWidget(self._drive_badge)

        # --- Info button (system info popup)
        self._info_btn = QPushButton()
        self._info_btn.setObjectName("cardInfoBtn")
        self._info_btn.setFixedSize(QSize(32, 38))
        self._info_btn.setIcon(svg_icon("info", "#aab4c4", 18))
        self._info_btn.setIconSize(QSize(18, 18))
        self._info_btn.setToolTip(tr("card.tooltip.info"))
        self._info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._info_btn.clicked.connect(lambda: self.info_requested.emit(self._conn.id))
        layout.addWidget(self._info_btn)

        # --- Edit button (per-card edit; disabled while mounted)
        self._edit_btn = QPushButton()
        self._edit_btn.setObjectName("cardEditBtn")
        self._edit_btn.setFixedSize(QSize(32, 38))
        self._edit_btn.setIcon(svg_icon("edit", "#aab4c4", 18))
        self._edit_btn.setIconSize(QSize(18, 18))
        self._edit_btn.setToolTip(tr("card.tooltip.edit"))
        self._edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._conn.id))
        layout.addWidget(self._edit_btn)

        # --- SSH Terminal button
        self._ssh_btn = QPushButton()
        self._ssh_btn.setObjectName("sshBtn")
        self._ssh_btn.setFixedSize(QSize(42, 38))
        self._ssh_btn.setIcon(svg_icon("terminal", "#00b4d8", 18))
        self._ssh_btn.setIconSize(QSize(18, 18))
        self._ssh_btn.setToolTip(tr("card.tooltip.ssh"))
        self._ssh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ssh_btn.clicked.connect(lambda: self.ssh_requested.emit(self._conn.id))
        layout.addWidget(self._ssh_btn)

        # --- Mount toggle button
        self._mount_btn = QPushButton()
        self._mount_btn.setObjectName("mountBtn")
        self._mount_btn.setFixedSize(QSize(42, 42))
        self._mount_btn.setIconSize(QSize(20, 20))
        self._mount_btn.setToolTip(tr("card.tooltip.mount"))
        self._mount_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mount_btn.clicked.connect(self._on_toggle)
        layout.addWidget(self._mount_btn)

    # ------------------------------------------------------------------
    # State update
    # ------------------------------------------------------------------

    def update_mount_state(self, mounted: bool):
        self._mounted = mounted

        # Update properties for self and child widgets
        self.setProperty("mounted", mounted)
        self._cloud_lbl.setProperty("mounted", mounted)
        self._drive_badge.setProperty("mounted", mounted)
        self._mount_btn.setProperty("mounted", mounted)

        # Icon: Ordner wenn verbunden, Wolke wenn getrennt
        icon_color = "#5ee7a0" if mounted else "#aab4c4"
        self._cloud_lbl.setPixmap(svg_pixmap(
            "folder" if mounted else "cloud", icon_color, 22
        ))
        # Mount-Button Symbol: check-circle / power
        self._mount_btn.setIcon(svg_icon(
            "check-circle" if mounted else "power",
            "#5ee7a0" if mounted else "#aab4c4",
            20
        ))

        # Cursor/Tooltip am Icon
        if mounted:
            self._cloud_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            self._cloud_lbl.setToolTip(tr("card.tooltip.open_path"))
        else:
            self._cloud_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            self._cloud_lbl.setToolTip(tr("card.tooltip.mount_off"))

        # Tooltip updates
        if mounted:
            self._mount_btn.setToolTip(tr("card.tooltip.mount_on"))
        else:
            self._mount_btn.setToolTip(tr("card.tooltip.mount_off"))

        # Edit nur erlaubt, solange NICHT gemountet
        self._edit_btn.setEnabled(not mounted)
        self._edit_btn.setToolTip(
            tr("card.tooltip.edit_locked") if mounted else tr("card.tooltip.edit")
        )

        # Force style re-polish
        for w in (self, self._cloud_lbl, self._drive_badge, self._mount_btn):
            w.style().unpolish(w)
            w.style().polish(w)

        self.update()

    def update_connection(self, conn: Connection):
        self._conn = conn
        self._name_lbl.setText(conn.name)
        self._detail_lbl.setText(f"{conn.host}  •  {conn.remote_path}")
        self._drive_badge.setText(conn.drive_letter)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_icon_clicked(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._mounted:
            self.open_path_requested.emit(self._conn.id)
        else:
            self.show_loading(tr("card.loading.connect"))
            self.mount_requested.emit(self._conn.id)

    def _on_toggle(self):
        if self._mounted:
            self.show_loading("Trenne")
            self.unmount_requested.emit(self._conn.id)
        else:
            self.show_loading("Verbinde")
            self.mount_requested.emit(self._conn.id)

    def show_loading(self, text="Lade..."):
        """Disable button during operation."""
        self._mount_btn.setEnabled(False)
        
    def hide_loading(self):
        """Re-enable button after operation."""
        self._mount_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def connection(self) -> Connection:
        return self._conn

    @property
    def is_mounted(self) -> bool:
        return self._mounted
