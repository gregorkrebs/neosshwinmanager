import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QWidget, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.dialog_utils import match_parent_height
from src.ui.frameless_dialog import FramelessDialog
from src.ui.widgets.no_wheel import NoWheelScrollArea
from src.i18n import tr

class UpdateDialog(FramelessDialog):
    """
    Dialog to show available updates and initiate the installation.
    """
    
    start_background_download = pyqtSignal()

    def __init__(self, parent=None, version: str = "", changelog: str = "", download_url: str = "", obj_type: str = "exe"):
        super().__init__(parent)
        self.version = version
        self.changelog = changelog
        self.download_url = download_url
        self.obj_type = obj_type
        
        self.setObjectName("dialogSurface")
        self.setWindowTitle("Update verfügbar")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        self.setModal(True)
        self._build_ui()
        match_parent_height(self, parent)

    def _build_ui(self):
        outer = QVBoxLayout(self._fdlg_content)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Hero
        hero = QFrame()
        hero.setObjectName("dialogHeroCard")
        hero_l = QVBoxLayout(hero)
        hero_l.setContentsMargins(22, 20, 22, 20)
        hero_l.setSpacing(8)

        title = QLabel(f"Version {self.version} ist verfügbar!")
        title.setObjectName("dialogTitle")
        hero_l.addWidget(title)

        lead = QLabel("Es liegt ein neues Update für NEO SSH-Win Manager vor.")
        lead.setObjectName("dialogLead")
        lead.setWordWrap(True)
        hero_l.addWidget(lead)
        outer.addWidget(hero)
        
        # Details / Changelog
        scroll = NoWheelScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_l = QVBoxLayout(inner)
        inner_l.setContentsMargins(22, 20, 22, 20)
        
        changelog_lbl = QLabel(self.changelog)
        changelog_lbl.setObjectName("fieldLabel")
        changelog_lbl.setWordWrap(True)
        changelog_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        inner_l.addWidget(changelog_lbl)
        inner_l.addStretch()
        
        scroll.setWidget(inner)
        outer.addWidget(scroll, stretch=1)
        
        # Progress (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(4)
        
        outer.addWidget(self.progress_bar)

        # Bottom Buttons
        btn_bar = QWidget()
        btn_bar.setObjectName("dialogBtnBar")
        btn_bar_layout = QHBoxLayout(btn_bar)
        btn_bar_layout.setContentsMargins(20, 16, 20, 16)
        btn_bar_layout.setSpacing(10)

        cancel_btn = QPushButton("Ignorieren")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        
        self.browser_btn = QPushButton("Im Browser herunterladen")
        self.browser_btn.setObjectName("secondaryBtn")
        self.browser_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browser_btn.clicked.connect(self._open_browser)
        
        self.install_btn = QPushButton("Update automatisch installieren")
        self.install_btn.setObjectName("primaryBtn")
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.clicked.connect(self._start_install)

        btn_bar_layout.addStretch()
        btn_bar_layout.addWidget(cancel_btn)
        btn_bar_layout.addWidget(self.browser_btn)
        
        if self.obj_type == "exe":
            btn_bar_layout.addWidget(self.install_btn)
            
        outer.addWidget(btn_bar)

    def _open_browser(self):
        if self.download_url:
            webbrowser.open(self.download_url)
        self.accept()

    def _start_install(self):
        self.install_btn.setEnabled(False)
        self.install_btn.setText("Lade herunter...")
        self.browser_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.start_background_download.emit()

    def update_progress(self, percent: int):
        self.progress_bar.setValue(percent)

    def on_download_finished(self, success: bool, msg: str):
        if success:
            self.install_btn.setText("Fertig (Installation bei Beenden)")
            self.install_btn.setStyleSheet("background-color: #2e7d32; color: #fff;")
            self.progress_bar.setValue(100)
            # Dialog automatisch nach 2 Sekunden schließen
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, self.accept)
        else:
            self.install_btn.setText("Fehler beim Herunterladen")
            self.install_btn.setEnabled(True)
            self.browser_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
