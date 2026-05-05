"""
add_edit_dialog.py – Dialog for adding or editing SSH connections.

Features:
  - Template-Dropdown: bestehende Verbindungen als Vorlage laden
    (alle Daten werden übernommen, Laufwerksbuchstabe wird automatisch
     auf den nächsten verfügbaren gesetzt, Name wird geleert)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QFrame, QFileDialog,
    QWidget, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QScreen
from PyQt6.QtWidgets import QApplication
from typing import List, Optional
import secrets

from src.config import Connection
from src.drive_utils import get_available_drives
from src.ui.dialog_utils import match_parent_height, make_maximize_button
from src.i18n import tr


class AddEditDialog(QDialog):

    def __init__(
        self,
        parent=None,
        connection: Connection = None,
        used_letters: List[str] = None,
        existing_connections: List[Connection] = None,
    ):
        super().__init__(parent)
        self._connection = connection          # None = Add-Modus
        self._used_letters = used_letters or []
        self._existing = existing_connections or []
        self._is_edit = connection is not None

        self.setObjectName("dialogSurface")
        self.setWindowTitle(tr("addedit.edit_title") if self._is_edit else tr("addedit.add_title"))
        self.setMinimumWidth(520)
        self.setMaximumWidth(680)
        self.setModal(True)
        self._build_ui()
        if self._is_edit:
            self._load_connection(connection)
        # Max-Höhe = Bildschirm, Start-Höhe = volle Hauptfenster-Höhe (scrollbar bei Overflow).
        screen = QApplication.primaryScreen()
        if screen:
            max_h = int(screen.availableGeometry().height() * 0.95)
            self.setMaximumHeight(max_h)
        match_parent_height(self, parent)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

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
        # Äußeres Layout: Scroll-Area + fixe Button-Zeile
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
        layout.setContentsMargins(20, 20, 20, 12)
        layout.setSpacing(14)

        # Titel
        title_text = tr("addedit.edit_title") if self._is_edit else tr("addedit.add_title")
        hero = QFrame()
        hero.setObjectName("dialogHeroCard")
        hero_l = QVBoxLayout(hero)
        hero_l.setContentsMargins(22, 20, 22, 20)
        hero_l.setSpacing(8)

        title = QLabel(title_text)
        title.setObjectName("dialogTitle")
        hero_l.addWidget(title)

        lead = QLabel(tr("dialog.lead.addedit.edit") if self._is_edit else tr("dialog.lead.addedit.add"))
        lead.setObjectName("dialogLead")
        lead.setWordWrap(True)
        hero_l.addWidget(lead)
        layout.addWidget(hero)

        form_card = QFrame()
        form_card.setObjectName("dialogSectionCard")
        form = QVBoxLayout(form_card)
        form.setContentsMargins(22, 20, 22, 20)
        form.setSpacing(8)

        # ── Template (nur im Add-Modus) ───────────────────────────────
        if not self._is_edit and self._existing:
            form.addWidget(self._section(tr("addedit.section.template")))

            template_row = QHBoxLayout()
            template_row.setContentsMargins(0, 0, 0, 0)
            template_row.setSpacing(8)

            self._template_combo = QComboBox()
            self._template_combo.addItem(tr("addedit.template.none"), userData=None)
            for conn in self._existing:
                self._template_combo.addItem(
                    f"{conn.name}  ({conn.host})",
                    userData=conn
                )
            self._template_combo.currentIndexChanged.connect(self._on_template_selected)
            template_row.addWidget(self._template_combo, stretch=1)

            form.addLayout(template_row)

            hint = QLabel(tr("addedit.template.hint"))
            hint.setObjectName("fieldLabel")
            hint.setWordWrap(True)
            form.addWidget(hint)
            form.addWidget(self._divider())

        # ── GENERAL ──────────────────────────────────────────────────
        form.addWidget(self._section(tr("addedit.section.general")))

        form.addWidget(self._field_label(tr("addedit.label.name")))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText(tr("addedit.placeholder.name"))
        form.addWidget(self._name_edit)

        form.addWidget(self._field_label(tr("addedit.label.host")))
        self._host_edit = QLineEdit()
        self._host_edit.setPlaceholderText("192.168.1.1 or server.example.com")
        form.addWidget(self._host_edit)

        host_row = QHBoxLayout()
        host_row.setContentsMargins(0, 0, 0, 0)
        host_row.setSpacing(12)

        user_col = QVBoxLayout()
        user_col.setSpacing(4)
        user_col.addWidget(self._field_label(tr("addedit.label.user")))
        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText("root")
        user_col.addWidget(self._user_edit)
        host_row.addLayout(user_col, stretch=2)

        port_col = QVBoxLayout()
        port_col.setSpacing(4)
        port_col.addWidget(self._field_label(tr("addedit.label.port")))
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(22)
        port_col.addWidget(self._port_spin)
        host_row.addLayout(port_col, stretch=1)

        form.addLayout(host_row)

        # ── PATH & DRIVE ─────────────────────────────────────────────
        form.addWidget(self._divider())
        form.addWidget(self._section(tr("addedit.section.path")))

        form.addWidget(self._field_label(tr("addedit.label.path")))
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("/home/user  or  /")
        self._path_edit.setText("/")
        form.addWidget(self._path_edit)

        form.addWidget(self._field_label(tr("addedit.label.drive")))
        self._drive_combo = QComboBox()
        self._populate_drive_combo()
        form.addWidget(self._drive_combo)

        # ── AUTHENTICATION ───────────────────────────────────────────
        form.addWidget(self._divider())
        form.addWidget(self._section(tr("addedit.section.auth")))

        form.addWidget(self._field_label(tr("addedit.label.method")))
        self._auth_combo = QComboBox()
        self._auth_combo.addItem(tr("addedit.auth.password"), "password")
        self._auth_combo.addItem(tr("addedit.auth.key"), "key")
        self._auth_combo.addItem(tr("addedit.auth.ask"), "ask")
        form.addWidget(self._auth_combo)

        # Passwort-Zeile (immer sichtbar)
        pw_layout = QVBoxLayout()
        pw_layout.setContentsMargins(0, 4, 0, 0)
        pw_layout.setSpacing(4)
        pw_layout.addWidget(self._field_label(tr("addedit.label.password")))
        self._pw_edit = QLineEdit()
        self._pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_edit.setPlaceholderText("••••••••")
        pw_layout.addWidget(self._pw_edit)
        form.addLayout(pw_layout)

        # Key-Zeile (immer sichtbar)
        key_layout = QVBoxLayout()
        key_layout.setContentsMargins(0, 4, 0, 0)
        key_layout.setSpacing(4)
        key_layout.addWidget(self._field_label(tr("addedit.label.key")))
        key_row = QHBoxLayout()
        key_row.setContentsMargins(0, 0, 0, 0)
        key_row.setSpacing(6)
        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText("C:/Users/user/.ssh/id_rsa")
        key_row.addWidget(self._key_edit, stretch=1)
        browse_btn = QPushButton("…")
        browse_btn.setObjectName("rpHeaderBtn")
        browse_btn.setFixedWidth(36)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_key)
        key_row.addWidget(browse_btn)
        key_layout.addLayout(key_row)
        form.addLayout(key_layout)

        # ── CLI ACCESS ───────────────────────────────────────────────
        form.addWidget(self._divider())
        form.addWidget(self._section(tr("addedit.section.cli")))

        self._cli_enabled_cb = QCheckBox(tr("addedit.cli.enable"))
        self._cli_enabled_cb.stateChanged.connect(self._on_cli_toggle)
        form.addWidget(self._cli_enabled_cb)

        self._cli_key_widget = QWidget()
        cli_key_layout = QVBoxLayout(self._cli_key_widget)
        cli_key_layout.setContentsMargins(0, 4, 0, 0)
        cli_key_layout.setSpacing(4)
        
        cli_key_layout.addWidget(self._field_label(tr("addedit.cli.label")))
        
        key_display_row = QHBoxLayout()
        key_display_row.setSpacing(6)
        
        self._cli_key_edit = QLineEdit()
        self._cli_key_edit.setReadOnly(True)
        self._cli_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._cli_key_edit.setPlaceholderText(tr("addedit.cli.none"))
        key_display_row.addWidget(self._cli_key_edit, stretch=1)
        
        self._cli_show_btn = QPushButton("👁")
        self._cli_show_btn.setObjectName("rpHeaderBtn")
        self._cli_show_btn.setFixedWidth(36)
        self._cli_show_btn.setCheckable(True)
        self._cli_show_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cli_show_btn.clicked.connect(self._toggle_cli_key_visibility)
        key_display_row.addWidget(self._cli_show_btn)
        
        self._cli_gen_btn = QPushButton(tr("addedit.cli.generate"))
        self._cli_gen_btn.setObjectName("actionBtn")
        self._cli_gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cli_gen_btn.clicked.connect(self._generate_new_cli_key)
        key_display_row.addWidget(self._cli_gen_btn)
        
        cli_key_layout.addLayout(key_display_row)
        
        self._cli_key_widget.setVisible(False)
        form.addWidget(self._cli_key_widget)

        form.addStretch()
        layout.addWidget(form_card)

        # ── Button-Leiste (außerhalb der ScrollArea, immer sichtbar) ─
        btn_frame = QWidget()
        btn_frame.setObjectName("dialogBtnBar")
        btn_outer = QVBoxLayout(btn_frame)
        btn_outer.setContentsMargins(20, 8, 20, 16)
        btn_outer.setSpacing(0)

        divider2 = self._divider()
        btn_outer.addWidget(divider2)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.setContentsMargins(0, 10, 0, 0)
        btn_row.addWidget(make_maximize_button(self))
        btn_row.addStretch()

        cancel_btn = QPushButton(tr("dialog.cancel"))
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedHeight(36)
        cancel_btn.setMinimumWidth(110)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton(tr("dialog.save"))
        save_btn.setObjectName("primaryBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setFixedHeight(36)
        save_btn.setMinimumWidth(140)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        btn_outer.addLayout(btn_row)
        outer.addWidget(btn_frame)

    # ------------------------------------------------------------------
    # Drive combo
    # ------------------------------------------------------------------

    def _populate_drive_combo(self, preselect: str = None):
        """Fülle den Laufwerksbuchstaben-Combo mit verfügbaren Buchstaben."""
        self._drive_combo.clear()
        available = get_available_drives(exclude=self._used_letters)

        # Falls beim Bearbeiten der aktuelle Buchstabe nicht in der Liste ist
        if self._connection:
            curr = self._connection.drive_letter.upper().rstrip("\\") + ":"
            if curr not in available:
                available.insert(0, curr)

        for letter in sorted(available):
            self._drive_combo.addItem(letter, letter)

        # Vorauswahl
        if preselect:
            idx = self._drive_combo.findData(preselect)
            if idx >= 0:
                self._drive_combo.setCurrentIndex(idx)
        elif self._connection:
            idx = self._drive_combo.findData(self._connection.drive_letter)
            if idx >= 0:
                self._drive_combo.setCurrentIndex(idx)

    def _next_available_letter(self) -> str | None:
        """Ersten verfügbaren Laufwerksbuchstaben zurückgeben."""
        available = get_available_drives(exclude=self._used_letters)
        return available[0] if available else None

    # ------------------------------------------------------------------
    # Template
    # ------------------------------------------------------------------

    def _on_template_selected(self, index: int):
        """Verbindung als Vorlage laden, neuen Laufwerksbuchstaben zuweisen."""
        conn: Connection | None = self._template_combo.itemData(index)
        if conn is None:
            # "Keine Vorlage" → leeren
            self._name_edit.clear()
            self._host_edit.clear()
            self._user_edit.clear()
            self._port_spin.setValue(22)
            self._path_edit.setText("/")
            self._pw_edit.clear()
            self._key_edit.clear()
            self._populate_drive_combo()
            return

        # Alle Felder aus der Vorlage übernehmen
        self._host_edit.setText(conn.host)
        self._user_edit.setText(conn.user)
        self._port_spin.setValue(conn.port)
        self._path_edit.setText(conn.remote_path)
        self._pw_edit.setText(conn.password)
        self._key_edit.setText(conn.key_path)

        # Auth-Methode setzen
        idx = self._auth_combo.findData(conn.auth_method)
        if idx >= 0:
            self._auth_combo.setCurrentIndex(idx)

        # Name leer lassen damit der User einen neuen eingibt
        self._name_edit.clear()
        self._name_edit.setPlaceholderText(tr("addedit.placeholder.copy", name=conn.name))
        self._name_edit.setFocus()

        # Nächsten freien Laufwerksbuchstaben automatisch wählen
        next_letter = self._next_available_letter()
        self._populate_drive_combo(preselect=next_letter)

    # ------------------------------------------------------------------
    # Auth toggle
    # ------------------------------------------------------------------

    def _on_auth_changed(self, index: int):
        pass  # Both fields are always visible

    def _browse_key(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("addedit.select_key"), "", "All Files (*)"
        )
        if path:
            self._key_edit.setText(path)

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load_connection(self, conn: Connection):
        self._name_edit.setText(conn.name)
        self._host_edit.setText(conn.host)
        self._user_edit.setText(conn.user)
        self._port_spin.setValue(conn.port)
        self._path_edit.setText(conn.remote_path)

        idx = self._auth_combo.findData(conn.auth_method)
        if idx >= 0:
            self._auth_combo.setCurrentIndex(idx)

        self._pw_edit.setText(conn.password)
        self._key_edit.setText(conn.key_path)
        
        self._cli_enabled_cb.setChecked(conn.cli_access_enabled)
        self._cli_key_edit.setText(conn.cli_access_key or "")
        self._cli_key_widget.setVisible(conn.cli_access_enabled)
        
        self._populate_drive_combo()

    def _on_cli_toggle(self, state: int):
        enabled = (state == Qt.CheckState.Checked.value)
        self._cli_key_widget.setVisible(enabled)
        if enabled and not self._cli_key_edit.text():
            self._generate_new_cli_key()
        elif not enabled:
            self._cli_key_edit.clear()
        self.adjustSize()

    def _generate_new_cli_key(self):
        new_key = secrets.token_hex(64) # 128 characters
        self._cli_key_edit.setText(new_key)

    def _toggle_cli_key_visibility(self, visible: bool):
        mode = QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        self._cli_key_edit.setEchoMode(mode)
        self._cli_show_btn.setText("🔒" if visible else "👁")

    def _on_save(self):
        name = self._name_edit.text().strip()
        host = self._host_edit.text().strip()
        user = self._user_edit.text().strip()

        errors = []
        if not name:
            errors.append(tr("addedit.required.name"))
        if not host:
            errors.append(tr("addedit.required.host"))
        if not user:
            errors.append(tr("addedit.required.user"))

        if errors:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, tr("addedit.required.title"), "\n".join(errors))
            return

        self.accept()

    def get_connection(self) -> Connection:
        auth_method = self._auth_combo.currentData()
        drive = self._drive_combo.currentData() or "Z:"

        conn = Connection(
            name=self._name_edit.text().strip(),
            host=self._host_edit.text().strip(),
            user=self._user_edit.text().strip(),
            remote_path=self._path_edit.text().strip() or "/",
            port=self._port_spin.value(),
            auth_method=auth_method,
            password=self._pw_edit.text(),
            key_path=self._key_edit.text().strip(),
            drive_letter=drive,
            cli_access_enabled=self._cli_enabled_cb.isChecked(),
            cli_access_key=self._cli_key_edit.text() if self._cli_enabled_cb.isChecked() else None
        )

        # Bei Bearbeitung: ID beibehalten
        if self._connection:
            conn.id = self._connection.id

        return conn
