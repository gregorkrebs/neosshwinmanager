"""
about_dialog.py – About dialog for SSH Win Manager.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QScrollArea, QWidget, QFrame, QApplication
)
from PyQt6.QtCore import Qt


import os
from PyQt6.QtGui import QIcon, QPixmap
from src.ui.dialog_utils import match_parent_height, make_maximize_button
from src.i18n import tr
APP_VERSION = "1.2.0"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("about.title"))
        self.setFixedWidth(340)
        self.setModal(True)
        self._build_ui()
        # Max-Höhe = Bildschirm, Start-Höhe = volle Hauptfenster-Höhe (Inhalt scrollt bei Overflow).
        screen = QApplication.primaryScreen()
        if screen:
            self.setMaximumHeight(int(screen.availableGeometry().height() * 0.95))
        match_parent_height(self, parent)

    def _build_ui(self):
        # Äußeres Layout: scrollbarer Content oben, fixer Close-Button unten.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll, stretch=1)

        inner = QWidget()
        scroll.setWidget(inner)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(28, 24, 28, 12)
        layout.setSpacing(6)

        # Icon / Header
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Get icon path (robust discovery)
        def get_resource_path(relative_path):
            import sys
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), relative_path)
            
        icon_path = get_resource_path(os.path.join("assets", "app_icon.png"))
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_lbl.setPixmap(pix)
        else:
            from src.ui.icons import pixmap as svg_pixmap
            icon_lbl.setPixmap(svg_pixmap("cloud", "#00b4d8", 64))
        
        layout.addWidget(icon_lbl)

        title_lbl = QLabel("NEO SSH-Win Manager")
        title_lbl.setObjectName("dialogTitle")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        ver_lbl = QLabel(tr("about.version", version=APP_VERSION))
        ver_lbl.setObjectName("fieldLabel")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver_lbl)

        layout.addSpacing(10)

        desc = QLabel(tr("about.desc"))
        desc.setObjectName("mutedLabel")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(8)

        req_lbl = QLabel(tr("about.requires"))
        req_lbl.setObjectName("accentLabel")
        req_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(req_lbl)

        layout.addSpacing(12)

        author_title = QLabel(tr("about.developers"))
        author_title.setObjectName("secondaryTitle")
        author_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author_title)

        author1 = QLabel('<a href="https://github.com/Den4ik53" style="color: #6a7a8a; text-decoration: none;">Den4ik53</a>')
        author1.setOpenExternalLinks(True)
        author1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author1)

        author2 = QLabel('<a href="https://github.com/gregorkrebs" style="color: #6a7a8a; text-decoration: none;">Gregor Krebs</a>')
        author2.setOpenExternalLinks(True)
        author2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author2)

        layout.addStretch()

        # Fixe Button-Leiste außerhalb der Scroll-Area.
        btn_bar = QWidget()
        btn_bar_layout = QVBoxLayout(btn_bar)
        btn_bar_layout.setContentsMargins(28, 8, 28, 20)
        btn_bar_layout.setSpacing(8)

        ok_btn = QPushButton(tr("dialog.close"))
        ok_btn.setObjectName("primaryBtn")
        ok_btn.setFixedWidth(100)
        ok_btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addWidget(make_maximize_button(self))
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addStretch()
        _sp = QWidget(); _sp.setFixedWidth(32); btn_row.addWidget(_sp)
        btn_bar_layout.addLayout(btn_row)

        self.layout().addWidget(btn_bar)
