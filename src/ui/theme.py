"""
theme.py – Global stylesheets for SSH Win Manager.
"""


def get_stylesheet(theme: str = "dark") -> str:
    """Return the stylesheet for the given theme ('dark' or 'light')."""
    if theme == "light":
        return LIGHT_STYLESHEET
    return STYLESHEET


STYLESHEET = """
/* ============================================================
   NEO SSH-Win Manager – Modern Cyber Theme (v2.0)
   ============================================================ */

/* ---- Global Bases ----------------------------------------- */
QWidget {
    background-color: #0d0d12;
    color: #c8d6e5;
    font-family: "Inter", "Segoe UI", sans-serif;
    font-size: 13px;
    border: none;
    outline: none;
}

QLabel, QCheckBox, QRadioButton, QGroupBox {
    background: transparent;
}

/* ---- Main Window ------------------------------------------ */
#MainWindow {
    background-color: #0d0d12;
}

/* ---- Sidebar / Left Panel --------------------------------- */
#sidePanel {
    background-color: #0a0a0f;
    border-right: 1px solid #1a1a2e;
}

/* ---- Scroll Area ------------------------------------------ */
#connectionScroll {
    background-color: transparent;
    border: none;
}

/* --- Dialog Elements --- */
#dialogTitle {
    color: #00b4d8;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 5px;
}

#dialogIconLarge {
    font-size: 36px;
    background: transparent;
    margin-bottom: 5px;
}

#sectionLabel {
    color: #58a6ff;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 10px;
}

#fieldLabel {
    color: #8b949e;
    font-size: 11px;
}

#errorLabel {
    color: #ef4444;
    font-size: 12px;
}

#mutedLabel {
    color: #6a7a8a;
    font-size: 12px;
}

#accentLabel {
    color: #00b4d8;
    font-size: 11px;
}

#secondaryTitle {
    color: #e4eaf0;
    font-size: 11px;
    font-weight: bold;
}

#divider {
    background-color: rgba(255, 255, 255, 0.05);
}

/* User Management Row */
#userBox {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
}

#userBox QLabel[state="user_row"] {
    color: #c8d6e5;
    font-size: 13px;
    background: transparent;
    border: none;
}

#connectionList {
    background-color: transparent;
}

QScrollBar:vertical {
    background: #0e0e1a;
    width: 8px;
    margin: 4px 0 4px 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #aab4c4;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #d0d8e4;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ---- Connection Card -------------------------------------- */
#connectionContainer {
    background: transparent;
    margin-bottom: 2px;
}

#connectionCard {
    background-color: #14141f;
    border: 1px solid #1e1e30;
    border-radius: 12px;
    margin: 6px 12px;
    padding: 2px;
}

#connectionCard:hover {
    background-color: #1a1a2e;
    border: 1px solid #2a2a4a;
}

/* Mounted State Properties */
#connectionCard[mounted="true"] {
    background-color: #121a22;
    border: 1px solid rgba(0, 180, 216, 0.4);
}

/* Selected State */
#connectionCard[selected="true"] {
    border: 1px solid #00b4d8;
    background-color: #16162a;
}

/* Expanded/Panel Open State */
#connectionCard[expanded="true"] {
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
    margin-bottom: 0px;
    border-bottom: none;
}

#connName {
    color: #e4eaf0;
    font-size: 14px;
    font-weight: 600;
}
#connDetail {
    color: #556070;
    font-size: 11px;
}

#cloudIcon {
    font-size: 22px;
    color: #2a3a4a;
}
#cloudIcon[mounted="true"] {
    color: #00b4d8;
}

#cloudIcon[state="large"] {
    font-size: 48px;
    padding: 8px;
}

#driveBadge {
    background-color: #1a1a2e;
    color: #00b4d8;
    font-size: 11px;
    font-weight: 700;
    border-radius: 6px;
    padding: 2px 8px;
    border: 1px solid #00b4d833;
}
#driveBadge[mounted="true"] {
    background-color: rgba(0, 212, 100, 0.1);
    color: #00d464;
    border: 1px solid #00d464;
}

/* ---- System Info Panel (Inside Card) ---------------------- */
#systemInfoPanel {
    background-color: #0f1218;
    border: 1px solid #1e1e30;
    border-top: none;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    margin: 0 12px 12px 12px;
    padding: 8px;
}

#sectionFrame {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 6px;
}

#sectionTitle {
    color: #58a6ff;
    font-size: 10px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

#infoLabel { color: #8b949e; font-size: 10px; }
#valueLabel { color: #e6edf3; font-size: 11px; font-weight: 500; }
#bigValue { color: #e6edf3; font-size: 15px; font-weight: bold; }

/* ---- Action Panel (Right) --------------------------------- */
#actionPanel {
    background-color: #0a0a0f;
    border-left: 1px solid #1a1a2e;
    min-width: 190px;
    max-width: 190px;
}

#divider {
    background-color: #1a1a2e;
    max-height: 1px;
    min-height: 1px;
    margin: 10px 4px;
}

/* ---- Global Action Buttons -------------------------------- */
#actionBtn, QPushButton#sshBtn, QPushButton#mountBtn {
    font-weight: 500;
}

/* Standard Secondary Action Button */
#actionBtn {
    background-color: #14141f;
    border: 1px solid #1e1e30;
    border-radius: 10px;
    color: #90a0b0;
    font-size: 12px;
    padding: 10px 14px;
    text-align: left;
}
#actionBtn:hover {
    background-color: #1a1a2e;
    border: 1px solid #2a2a4a;
    color: #c8d6e5;
}

/* Primary Brand Button (Add, etc) */
#actionBtn[btn_type="primary"], #primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0077b6, stop:1 #00b4d8);
    border: none;
    color: #fff;
    font-weight: 600;
    padding: 10px 14px;
    border-radius: 6px;
    min-height: 36px;
    text-align: left;
}
#actionBtn[btn_type="primary"]:hover, #primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0096c7, stop:1 #48cae4);
}

/* Dialog Button Bar */
#dialogBtnBar {
    background-color: #0d0d12;
    border-top: 1px solid #1a1a2e;
}

/* Danger Button */
#actionBtn[btn_type="danger"], #dangerBtn {
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #ef4444;
}
#actionBtn[btn_type="danger"]:hover, #dangerBtn:hover {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
}

/* Warning Button (Debug) */
#actionBtn[btn_type="warning"] {
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.2);
    color: #f59e0b;
}
#actionBtn[btn_type="warning"]:hover {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
}

/* SSH Circular/Small Button */
QPushButton#sshBtn {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    color: #00b4d8;
    border-radius: 8px;
    font-size: 11px;
}
QPushButton#sshBtn:hover {
    background: rgba(0, 180, 216, 0.12);
    border: 1px solid #00b4d8;
}

/* Card-internal Info/Edit Buttons */
QPushButton#cardInfoBtn, QPushButton#cardEditBtn {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    color: #aab4c4;
    border-radius: 8px;
    font-size: 14px;
}
QPushButton#cardInfoBtn:hover, QPushButton#cardEditBtn:hover {
    background: rgba(170, 180, 196, 0.12);
    border: 1px solid #aab4c4;
    color: #d0d8e4;
}
QPushButton#cardEditBtn:disabled {
    color: #3a3a4a;
    border: 1px solid #1e1e2e;
    background: #14141f;
}

/* Mount Toggle Circle */
QPushButton#mountBtn {
    background-color: #1a1a2e;
    border: 1px solid #3a4a6a;
    border-radius: 21px;
    color: #aab4c4;
    font-size: 18px;
}
QPushButton#mountBtn:hover {
    background-color: rgba(0, 180, 216, 0.12);
    border: 1px solid #00b4d8;
    color: #00b4d8;
}
QPushButton#mountBtn[mounted="true"] {
    background-color: rgba(0, 212, 100, 0.12);
    border: 1px solid #00d464;
    color: #00d464;
}
QPushButton#mountBtn[mounted="true"]:hover {
    background-color: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #ef4444;
}

/* ---- Inputs ----------------------------------------------- */
QLineEdit, QSpinBox, QComboBox {
    background-color: #14141f;
    border: 1px solid #1e1e30;
    border-radius: 8px;
    color: #c8d6e5;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #00b4d8;
    background-color: #16162a;
}
QLineEdit::placeholder {
    color: #3f4e5e;
}

QComboBox::drop-down { border: none; width: 30px; }
QComboBox::down-arrow {
    image: none; border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #556070;
    margin-right: 10px;
}

/* ---- Status Bar ------------------------------------------- */
#statusBar {
    background-color: #08080c;
    border-top: 1px solid #1a1a2e;
    color: #4a5a6a;
    font-size: 11px;
    padding: 4px 12px;
    min-height: 24px;
}
#statusDot { color: #00d464; font-size: 10px; margin-right: 4px; }

/* ---- Progress Bars ---------------------------------------- */
QProgressBar {
    background-color: #1a1a2e;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: transparent;
    height: 8px;
}
QProgressBar::chunk {
    background-color: #00b4d8;
    border-radius: 4px;
}

/* ---- Tabs ------------------------------------------------- */
QTabWidget::pane {
    border: 1px solid #1e1e30;
    border-radius: 10px;
    background: #0f0f1a;
    margin-top: -1px;
}
QTabBar::tab {
    background: transparent;
    border-bottom: 2px solid transparent;
    color: #556070;
    font-size: 12px;
    padding: 10px 20px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    color: #00b4d8;
    border-bottom: 2px solid #00b4d8;
    font-weight: 600;
}

/* ---- Dialogs ---------------------------------------------- */
QDialog {
    background-color: #0d0d12;
}

#dialogTitle {
    color: #e4eaf0;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 8px;
}

#sectionLabel {
    color: #00b4d8;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding-top: 12px;
}

#fieldLabel {
    color: #556070;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 2px;
}

/* ---- Tooltips / Messagebox -------------------------------- */
QToolTip {
    background-color: #1a1a2e;
    border: 1px solid #2a2a4a;
    color: #c8d6e5;
    border-radius: 6px;
    padding: 5px 10px;
}

QMessageBox {
    background-color: #0d0d12;
}
QMessageBox QPushButton {
    min-width: 90px;
}
"""

LIGHT_STYLESHEET = """
/* ============================================================
   NEO SSH-Win Manager – Light Theme
   ============================================================ */

QWidget {
    background-color: #f0f2f5;
    color: #1a2332;
    font-family: "Inter", "Segoe UI", sans-serif;
    font-size: 13px;
    border: none;
    outline: none;
}

QLabel, QCheckBox, QRadioButton, QGroupBox {
    background: transparent;
}

#MainWindow {
    background-color: #f0f2f5;
}

#sidePanel {
    background-color: #e4e8ef;
    border-right: 1px solid #c8d0dc;
}

#connectionScroll {
    background-color: transparent;
    border: none;
}

#dialogTitle {
    color: #0077b6;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 5px;
}

#sectionLabel {
    color: #0077b6;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 10px;
}

#fieldLabel {
    color: #4a5a6a;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 2px;
}

#errorLabel { color: #dc2626; font-size: 12px; }
#mutedLabel { color: #6a7a8a; font-size: 12px; }
#accentLabel { color: #0077b6; font-size: 11px; }
#secondaryTitle { color: #2a3a4a; font-size: 11px; font-weight: bold; }

#divider {
    background-color: rgba(0, 0, 0, 0.10);
    max-height: 1px;
    min-height: 1px;
    margin: 10px 4px;
}

#userBox {
    background: rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(0, 0, 0, 0.10);
    border-radius: 6px;
}

QScrollBar:vertical {
    background: #e0e4ea;
    width: 8px;
    margin: 4px 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #9aacbe;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #6a8aaa; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

#connectionCard {
    background-color: #ffffff;
    border: 1px solid #d0d8e4;
    border-radius: 12px;
    margin: 6px 12px;
    padding: 2px;
}
#connectionCard:hover {
    background-color: #eaf1fa;
    border: 1px solid #a8c0d8;
}
#connectionCard[mounted="true"] {
    background-color: #e8f5fc;
    border: 1px solid rgba(0, 119, 182, 0.5);
}
#connectionCard[selected="true"] {
    border: 1px solid #0077b6;
    background-color: #dceef8;
}
#connectionCard[expanded="true"] {
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
    margin-bottom: 0px;
    border-bottom: none;
}

#connName { color: #1a2332; font-size: 14px; font-weight: 600; }
#connDetail { color: #6a7a8a; font-size: 11px; }

#cloudIcon { font-size: 22px; color: #b0bac4; }
#cloudIcon[mounted="true"] { color: #0077b6; }
#cloudIcon[state="large"] { font-size: 48px; padding: 8px; }

#driveBadge {
    background-color: #dceef8;
    color: #0077b6;
    font-size: 11px;
    font-weight: 700;
    border-radius: 6px;
    padding: 2px 8px;
    border: 1px solid #a8d0ee;
}
#driveBadge[mounted="true"] {
    background-color: rgba(0, 180, 80, 0.12);
    color: #007a3d;
    border: 1px solid #007a3d;
}

#systemInfoPanel {
    background-color: #eef2f7;
    border: 1px solid #c8d0dc;
    border-top: none;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    margin: 0 12px 12px 12px;
    padding: 8px;
}

#sectionFrame {
    background-color: #ffffff;
    border: 1px solid #d0d8e4;
    border-radius: 8px;
    padding: 6px;
}

#sectionTitle { color: #0077b6; font-size: 10px; font-weight: bold; text-transform: uppercase; }
#infoLabel { color: #6a7a8a; font-size: 10px; }
#valueLabel { color: #1a2332; font-size: 11px; font-weight: 500; }
#bigValue { color: #1a2332; font-size: 15px; font-weight: bold; }

#actionPanel {
    background-color: #e4e8ef;
    border-left: 1px solid #c8d0dc;
    min-width: 190px;
    max-width: 190px;
}

#actionBtn {
    background-color: #ffffff;
    border: 1px solid #c8d0dc;
    border-radius: 10px;
    color: #4a5a6a;
    font-size: 12px;
    padding: 10px 14px;
    text-align: left;
}
#actionBtn:hover {
    background-color: #dceef8;
    border: 1px solid #0077b6;
    color: #1a2332;
}

#actionBtn[btn_type="primary"], #primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0077b6, stop:1 #00b4d8);
    border: none;
    color: #fff;
    font-weight: 600;
    padding: 10px 14px;
    border-radius: 6px;
    min-height: 36px;
    text-align: left;
}
#actionBtn[btn_type="primary"]:hover, #primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0096c7, stop:1 #48cae4);
}

#dialogBtnBar {
    background-color: #eef2f7;
    border-top: 1px solid #c8d0dc;
}

#actionBtn[btn_type="danger"], #dangerBtn {
    background: rgba(220, 38, 38, 0.08);
    border: 1px solid rgba(220, 38, 38, 0.3);
    color: #dc2626;
}
#actionBtn[btn_type="danger"]:hover, #dangerBtn:hover {
    background: rgba(220, 38, 38, 0.15);
    border: 1px solid #dc2626;
}

#actionBtn[btn_type="warning"] {
    background: rgba(217, 119, 6, 0.08);
    border: 1px solid rgba(217, 119, 6, 0.3);
    color: #d97706;
}
#actionBtn[btn_type="warning"]:hover {
    background: rgba(217, 119, 6, 0.15);
    border: 1px solid #d97706;
}

QPushButton#sshBtn {
    background: #dceef8;
    border: 1px solid #a8d0ee;
    color: #0077b6;
    border-radius: 8px;
    font-size: 11px;
}
QPushButton#sshBtn:hover {
    background: rgba(0, 119, 182, 0.15);
    border: 1px solid #0077b6;
}

QPushButton#cardInfoBtn, QPushButton#cardEditBtn {
    background: #eef2f7;
    border: 1px solid #c8d0dc;
    color: #4a5a6a;
    border-radius: 8px;
    font-size: 14px;
}
QPushButton#cardInfoBtn:hover, QPushButton#cardEditBtn:hover {
    background: rgba(0, 119, 182, 0.10);
    border: 1px solid #0077b6;
    color: #0077b6;
}
QPushButton#cardEditBtn:disabled {
    color: #b0bac4;
    border: 1px solid #d0d8e4;
    background: #f0f2f5;
}

QPushButton#mountBtn {
    background-color: #eef2f7;
    border: 1px solid #a8b8c8;
    border-radius: 21px;
    color: #4a5a6a;
    font-size: 18px;
}
QPushButton#mountBtn:hover {
    background-color: rgba(0, 119, 182, 0.10);
    border: 1px solid #0077b6;
    color: #0077b6;
}
QPushButton#mountBtn[mounted="true"] {
    background-color: rgba(0, 180, 80, 0.10);
    border: 1px solid #007a3d;
    color: #007a3d;
}
QPushButton#mountBtn[mounted="true"]:hover {
    background-color: rgba(220, 38, 38, 0.12);
    border: 1px solid #dc2626;
    color: #dc2626;
}

QLineEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1px solid #c8d0dc;
    border-radius: 8px;
    color: #1a2332;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #0077b6;
    background-color: #f5faff;
}
QLineEdit::placeholder { color: #9aacbe; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #6a7a8a;
    margin-right: 10px;
}

#statusBar {
    background-color: #e4e8ef;
    border-top: 1px solid #c8d0dc;
    color: #4a5a6a;
    font-size: 11px;
    padding: 4px 12px;
    min-height: 24px;
}
#statusDot { color: #007a3d; font-size: 10px; margin-right: 4px; }

QProgressBar {
    background-color: #dde2ea;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: transparent;
    height: 8px;
}
QProgressBar::chunk {
    background-color: #0077b6;
    border-radius: 4px;
}

QTabWidget::pane {
    border: 1px solid #c8d0dc;
    border-radius: 10px;
    background: #f8fafc;
    margin-top: -1px;
}
QTabBar::tab {
    background: transparent;
    border-bottom: 2px solid transparent;
    color: #6a7a8a;
    font-size: 12px;
    padding: 10px 20px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    color: #0077b6;
    border-bottom: 2px solid #0077b6;
    font-weight: 600;
}

QDialog { background-color: #f0f2f5; }

#dialogTitle {
    color: #1a2332;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 8px;
}

#sectionLabel {
    color: #0077b6;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding-top: 12px;
}

#fieldLabel {
    color: #4a5a6a;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 2px;
}

QToolTip {
    background-color: #ffffff;
    border: 1px solid #c8d0dc;
    color: #1a2332;
    border-radius: 6px;
    padding: 5px 10px;
}

QMessageBox { background-color: #f0f2f5; }
QMessageBox QPushButton { min-width: 90px; }
"""
