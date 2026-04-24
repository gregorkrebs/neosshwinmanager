"""
settings_dialog.py – Settings dialog for NEO SSH-Win Manager.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QSpinBox, QFrame, QWidget, QLineEdit,
    QFileDialog, QMessageBox, QScrollArea, QApplication, QComboBox
)
from PyQt6.QtCore import Qt
from src.config import AppSettings
from src.sshfs_controller import SSHFSController
from src.ui.dialog_utils import match_parent_height, make_maximize_button
from src.i18n import tr, available_languages


_LANG_LABELS = {"en": "English", "de": "Deutsch"}


class SettingsDialog(QDialog):

    def __init__(self, parent=None, settings: AppSettings = None):
        super().__init__(parent)
        self._settings = settings or AppSettings()
        self.setWindowTitle(tr("settings.title"))
        self.setMinimumWidth(440)
        self.setModal(True)
        self._build_ui()
        self._load_settings()
        screen = QApplication.primaryScreen()
        if screen:
            self.setMaximumHeight(int(screen.availableGeometry().height() * 0.95))
        match_parent_height(self, parent)

    def _section(self, title: str) -> QLabel:
        lbl = QLabel(title)
        lbl.setObjectName("sectionLabel")
        return lbl

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("fieldLabel")
        return lbl

    def _divider(self) -> QFrame:
        f = QFrame()
        f.setObjectName("divider")
        f.setFixedHeight(1)
        return f

    def _build_ui(self):
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
        layout.setContentsMargins(24, 20, 24, 12)
        layout.setSpacing(10)

        title = QLabel(tr("settings.title"))
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        layout.addWidget(self._divider())

        # ── LANGUAGE ─────────────────────────────────────────────────
        layout.addWidget(self._section(tr("settings.section.language")))
        lang_row = QHBoxLayout()
        lang_row.setContentsMargins(0, 0, 0, 0)
        lang_lbl = QLabel(tr("settings.language.label"))
        lang_lbl.setObjectName("fieldLabel")
        self._lang_combo = QComboBox()
        for code in available_languages():
            self._lang_combo.addItem(_LANG_LABELS.get(code, code), code)
        self._lang_combo.setFixedWidth(140)
        lang_row.addWidget(lang_lbl)
        lang_row.addStretch()
        lang_row.addWidget(self._lang_combo)
        layout.addLayout(lang_row)

        restart_hint = QLabel(tr("settings.language.restart"))
        restart_hint.setObjectName("fieldLabel")
        restart_hint.setWordWrap(True)
        layout.addWidget(restart_hint)
        layout.addWidget(self._divider())

        # ── GENERAL ──────────────────────────────────────────────────
        layout.addWidget(self._section(tr("settings.section.general")))
        self._start_with_windows = QCheckBox(tr("settings.start_with_windows"))
        self._minimize_to_tray = QCheckBox(tr("settings.minimize_to_tray"))
        self._require_admin = QCheckBox(tr("settings.require_admin"))
        layout.addWidget(self._start_with_windows)
        layout.addWidget(self._minimize_to_tray)
        layout.addWidget(self._require_admin)
        layout.addWidget(self._divider())

        # ── MOUNT STATUS ─────────────────────────────────────────────
        layout.addWidget(self._section(tr("settings.section.mount")))

        interval_row = QHBoxLayout()
        interval_row.setContentsMargins(0, 0, 0, 0)
        interval_lbl = QLabel(tr("settings.check_interval"))
        interval_lbl.setObjectName("fieldLabel")
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(5, 300)
        self._interval_spin.setValue(30)
        self._interval_spin.setFixedWidth(80)
        interval_row.addWidget(interval_lbl)
        interval_row.addStretch()
        interval_row.addWidget(self._interval_spin)
        layout.addLayout(interval_row)

        self._auto_reconnect = QCheckBox(tr("settings.auto_reconnect"))
        self._auto_remount_on_lost = QCheckBox(tr("settings.auto_remount"))
        layout.addWidget(self._auto_reconnect)
        layout.addWidget(self._auto_remount_on_lost)
        layout.addWidget(self._divider())

        # ── SSH TERMINAL ─────────────────────────────────────────────
        layout.addWidget(self._section(tr("settings.section.terminal")))

        self._use_putty = QCheckBox(tr("settings.use_putty"))
        self._use_putty.toggled.connect(self._on_putty_toggled)
        layout.addWidget(self._use_putty)

        self._putty_path_widget = QWidget()
        putty_layout = QVBoxLayout(self._putty_path_widget)
        putty_layout.setContentsMargins(0, 6, 0, 0)
        putty_layout.setSpacing(4)
        putty_layout.addWidget(self._field_label(tr("settings.putty_path")))

        putty_row = QHBoxLayout()
        putty_row.setContentsMargins(0, 0, 0, 0)
        putty_row.setSpacing(6)
        self._putty_path_edit = QLineEdit()
        self._putty_path_edit.setPlaceholderText(r"C:\Program Files\PuTTY\putty.exe")
        putty_row.addWidget(self._putty_path_edit, stretch=1)
        browse_btn = QPushButton("…")
        browse_btn.setFixedWidth(36)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_putty)
        putty_row.addWidget(browse_btn)
        putty_layout.addLayout(putty_row)

        hint = QLabel(tr("settings.putty_hint"))
        hint.setObjectName("fieldLabel")
        hint.setWordWrap(True)
        putty_layout.addWidget(hint)

        self._putty_path_widget.setVisible(False)
        layout.addWidget(self._putty_path_widget)
        layout.addWidget(self._divider())

        # ── DEVELOPER ────────────────────────────────────────────────
        layout.addWidget(self._section(tr("settings.section.developer")))
        self._debug_mode = QCheckBox(tr("settings.debug_mode"))
        self._debug_mode.toggled.connect(self._on_debug_toggled)
        layout.addWidget(self._debug_mode)
        layout.addSpacing(4)

        # ── TOOLS & RECOVERY ───────────────────────
        self._tools_widget = QWidget()
        tools_layout = QVBoxLayout(self._tools_widget)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(8)
        tools_layout.addWidget(self._divider())
        tools_layout.addWidget(self._section(tr("settings.section.tools")))

        self._fix_ghosts_btn = QPushButton(tr("settings.fix_ghosts"))
        self._fix_ghosts_btn.setObjectName("actionBtn")
        self._fix_ghosts_btn.setMinimumHeight(36)
        self._fix_ghosts_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fix_ghosts_btn.setProperty("btn_type", "primary")
        self._fix_ghosts_btn.clicked.connect(self._on_fix_ghosts)
        tools_layout.addWidget(self._fix_ghosts_btn)

        self._restart_explorer_btn = QPushButton(tr("settings.restart_explorer"))
        self._restart_explorer_btn.setObjectName("actionBtn")
        self._restart_explorer_btn.setMinimumHeight(36)
        self._restart_explorer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._restart_explorer_btn.clicked.connect(self._on_restart_explorer)
        tools_layout.addWidget(self._restart_explorer_btn)

        self._tools_widget.setVisible(False)
        layout.addWidget(self._tools_widget)
        layout.addStretch()

        # ── Buttons ──────────
        btn_bar = QWidget()
        btn_bar_layout = QVBoxLayout(btn_bar)
        btn_bar_layout.setContentsMargins(24, 8, 24, 16)
        btn_bar_layout.setSpacing(8)
        btn_bar_layout.addWidget(self._divider())

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addWidget(make_maximize_button(self))
        btn_row.addStretch()
        cancel_btn = QPushButton(tr("dialog.cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton(tr("dialog.save"))
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        btn_bar_layout.addLayout(btn_row)

        self.layout().addWidget(btn_bar)

    def _load_settings(self):
        s = self._settings
        self._start_with_windows.setChecked(s.start_with_windows)
        self._minimize_to_tray.setChecked(s.minimize_to_tray)
        self._require_admin.setChecked(s.require_admin)
        self._interval_spin.setValue(s.check_interval_seconds)
        self._auto_reconnect.setChecked(s.auto_reconnect)
        self._auto_remount_on_lost.setChecked(s.auto_remount_on_lost)
        self._debug_mode.setChecked(s.debug_mode)
        self._use_putty.setChecked(getattr(s, 'use_putty', False))
        self._putty_path_edit.setText(getattr(s, 'putty_path', r"C:\Program Files\PuTTY\putty.exe"))
        self._putty_path_widget.setVisible(getattr(s, 'use_putty', False))
        self._tools_widget.setVisible(s.debug_mode)
        # Language
        lang = getattr(s, 'language', 'en') or 'en'
        idx = self._lang_combo.findData(lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)

    def _on_putty_toggled(self, checked: bool):
        self._putty_path_widget.setVisible(checked)
        self.adjustSize()

    def _on_debug_toggled(self, checked: bool):
        self._tools_widget.setVisible(checked)
        self.adjustSize()

    def _browse_putty(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("settings.select_putty"),
            r"C:\Program Files\PuTTY",
            "Executables (*.exe)"
        )
        if path:
            self._putty_path_edit.setText(path)

    def _on_fix_ghosts(self):
        controller = SSHFSController()
        ok = controller.purge_all_stale_mounts()
        if ok:
            QMessageBox.information(self, tr("dialog.success"), tr("settings.ghosts_ok"))
            SSHFSController.restart_explorer()
        else:
            QMessageBox.warning(self, tr("dialog.error"), tr("settings.ghosts_failed"))

    def _on_restart_explorer(self):
        SSHFSController.restart_explorer()
        QMessageBox.information(self, "Explorer", tr("settings.explorer_restarted"))

    def _on_save(self):
        if self._use_putty.isChecked():
            import os
            path = self._putty_path_edit.text().strip()
            if not path:
                QMessageBox.warning(self, "PuTTY", tr("settings.putty_missing"))
                return
            if not os.path.exists(path):
                reply = QMessageBox.question(
                    self, tr("settings.putty_not_found_title"),
                    tr("settings.putty_not_found", path=path),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
        self.accept()

    def get_settings(self) -> AppSettings:
        s = AppSettings(
            start_with_windows=self._start_with_windows.isChecked(),
            minimize_to_tray=self._minimize_to_tray.isChecked(),
            require_admin=self._require_admin.isChecked(),
            check_interval_seconds=self._interval_spin.value(),
            auto_reconnect=self._auto_reconnect.isChecked(),
            auto_remount_on_lost=self._auto_remount_on_lost.isChecked(),
            debug_mode=self._debug_mode.isChecked(),
            use_putty=self._use_putty.isChecked(),
            putty_path=self._putty_path_edit.text().strip(),
            language=self._lang_combo.currentData() or "en",
        )
        self._apply_autostart(s.start_with_windows)
        return s

    @staticmethod
    def _apply_autostart(enabled: bool):
        try:
            import winreg, sys
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            app_name = "NeoSSHWinManager"
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{sys.executable}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            from src.app_logger import logger
            logger.warning(f"Autostart konnte nicht gesetzt werden: {e}")
