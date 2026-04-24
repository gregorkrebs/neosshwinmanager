"""
loading_overlay.py – A very simple loading overlay without animations.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LoadingOverlay(QWidget):
    """A very simple overlay with just text - no animations to prevent crashes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_active = False
        self._setup_ui()
        self.hide()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create a semi-transparent background frame
        self._bg_frame = QFrame()
        self._bg_frame.setObjectName("loadingFrame")
        self._bg_frame.setStyleSheet("""
            QFrame#loadingFrame {
                background-color: rgba(40, 44, 52, 240);
                border: 2px solid rgba(74, 158, 255, 0.5);
                border-radius: 8px;
            }
        """)
        
        bg_layout = QVBoxLayout(self._bg_frame)
        bg_layout.setContentsMargins(40, 30, 40, 30)
        bg_layout.setSpacing(15)
        
        # Loading text
        self._loading_label = QLabel("Verbinde...")
        self._loading_label.setObjectName("loadingText")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.setStyleSheet("""
            QLabel#loadingText {
                color: #ffffff;
                font-size: 16px;
                font-weight: 600;
            }
        """)
        
        # Simple loading dots animation using text
        self._dots_label = QLabel("...")
        self._dots_label.setObjectName("loadingDots")
        self._dots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dots_label.setStyleSheet("""
            QLabel#loadingDots {
                color: #4a9eff;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        
        bg_layout.addWidget(self._loading_label)
        bg_layout.addWidget(self._dots_label)
        
        layout.addWidget(self._bg_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def show_loading(self, text="Verbinde"):
        """Show the loading overlay."""
        self._loading_label.setText(text)
        self._is_active = True
        
        # Resize to cover parent
        if self.parent():
            self.setGeometry(self.parent().rect())
        
        self.show()
        self.raise_()
        
    def hide_loading(self):
        """Hide the loading overlay."""
        if not self._is_active:
            return
            
        self._is_active = False
        self.hide()
        
    def resizeEvent(self, event):
        """Handle parent resize."""
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())
