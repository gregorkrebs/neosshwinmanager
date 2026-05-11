"""
styled_message_box.py – A beautiful custom alternative to QMessageBox.
Supports Emojis and modern UI styling matching NEO SSH-Win Manager.
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QFrame
from PyQt6.QtCore import Qt, QSize
from src.config import AppSettings

class StyledMessageBox(QDialog):
    @classmethod
    def information(cls, parent, title: str, text: str):
        dlg = cls(parent, title, text, "info")
        dlg.exec()

    @classmethod
    def warning(cls, parent, title: str, text: str):
        dlg = cls(parent, title, text, "warning")
        dlg.exec()

    @classmethod
    def critical(cls, parent, title: str, text: str):
        dlg = cls(parent, title, text, "error")
        dlg.exec()

    @classmethod
    def question(cls, parent, title: str, text: str, yes_text: str = "Ja", no_text: str = "Nein") -> bool:
        dlg = cls(parent, title, text, "question", yes_text=yes_text, no_text=no_text)
        return dlg.exec() == QDialog.DialogCode.Accepted

    def __init__(self, parent, title: str, text: str, mode: str = "info", yes_text: str = "Ja", no_text: str = "Nein"):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        self.setObjectName("dialogSurface")
        # Determine theme base
        try:
             theme = AppSettings().theme or "dark"
        except:
             theme = "dark"
             
        self.setStyleSheet(f"""
            QDialog#dialogSurface {{
                background-color: {'#0d1117' if theme == 'dark' else '#f8fafc'};
                border-radius: 8px;
            }}
            QLabel#msgText {{
                color: {'#deebf7' if theme == 'dark' else '#1a2332'};
                font-size: 14px;
            }}
            QLabel#msgTitle {{
                color: {'#ffffff' if theme == 'dark' else '#000000'};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton {{
                background-color: #00b4d8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 14px;
                font-weight: bold;
                font-size: 13px;
                min-height: 32px;
                max-height: 32px;
            }}
            QPushButton:hover {{
                background-color: #0096b4;
            }}
            QPushButton#secondaryBtn {{
                background-color: {'#21262d' if theme == 'dark' else '#e1e4e8'};
                color: {'#c9d1d9' if theme == 'dark' else '#24292e'};
            }}
            QPushButton#secondaryBtn:hover {{
                background-color: {'#30363d' if theme == 'dark' else '#d1d5da'};
            }}
            QPushButton#dangerBtn {{
                background-color: #ef4444;
            }}
            QPushButton#dangerBtn:hover {{
                background-color: #dc2626;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        # Content Row
        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # Icon/Emoji
        emoji_map = {
            "info": "💡",
            "warning": "🚨",
            "error": "💥",
            "question": "🤔"
        }
        icon_lbl = QLabel(emoji_map.get(mode, "💬"))
        icon_lbl.setStyleSheet("font-size: 42px; background: transparent; margin-right: 10px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_row.addWidget(icon_lbl)

        # Text Layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        
        title_lbl = QLabel(title)
        title_lbl.setObjectName("msgTitle")
        text_layout.addWidget(title_lbl)

        msg_lbl = QLabel(text)
        msg_lbl.setObjectName("msgText")
        msg_lbl.setWordWrap(True)
        msg_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_layout.addWidget(msg_lbl)
        
        content_row.addLayout(text_layout, stretch=1)
        layout.addLayout(content_row)
        
        layout.addSpacing(8)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        if mode == "question":
            no_btn = QPushButton(no_text)
            no_btn.setObjectName("secondaryBtn")
            no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            no_btn.clicked.connect(self.reject)
            btn_layout.addWidget(no_btn)

            yes_btn = QPushButton(yes_text)
            yes_btn.setObjectName("dangerBtn" if "löschen" in text.lower() or "delete" in text.lower() else "primaryBtn")
            yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            yes_btn.clicked.connect(self.accept)
            btn_layout.addWidget(yes_btn)
        else:
            ok_btn = QPushButton("OK")
            ok_btn.setObjectName("primaryBtn")
            ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            ok_btn.clicked.connect(self.accept)
            btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)
