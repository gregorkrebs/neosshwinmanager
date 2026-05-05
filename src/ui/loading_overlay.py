"""
loading_overlay.py – A very simple loading overlay without animations.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt


class LoadingOverlay(QWidget):
    """A very simple overlay with just text - no animations to prevent crashes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_active = False
        self._setup_ui()
        self.hide()
        
    def _setup_ui(self):
        self.setObjectName("loadingOverlay")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create a semi-transparent background frame
        self._bg_frame = QFrame()
        self._bg_frame.setObjectName("loadingFrame")
        
        bg_layout = QVBoxLayout(self._bg_frame)
        bg_layout.setContentsMargins(34, 26, 34, 26)
        bg_layout.setSpacing(8)
        
        # Loading text
        self._loading_label = QLabel("Verbinde...")
        self._loading_label.setObjectName("loadingText")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Simple loading dots animation using text
        self._dots_label = QLabel("...")
        self._dots_label.setObjectName("loadingDots")
        self._dots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._hint_label = QLabel("Frontend-artiger Wartestatus fuer den aktuellen Vorgang")
        self._hint_label.setObjectName("loadingHint")
        self._hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint_label.setWordWrap(True)
        
        bg_layout.addWidget(self._loading_label)
        bg_layout.addWidget(self._dots_label)
        bg_layout.addWidget(self._hint_label)
        
        layout.addWidget(self._bg_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def show_loading(self, text="Verbinde"):
        """Show the loading overlay."""
        self._loading_label.setText(text)
        self._dots_label.setText("...")
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
