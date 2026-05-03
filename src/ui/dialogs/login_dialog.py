"""
login_dialog.py – Login-Dialog für NEO SSH-Win Manager.

Zeigt beim ersten Start ein Registrierungsformular.
Bei weiteren Starts einen Login-Dialog.
Admins können weitere Benutzer anlegen.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox, QMessageBox, QTabWidget, QWidget,
    QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon
import os

from src.auth_manager import AuthManager, Session
from src.crypto import is_available
from src.ui.dialog_utils import match_parent_height, make_maximize_button
from src.ui.icons import icon as svg_icon
from src.i18n import tr

class LoginDialog(QDialog):
    """
    Wird beim App-Start angezeigt.
    - Erster Start: Registrierungsformular
    - Weitere Starts: Login
    - Admin-Tab zum Anlegen weiterer Benutzer
    """

    login_successful = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("login.title"))
        self.setMinimumWidth(380)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        for icon_file in ("app_icon.ico", "app_icon.png"):
            icon_path = self._resource_path(os.path.join("assets", icon_file))
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break

        self._first_run = not AuthManager.has_any_users()
        self._build_ui()

    @staticmethod
    def _resource_path(relative_path: str) -> str:
        import sys
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            relative_path
        )

    def _divider(self) -> QFrame:
        f = QFrame()
        f.setObjectName("divider")
        f.setFixedHeight(1)
        return f

    def _input(self, placeholder="", password=False) -> QLineEdit:
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        if password:
            w.setEchoMode(QLineEdit.EchoMode.Password)
        return w

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        # Header
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setObjectName("dialogIconLarge")
        try:
            icon_path = self._resource_path(os.path.join("assets", "app_icon.png"))
            if os.path.exists(icon_path):
                from PyQt6.QtGui import QPixmap
                pm = QPixmap(icon_path).scaled(
                    64, 64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                icon_lbl.setPixmap(pm)
            else:
                icon_lbl.setText("🔐")
        except Exception:
            icon_lbl.setText("🔐")
        layout.addWidget(icon_lbl)

        title = QLabel("NEO SSH-Win Manager")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(self._divider())

        if self._first_run:
            self._build_register_form(layout)
        else:
            self._build_login_form(layout)

    def _build_login_form(self, layout: QVBoxLayout):
        sub = QLabel(tr("login.please_sign_in"))
        sub.setObjectName("fieldLabel")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(4)

        lbl_user = QLabel(tr("login.username"))
        lbl_user.setObjectName("fieldLabel")
        layout.addWidget(lbl_user)
        self._login_user = self._input(tr("login.username"))
        layout.addWidget(self._login_user)

        lbl_pw = QLabel(tr("login.password"))
        lbl_pw.setObjectName("fieldLabel")
        layout.addWidget(lbl_pw)
        self._login_pw = self._input(tr("login.password"), password=True)
        self._login_pw.returnPressed.connect(self._do_login)
        layout.addWidget(self._login_pw)

        self._login_error = QLabel("")
        self._login_error.setObjectName("errorLabel")
        self._login_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._login_error.setVisible(False)
        layout.addWidget(self._login_error)

        layout.addSpacing(4)
        layout.addWidget(self._divider())

        btn = QPushButton(tr("login.sign_in"))
        btn.setObjectName("primaryBtn")
        btn.setMinimumHeight(40)
        btn.clicked.connect(self._do_login)
        layout.addWidget(btn)

        self._login_user.setFocus()

    def _build_register_form(self, layout: QVBoxLayout):
        sub = QLabel(tr("login.create_first"))
        sub.setObjectName("fieldLabel")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(4)

        for attr, lbl, ph, pw in [
            ("_reg_user", tr("login.username"), tr("login.username"), False),
            ("_reg_pw",   tr("login.password"), tr("login.pw_min"), True),
            ("_reg_pw2",  tr("login.pw_confirm"), tr("login.pw_repeat"), True),
        ]:
            label = QLabel(lbl)
            label.setObjectName("fieldLabel")
            layout.addWidget(label)
            field = self._input(ph, pw)
            setattr(self, attr, field)
            layout.addWidget(field)

        self._reg_error = QLabel("")
        self._reg_error.setObjectName("errorLabel")
        self._reg_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._reg_error.setVisible(False)
        layout.addWidget(self._reg_error)

        layout.addSpacing(4)
        layout.addWidget(self._divider())

        btn = QPushButton(tr("login.create_account"))
        btn.setObjectName("primaryBtn")
        btn.setMinimumHeight(40)
        btn.clicked.connect(self._do_register)
        layout.addWidget(btn)

        self._reg_user.setFocus()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _do_login(self):
        username = self._login_user.text().strip()
        password = self._login_pw.text()

        if not username or not password:
            self._show_login_error(tr("login.fill_all"))
            return

        user = AuthManager.authenticate(username, password)
        if user is None:
            self._show_login_error(tr("login.invalid"))
            self._login_pw.clear()
            self._login_pw.setFocus()
            return

        Session.login(user)
        self.accept()

    def _do_register(self):
        username = self._reg_user.text().strip()
        pw = self._reg_pw.text()
        pw2 = self._reg_pw2.text()

        if not username:
            self._show_reg_error(tr("login.enter_username"))
            return
        if len(username) < 3:
            self._show_reg_error(tr("login.username_min"))
            return
        if len(pw) < 6:
            self._show_reg_error(tr("login.password_min"))
            return
        if pw != pw2:
            self._show_reg_error(tr("login.passwords_differ"))
            self._reg_pw2.clear()
            self._reg_pw2.setFocus()
            return

        if not is_available():
            QMessageBox.critical(self, tr("dialog.error"), tr("login.no_crypto"))
            return

        try:
            user = AuthManager.register(username, pw, is_admin=True)
            Session.login(user)
            self.accept()
        except Exception as e:
            self._show_reg_error(str(e))

    def _show_login_error(self, msg: str):
        self._login_error.setText(f"⚠ {msg}")
        self._login_error.setVisible(True)

    def _show_reg_error(self, msg: str):
        self._reg_error.setText(f"⚠ {msg}")
        self._reg_error.setVisible(True)

    def closeEvent(self, event):
        # Wenn nicht eingeloggt → App beenden
        if not Session.is_logged_in():
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()
        super().closeEvent(event)


class UserManagementDialog(QDialog):
    """Admin-Dialog zum Verwalten von Benutzern."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("users.title"))
        self.setMinimumWidth(440)
        self.setMinimumHeight(400)
        self.setModal(True)
        self._build_ui()
        self._refresh_users()
        # Max-Höhe = Bildschirm, Start-Höhe = volle Hauptfenster-Höhe (scrollbar bei Overflow).
        screen = QApplication.primaryScreen()
        if screen:
            self.setMaximumHeight(int(screen.availableGeometry().height() * 0.95))
        match_parent_height(self, parent)

    def _divider(self) -> QFrame:
        f = QFrame()
        f.setObjectName("divider")
        f.setFixedHeight(1)
        return f

    def _input(self, placeholder="", password=False) -> QLineEdit:
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        if password:
            w.setEchoMode(QLineEdit.EchoMode.Password)
        return w

    def _build_ui(self):
        # Äußeres Layout: scrollbarer Content oben, fixe Button-Leiste unten.
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

        title = QLabel(tr("users.title"))
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        layout.addWidget(self._divider())

        # Benutzerliste
        list_lbl = QLabel(tr("users.section.users"))
        list_lbl.setObjectName("sectionLabel")
        layout.addWidget(list_lbl)

        self._users_layout = QVBoxLayout()
        self._users_layout.setSpacing(4)
        layout.addLayout(self._users_layout)

        layout.addWidget(self._divider())

        # Neuen Benutzer anlegen
        new_lbl = QLabel(tr("users.section.new"))
        new_lbl.setObjectName("sectionLabel")
        layout.addWidget(new_lbl)

        self._new_user = self._input(tr("users.placeholder.username"))
        layout.addWidget(self._new_user)

        self._new_pw = self._input(tr("users.placeholder.password"), password=True)
        layout.addWidget(self._new_pw)

        self._new_is_admin = QCheckBox(tr("users.admin"))
        layout.addWidget(self._new_is_admin)

        add_btn = QPushButton(tr("users.create"))
        add_btn.setObjectName("primaryBtn")
        add_btn.setMinimumHeight(36)
        add_btn.clicked.connect(self._add_user)
        layout.addWidget(add_btn)

        layout.addStretch()

        # Fixe Button-Leiste außerhalb der Scroll-Area.
        btn_bar = QWidget()
        btn_bar_layout = QVBoxLayout(btn_bar)
        btn_bar_layout.setContentsMargins(24, 8, 24, 16)
        btn_bar_layout.setSpacing(8)
        btn_bar_layout.addWidget(self._divider())

        close_row = QHBoxLayout()
        close_row.addWidget(make_maximize_button(self))
        close_row.addStretch()
        close_btn = QPushButton(tr("dialog.close"))
        close_btn.setMinimumHeight(36)
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        close_row.addStretch()
        _sp = QWidget(); _sp.setFixedWidth(32); close_row.addWidget(_sp)
        btn_bar_layout.addLayout(close_row)

        outer.addWidget(btn_bar)

    def _refresh_users(self):
        # Liste leeren
        while self._users_layout.count():
            item = self._users_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        current_id = Session.current().id if Session.current() else None
        users = AuthManager.list_users()

        for u in users:
            row = QWidget()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(8, 4, 8, 4)

            icon = "👑" if u["is_admin"] else "👤"
            name = u["username"]
            suffix = tr("users.you") if u["id"] == current_id else ""
            lbl = QLabel(f"{icon}  {name}{suffix}")
            lbl.setObjectName("connName")
            lbl.setProperty("state", "user_row")
            row_l.addWidget(lbl, stretch=1)

            if u["id"] == current_id:
                # Eigener Eintrag: Passwort-ändern-Button
                chg_btn = QPushButton()
                chg_btn.setFixedSize(32, 28)
                chg_btn.setIcon(svg_icon("key", "#aab4c4", 16))
                chg_btn.setIconSize(QSize(16, 16))
                chg_btn.setToolTip(tr("users.tooltip.change_pw"))
                chg_btn.clicked.connect(self._change_own_password)
                row_l.addWidget(chg_btn)
            else:
                # Admin-Aktionen für andere User
                if Session.is_admin():
                    reset_btn = QPushButton()
                    reset_btn.setFixedSize(32, 28)
                    reset_btn.setIcon(svg_icon("rotate-cw", "#aab4c4", 16))
                    reset_btn.setIconSize(QSize(16, 16))
                    reset_btn.setToolTip(tr("users.tooltip.reset_pw", name=name))
                    uid_r = u["id"]
                    reset_btn.clicked.connect(lambda _, i=uid_r, n=name: self._reset_user_password(i, n))
                    row_l.addWidget(reset_btn)

                del_btn = QPushButton()
                del_btn.setFixedSize(32, 28)
                del_btn.setIcon(svg_icon("trash", "#ff6b7a", 16))
                del_btn.setIconSize(QSize(16, 16))
                del_btn.setToolTip(tr("users.tooltip.delete", name=name))
                del_btn.setProperty("btn_type", "danger")
                uid = u["id"]
                del_btn.clicked.connect(lambda _, i=uid, n=name: self._delete_user(i, n))
                row_l.addWidget(del_btn)

            row.setObjectName("userBox")
            self._users_layout.addWidget(row)

    def _add_user(self):
        username = self._new_user.text().strip()
        pw = self._new_pw.text()
        is_admin = self._new_is_admin.isChecked()

        if not username or len(username) < 3:
            QMessageBox.warning(self, tr("dialog.error"), tr("users.username_min"))
            return
        if len(pw) < 6:
            QMessageBox.warning(self, tr("dialog.error"), tr("users.password_min"))
            return

        try:
            AuthManager.register(username, pw, is_admin=is_admin)
            self._new_user.clear()
            self._new_pw.clear()
            self._new_is_admin.setChecked(False)
            self._refresh_users()
        except Exception as e:
            QMessageBox.critical(self, tr("dialog.error"), str(e))

    def _delete_user(self, user_id: str, username: str):
        reply = QMessageBox.question(
            self, tr("users.delete.title"),
            tr("users.delete.confirm", name=username),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            AuthManager.delete_user(user_id)
            self._refresh_users()

    def _reset_user_password(self, user_id: str, username: str):
        reply = QMessageBox.question(
            self, tr("users.reset.title"),
            tr("users.reset.confirm", name=username),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        new_pw = AuthManager.admin_reset_password(user_id)
        if not new_pw:
            QMessageBox.critical(self, tr("dialog.error"), tr("users.not_found"))
            return
        box = QMessageBox(self)
        box.setWindowTitle(tr("users.reset.new_title"))
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(tr("users.reset.new_msg", name=username, pw=new_pw))
        box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.exec()

    def _change_own_password(self):
        user = Session.current()
        if not user:
            return
        dlg = ChangePasswordDialog(user.id, self)
        dlg.exec()


class ChangePasswordDialog(QDialog):
    """Dialog für den User, um das eigene Passwort zu ändern."""

    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self.setWindowTitle(tr("chgpw.title"))
        self.setMinimumWidth(380)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(10)

        title = QLabel(tr("chgpw.title"))
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        self._old_pw = QLineEdit()
        self._old_pw.setPlaceholderText(tr("chgpw.current"))
        self._old_pw.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._old_pw)

        self._new_pw = QLineEdit()
        self._new_pw.setPlaceholderText(tr("chgpw.new"))
        self._new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._new_pw)

        self._confirm_pw = QLineEdit()
        self._confirm_pw.setPlaceholderText(tr("chgpw.confirm"))
        self._confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._confirm_pw)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton(tr("dialog.cancel"))
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        save = QPushButton(tr("dialog.save"))
        save.setObjectName("primaryBtn")
        save.clicked.connect(self._save)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _save(self):
        old_pw = self._old_pw.text()
        new_pw = self._new_pw.text()
        confirm = self._confirm_pw.text()
        if len(new_pw) < 6:
            QMessageBox.warning(self, tr("dialog.error"), tr("chgpw.new_min"))
            return
        if new_pw != confirm:
            QMessageBox.warning(self, tr("dialog.error"), tr("chgpw.mismatch"))
            return
        ok = AuthManager.change_password(self._user_id, old_pw, new_pw)
        if not ok:
            QMessageBox.critical(self, tr("dialog.error"), tr("chgpw.wrong_old"))
            return
        QMessageBox.information(self, tr("dialog.success"), tr("chgpw.success"))
        self.accept()
