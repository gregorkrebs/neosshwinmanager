"""
debug_window.py – Live log viewer dialog for SSH Win Manager.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QCheckBox, QFileDialog, QWidget
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

import src.app_logger as _app_logger
from src.auth_manager import Session, UserConnectionManager
from src.sshfs_controller import SSHFSController


def _emitter():
    """Return the live log_emitter, or None if not yet initialised."""
    return _app_logger.log_emitter


class DebugWindow(QDialog):
    """Floating live log viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH Win Manager – Debug Log")
        self.setMinimumSize(700, 480)
        self.resize(860, 560)
        self.setModal(False)
        self._auto_scroll = True
        self._build_ui()
        self._load_history()

        em = _emitter()
        if em is not None:
            em.new_record.connect(self._on_new_record)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_toolbar())

        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setFont(QFont("Consolas", 10))
        self._log_view.setObjectName("debugLogView")
        self._log_view.setStyleSheet(
            "QTextEdit#debugLogView { background-color:#080810; color:#c8d6e5; border:none; padding:10px; }"
        )
        layout.addWidget(self._log_view, stretch=1)

    def _build_toolbar(self) -> QWidget:
        tb = QWidget()
        tb.setFixedHeight(50)
        tb.setObjectName("debugToolbar")
        tb.setStyleSheet(
            "QWidget#debugToolbar { background:#0a0a14; border-bottom:1px solid #1a1a2e; }"
        )
        h = QHBoxLayout(tb)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(10)

        dot = QLabel("●")
        dot.setObjectName("statusDot")
        title = QLabel("Live Debug Log")
        title.setObjectName("connName") # Use existing name style
        h.addWidget(dot)
        h.addWidget(title)
        h.addStretch()

        self._auto_scroll_cb = QCheckBox("Auto-scroll")
        self._auto_scroll_cb.setChecked(True)
        self._auto_scroll_cb.toggled.connect(
            lambda v: setattr(self, "_auto_scroll", v)
        )
        h.addWidget(self._auto_scroll_cb)

        for label, slot, btn_type in [
            ("Bereinigen", self._purge_mounts, "danger"),
            ("Test CPU", self._test_decryption, "warning"), # simplified label for space
            ("Leeren",    self._clear,     "secondary"),
            ("Speichern", self._save_log,  "primary"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("actionBtn")
            if btn_type != "secondary":
                btn.setProperty("btn_type", btn_type)
            btn.setFixedSize(90 if len(label) < 10 else 110, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        return tb

    # ------------------------------------------------------------------
    # Log rendering
    # ------------------------------------------------------------------

    def _load_history(self):
        for line in _app_logger.get_all_logs():
            self._render_line(line)
        self._scroll_to_bottom()

    @pyqtSlot(str)
    def _on_new_record(self, line: str):
        self._render_line(line)
        if self._auto_scroll:
            self._scroll_to_bottom()

    def _render_line(self, line: str):
        color = "#c8d6e5"
        lu = line.upper()
        if "[WARNING" in lu:
            color = "#f59e0b"
        elif "[ERROR" in lu:
            color = "#ef4444"
        elif "[CRITICAL" in lu:
            color = "#ff00cc"
        elif "[DEBUG" in lu:
            color = "#4a5a6a"

        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self._log_view.append(
            f'<span style="color:{color}; font-family:Consolas,monospace;">{safe}</span>'
        )

    def _scroll_to_bottom(self):
        sb = self._log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _clear(self):
        self._log_view.clear()

    def _save_log(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Log speichern", "sshwinmanager_debug.log",
            "Log Files (*.log);;All Files (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._log_view.toPlainText())

    def _purge_mounts(self):
        from src.app_logger import logger
        logger.warning("Benutzer hat 'Laufwerke bereinigen' gestartet...")
        ok = SSHFSController().purge_all_stale_mounts()
        if ok:
            logger.info("Bereinigung erfolgreich.")
        else:
            logger.error("Bereinigung fehlgeschlagen.")

    def _test_decryption(self):
        from src.app_logger import logger
        logger.info("Starte Entschlüsselungs-Test...")
        user = Session.current()
        if not user:
            logger.error("Kein Benutzer eingeloggt.")
            return

        mgr = UserConnectionManager(user)
        conns = mgr.get_all()
        logger.info(f"Test für {len(conns)} Verbindungen...")
        for c in conns:
            if c.password:
                logger.info(f"✓ {c.name}: Passwort erfolgreich entschlüsselt.")
            else:
                logger.warning(f"⚠ {c.name}: Passwort ist leer oder Entschlüsselung fehlgeschlagen.")
        logger.info("Test abgeschlossen.")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        em = _emitter()
        if em is not None:
            try:
                em.new_record.disconnect(self._on_new_record)
            except Exception:
                pass
        super().closeEvent(event)
