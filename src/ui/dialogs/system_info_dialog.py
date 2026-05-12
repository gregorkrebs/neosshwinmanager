"""
system_info_dialog.py – Legacy standalone wrapper around the modern SystemInfoPanel.
"""

from PyQt6.QtWidgets import (
    QApplication, QDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget
)
from PyQt6.QtCore import Qt

from src.config import Connection
from src.i18n import tr
from src.ui.dialog_utils import make_maximize_button, match_parent_height
from src.ui.system_info_panel import SystemInfoPanel


class SystemInfoDialog(QDialog):
    """Standalone dialog that reuses the themed SystemInfoPanel."""

    def __init__(self, conn: Connection, parent=None):
        super().__init__(parent)
        self._conn = conn
        self.setObjectName("dialogSurface")
        self.setWindowTitle(tr("sysinfo.title", name=conn.name))
        self.setMinimumSize(560, 560)
        self.setModal(True)
        self._build_ui()

        screen = QApplication.primaryScreen()
        if screen:
            self.setMaximumHeight(int(screen.availableGeometry().height() * 0.95))
        match_parent_height(self, parent)

    def _divider(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("divider")
        frame.setFixedHeight(1)
        return frame

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("dialogHeroCard")
        hero_l = QVBoxLayout(hero)
        hero_l.setContentsMargins(22, 20, 22, 20)
        hero_l.setSpacing(8)

        title = QLabel(tr("sysinfo.title", name=self._conn.name))
        title.setObjectName("dialogTitle")
        hero_l.addWidget(title)

        lead = QLabel(f"{self._conn.user}@{self._conn.host}:{self._conn.port}  ·  {self._conn.remote_path}")
        lead.setObjectName("dialogLead")
        lead.setWordWrap(True)
        hero_l.addWidget(lead)
        outer.addWidget(hero)

        content = QFrame()
        content.setObjectName("dialogSectionCard")
        content_l = QVBoxLayout(content)
        content_l.setContentsMargins(0, 0, 0, 0)
        content_l.setSpacing(0)
        content_l.addWidget(SystemInfoPanel(self._conn, parent=content, settings=self._settings))
        outer.addWidget(content, stretch=1)

        footer = QWidget()
        footer.setObjectName("dialogBtnBar")
        footer_l = QVBoxLayout(footer)
        footer_l.setContentsMargins(0, 8, 0, 0)
        footer_l.setSpacing(0)
        footer_l.addWidget(self._divider())

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 10, 0, 0)
        btn_row.addWidget(make_maximize_button(self))
        btn_row.addStretch()

        close_btn = QPushButton(tr("dialog.close"))
        close_btn.setObjectName("secondaryBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        footer_l.addLayout(btn_row)
        outer.addWidget(footer)