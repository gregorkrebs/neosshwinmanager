from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
from PyQt6.QtCore import Qt
from src.ui.dialog_utils import match_parent_height
from src.i18n import tr

class TelemetryPromptDialog(QDialog):
    """
    Zeigt den Opt-In Dialog für die Telemetrie "Volkszählung" beim ersten Start.
    Gibt Accepted (Erlaubt) oder Rejected (Abgelehnt) zurück.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dialogSurface")
        self.setWindowTitle("Software verbessern?")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._build_ui()
        match_parent_height(self, parent)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("dialogHeroCard")
        hero_l = QVBoxLayout(hero)
        hero_l.setContentsMargins(22, 20, 22, 20)
        hero_l.setSpacing(8)

        title = QLabel("Helfen Sie uns, NEO SSH-Win Manager zu verbessern")
        title.setObjectName("dialogTitle")
        hero_l.addWidget(title)

        lead = QLabel("Wir würden uns sehr freuen, wenn Sie an unserer kleinen 'Volkszählung' teilnehmen würden.\n\n"
                      "Was bedeutet das?\n"
                      "Die Anwendung sendet lediglich beim ersten Start und bei der Anmeldung "
                      "einen anonymen Zähler hoch («+1 Installation», «+1 Login»).\n\n"
                      "Warum das gut ist:\n"
                      "Es werden keinerlei persönliche oder sensible Daten (weder Benutzernamen noch IP-Adressen) gesammelt! "
                      "Es hilft uns aber enorm zu sehen, ob das Projekt überhaupt genutzt wird und motiviert unser kleines Team,\n"
                      "weiterhin kostenlose Updates bereitzustellen.\n\n"
                      "Sie können diese Entscheidung jederzeit in den Einstellungen ändern.")
        lead.setObjectName("dialogLead")
        lead.setWordWrap(True)
        hero_l.addWidget(lead)
        outer.addWidget(hero)

        outer.addStretch()

        # Buttons
        btn_bar = QWidget() if globals().get('QWidget') else None # Workaround for missing QWidget import if any
        if not btn_bar:
            from PyQt6.QtWidgets import QWidget
            btn_bar = QWidget()
            
        btn_bar.setObjectName("dialogBtnBar")
        btn_bar_layout = QHBoxLayout(btn_bar)
        btn_bar_layout.setContentsMargins(0, 10, 0, 0)
        btn_bar_layout.setSpacing(10)

        decline_btn = QPushButton("Nein, danke")
        decline_btn.setObjectName("secondaryBtn")
        decline_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        decline_btn.clicked.connect(self.reject)
        
        accept_btn = QPushButton("Ja, Volkszählung aktivieren")
        accept_btn.setObjectName("primaryBtn")
        accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        accept_btn.clicked.connect(self.accept)

        btn_bar_layout.addStretch()
        btn_bar_layout.addWidget(decline_btn)
        btn_bar_layout.addWidget(accept_btn)
        
        outer.addWidget(btn_bar)
