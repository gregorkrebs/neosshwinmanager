(function () {
  "use strict";

  const root = document.querySelector("[data-app-sim]");
  if (!root) return;

  const resetButton = document.querySelector("[data-app-sim-reset]");
  const DRIVE_POOL = Array.from({ length: 23 }, (_, index) => String.fromCharCode(68 + index) + ":");

  const ICONS = {
    cloud: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19a4.5 4.5 0 1 0-1.41-8.775 6 6 0 1 0-11.59 2.275A4 4 0 0 0 6 19h11.5z"/></svg>',
    users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    bug: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="6" width="8" height="14" rx="4"/><path d="M12 20v-8M8 10 5 7M16 10l3-3M8 14H4M20 14h-4M8 18l-3 3M16 18l3 3M9 6V4a3 3 0 0 1 6 0v2"/></svg>',
    settings: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 0 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3h.1a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8v.1a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z"/></svg>',
    logout: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>',
    terminal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
    key: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="7.5" cy="15.5" r="5.5"/><path d="M21 2l-9.6 9.6"/><path d="M15.5 7.5h4.5v4.5"/></svg>',
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>',
    edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
    trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>',
    close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    arrowRight: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',
    minus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/></svg>',
    refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15.55-6.36L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15.55 6.36L3 16"/></svg>',
    lock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
  };

  const COPY = {
    de: {
      "app.ready": "Bereit",
      "app.no_connections": "Keine Verbindungen",
      "header.connections": "Verbindungen",
      "badge.n_active": "{n} aktiv",
      "badge.n_mounted": "{n} verbunden",
      "main.add_connection": "Verbindung hinzufügen",
      "main.settings": "Einstellungen",
      "main.users": "Benutzer",
      "main.debug": "Debug",
      "main.delete": "Löschen",
      "main.logout": "Abmelden",
      "status.connecting": "Verbinde {name} → {drive}…",
      "status.disconnecting": "Trenne {drive}…",
      "status.connected": "✓ {name} verbunden als {drive}",
      "status.disconnected": "✓ {name} getrennt.",
      "status.connect_failed": "✗ Verbinden fehlgeschlagen: {name}",
      "status.connection_added": "Verbindung '{name}' hinzugefügt.",
      "status.connection_updated": "Verbindung '{name}' aktualisiert.",
      "status.connection_deleted": "Verbindung '{name}' gelöscht.",
      "status.user_created": "Benutzer '{name}' angelegt.",
      "status.user_deleted": "Benutzer '{name}' gelöscht.",
      "status.password_changed": "Passwort geändert.",
      "status.password_reset": "Passwort für '{name}' zurückgesetzt.",
      "status.settings_saved": "Einstellungen gespeichert.",
      "status.opening_explorer": "Öffne {path} im Explorer",
      "status.ssh_started": "{backend}-Terminal für '{name}' gestartet.",
      "dialog.cancel": "Abbrechen",
      "dialog.save": "Speichern",
      "dialog.close": "Schließen",
      "dialog.ok": "OK",
      "dialog.yes": "Ja",
      "dialog.no": "Nein",
      "dialog.error": "Fehler",
      "dialog.success": "Erfolg",
      "dialog.warning": "Warnung",
      "mount.failed.title": "Verbindung fehlgeschlagen",
      "mount.failed.main": "Die Verbindung zu '{name}' konnte nicht aufgebaut werden.",
      "mount.failed.troubleshoot": "\n\nBitte prüfe folgende Punkte:\n • Ist das Gerät im Netzwerk erreichbar? (IP: {host})\n • Sind die Zugangsdaten (Passwort/Key) korrekt?\n • Ist der SSH-Dienst auf dem Zielgerät aktiv?\n • Blockiert eine Firewall den Port {port}?",
      "mount.failed.details": "\n\nTechnische Details:\n{msg}",
      "mount.failed.retry": "Erneut versuchen",
      "delete.title": "Löschen",
      "delete.select_one": "Bitte eine Verbindung auswählen.",
      "delete.mounted_confirm": "'{name}' ist verbunden. Trennen und löschen?",
      "delete.confirm": "Verbindung '{name}' löschen?",
      "edit.locked.title": "Bearbeiten gesperrt",
      "edit.locked.msg": "Diese Verbindung ist aktuell gemountet und kann nicht bearbeitet werden.\nBitte zuerst trennen.",
      "logout.title": "Abmelden",
      "logout.confirm": "Wirklich abmelden?\nAlle aktiven Verbindungen werden getrennt.",
      "card.tooltip.info": "Systeminformationen anzeigen",
      "card.tooltip.edit": "Verbindung bearbeiten",
      "card.tooltip.edit_locked": "Bearbeitung gesperrt: Verbindung ist gemountet",
      "card.tooltip.ssh": "Direkte SSH-Sitzung öffnen (Terminal)",
      "card.tooltip.mount_on": "Klicken zum TRENNEN",
      "card.tooltip.mount_off": "Klicken zum VERBINDEN",
      "card.tooltip.open_path": "Gemounteten Pfad im Explorer öffnen",
      "card.loading.connect": "Verbinde…",
      "card.loading.disconnect": "Trenne…",
      "settings.title": "Einstellungen",
      "settings.section.language": "SPRACHE",
      "settings.section.theme": "DESIGN",
      "settings.section.general": "ALLGEMEIN",
      "settings.section.mount": "MOUNT-STATUS",
      "settings.section.terminal": "SSH-TERMINAL",
      "settings.section.developer": "ENTWICKLER",
      "settings.section.tools": "TOOLS & WIEDERHERSTELLUNG",
      "settings.start_with_windows": "Mit Windows starten",
      "settings.minimize_to_tray": "Beim Schließen in den Infobereich minimieren",
      "settings.require_admin": "Immer als Administrator ausführen (Registry)",
      "settings.check_interval": "Prüfintervall (Sekunden):",
      "settings.auto_reconnect": "Beim Start automatisch verbinden",
      "settings.auto_remount": "Automatisch neu verbinden bei Verbindungsverlust",
      "settings.use_putty": "PuTTY statt nativem SSH verwenden",
      "settings.putty_path": "Pfad zu putty.exe",
      "settings.putty_hint": "Hinweis: PuTTY benötigt Schlüssel im .ppk-Format.\nOpenSSH-Schlüssel können mit PuTTYgen konvertiert werden.",
      "settings.debug_mode": "Debug-Modus aktivieren",
      "settings.language.label": "Oberflächensprache",
      "settings.language.restart": "Sprachänderung wird nach einem Neustart wirksam.",
      "settings.theme.label": "Oberflächendesign",
      "settings.theme.dark": "Dunkel",
      "settings.theme.light": "Hell",
      "settings.fix_ghosts": "Geister-Laufwerke fixen",
      "settings.restart_explorer": "Explorer neu starten",
      "settings.ghosts_ok": "Geister-Laufwerke wurden bereinigt.\nExplorer wird neu gestartet…",
      "settings.explorer_restarted": "Explorer wurde neu gestartet.",
      "debug.title": "Live Debug Log",
      "debug.subtitle": "Interne Events, Mounting und SSH-Status seit Demo-Start oder Reset.",
      "debug.autoscroll": "Auto-scroll",
      "debug.clear": "Leeren",
      "debug.save": "Speichern",
      "debug.session_started": "Demo-Sitzung gestartet.",
      "debug.session_reset": "Demo wurde zurückgesetzt.",
      "debug.log_saved": "Debug-Log wurde exportiert.",
      "debug.log_cleared": "Debug-Log wurde geleert.",
      "debug.ghost_cleanup": "Simulierte Bereinigung von Geister-Laufwerken ausgeführt.",
      "debug.cpu_test": "Simulierter CPU-/Entschlüsselungstest abgeschlossen.",
      "settings.putty_missing": "Bitte den Pfad zu putty.exe eintragen.",
      "settings.putty_not_found": "putty.exe wurde nicht gefunden unter:\n{path}\n\nTrotzdem speichern?",
      "settings.putty_not_found_title": "PuTTY nicht gefunden",
      "addedit.edit_title": "Verbindung bearbeiten",
      "addedit.add_title": "Verbindung hinzufügen",
      "addedit.section.general": "ALLGEMEIN",
      "addedit.section.path": "PFAD & LAUFWERK",
      "addedit.section.auth": "AUTHENTIFIZIERUNG",
      "addedit.section.cli": "CLI-ZUGRIFF",
      "addedit.label.name": "Name",
      "addedit.label.host": "Host / IP",
      "addedit.label.user": "Benutzer",
      "addedit.label.port": "Port",
      "addedit.label.path": "Remote-Pfad",
      "addedit.label.drive": "Laufwerksbuchstabe",
      "addedit.label.method": "Methode",
      "addedit.label.password": "Passwort",
      "addedit.label.key": "Pfad zum privaten Schlüssel",
      "addedit.auth.password": "Passwort verwenden",
      "addedit.auth.key": "Privaten Schlüssel verwenden",
      "addedit.auth.ask": "Jedes Mal fragen",
      "addedit.auth.ask.title": "Authentifizierung wählen",
      "addedit.auth.ask.prompt": "Wie möchtest du dich mit '{name}' verbinden?",
      "auth.enter_password.title": "Passwort eingeben",
      "auth.enter_password.prompt": "Passwort für '{name}':",
      "addedit.placeholder.name": "Mein Server",
      "addedit.cli.enable": "CLI-Zugriff für Agenten aktivieren",
      "addedit.cli.label": "CLI Access Key (128 Zeichen)",
      "addedit.cli.none": "Kein Key generiert",
      "addedit.cli.generate": "Neu generieren",
      "addedit.required.title": "Pflichtfelder",
      "addedit.required.name": "Name darf nicht leer sein.",
      "addedit.required.host": "Host darf nicht leer sein.",
      "addedit.required.user": "Benutzer darf nicht leer sein.",
      "sysinfo.loading": "Lade Systeminformationen…",
      "sysinfo.refresh": "Aktualisieren",
      "sysinfo.os": "Betriebssystem",
      "sysinfo.host": "Hostname / Uptime",
      "sysinfo.cpu": "CPU",
      "sysinfo.ram": "RAM",
      "sysinfo.disk": "Festplatte (/)",
      "sysinfo.temp": "Temp",
      "sysinfo.users": "Nutzer",
      "sysinfo.processes": "Prozesse",
      "sysinfo.load": "Last",
      "sysinfo.ip": "IP-Adresse",
      "sysinfo.cores_suffix": "{n} Kerne",
      "sysinfo.uptime": "Uptime",
      "login.title": "NEO SSH-Win Manager – Anmeldung",
      "login.please_sign_in": "Bitte anmelden",
      "login.username": "Benutzername",
      "login.password": "Passwort",
      "login.sign_in": "Anmelden",
      "login.fill_all": "Bitte alle Felder ausfüllen.",
      "dialog.lead.users": "Verwalte Benutzer, Rollen und Passwortwechsel in einer einheitlichen Kartenansicht.",
      "users.title": "Benutzerverwaltung",
      "users.section.users": "BENUTZER",
      "users.section.new": "NEUEN BENUTZER ANLEGEN",
      "users.section.password": "PASSWORT ÄNDERN",
      "users.placeholder.username": "Benutzername",
      "users.placeholder.password": "Passwort (min. 6 Zeichen)",
      "users.admin": "Administrator",
      "users.create": "Benutzer anlegen",
      "users.you": " (Du)",
      "users.badge.you": "Du",
      "users.role.member": "Standard",
      "users.summary": "{users} Benutzer · {admins} Admins",
      "users.connections.one": "{n} Verbindung",
      "users.connections.many": "{n} Verbindungen",
      "users.tooltip.change_pw": "Eigenes Passwort ändern",
      "users.tooltip.reset_pw": "Passwort von '{name}' zurücksetzen",
      "users.tooltip.delete": "Benutzer '{name}' löschen",
      "users.delete.title": "Benutzer löschen",
      "users.delete.confirm": "Benutzer '{name}' und alle seine Verbindungen wirklich löschen?",
      "users.reset.title": "Passwort zurücksetzen",
      "users.reset.confirm": "Passwort von '{name}' wirklich zurücksetzen?\n\nEin neues Passwort wird generiert und angezeigt. Gespeicherte SSH-Passwörter dieses Benutzers gehen dabei verloren (Key-basierte Verbindungen bleiben erhalten).",
      "users.reset.new_title": "Neues Passwort",
      "users.reset.new_msg": "Neues Passwort für '{name}':\n\n{pw}\n\nBitte dem Benutzer übermitteln. Er sollte es nach dem nächsten Login selbst ändern.",
      "users.not_found": "Benutzer nicht gefunden.",
      "users.username_min": "Benutzername muss mindestens 3 Zeichen haben.",
      "users.password_min": "Passwort muss mindestens 6 Zeichen haben.",
      "users.duplicate": "Dieser Benutzername existiert bereits.",
      "chgpw.title": "Passwort ändern",
      "chgpw.current": "Aktuelles Passwort",
      "chgpw.new": "Neues Passwort (min. 6 Zeichen)",
      "chgpw.confirm": "Neues Passwort bestätigen",
      "chgpw.new_min": "Neues Passwort muss mindestens 6 Zeichen haben.",
      "chgpw.mismatch": "Die Passwörter stimmen nicht überein.",
      "chgpw.wrong_old": "Aktuelles Passwort ist falsch.",
      "chgpw.success": "Passwort geändert.",
      "sim.info.connected": "Connected",
      "sim.info.disconnected": "Disconnected",
      "sim.empty.title": "Bereit für den nächsten Schritt",
      "sim.empty.body": "Wähle eine Verbindung oder lege oben rechts eine neue an, um den Desktop-Flow weiterzuspielen.",
      "sim.popup.title": "SSH-Terminal · {name}",
      "sim.popup.body": "Dieses Popup simuliert nur das Öffnen des SSH-Terminals. Es wird keine Netzwerkverbindung aufgebaut und kein lokales Terminal gestartet.",
      "sim.popup.future": "Platzhalter für eine spätere interaktive Terminal-Simulation.",
      "sim.login.note": "Browser-Mock: Für die Demo reicht ein beliebiger nicht-leerer Benutzername mit Passwort.",
      "sim.mounts.one": "· 1 mount",
      "sim.mounts.many": "· {n} mounts",
      "sim.language.de": "Deutsch",
      "sim.language.en": "English"
    },
    en: {
      "app.ready": "Ready",
      "app.no_connections": "No connections",
      "header.connections": "Connections",
      "badge.n_active": "{n} active",
      "badge.n_mounted": "{n} mounted",
      "main.add_connection": "Add connection",
      "main.settings": "Settings",
      "main.users": "Users",
      "main.debug": "Debug",
      "main.delete": "Delete",
      "main.logout": "Logout",
      "status.connecting": "Connecting {name} → {drive}…",
      "status.disconnecting": "Disconnecting {drive}…",
      "status.connected": "✓ {name} connected as {drive}",
      "status.disconnected": "✓ {name} disconnected.",
      "status.connect_failed": "✗ Connection failed: {name}",
      "status.connection_added": "Connection '{name}' added.",
      "status.connection_updated": "Connection '{name}' updated.",
      "status.connection_deleted": "Connection '{name}' deleted.",
      "status.user_created": "User '{name}' created.",
      "status.user_deleted": "User '{name}' deleted.",
      "status.password_changed": "Password changed.",
      "status.password_reset": "Password for '{name}' was reset.",
      "status.settings_saved": "Settings saved.",
      "status.opening_explorer": "Opening {path} in Explorer",
      "status.ssh_started": "{backend} terminal started for '{name}'.",
      "dialog.cancel": "Cancel",
      "dialog.save": "Save",
      "dialog.close": "Close",
      "dialog.ok": "OK",
      "dialog.yes": "Yes",
      "dialog.no": "No",
      "dialog.error": "Error",
      "dialog.success": "Success",
      "dialog.warning": "Warning",
      "mount.failed.title": "Connection failed",
      "mount.failed.main": "Could not connect to '{name}'.",
      "mount.failed.troubleshoot": "\n\nPlease check:\n • Is the device reachable on the network? (IP: {host})\n • Are credentials (password/key) correct?\n • Is the SSH service running on the target?\n • Is a firewall blocking port {port}?",
      "mount.failed.details": "\n\nTechnical details:\n{msg}",
      "mount.failed.retry": "Retry",
      "delete.title": "Delete",
      "delete.select_one": "Please select a connection.",
      "delete.mounted_confirm": "'{name}' is connected. Disconnect and delete?",
      "delete.confirm": "Delete connection '{name}'?",
      "edit.locked.title": "Editing locked",
      "edit.locked.msg": "This connection is currently mounted and cannot be edited.\nPlease disconnect first.",
      "logout.title": "Logout",
      "logout.confirm": "Really log out?\nAll active mounts will be disconnected.",
      "card.tooltip.info": "Show system information",
      "card.tooltip.edit": "Edit connection",
      "card.tooltip.edit_locked": "Editing locked: connection is mounted",
      "card.tooltip.ssh": "Open direct SSH session (terminal)",
      "card.tooltip.mount_on": "Click to DISCONNECT",
      "card.tooltip.mount_off": "Click to CONNECT",
      "card.tooltip.open_path": "Open mounted path in Explorer",
      "card.loading.connect": "Connecting…",
      "card.loading.disconnect": "Disconnecting…",
      "settings.title": "Settings",
      "settings.section.language": "LANGUAGE",
      "settings.section.theme": "THEME",
      "settings.section.general": "GENERAL",
      "settings.section.mount": "MOUNT STATUS",
      "settings.section.terminal": "SSH TERMINAL",
      "settings.section.developer": "DEVELOPER",
      "settings.section.tools": "TOOLS & RECOVERY",
      "settings.start_with_windows": "Start with Windows",
      "settings.minimize_to_tray": "Minimize to system tray on close",
      "settings.require_admin": "Always run as administrator (Registry)",
      "settings.check_interval": "Check interval (seconds):",
      "settings.auto_reconnect": "Auto-connect on start",
      "settings.auto_remount": "Auto-reconnect on connection loss",
      "settings.use_putty": "Use PuTTY instead of native SSH",
      "settings.putty_path": "Path to putty.exe",
      "settings.putty_hint": "Hint: PuTTY requires keys in .ppk format.\nOpenSSH keys can be converted with PuTTYgen.",
      "settings.debug_mode": "Enable debug mode",
      "settings.language.label": "Interface language",
      "settings.language.restart": "Language change takes effect after restart.",
      "settings.theme.label": "Interface theme",
      "settings.theme.dark": "Dark",
      "settings.theme.light": "Light",
      "settings.fix_ghosts": "Fix ghost drives",
      "settings.restart_explorer": "Restart Explorer",
      "settings.ghosts_ok": "Ghost drives cleaned up.\nExplorer is restarting…",
      "settings.explorer_restarted": "Explorer has been restarted.",
      "debug.title": "Live Debug Log",
      "debug.subtitle": "Internal events, mounting and SSH state since demo start or reset.",
      "debug.autoscroll": "Auto-scroll",
      "debug.clear": "Clear",
      "debug.save": "Save",
      "debug.session_started": "Demo session started.",
      "debug.session_reset": "Demo was reset.",
      "debug.log_saved": "Debug log exported.",
      "debug.log_cleared": "Debug log cleared.",
      "debug.ghost_cleanup": "Simulated ghost-drive cleanup executed.",
      "debug.cpu_test": "Simulated CPU/decryption test completed.",
      "settings.putty_missing": "Please enter the path to putty.exe.",
      "settings.putty_not_found": "putty.exe was not found at:\n{path}\n\nSave anyway?",
      "settings.putty_not_found_title": "PuTTY not found",
      "addedit.edit_title": "Edit connection",
      "addedit.add_title": "Add connection",
      "addedit.section.general": "GENERAL",
      "addedit.section.path": "PATH & DRIVE",
      "addedit.section.auth": "AUTHENTICATION",
      "addedit.section.cli": "CLI ACCESS",
      "addedit.label.name": "Name",
      "addedit.label.host": "Host / IP",
      "addedit.label.user": "User",
      "addedit.label.port": "Port",
      "addedit.label.path": "Remote path",
      "addedit.label.drive": "Drive letter",
      "addedit.label.method": "Method",
      "addedit.label.password": "Password",
      "addedit.label.key": "Private key path",
      "addedit.auth.password": "Use password",
      "addedit.auth.key": "Use private key",
      "addedit.auth.ask": "Ask each time",
      "addedit.auth.ask.title": "Choose authentication",
      "addedit.auth.ask.prompt": "How do you want to connect to '{name}'?",
      "auth.enter_password.title": "Enter password",
      "auth.enter_password.prompt": "Password for '{name}':",
      "addedit.placeholder.name": "My server",
      "addedit.cli.enable": "Enable CLI access for agents",
      "addedit.cli.label": "CLI Access Key (128 char)",
      "addedit.cli.none": "No key generated",
      "addedit.cli.generate": "Generate new",
      "addedit.required.title": "Required fields",
      "addedit.required.name": "Name must not be empty.",
      "addedit.required.host": "Host must not be empty.",
      "addedit.required.user": "User must not be empty.",
      "sysinfo.loading": "Loading system information…",
      "sysinfo.refresh": "Refresh",
      "sysinfo.os": "Operating system",
      "sysinfo.host": "Hostname / uptime",
      "sysinfo.cpu": "CPU",
      "sysinfo.ram": "RAM",
      "sysinfo.disk": "Disk (/)",
      "sysinfo.temp": "Temp",
      "sysinfo.users": "Users",
      "sysinfo.processes": "Processes",
      "sysinfo.load": "Load",
      "sysinfo.ip": "IP address",
      "sysinfo.cores_suffix": "{n} cores",
      "sysinfo.uptime": "Uptime",
      "login.title": "NEO SSH-Win Manager – Login",
      "login.please_sign_in": "Please sign in",
      "login.username": "Username",
      "login.password": "Password",
      "login.sign_in": "Sign in",
      "login.fill_all": "Please fill in all fields.",
      "dialog.lead.users": "Manage users, roles and password changes in one consistent card layout.",
      "users.title": "User Management",
      "users.section.users": "USERS",
      "users.section.new": "CREATE NEW USER",
      "users.section.password": "CHANGE PASSWORD",
      "users.placeholder.username": "Username",
      "users.placeholder.password": "Password (min. 6 characters)",
      "users.admin": "Administrator",
      "users.create": "Create user",
      "users.you": " (you)",
      "users.badge.you": "You",
      "users.role.member": "Standard",
      "users.summary": "{users} users · {admins} admins",
      "users.connections.one": "{n} connection",
      "users.connections.many": "{n} connections",
      "users.tooltip.change_pw": "Change own password",
      "users.tooltip.reset_pw": "Reset password of '{name}'",
      "users.tooltip.delete": "Delete user '{name}'",
      "users.delete.title": "Delete user",
      "users.delete.confirm": "Really delete user '{name}' and all their connections?",
      "users.reset.title": "Reset password",
      "users.reset.confirm": "Really reset password of '{name}'?\n\nA new password will be generated and shown. Stored SSH passwords for this user will be lost (key-based connections are preserved).",
      "users.reset.new_title": "New password",
      "users.reset.new_msg": "New password for '{name}':\n\n{pw}\n\nPlease share it with the user. They should change it after their next login.",
      "users.not_found": "User not found.",
      "users.username_min": "Username must have at least 3 characters.",
      "users.password_min": "Password must have at least 6 characters.",
      "users.duplicate": "That username already exists.",
      "chgpw.title": "Change Password",
      "chgpw.current": "Current password",
      "chgpw.new": "New password (min. 6 characters)",
      "chgpw.confirm": "Confirm new password",
      "chgpw.new_min": "New password must have at least 6 characters.",
      "chgpw.mismatch": "The passwords do not match.",
      "chgpw.wrong_old": "Current password is incorrect.",
      "chgpw.success": "Password changed.",
      "sim.info.connected": "Connected",
      "sim.info.disconnected": "Disconnected",
      "sim.empty.title": "Ready for the next step",
      "sim.empty.body": "Pick a connection or create a new one in the top-right corner to continue the desktop flow.",
      "sim.popup.title": "SSH terminal · {name}",
      "sim.popup.body": "This popup only simulates opening the SSH terminal. No network connection is made and no local terminal is started.",
      "sim.popup.future": "Placeholder for a future interactive terminal simulation.",
      "sim.login.note": "Browser mock: any non-empty username and password pair will sign you back in.",
      "sim.mounts.one": "· 1 mount",
      "sim.mounts.many": "· {n} mounts",
      "sim.language.de": "German",
      "sim.language.en": "English"
    }
  };

  let state = createInitialState();
  let activeResize = null;
  seedDebugLog("debug.session_started");

  if (resetButton) {
    resetButton.addEventListener("click", () => {
      state = createInitialState();
      seedDebugLog("debug.session_reset");
      render();
    });
  }

  root.addEventListener("click", handleClick);
  root.addEventListener("input", handleInput);
  root.addEventListener("change", handleChange);
  root.addEventListener("pointerdown", handlePointerDown);
  root.addEventListener("dblclick", handleDoubleClick);
  document.addEventListener("keydown", handleKeydown);
  document.addEventListener("pointermove", handlePointerMove);
  document.addEventListener("pointerup", handlePointerUp);
  window.neoI18n?.onChange?.(() => render());

  render();

  function createInitialState() {
    const theme = getCurrentTheme();
    const language = getLang();

    return {
      version: "v1.3.1",
      workstation: "workstation",
      currentUser: "admin",
      currentUserId: "user-admin",
      loggedIn: true,
      pageMode: "connections",
      selectedConnectionId: "prod",
      panel: { mode: "info", connectionId: "prod" },
      layout: { listWidth: 396 },
      status: { key: "app.ready", params: {} },
      settings: {
        start_with_windows: false,
        minimize_to_tray: true,
        require_admin: false,
        check_interval_seconds: 30,
        auto_reconnect: false,
        auto_remount_on_lost: true,
        debug_mode: false,
        use_putty: false,
        putty_path: "C:\\Program Files\\PuTTY\\putty.exe",
        language,
        theme
      },
      settingsDraft: null,
      connectionDraft: null,
      userDraft: createUserDraft(),
      passwordDraft: createPasswordDraft(),
      usersFocusTarget: null,
      loginDraft: { username: "admin", password: "" },
      loginErrorKey: null,
      modal: null,
      popup: null,
      inlineMessage: null,
      debug: {
        windowOpen: false,
        autoScroll: true,
        sessionStartedAt: Date.now(),
        entries: []
      },
      users: defaultUsers(),
      connections: defaultConnections()
    };
  }

  function defaultUsers() {
    return [
      {
        id: "user-admin",
        username: "admin",
        is_admin: true,
        password: "admin123",
        created_at: "2026-04-12 09:18"
      },
      {
        id: "user-gregor",
        username: "gregor",
        is_admin: false,
        password: "homelab99",
        created_at: "2026-04-18 13:42"
      },
      {
        id: "user-ops",
        username: "ops",
        is_admin: true,
        password: "ops-lab-42",
        created_at: "2026-04-22 08:05"
      }
    ];
  }

  function defaultConnections() {
    return [
      {
        id: "prod",
        owner_id: "user-admin",
        name: "Production · web-01",
        host: "10.0.4.21",
        user: "deploy",
        remote_path: "/var/www",
        port: 22,
        auth_method: "password",
        password: "demo-secret",
        key_path: "",
        drive_letter: "Z:",
        mounted: true,
        loading: null,
        cli_access_enabled: true,
        cli_access_key: generateCliKey(),
        mountFailuresRemaining: 0,
        sysinfoLoading: false,
        systemInfo: {
          os: "Ubuntu 24.04 LTS",
          hostname: "web-01",
          uptime: "4d 03h 18m",
          cpuModel: "AMD EPYC 7B13",
          cpuCores: 8,
          cpuPct: 14,
          ramUsedGb: 2.1,
          ramTotalGb: 8,
          diskUsedGb: 96,
          diskTotalGb: 320,
          tempC: 42,
          users: 2,
          processes: 214,
          load: "0.42 0.31 0.27",
          ip: "10.0.4.21",
          lastSeen: "00:01"
        }
      },
      {
        id: "nas",
        owner_id: "user-gregor",
        name: "Homelab · NAS",
        host: "nas.local",
        user: "gregor",
        remote_path: "/volume1",
        port: 22,
        auth_method: "key",
        password: "",
        key_path: "C:\\Users\\gregor\\.ssh\\id_ed25519",
        drive_letter: "N:",
        mounted: false,
        loading: null,
        cli_access_enabled: false,
        cli_access_key: "",
        mountFailuresRemaining: 0,
        sysinfoLoading: false,
        systemInfo: {
          os: "Synology DSM 7.2",
          hostname: "nas",
          uptime: "12d 11h 05m",
          cpuModel: "Intel Celeron J4125",
          cpuCores: 4,
          cpuPct: 22,
          ramUsedGb: 3.7,
          ramTotalGb: 8,
          diskUsedGb: 511,
          diskTotalGb: 1024,
          tempC: 39,
          users: 1,
          processes: 162,
          load: "0.84 0.63 0.41",
          ip: "192.168.178.12",
          lastSeen: "02:14"
        }
      },
      {
        id: "staging",
        owner_id: "user-admin",
        name: "Staging · db-replica",
        host: "10.0.4.45",
        user: "root",
        remote_path: "/srv",
        port: 22,
        auth_method: "ask",
        password: "",
        key_path: "C:\\Users\\admin\\.ssh\\staging-demo.ppk",
        drive_letter: "S:",
        mounted: false,
        loading: null,
        cli_access_enabled: false,
        cli_access_key: "",
        mountFailuresRemaining: 1,
        sysinfoLoading: false,
        systemInfo: {
          os: "Debian 12",
          hostname: "db-replica",
          uptime: "18h 47m",
          cpuModel: "Intel Xeon Gold 6226R",
          cpuCores: 12,
          cpuPct: 31,
          ramUsedGb: 7.8,
          ramTotalGb: 16,
          diskUsedGb: 274,
          diskTotalGb: 512,
          tempC: 47,
          users: 4,
          processes: 281,
          load: "1.52 1.21 0.97",
          ip: "10.0.4.45",
          lastSeen: "00:24"
        }
      }
    ];
  }

  function handleClick(event) {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) return;

    const actionTarget = target.closest("[data-action]");
    if (actionTarget) {
      event.preventDefault();
      runAction(actionTarget.dataset.action, actionTarget.dataset);
      return;
    }

    const row = target.closest("[data-connection-row]");
    if (row && state.pageMode === "connections" && !state.modal) {
      openInfo(row.dataset.connectionRow);
    }
  }

  function handlePointerDown(event) {
    const target = event.target instanceof Element ? event.target : null;
    const handle = target?.closest("[data-split-handle]");
    if (!handle || window.innerWidth <= 1100 || state.pageMode !== "connections") return;

    const view = root.querySelector(".sim-home-view");
    if (!view) return;

    const rect = view.getBoundingClientRect();
    activeResize = {
      pointerId: event.pointerId,
      left: rect.left,
      min: Math.round((rect.width - 14) * 0.4),
      max: Math.round((rect.width - 14) * 0.6)
    };
    root.dataset.resizing = "true";
    event.preventDefault();
  }

  function handlePointerMove(event) {
    if (!activeResize || event.pointerId !== activeResize.pointerId) return;
    state.layout.listWidth = clamp(Math.round(event.clientX - activeResize.left - 7), activeResize.min, activeResize.max);
    applyLayoutVars();
  }

  function handlePointerUp(event) {
    if (!activeResize || event.pointerId !== activeResize.pointerId) return;
    activeResize = null;
    delete root.dataset.resizing;
  }

  function handleDoubleClick(event) {
    const target = event.target instanceof Element ? event.target : null;
    if (!target?.closest("[data-split-handle]")) return;
    state.layout.listWidth = 396;
    applyLayoutVars();
  }

  function handleInput(event) {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) return;

    if (target.matches("[data-connection-field]")) {
      if (!state.connectionDraft) return;
      updateObjectFromInput(state.connectionDraft, target.dataset.connectionField, target);
      if (state.inlineMessage?.scope === "connection") {
        state.inlineMessage = null;
      }
      return;
    }

    if (target.matches("[data-settings-field]")) {
      if (!state.settingsDraft) return;
      updateObjectFromInput(state.settingsDraft, target.dataset.settingsField, target);
      if (state.inlineMessage?.scope === "settings") {
        state.inlineMessage = null;
      }
      return;
    }

    if (target.matches("[data-user-field]")) {
      if (!state.userDraft) return;
      updateObjectFromInput(state.userDraft, target.dataset.userField, target);
      if (state.inlineMessage?.scope === "users") {
        state.inlineMessage = null;
      }
      return;
    }

    if (target.matches("[data-password-field]")) {
      if (!state.passwordDraft) return;
      state.passwordDraft[target.dataset.passwordField] = target.value;
      if (state.inlineMessage?.scope === "users") {
        state.inlineMessage = null;
      }
      return;
    }

    if (target.matches("[data-login-field]")) {
      state.loginDraft[target.dataset.loginField] = target.value;
      state.loginErrorKey = null;
      return;
    }

    if (target.matches("[data-modal-field='password']") && state.modal?.type === "password-prompt") {
      state.modal.value = target.value;
      return;
    }

    if (target.matches("[data-modal-field='auth-method']") && state.modal?.type === "auth-choice") {
      state.modal.selectedMethod = target.value;
    }
  }

  function handleChange(event) {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) return;

    if (target.matches("[data-connection-field]")) {
      handleInput(event);
      const field = target.dataset.connectionField;
      if (field === "cli_access_enabled" && state.connectionDraft?.cli_access_enabled && !state.connectionDraft.cli_access_key) {
        state.connectionDraft.cli_access_key = generateCliKey();
      }
      render();
      return;
    }

    if (target.matches("[data-settings-field]")) {
      handleInput(event);
      render();
      return;
    }

    if (target.matches("[data-user-field]")) {
      handleInput(event);
      render();
      return;
    }

    if (target.matches("[data-debug-field]")) {
      if (target instanceof HTMLInputElement && target.type === "checkbox") {
        state.debug[target.dataset.debugField] = target.checked;
      }
      render();
      return;
    }

    if (target.matches("[data-modal-field='auth-method']")) {
      handleInput(event);
      render();
    }
  }

  function handleKeydown(event) {
    if (event.key !== "Escape") return;
    if (state.modal) {
      state.modal = null;
      render();
      return;
    }
    if (state.popup) {
      state.popup = null;
      render();
      return;
    }
    if (state.debug?.windowOpen) {
      state.debug.windowOpen = false;
      render();
    }
  }

  function runAction(action, data) {
    switch (action) {
      case "nav-home":
        goHome();
        break;
      case "nav-settings":
        openSettings();
        break;
      case "nav-users":
        openUsers();
        break;
      case "nav-debug":
        state.debug.windowOpen = true;
        render();
        break;
      case "nav-logout":
        promptLogout();
        break;
      case "add-connection":
        openAddForm();
        break;
      case "panel-close":
        closeCurrentPanel();
        break;
      case "edit-connection":
        openEditForm(data.connId || state.panel.connectionId);
        break;
      case "delete-connection":
        requestDelete(data.connId || state.panel.connectionId);
        break;
      case "open-path":
        handleCloudButton(data.connId);
        break;
      case "open-sysinfo":
        openSysinfo(data.connId);
        break;
      case "open-ssh":
        requestResolvedAction(data.connId, "ssh");
        break;
      case "toggle-mount":
        toggleMount(data.connId);
        break;
      case "save-connection":
        saveConnectionDraft();
        break;
      case "cancel-connection":
        cancelConnectionDraft();
        break;
      case "save-settings":
        saveSettingsDraft();
        break;
      case "cancel-settings":
        goHome();
        break;
      case "save-user":
        saveUserDraft();
        break;
      case "request-delete-user":
        requestUserDelete(data.userId);
        break;
      case "request-reset-user":
        requestResetUserPassword(data.userId);
        break;
      case "focus-change-password":
        state.usersFocusTarget = "password";
        render();
        break;
      case "save-password-change":
        savePasswordChange();
        break;
      case "settings-fix-ghosts":
        pushDebugLog("warning", t("debug.ghost_cleanup"));
        showNoticeModal({ titleKey: "dialog.success", bodyKey: "settings.ghosts_ok", tone: "info" });
        break;
      case "settings-restart-explorer":
        pushDebugLog("info", t("settings.explorer_restarted"));
        showNoticeModal({ titleText: "Explorer", bodyKey: "settings.explorer_restarted", tone: "info" });
        break;
      case "debug-close":
        state.debug.windowOpen = false;
        render();
        break;
      case "debug-clear":
        state.debug.entries = [];
        pushDebugLog("info", t("debug.log_cleared"));
        render();
        break;
      case "debug-save":
        downloadDebugLog();
        break;
      case "debug-purge":
        pushDebugLog("warning", t("debug.ghost_cleanup"));
        render();
        break;
      case "debug-test-cpu":
        runDebugCpuTest();
        render();
        break;
      case "generate-cli-key":
        if (state.connectionDraft) {
          state.connectionDraft.cli_access_enabled = true;
          state.connectionDraft.cli_access_key = generateCliKey();
          render();
        }
        break;
      case "close-popup":
        state.popup = null;
        render();
        break;
      case "modal-confirm":
        confirmModal();
        break;
      case "modal-cancel":
        cancelModal();
        break;
      case "modal-retry":
        retryModal();
        break;
      case "login-submit":
        submitLogin();
        break;
      case "sysinfo-refresh":
        refreshSystemInfo(data.connId);
        break;
      default:
        break;
    }
  }

  function getLang() {
    return window.neoI18n?.getLang?.() === "en" ? "en" : "de";
  }

  function getCurrentTheme() {
    return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function t(key, params) {
    const lang = getLang();
    const template = COPY[lang]?.[key] ?? COPY.de[key] ?? key;
    return String(template).replace(/\{(\w+)\}/g, (_, token) => {
      if (!params || !(token in params)) return `{${token}}`;
      return String(params[token]);
    });
  }

  function debugToneForStatus(key) {
    if (/failed|error/i.test(key)) return "error";
    if (/warning|delete\.select_one|not_found/i.test(key)) return "warning";
    return "info";
  }

  function pushDebugLog(level, message) {
    if (!state.debug) return;
    state.debug.entries.push({
      id: `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
      level,
      message,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    });
  }

  function seedDebugLog(messageKey) {
    if (!state.debug) return;
    state.debug.entries = [];
    pushDebugLog("info", t(messageKey));
    pushDebugLog("info", t("app.ready"));
  }

  function syncDebugWindow() {
    window.requestAnimationFrame(() => {
      if (!state.debug?.windowOpen || !state.debug.autoScroll) return;
      const log = root.querySelector("[data-debug-log]");
      if (log) log.scrollTop = log.scrollHeight;
    });
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function generateCliKey() {
    const bytes = new Uint8Array(64);
    if (window.crypto?.getRandomValues) {
      window.crypto.getRandomValues(bytes);
    } else {
      for (let index = 0; index < bytes.length; index += 1) {
        bytes[index] = Math.floor(Math.random() * 256);
      }
    }
    return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
  }

  function generateUserPassword() {
    const alphabet = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    const values = new Uint8Array(14);
    if (window.crypto?.getRandomValues) {
      window.crypto.getRandomValues(values);
    } else {
      for (let index = 0; index < values.length; index += 1) {
        values[index] = Math.floor(Math.random() * alphabet.length);
      }
    }
    return Array.from(values, (value) => alphabet[value % alphabet.length]).join("");
  }

  function createUserDraft() {
    return { username: "", password: "", is_admin: false };
  }

  function createPasswordDraft() {
    return { current: "", next: "", confirm: "" };
  }

  function applyLayoutVars() {
    root.style.setProperty("--sim-list-width", `${state.layout.listWidth}px`);
  }

  function getConnection(connId) {
    return state.connections.find((connection) => connection.id === connId) || null;
  }

  function getUserById(userId) {
    return state.users.find((user) => user.id === userId) || null;
  }

  function getCurrentUser() {
    return getUserById(state.currentUserId);
  }

  function isCurrentUserAdmin() {
    return Boolean(getCurrentUser()?.is_admin);
  }

  function getUserConnectionCount(userId) {
    return state.connections.filter((connection) => connection.owner_id === userId).length;
  }

  function getMountedCount() {
    return state.connections.filter((connection) => connection.mounted).length;
  }

  function assignStatus(key, params) {
    state.status = { key, params: params || {} };
    pushDebugLog(debugToneForStatus(key), t(key, params));
  }

  function updateObjectFromInput(targetObject, field, element) {
    if (element instanceof HTMLInputElement && element.type === "checkbox") {
      targetObject[field] = element.checked;
      return;
    }
    if (element instanceof HTMLInputElement && element.type === "number") {
      targetObject[field] = Number(element.value || 0);
      return;
    }
    targetObject[field] = element.value;
  }

  function goHome() {
    state.pageMode = "connections";
    state.panel = { mode: "none", connectionId: null };
    state.selectedConnectionId = null;
    state.settingsDraft = null;
    state.connectionDraft = null;
    state.usersFocusTarget = null;
    state.inlineMessage = null;
    render();
  }

  function openSettings() {
    state.pageMode = "settings";
    state.settingsDraft = clone(state.settings);
    state.connectionDraft = null;
    state.usersFocusTarget = null;
    state.inlineMessage = null;
    render();
  }

  function openUsers() {
    state.pageMode = "users";
    state.panel = { mode: "none", connectionId: null };
    state.selectedConnectionId = null;
    state.settingsDraft = null;
    state.connectionDraft = null;
    state.inlineMessage = null;
    render();
  }

  function openInfo(connId) {
    if (!getConnection(connId)) return;
    state.pageMode = "connections";
    state.selectedConnectionId = connId;
    state.panel = { mode: "info", connectionId: connId };
    state.connectionDraft = null;
    state.inlineMessage = null;
    render();
  }

  function openSysinfo(connId) {
    if (!getConnection(connId)) return;
    state.pageMode = "connections";
    state.selectedConnectionId = connId;
    state.panel = { mode: "sysinfo", connectionId: connId };
    state.connectionDraft = null;
    state.inlineMessage = null;
    render();
  }

  function nextAvailableDriveLetter(excludeId) {
    const used = new Set(
      state.connections
        .filter((connection) => connection.id !== excludeId)
        .map((connection) => connection.drive_letter)
    );
    return DRIVE_POOL.find((letter) => !used.has(letter)) || "Z:";
  }

  function createConnectionDraft(connection) {
    if (connection) {
      return {
        id: connection.id,
        name: connection.name,
        host: connection.host,
        user: connection.user,
        remote_path: connection.remote_path,
        port: connection.port,
        auth_method: connection.auth_method,
        password: connection.password,
        key_path: connection.key_path,
        drive_letter: connection.drive_letter,
        cli_access_enabled: Boolean(connection.cli_access_enabled),
        cli_access_key: connection.cli_access_key || ""
      };
    }

    return {
      id: null,
      name: "",
      host: "",
      user: "",
      remote_path: "/",
      port: 22,
      auth_method: "password",
      password: "",
      key_path: "",
      drive_letter: nextAvailableDriveLetter(null),
      cli_access_enabled: false,
      cli_access_key: ""
    };
  }

  function openAddForm() {
    state.pageMode = "connections";
    state.connectionDraft = createConnectionDraft(null);
    state.panel = { mode: "add", connectionId: null };
    state.inlineMessage = null;
    render();
  }

  function openEditForm(connId) {
    const connection = getConnection(connId);
    if (!connection) return;
    if (connection.mounted) {
      state.inlineMessage = {
        scope: "connection",
        title: t("edit.locked.title"),
        body: t("edit.locked.msg"),
        tone: "error"
      };
      state.pageMode = "connections";
      state.selectedConnectionId = connId;
      state.panel = { mode: "info", connectionId: connId };
      render();
      return;
    }

    state.pageMode = "connections";
    state.selectedConnectionId = connId;
    state.connectionDraft = createConnectionDraft(connection);
    state.panel = { mode: "edit", connectionId: connId };
    state.inlineMessage = null;
    render();
  }

  function closeCurrentPanel() {
    if (state.pageMode === "settings") {
      goHome();
      return;
    }

    state.panel = { mode: "none", connectionId: null };
    state.selectedConnectionId = null;
    state.connectionDraft = null;
    state.inlineMessage = null;
    render();
  }

  function buildSystemInfo(connection) {
    const isDatabase = /db|sql|replica/i.test(connection.name + connection.host);
    const cpuCores = isDatabase ? 12 : 6;
    const ramTotalGb = isDatabase ? 16 : 8;
    const diskTotalGb = isDatabase ? 512 : 256;
    const cpuPct = isDatabase ? 28 : 17;
    const ramUsedGb = Number((ramTotalGb * (isDatabase ? 0.49 : 0.31)).toFixed(1));
    const diskUsedGb = Number((diskTotalGb * (isDatabase ? 0.53 : 0.34)).toFixed(0));

    return {
      os: isDatabase ? "Debian 12" : "Ubuntu 24.04 LTS",
      hostname: connection.host.split(/[.:]/)[0] || connection.host,
      uptime: isDatabase ? "09h 42m" : "1d 06h 12m",
      cpuModel: isDatabase ? "Intel Xeon Gold 6226R" : "AMD EPYC 7B12",
      cpuCores,
      cpuPct,
      ramUsedGb,
      ramTotalGb,
      diskUsedGb,
      diskTotalGb,
      tempC: isDatabase ? 45 : 39,
      users: isDatabase ? 3 : 1,
      processes: isDatabase ? 244 : 168,
      load: formatLoad(cpuPct),
      ip: connection.host,
      lastSeen: "00:00"
    };
  }

  function saveConnectionDraft() {
    const draft = state.connectionDraft;
    if (!draft) return;

    const errors = [];
    if (!draft.name.trim()) errors.push(t("addedit.required.name"));
    if (!draft.host.trim()) errors.push(t("addedit.required.host"));
    if (!draft.user.trim()) errors.push(t("addedit.required.user"));

    if (errors.length) {
      state.inlineMessage = {
        scope: "connection",
        title: t("addedit.required.title"),
        body: errors.join("\n"),
        tone: "error"
      };
      render();
      return;
    }

    if (state.panel.mode === "edit") {
      const connection = getConnection(state.panel.connectionId);
      if (!connection) return;
      Object.assign(connection, {
        name: draft.name.trim(),
        host: draft.host.trim(),
        user: draft.user.trim(),
        remote_path: draft.remote_path.trim() || "/",
        port: Number(draft.port) || 22,
        auth_method: draft.auth_method,
        password: draft.password,
        key_path: draft.key_path.trim(),
        drive_letter: draft.drive_letter,
        cli_access_enabled: Boolean(draft.cli_access_enabled),
        cli_access_key: draft.cli_access_enabled ? draft.cli_access_key : ""
      });
      assignStatus("status.connection_updated", { name: connection.name });
      state.inlineMessage = null;
      state.connectionDraft = null;
      state.panel = { mode: "info", connectionId: connection.id };
      state.selectedConnectionId = connection.id;
      render();
      return;
    }

    const newConnection = {
      id: `conn-${Date.now()}`,
      owner_id: state.currentUserId || "user-admin",
      name: draft.name.trim(),
      host: draft.host.trim(),
      user: draft.user.trim(),
      remote_path: draft.remote_path.trim() || "/",
      port: Number(draft.port) || 22,
      auth_method: draft.auth_method,
      password: draft.password,
      key_path: draft.key_path.trim(),
      drive_letter: draft.drive_letter,
      mounted: false,
      loading: null,
      cli_access_enabled: Boolean(draft.cli_access_enabled),
      cli_access_key: draft.cli_access_enabled ? draft.cli_access_key : "",
      mountFailuresRemaining: 0,
      sysinfoLoading: false,
      systemInfo: buildSystemInfo(draft)
    };

    state.connections.unshift(newConnection);
    assignStatus("status.connection_added", { name: newConnection.name });
    state.inlineMessage = null;
    state.connectionDraft = null;
    state.panel = { mode: "info", connectionId: newConnection.id };
    state.selectedConnectionId = newConnection.id;
    render();
  }

  function cancelConnectionDraft() {
    if (state.panel.mode === "edit" && state.panel.connectionId) {
      openInfo(state.panel.connectionId);
      return;
    }
    state.connectionDraft = null;
    state.panel = { mode: "none", connectionId: null };
    state.selectedConnectionId = null;
    state.inlineMessage = null;
    render();
  }

  function saveUserDraft() {
    const username = String(state.userDraft.username || "").trim();
    const password = String(state.userDraft.password || "");

    if (username.length < 3) {
      state.inlineMessage = {
        scope: "users",
        title: t("dialog.error"),
        body: t("users.username_min"),
        tone: "error"
      };
      render();
      return;
    }

    if (password.length < 6) {
      state.inlineMessage = {
        scope: "users",
        title: t("dialog.error"),
        body: t("users.password_min"),
        tone: "error"
      };
      render();
      return;
    }

    if (state.users.some((user) => user.username.toLowerCase() === username.toLowerCase())) {
      state.inlineMessage = {
        scope: "users",
        title: t("dialog.error"),
        body: t("users.duplicate"),
        tone: "error"
      };
      render();
      return;
    }

    state.users.push({
      id: `user-${Date.now()}`,
      username,
      is_admin: Boolean(state.userDraft.is_admin),
      password,
      created_at: new Date().toISOString().slice(0, 16).replace("T", " ")
    });
    state.users.sort((left, right) => left.username.localeCompare(right.username, undefined, { sensitivity: "base" }));
    state.userDraft = createUserDraft();
    state.inlineMessage = null;
    assignStatus("status.user_created", { name: username });
    render();
  }

  function requestUserDelete(userId) {
    const user = getUserById(userId);
    if (!user) return;
    state.modal = {
      type: "confirm",
      titleKey: "users.delete.title",
      bodyKey: "users.delete.confirm",
      bodyParams: { name: user.username },
      confirmAction: { type: "delete-user", userId },
      confirmVariant: "danger"
    };
    render();
  }

  function deleteUser(userId) {
    const user = getUserById(userId);
    if (!user) return;

    state.users = state.users.filter((entry) => entry.id !== userId);
    state.connections = state.connections.filter((connection) => connection.owner_id !== userId);
    state.userDraft = createUserDraft();
    state.passwordDraft = createPasswordDraft();
    state.inlineMessage = null;

    if (!getConnection(state.selectedConnectionId)) {
      const fallback = state.connections[0] || null;
      state.selectedConnectionId = fallback?.id || null;
      state.panel = fallback ? { mode: "info", connectionId: fallback.id } : { mode: "none", connectionId: null };
    }

    assignStatus("status.user_deleted", { name: user.username });
    render();
  }

  function requestResetUserPassword(userId) {
    const user = getUserById(userId);
    if (!user) return;
    state.modal = {
      type: "confirm",
      titleKey: "users.reset.title",
      bodyKey: "users.reset.confirm",
      bodyParams: { name: user.username },
      confirmAction: { type: "reset-user-password", userId },
      confirmVariant: "primary"
    };
    render();
  }

  function resetUserPassword(userId) {
    const user = getUserById(userId);
    if (!user) {
      assignStatus("users.not_found");
      render();
      return;
    }

    const newPassword = generateUserPassword();
    user.password = newPassword;
    assignStatus("status.password_reset", { name: user.username });
    showNoticeModal({
      titleKey: "users.reset.new_title",
      bodyKey: "users.reset.new_msg",
      bodyParams: { name: user.username, pw: newPassword },
      tone: "info"
    });
  }

  function savePasswordChange() {
    const currentUser = getCurrentUser();
    if (!currentUser) return;
    const draft = state.passwordDraft;

    if (String(draft.next || "").length < 6) {
      state.inlineMessage = {
        scope: "users",
        title: t("dialog.error"),
        body: t("chgpw.new_min"),
        tone: "error"
      };
      render();
      return;
    }

    if (draft.next !== draft.confirm) {
      state.inlineMessage = {
        scope: "users",
        title: t("dialog.error"),
        body: t("chgpw.mismatch"),
        tone: "error"
      };
      render();
      return;
    }

    if (draft.current !== currentUser.password) {
      state.inlineMessage = {
        scope: "users",
        title: t("dialog.error"),
        body: t("chgpw.wrong_old"),
        tone: "error"
      };
      render();
      return;
    }

    currentUser.password = draft.next;
    state.passwordDraft = createPasswordDraft();
    state.usersFocusTarget = null;
    state.inlineMessage = null;
    assignStatus("status.password_changed");
    showNoticeModal({ titleKey: "dialog.success", bodyKey: "chgpw.success", tone: "info" });
  }

  function saveSettingsDraft() {
    const draft = state.settingsDraft;
    if (!draft) return;

    if (draft.use_putty) {
      const path = String(draft.putty_path || "").trim();
      if (!path) {
        state.inlineMessage = {
          scope: "settings",
          title: "PuTTY",
          body: t("settings.putty_missing"),
          tone: "error"
        };
        render();
        return;
      }
      if (!/\.exe$/i.test(path)) {
        state.inlineMessage = {
          scope: "settings",
          title: t("settings.putty_not_found_title"),
          body: t("settings.putty_not_found", { path }),
          tone: "error"
        };
        render();
        return;
      }
    }

    state.settings = clone(draft);
    state.inlineMessage = null;
    if (!state.settings.debug_mode) {
      state.debug.windowOpen = false;
    }
    if (window.neoSite?.applyTheme) {
      window.neoSite.applyTheme(state.settings.theme);
    } else {
      document.documentElement.setAttribute("data-theme", state.settings.theme);
      try {
        localStorage.setItem("nswm.theme", state.settings.theme);
      } catch {
        /* no-op */
      }
    }
    assignStatus("status.settings_saved");
    state.pageMode = "connections";
    state.settingsDraft = null;
    state.panel = { mode: "none", connectionId: null };
    state.selectedConnectionId = null;
    render();
  }

  function downloadDebugLog() {
    const content = state.debug.entries
      .map((entry) => `[${entry.timestamp}] [${entry.level.toUpperCase()}] ${entry.message}`)
      .join("\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "neosshwinmanager-debug.log";
    link.click();
    URL.revokeObjectURL(url);
    pushDebugLog("info", t("debug.log_saved"));
    render();
  }

  function runDebugCpuTest() {
    pushDebugLog("info", "Starte simulierten CPU-/Entschlüsselungstest...");
    state.connections.forEach((connection) => {
      pushDebugLog(
        connection.password ? "info" : "warning",
        connection.password
          ? `✓ ${connection.name}: Passwort erfolgreich validiert.`
          : `⚠ ${connection.name}: Kein gespeichertes Passwort vorhanden.`
      );
    });
    pushDebugLog("info", t("debug.cpu_test"));
  }

  function promptLogout() {
    state.modal = {
      type: "confirm",
      titleKey: "logout.title",
      bodyKey: "logout.confirm",
      confirmAction: { type: "logout" },
      confirmVariant: "danger"
    };
    render();
  }

  function requestDelete(connId) {
    const connection = getConnection(connId);
    if (!connection) {
      assignStatus("delete.select_one");
      render();
      return;
    }

    state.modal = {
      type: "confirm",
      titleKey: "delete.title",
      bodyKey: connection.mounted ? "delete.mounted_confirm" : "delete.confirm",
      bodyParams: { name: connection.name },
      confirmAction: { type: "delete-connection", connId },
      confirmVariant: "danger"
    };
    render();
  }

  function handleCloudButton(connId) {
    const connection = getConnection(connId);
    if (!connection || connection.loading) return;
    if (connection.mounted) {
      assignStatus("status.opening_explorer", { path: `${connection.drive_letter}\\` });
      render();
      return;
    }
    requestResolvedAction(connId, "mount");
  }

  function toggleMount(connId) {
    const connection = getConnection(connId);
    if (!connection || connection.loading) return;
    if (connection.mounted) {
      startUnmount(connId);
      return;
    }
    requestResolvedAction(connId, "mount");
  }

  function requestResolvedAction(connId, nextAction) {
    const connection = getConnection(connId);
    if (!connection || connection.loading) return;

    if (connection.auth_method !== "ask") {
      executeResolvedAction(connId, nextAction);
      return;
    }

    if (!connection.key_path) {
      state.modal = {
        type: "password-prompt",
        connectionId: connId,
        nextAction,
        value: ""
      };
      render();
      return;
    }

    state.modal = {
      type: "auth-choice",
      connectionId: connId,
      nextAction,
      selectedMethod: connection.password ? "password" : "key"
    };
    render();
  }

  function executeResolvedAction(connId, nextAction) {
    if (nextAction === "ssh") {
      openSshPopup(connId);
      return;
    }
    startMount(connId);
  }

  function startMount(connId) {
    const connection = getConnection(connId);
    if (!connection) return;

    connection.loading = "connect";
    state.modal = null;
    assignStatus("status.connecting", { name: connection.name, drive: connection.drive_letter });
    render();

    window.setTimeout(() => {
      const freshConnection = getConnection(connId);
      if (!freshConnection) return;
      freshConnection.loading = null;
      if (freshConnection.mountFailuresRemaining > 0) {
        freshConnection.mountFailuresRemaining -= 1;
        state.modal = {
          type: "mount-failed",
          connectionId: connId,
          details: `ssh: connect to host ${freshConnection.host} port ${freshConnection.port}: Connection timed out`
        };
        render();
        return;
      }
      freshConnection.mounted = true;
      assignStatus("status.connected", { name: freshConnection.name, drive: freshConnection.drive_letter });
      render();
    }, 850);
  }

  function startUnmount(connId) {
    const connection = getConnection(connId);
    if (!connection) return;

    connection.loading = "disconnect";
    assignStatus("status.disconnecting", { drive: connection.drive_letter });
    render();

    window.setTimeout(() => {
      const freshConnection = getConnection(connId);
      if (!freshConnection) return;
      freshConnection.loading = null;
      freshConnection.mounted = false;
      assignStatus("status.disconnected", { name: freshConnection.name });
      render();
    }, 620);
  }

  function openSshPopup(connId) {
    const connection = getConnection(connId);
    if (!connection) return;
    const backend = state.settings.use_putty ? "PuTTY" : "SSH";
    state.popup = { connectionId: connId, backend };
    state.modal = null;
    assignStatus("status.ssh_started", { backend, name: connection.name });
    render();
  }

  function deleteConnection(connId) {
    const connection = getConnection(connId);
    if (!connection) return;

    state.connections = state.connections.filter((entry) => entry.id !== connId);
    state.panel = { mode: "none", connectionId: null };
    state.selectedConnectionId = null;
    state.connectionDraft = null;
    assignStatus("status.connection_deleted", { name: connection.name });
    render();
  }

  function performLogout() {
    state.connections.forEach((connection) => {
      connection.mounted = false;
      connection.loading = null;
    });
    state.loggedIn = false;
    state.pageMode = "connections";
    state.panel = { mode: "none", connectionId: null };
    state.selectedConnectionId = null;
    state.currentUserId = null;
    state.connectionDraft = null;
    state.settingsDraft = null;
    state.userDraft = createUserDraft();
    state.passwordDraft = createPasswordDraft();
    state.usersFocusTarget = null;
    state.modal = null;
    state.popup = null;
    state.inlineMessage = null;
    state.loginErrorKey = null;
    state.loginDraft = { username: state.currentUser, password: "" };
    assignStatus("app.ready");
    render();
  }

  function submitLogin() {
    const username = String(state.loginDraft.username || "").trim();
    const password = String(state.loginDraft.password || "").trim();
    if (!username || !password) {
      state.loginErrorKey = "login.fill_all";
      render();
      return;
    }

    const matchingUser = state.users.find((user) => user.username.toLowerCase() === username.toLowerCase()) || null;
    state.currentUser = matchingUser?.username || username;
    state.currentUserId = matchingUser?.id || null;
    state.loggedIn = true;
    state.loginErrorKey = null;
    state.loginDraft.password = "";
    state.pageMode = "connections";
    state.selectedConnectionId = state.connections[0]?.id || null;
    state.panel = state.connections[0] ? { mode: "info", connectionId: state.connections[0].id } : { mode: "none", connectionId: null };
    assignStatus("app.ready");
    render();
  }

  function refreshSystemInfo(connId) {
    const connection = getConnection(connId);
    if (!connection || connection.sysinfoLoading) return;
    connection.sysinfoLoading = true;
    render();

    window.setTimeout(() => {
      const freshConnection = getConnection(connId);
      if (!freshConnection) return;
      const info = freshConnection.systemInfo;
      info.cpuPct = clamp(info.cpuPct + randomBetween(-8, 11), 4, 82);
      info.ramUsedGb = clamp(Number((info.ramUsedGb + randomBetween(-0.4, 0.7)).toFixed(1)), 0.8, info.ramTotalGb - 0.2);
      info.diskUsedGb = clamp(Math.round(info.diskUsedGb + randomBetween(-6, 8)), Math.round(info.diskTotalGb * 0.15), info.diskTotalGb - 12);
      info.tempC = clamp(Math.round(info.tempC + randomBetween(-2, 3)), 30, 72);
      info.processes = clamp(Math.round(info.processes + randomBetween(-18, 21)), 80, 420);
      info.load = formatLoad(info.cpuPct);
      info.lastSeen = "00:00";
      freshConnection.sysinfoLoading = false;
      render();
    }, 550);
  }

  function randomBetween(min, max) {
    return Math.random() * (max - min) + min;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function formatLoad(cpuPct) {
    const one = (cpuPct / 33).toFixed(2);
    const five = (cpuPct / 42).toFixed(2);
    const fifteen = (cpuPct / 50).toFixed(2);
    return `${one} ${five} ${fifteen}`;
  }

  function showNoticeModal(config) {
    state.modal = {
      type: "notice",
      tone: config.tone || "info",
      titleKey: config.titleKey,
      titleText: config.titleText,
      bodyKey: config.bodyKey,
      bodyText: config.bodyText,
      bodyParams: config.bodyParams || {}
    };
    render();
  }

  function confirmModal() {
    if (!state.modal) return;

    if (state.modal.type === "notice") {
      state.modal = null;
      render();
      return;
    }

    if (state.modal.type === "confirm") {
      const action = state.modal.confirmAction;
      state.modal = null;
      if (action?.type === "logout") {
        performLogout();
      } else if (action?.type === "delete-connection") {
        deleteConnection(action.connId);
      } else if (action?.type === "delete-user") {
        deleteUser(action.userId);
      } else if (action?.type === "reset-user-password") {
        resetUserPassword(action.userId);
      }
      return;
    }

    if (state.modal.type === "auth-choice") {
      const modal = state.modal;
      const connection = getConnection(modal.connectionId);
      if (!connection) {
        state.modal = null;
        render();
        return;
      }
      if (modal.selectedMethod === "password" && !connection.password) {
        state.modal = {
          type: "password-prompt",
          connectionId: modal.connectionId,
          nextAction: modal.nextAction,
          value: ""
        };
        render();
        return;
      }
      state.modal = null;
      executeResolvedAction(modal.connectionId, modal.nextAction);
      return;
    }

    if (state.modal.type === "password-prompt") {
      const modal = state.modal;
      state.modal = null;
      executeResolvedAction(modal.connectionId, modal.nextAction);
      return;
    }

    if (state.modal.type === "mount-failed") {
      const connection = getConnection(state.modal.connectionId);
      assignStatus("status.connect_failed", { name: connection?.name || "?" });
      state.modal = null;
      render();
    }
  }

  function cancelModal() {
    if (!state.modal) return;
    if (state.modal.type === "mount-failed") {
      const connection = getConnection(state.modal.connectionId);
      assignStatus("status.connect_failed", { name: connection?.name || "?" });
    }
    state.modal = null;
    render();
  }

  function retryModal() {
    if (!state.modal || state.modal.type !== "mount-failed") return;
    const connId = state.modal.connectionId;
    state.modal = null;
    requestResolvedAction(connId, "mount");
  }

  function render() {
    root.innerHTML = `<div class="sim-app">${state.loggedIn ? renderLoggedIn() : renderLoggedOut()}</div>`;
    applyLayoutVars();
    focusInteractiveInput();
    syncDebugWindow();
  }

  function focusInteractiveInput() {
    window.requestAnimationFrame(() => {
      if (!state.loggedIn) {
        const loginField = root.querySelector("[data-login-field='password']");
        loginField?.focus();
        return;
      }
      if (state.pageMode === "users" && state.usersFocusTarget === "password") {
        const field = root.querySelector("[data-password-field='current']");
        field?.closest(".sim-section-card")?.scrollIntoView({ block: "center", behavior: "smooth" });
        field?.focus();
        state.usersFocusTarget = null;
        return;
      }
      if (state.modal?.type === "password-prompt") {
        root.querySelector("[data-modal-field='password']")?.focus();
      }
    });
  }

  function renderLoggedIn() {
    return `
      <div class="sim-window-titlebar">
        <div class="sim-titlebar-left">
          <span class="sim-window-dots"><span></span><span></span><span></span></span>
          <span class="sim-window-title">NEO SSH-Win Manager — ${escapeHtml(state.currentUser)}@${escapeHtml(state.workstation)}</span>
        </div>
        <div class="sim-titlebar-right">
          <span class="sim-window-tag">frontend-only</span>
        </div>
      </div>
      <div class="sim-shell">
        ${renderSidebar()}
        <div class="sim-main">
          ${state.pageMode === "settings" ? renderSettingsView() : state.pageMode === "users" ? renderUsersView() : renderConnectionsView()}
        </div>
      </div>
      <div class="sim-statusbar">
        <div class="sim-status-left">
          <span class="sim-status-dot"></span>
          <span class="sim-status-text">${escapeHtml(t(state.status.key, state.status.params))}</span>
        </div>
        <div class="sim-status-right">
          <span>${escapeHtml(renderMountCountLabel())}</span>
          <span>${escapeHtml(state.version)}</span>
        </div>
      </div>
      ${state.debug.windowOpen ? renderDebugWindow() : ""}
      ${state.popup ? renderPopup() : ""}
      ${state.modal ? renderModal() : ""}
    `;
  }

  function renderLoggedOut() {
    return `
      <div class="sim-window-titlebar">
        <div class="sim-titlebar-left">
          <span class="sim-window-dots"><span></span><span></span><span></span></span>
          <span class="sim-window-title">${escapeHtml(t("login.title"))}</span>
        </div>
      </div>
      <div class="sim-login-shell">
        <div class="sim-login-card">
          <div class="sim-login-mark">${ICONS.lock}</div>
          <h2 class="sim-login-title">${escapeHtml(t("login.please_sign_in"))}</h2>
          <p class="sim-login-copy">NEO SSH-Win Manager</p>
          ${state.loginErrorKey ? renderInlineMessage({ title: t("dialog.warning"), body: t(state.loginErrorKey), tone: "error" }) : ""}
          <div class="sim-form-grid">
            ${renderInputField("login.username", "loginDraft", "username", state.loginDraft.username, { loginField: "username" })}
            ${renderInputField("login.password", "loginDraft", "password", state.loginDraft.password, { loginField: "password", type: "password" })}
          </div>
          <div class="sim-form-footer" style="padding-left:0; padding-right:0; border-top:0; background:transparent;">
            <div class="sim-footer-actions" style="width:100%; margin-left:0;">
              <button type="button" class="sim-btn sim-btn-primary" data-action="login-submit">${escapeHtml(t("login.sign_in"))}</button>
            </div>
          </div>
          <p class="sim-login-note">${escapeHtml(t("sim.login.note"))}</p>
        </div>
      </div>
      ${state.modal ? renderModal() : ""}
    `;
  }

  function renderSidebar() {
    return `
      <aside class="sim-sidebar">
        <div class="sim-side-group">
          <button type="button" class="sim-side-btn ${state.pageMode === "connections" ? "is-active" : ""}" data-action="nav-home" title="${escapeHtml(t("header.connections"))}">${ICONS.cloud}</button>
          <button type="button" class="sim-side-btn ${state.pageMode === "settings" ? "is-active" : ""}" data-action="nav-settings" title="${escapeHtml(t("main.settings"))}">${ICONS.settings}</button>
          ${isCurrentUserAdmin() ? `<button type="button" class="sim-side-btn ${state.pageMode === "users" ? "is-active" : ""}" data-action="nav-users" title="${escapeHtml(t("main.users"))}">${ICONS.users}</button>` : ""}
        </div>
        <div class="sim-sidebar-spacer"></div>
        <div class="sim-side-group">
          ${state.settings.debug_mode ? `<button type="button" class="sim-side-btn is-warning" data-action="nav-debug" title="${escapeHtml(t("main.debug"))}">${ICONS.bug}</button>` : ""}
          <button type="button" class="sim-side-btn is-danger" data-action="nav-logout" title="${escapeHtml(t("main.logout"))}">${ICONS.logout}</button>
        </div>
      </aside>
    `;
  }

  function renderDebugWindow() {
    return `
      <div class="sim-overlay sim-debug-overlay">
        <div class="sim-debug-surface">
          <div class="sim-debug-toolbar">
            <div class="sim-debug-copy">
              <div class="sim-debug-title-row">
                <span class="sim-status-dot"></span>
                <h3>${escapeHtml(t("debug.title"))}</h3>
              </div>
              <p>${escapeHtml(t("debug.subtitle"))}</p>
            </div>
            <div class="sim-debug-actions">
              <label class="sim-checkbox sim-checkbox-compact">
                <input type="checkbox" data-debug-field="autoScroll" ${state.debug.autoScroll ? "checked" : ""} />
                <span class="sim-checkbox-indicator${state.debug.autoScroll ? " is-checked" : ""}" aria-hidden="true"></span>
                <span>${escapeHtml(t("debug.autoscroll"))}</span>
              </label>
              <button type="button" class="sim-btn sim-btn-danger" data-action="debug-purge">${escapeHtml(t("settings.fix_ghosts"))}</button>
              <button type="button" class="sim-btn sim-btn-warning" data-action="debug-test-cpu">Test CPU</button>
              <button type="button" class="sim-btn" data-action="debug-clear">${escapeHtml(t("debug.clear"))}</button>
              <button type="button" class="sim-btn sim-btn-primary" data-action="debug-save">${escapeHtml(t("debug.save"))}</button>
              <button type="button" class="sim-icon-btn" data-action="debug-close" title="${escapeHtml(t("dialog.close"))}">${ICONS.close}</button>
            </div>
          </div>
          <div class="sim-debug-log" data-debug-log>
            ${state.debug.entries.map(renderDebugEntry).join("")}
          </div>
        </div>
      </div>
    `;
  }

  function renderDebugEntry(entry) {
    return `
      <div class="sim-debug-entry is-${escapeHtml(entry.level)}">
        <span class="sim-debug-entry-time">${escapeHtml(entry.timestamp)}</span>
        <span class="sim-debug-entry-level">${escapeHtml(entry.level.toUpperCase())}</span>
        <span class="sim-debug-entry-message">${escapeHtml(entry.message)}</span>
      </div>
    `;
  }

  function renderConnectionsView() {
    return `
      <div class="sim-home-view">
        <section class="sim-list-panel">
          <div class="sim-panel-head">
            <div>
              <p class="sim-panel-kicker">${escapeHtml(t("header.connections"))}</p>
              <h2>${escapeHtml(t("header.connections"))}</h2>
            </div>
            <div class="sim-head-actions">
              <button type="button" class="sim-icon-btn" data-action="add-connection" title="${escapeHtml(t("main.add_connection"))}">${ICONS.plus}</button>
              ${state.connections.length ? `<span class="sim-toolbar-pill">${escapeHtml(renderBadgeText())}</span>` : ""}
            </div>
          </div>
          <div class="sim-list">
            ${state.connections.length ? state.connections.map(renderConnectionRow).join("") : renderEmptyState()}
          </div>
        </section>
        <div class="sim-splitter" data-split-handle role="separator" aria-orientation="vertical" title="Resize panels"></div>
        <section class="sim-right-panel">
          ${renderRightPanel()}
        </section>
      </div>
    `;
  }

  function renderUsersView() {
    const currentUser = getCurrentUser();
    const adminCount = state.users.filter((user) => user.is_admin).length;

    return `
      <div class="sim-users-view">
        <div class="sim-panel-head">
          <div>
            <p class="sim-panel-kicker">${escapeHtml(t("main.users"))}</p>
            <h2>${escapeHtml(t("users.title"))}</h2>
          </div>
          <div class="sim-head-actions">
            <button type="button" class="sim-icon-btn" data-action="nav-home" title="${escapeHtml(t("dialog.close"))}">${ICONS.close}</button>
          </div>
        </div>
        <div class="sim-panel-scroll">
          <div class="sim-users-body">
            ${state.inlineMessage?.scope === "users" ? renderInlineMessage(state.inlineMessage) : ""}
            <section class="sim-users-hero">
              <div>
                <p class="sim-panel-kicker">${escapeHtml(t("users.section.users"))}</p>
                <h3>${escapeHtml(t("dialog.lead.users"))}</h3>
              </div>
              <span class="sim-toolbar-pill">${escapeHtml(t("users.summary", { users: state.users.length, admins: adminCount }))}</span>
            </section>
            <div class="sim-users-grid">
              <section class="sim-section-card sim-users-list-card">
                <div class="sim-section-card-head">
                  <h3>${escapeHtml(t("users.section.users"))}</h3>
                  <span class="sim-toolbar-pill">${escapeHtml(state.currentUser)}</span>
                </div>
                <div class="sim-users-list">
                  ${state.users.map(renderUserRow).join("")}
                </div>
              </section>
              <div class="sim-users-stack">
                ${isCurrentUserAdmin() ? renderCreateUserCard() : ""}
                ${currentUser ? renderPasswordCard(currentUser) : ""}
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  function renderUserRow(user) {
    const isCurrent = user.id === state.currentUserId;
    const connectionCount = getUserConnectionCount(user.id);
    const connectionLabel = connectionCount === 1
      ? t("users.connections.one", { n: connectionCount })
      : t("users.connections.many", { n: connectionCount });

    return `
      <article class="sim-user-row ${isCurrent ? "is-current" : ""}">
        <div class="sim-user-avatar ${user.is_admin ? "is-admin" : ""}">${escapeHtml(user.username.slice(0, 2).toUpperCase())}</div>
        <div class="sim-user-copy">
          <div class="sim-user-line">
            <strong>${escapeHtml(user.username)}</strong>
            <span class="sim-user-badge ${user.is_admin ? "is-admin" : ""}">${escapeHtml(user.is_admin ? t("users.admin") : t("users.role.member"))}</span>
            ${isCurrent ? `<span class="sim-user-badge is-current">${escapeHtml(t("users.badge.you"))}</span>` : ""}
          </div>
          <p>${escapeHtml(connectionLabel)}</p>
        </div>
        <div class="sim-row-actions">
          ${isCurrent ? `<button type="button" class="sim-icon-btn" data-action="focus-change-password" title="${escapeHtml(t("users.tooltip.change_pw"))}">${ICONS.key}</button>` : `${isCurrentUserAdmin() ? `<button type="button" class="sim-icon-btn" data-action="request-reset-user" data-user-id="${escapeHtml(user.id)}" title="${escapeHtml(t("users.tooltip.reset_pw", { name: user.username }))}">${ICONS.refresh}</button>` : ""}<button type="button" class="sim-icon-btn is-danger" data-action="request-delete-user" data-user-id="${escapeHtml(user.id)}" title="${escapeHtml(t("users.tooltip.delete", { name: user.username }))}">${ICONS.trash}</button>`}
        </div>
      </article>
    `;
  }

  function renderCreateUserCard() {
    const draft = state.userDraft;
    return `
      <section class="sim-section-card">
        <div class="sim-section-card-head">
          <h3>${escapeHtml(t("users.section.new"))}</h3>
        </div>
        <div class="sim-form-grid">
          ${renderUserField("users.placeholder.username", "username", draft.username)}
          ${renderUserField("users.placeholder.password", "password", draft.password, { type: "password" })}
          ${renderUserCheckbox("is_admin", t("users.admin"), draft.is_admin)}
          <div class="sim-inline-actions">
            <button type="button" class="sim-btn sim-btn-primary" data-action="save-user">${escapeHtml(t("users.create"))}</button>
          </div>
        </div>
      </section>
    `;
  }

  function renderPasswordCard(currentUser) {
    const draft = state.passwordDraft;
    return `
      <section class="sim-section-card">
        <div class="sim-section-card-head">
          <h3>${escapeHtml(t("users.section.password"))}</h3>
          <span class="sim-toolbar-pill">${escapeHtml(currentUser.username)}</span>
        </div>
        <div class="sim-form-grid">
          ${renderPasswordField("chgpw.current", "current", draft.current)}
          ${renderPasswordField("chgpw.new", "next", draft.next)}
          ${renderPasswordField("chgpw.confirm", "confirm", draft.confirm)}
          <div class="sim-inline-actions">
            <button type="button" class="sim-btn sim-btn-primary" data-action="save-password-change">${escapeHtml(t("dialog.save"))}</button>
          </div>
        </div>
      </section>
    `;
  }

  function renderEmptyState() {
    return `
      <div class="sim-empty-state">
        <h3>${escapeHtml(t("app.no_connections"))}</h3>
        <p>${escapeHtml(t("sim.empty.body"))}</p>
      </div>
    `;
  }

  function renderRightPanel() {
    const connection = getConnection(state.panel.connectionId);

    if (state.panel.mode === "info" && connection) {
      return renderInfoPanel(connection);
    }

    if (state.panel.mode === "sysinfo" && connection) {
      return renderSysinfoPanel(connection);
    }

    if ((state.panel.mode === "edit" || state.panel.mode === "add") && state.connectionDraft) {
      return renderConnectionFormPanel();
    }

    return `
      <div class="sim-panel-scroll">
        <div class="sim-panel-body sim-empty-state">
          <h3>${escapeHtml(t("sim.empty.title"))}</h3>
          <p>${escapeHtml(t("sim.empty.body"))}</p>
        </div>
      </div>
    `;
  }

  function renderConnectionRow(connection) {
    const isSelected = state.selectedConnectionId === connection.id && state.panel.mode !== "none";
    const rowClasses = ["sim-row"];
    if (connection.mounted) rowClasses.push("is-mounted");
    if (isSelected) rowClasses.push("is-selected");
    if (connection.loading) rowClasses.push("is-loading");

    const loadingPill = connection.loading
      ? `<span class="sim-loading-pill"><span class="sim-spinner"></span>${escapeHtml(t(connection.loading === "connect" ? "card.loading.connect" : "card.loading.disconnect"))}</span>`
      : `
        <button type="button" class="sim-icon-btn sim-info-btn" data-action="open-sysinfo" data-conn-id="${escapeHtml(connection.id)}" title="${escapeHtml(t("card.tooltip.info"))}">i</button>
        <button type="button" class="sim-icon-btn" data-action="edit-connection" data-conn-id="${escapeHtml(connection.id)}" title="${escapeHtml(t(connection.mounted ? "card.tooltip.edit_locked" : "card.tooltip.edit"))}">${ICONS.edit}</button>
        <button type="button" class="sim-icon-btn" data-action="open-ssh" data-conn-id="${escapeHtml(connection.id)}" title="${escapeHtml(t("card.tooltip.ssh"))}">${ICONS.terminal}</button>
        <button type="button" class="sim-toggle-btn" data-action="toggle-mount" data-conn-id="${escapeHtml(connection.id)}" title="${escapeHtml(t(connection.mounted ? "card.tooltip.mount_on" : "card.tooltip.mount_off"))}">${connection.mounted ? ICONS.minus : ICONS.arrowRight}</button>
      `;

    return `
      <article class="${rowClasses.join(" ")}" data-connection-row="${escapeHtml(connection.id)}">
        <button type="button" class="sim-row-icon cloud" data-action="open-path" data-conn-id="${escapeHtml(connection.id)}" title="${escapeHtml(t(connection.mounted ? "card.tooltip.open_path" : "card.tooltip.mount_off"))}">${ICONS.cloud}</button>
        <div class="sim-conn-meta">
          <div class="sim-conn-name">${escapeHtml(connection.name)}</div>
          <div class="sim-conn-host">${escapeHtml(`${connection.user}@${connection.host}:${connection.remote_path}`)}</div>
        </div>
        <span class="sim-drive-chip">${escapeHtml(connection.drive_letter)}</span>
        <div class="sim-row-actions">${loadingPill}</div>
      </article>
    `;
  }

  function renderInfoPanel(connection) {
    const authMap = {
      password: t("addedit.auth.password"),
      key: t("addedit.auth.key"),
      ask: t("addedit.auth.ask")
    };

    const items = [
      renderInfoItem(t("addedit.label.name"), connection.name),
      renderInfoItem(t("addedit.label.host"), connection.host, true),
      renderInfoItem(t("addedit.label.user"), connection.user, true),
      renderInfoItem(t("addedit.label.port"), String(connection.port), true)
    ];

    const pathItems = [
      renderInfoItem(t("addedit.label.path"), connection.remote_path, true),
      renderInfoItem(t("addedit.label.drive"), connection.drive_letter, true)
    ];

    const authItems = [
      renderInfoItem(t("addedit.label.method"), authMap[connection.auth_method] || connection.auth_method)
    ];

    if (connection.password) {
      authItems.push(renderInfoItem(t("addedit.label.password"), "••••••••"));
    }
    if (connection.key_path) {
      authItems.push(renderInfoItem(t("addedit.label.key"), connection.key_path, true));
    }

    const cliItems = connection.cli_access_enabled
      ? `
        <div class="sim-section-label">${escapeHtml(t("addedit.section.cli"))}</div>
        <div class="sim-info-list">
          ${renderInfoItem(t("addedit.cli.label"), connection.cli_access_key || t("addedit.cli.none"), true)}
        </div>
      `
      : "";

    return `
      <div class="sim-panel-head">
        <div>
          <p class="sim-panel-kicker">${escapeHtml(connection.name)}</p>
          <h2>${escapeHtml(connection.name.toUpperCase())}</h2>
        </div>
        <div class="sim-head-actions">
          <button type="button" class="sim-icon-btn" data-action="edit-connection" data-conn-id="${escapeHtml(connection.id)}" title="${escapeHtml(t(connection.mounted ? "card.tooltip.edit_locked" : "card.tooltip.edit"))}">${ICONS.edit}</button>
          <button type="button" class="sim-icon-btn is-danger" data-action="delete-connection" data-conn-id="${escapeHtml(connection.id)}" title="${escapeHtml(t("main.delete"))}">${ICONS.trash}</button>
          <button type="button" class="sim-icon-btn" data-action="panel-close" title="${escapeHtml(t("dialog.close"))}">${ICONS.close}</button>
        </div>
      </div>
      <div class="sim-panel-scroll">
        <div class="sim-panel-body">
          ${state.inlineMessage?.scope === "connection" ? renderInlineMessage(state.inlineMessage) : ""}
          <div class="sim-status-row">
            <span class="sim-status-chip ${connection.mounted ? "is-mounted" : ""}"><i></i>${escapeHtml(t(connection.mounted ? "sim.info.connected" : "sim.info.disconnected"))}</span>
            <span class="sim-drive-chip">${escapeHtml(connection.drive_letter)}</span>
          </div>
          <div class="sim-section-label">${escapeHtml(t("addedit.section.general"))}</div>
          <div class="sim-info-list">${items.join("")}</div>
          <div class="sim-section-label">${escapeHtml(t("addedit.section.path"))}</div>
          <div class="sim-info-list">${pathItems.join("")}</div>
          <div class="sim-section-label">${escapeHtml(t("addedit.section.auth"))}</div>
          <div class="sim-info-list">${authItems.join("")}</div>
          ${cliItems}
        </div>
      </div>
    `;
  }

  function renderInfoItem(label, value, mono) {
    return `
      <div class="sim-info-item">
        <strong>${escapeHtml(label)}</strong>
        <span class="${mono ? "is-mono" : ""}">${escapeHtml(value)}</span>
      </div>
    `;
  }

  function renderSysinfoPanel(connection) {
    const info = connection.systemInfo;
    const ramPct = Math.round((info.ramUsedGb / info.ramTotalGb) * 100);
    const diskPct = Math.round((info.diskUsedGb / info.diskTotalGb) * 100);

    return `
      <div class="sim-panel-head">
        <div>
          <p class="sim-panel-kicker">${escapeHtml(t("card.tooltip.info"))}</p>
          <h2>${escapeHtml(connection.name.toUpperCase())}</h2>
        </div>
        <div class="sim-head-actions">
          <button type="button" class="sim-btn" data-action="sysinfo-refresh" data-conn-id="${escapeHtml(connection.id)}">${escapeHtml(t("sysinfo.refresh"))}</button>
          <button type="button" class="sim-icon-btn" data-action="panel-close" title="${escapeHtml(t("dialog.close"))}">${ICONS.close}</button>
        </div>
      </div>
      <div class="sim-panel-scroll">
        <div class="sim-panel-body">
          ${connection.sysinfoLoading ? `<p class="sim-login-copy">${escapeHtml(t("sysinfo.loading"))}</p>` : `
            <div class="sim-sys-grid">
              <div class="sim-sys-card">
                <h3>${escapeHtml(t("sysinfo.host"))}</h3>
                <div class="sim-sys-meta"><span>${escapeHtml(info.hostname)}</span><span>${escapeHtml(info.uptime)}</span></div>
                <div class="sim-info-list">
                  ${renderInfoItem(t("sysinfo.os"), info.os)}
                  ${renderInfoItem(t("sysinfo.ip"), info.ip, true)}
                </div>
              </div>
              <div class="sim-sys-card">
                <h3>${escapeHtml(t("sysinfo.cpu"))}</h3>
                <div class="sim-sys-meta"><span>${escapeHtml(info.cpuModel)}</span><span>${escapeHtml(info.cpuPct + "%")}</span></div>
                <div class="sim-progress"><span style="width:${escapeHtml(String(info.cpuPct))}%"></span></div>
                <p class="sim-form-hint">${escapeHtml(t("sysinfo.cores_suffix", { n: info.cpuCores }))} · ${escapeHtml(t("sysinfo.load"))}: ${escapeHtml(info.load)}</p>
              </div>
              <div class="sim-sys-card">
                <h3>${escapeHtml(t("sysinfo.ram"))}</h3>
                <div class="sim-sys-meta"><span>${escapeHtml(`${info.ramUsedGb.toFixed(1)} / ${info.ramTotalGb} GB`)}</span><span>${escapeHtml(ramPct + "%")}</span></div>
                <div class="sim-progress"><span style="width:${escapeHtml(String(ramPct))}%"></span></div>
              </div>
              <div class="sim-sys-card">
                <h3>${escapeHtml(t("sysinfo.disk"))}</h3>
                <div class="sim-sys-meta"><span>${escapeHtml(`${info.diskUsedGb} / ${info.diskTotalGb} GB`)}</span><span>${escapeHtml(diskPct + "%")}</span></div>
                <div class="sim-progress"><span style="width:${escapeHtml(String(diskPct))}%"></span></div>
              </div>
              <div class="sim-sys-card">
                <h3>${escapeHtml(t("sysinfo.uptime"))}</h3>
                <div class="sim-info-list">
                  ${renderInfoItem(t("sysinfo.temp"), `${info.tempC} °C`, true)}
                  ${renderInfoItem(t("sysinfo.users"), String(info.users), true)}
                  ${renderInfoItem(t("sysinfo.processes"), String(info.processes), true)}
                </div>
              </div>
            </div>
          `}
        </div>
      </div>
    `;
  }

  function renderConnectionFormPanel() {
    const draft = state.connectionDraft;
    const isEdit = state.panel.mode === "edit";

    return `
      <div class="sim-panel-head">
        <div>
          <p class="sim-panel-kicker">${escapeHtml(isEdit ? t("addedit.edit_title") : t("addedit.add_title"))}</p>
          <h2>${escapeHtml((isEdit ? t("addedit.edit_title") : t("addedit.add_title")).toUpperCase())}</h2>
        </div>
        <div class="sim-head-actions">
          <button type="button" class="sim-icon-btn" data-action="panel-close" title="${escapeHtml(t("dialog.close"))}">${ICONS.close}</button>
        </div>
      </div>
      <div class="sim-panel-scroll">
        <div class="sim-form-body">
          ${state.inlineMessage?.scope === "connection" ? renderInlineMessage(state.inlineMessage) : ""}
          <div class="sim-section-label">${escapeHtml(t("addedit.section.general"))}</div>
          <div class="sim-form-grid">
            ${renderConnectionField("addedit.label.name", "name", draft.name, { placeholder: t("addedit.placeholder.name") })}
            ${renderConnectionField("addedit.label.host", "host", draft.host, { placeholder: "192.168.1.10" })}
          </div>
          <div class="sim-form-grid split">
            ${renderConnectionField("addedit.label.user", "user", draft.user, { placeholder: "root" })}
            ${renderConnectionField("addedit.label.port", "port", draft.port, { type: "number" })}
          </div>
          <div class="sim-section-label">${escapeHtml(t("addedit.section.path"))}</div>
          <div class="sim-form-grid split">
            ${renderConnectionField("addedit.label.path", "remote_path", draft.remote_path, { placeholder: "/" })}
            ${renderDriveSelect(draft)}
          </div>
          <div class="sim-section-label">${escapeHtml(t("addedit.section.auth"))}</div>
          <div class="sim-form-grid">
            ${renderConnectionSelect("addedit.label.method", "auth_method", draft.auth_method, [
              ["password", t("addedit.auth.password")],
              ["key", t("addedit.auth.key")],
              ["ask", t("addedit.auth.ask")]
            ])}
            ${renderConnectionField("addedit.label.password", "password", draft.password, { type: "password", placeholder: "••••••••" })}
            ${renderConnectionField("addedit.label.key", "key_path", draft.key_path, { placeholder: "C:\\Users\\user\\.ssh\\id_ed25519", mono: true })}
          </div>
          <div class="sim-section-label">${escapeHtml(t("addedit.section.cli"))}</div>
          <div class="sim-form-grid">
            ${renderConnectionCheckbox("cli_access_enabled", t("addedit.cli.enable"), draft.cli_access_enabled)}
            ${draft.cli_access_enabled ? `
              ${renderReadOnlyField(t("addedit.cli.label"), draft.cli_access_key || t("addedit.cli.none"), true)}
              <div class="sim-inline-actions">
                <button type="button" class="sim-btn" data-action="generate-cli-key">${escapeHtml(t("addedit.cli.generate"))}</button>
              </div>
            ` : ""}
          </div>
        </div>
      </div>
      <div class="sim-form-footer">
        <div class="sim-footer-actions">
          <button type="button" class="sim-btn" data-action="cancel-connection">${escapeHtml(t("dialog.cancel"))}</button>
          <button type="button" class="sim-btn sim-btn-primary" data-action="save-connection">${escapeHtml(t("dialog.save"))}</button>
        </div>
      </div>
    `;
  }

  function renderSettingsView() {
    const draft = state.settingsDraft || clone(state.settings);
    const languageOptions = [
      ["de", t("sim.language.de")],
      ["en", t("sim.language.en")]
    ];

    return `
      <div class="sim-settings-view">
        <div class="sim-panel-head">
          <div>
            <p class="sim-panel-kicker">${escapeHtml(t("main.settings"))}</p>
            <h2>${escapeHtml(t("settings.title"))}</h2>
          </div>
          <div class="sim-head-actions">
            <button type="button" class="sim-icon-btn" data-action="cancel-settings" title="${escapeHtml(t("dialog.close"))}">${ICONS.close}</button>
          </div>
        </div>
        <div class="sim-panel-scroll">
          <div class="sim-form-body">
            ${state.inlineMessage?.scope === "settings" ? renderInlineMessage(state.inlineMessage) : ""}
            <div class="sim-section-label">${escapeHtml(t("settings.section.language"))}</div>
            <div class="sim-form-grid split equal">
              ${renderSettingsSelect("settings.language.label", "language", draft.language, languageOptions)}
              ${renderSettingsSelect("settings.theme.label", "theme", draft.theme, [["dark", t("settings.theme.dark")], ["light", t("settings.theme.light")]])}
            </div>
            <p class="sim-form-hint">${escapeHtml(t("settings.language.restart"))}</p>
            <div class="sim-section-label">${escapeHtml(t("settings.section.general"))}</div>
            <div class="sim-form-grid">
              ${renderSettingsCheckbox("start_with_windows", t("settings.start_with_windows"), draft.start_with_windows)}
              ${renderSettingsCheckbox("minimize_to_tray", t("settings.minimize_to_tray"), draft.minimize_to_tray)}
              ${renderSettingsCheckbox("require_admin", t("settings.require_admin"), draft.require_admin)}
            </div>
            <div class="sim-section-label">${escapeHtml(t("settings.section.mount"))}</div>
            <div class="sim-form-grid split">
              ${renderSettingsField("settings.check_interval", "check_interval_seconds", draft.check_interval_seconds, { type: "number" })}
              <div></div>
            </div>
            <div class="sim-form-grid">
              ${renderSettingsCheckbox("auto_reconnect", t("settings.auto_reconnect"), draft.auto_reconnect)}
              ${renderSettingsCheckbox("auto_remount_on_lost", t("settings.auto_remount"), draft.auto_remount_on_lost)}
            </div>
            <div class="sim-section-label">${escapeHtml(t("settings.section.terminal"))}</div>
            <div class="sim-form-grid">
              ${renderSettingsCheckbox("use_putty", t("settings.use_putty"), draft.use_putty)}
              ${draft.use_putty ? `${renderSettingsField("settings.putty_path", "putty_path", draft.putty_path, { mono: true })}<p class="sim-form-hint">${escapeHtml(t("settings.putty_hint"))}</p>` : ""}
            </div>
            <div class="sim-section-label">${escapeHtml(t("settings.section.developer"))}</div>
            <div class="sim-form-grid">
              ${renderSettingsCheckbox("debug_mode", t("settings.debug_mode"), draft.debug_mode)}
            </div>
            ${draft.debug_mode ? `
              <div class="sim-section-label">${escapeHtml(t("settings.section.tools"))}</div>
              <div class="sim-inline-actions">
                <button type="button" class="sim-btn sim-btn-primary" data-action="settings-fix-ghosts">${escapeHtml(t("settings.fix_ghosts"))}</button>
                <button type="button" class="sim-btn" data-action="settings-restart-explorer">${escapeHtml(t("settings.restart_explorer"))}</button>
              </div>
            ` : ""}
          </div>
        </div>
        <div class="sim-form-footer">
          <div class="sim-footer-actions">
            <button type="button" class="sim-btn" data-action="cancel-settings">${escapeHtml(t("dialog.cancel"))}</button>
            <button type="button" class="sim-btn sim-btn-primary" data-action="save-settings">${escapeHtml(t("dialog.save"))}</button>
          </div>
        </div>
      </div>
    `;
  }

  function renderInputField(labelKey, scope, field, value, options) {
    const inputType = options?.type || "text";
    const placeholder = options?.placeholder ? ` placeholder="${escapeHtml(options.placeholder)}"` : "";
    const loginData = options?.loginField ? ` data-login-field="${escapeHtml(options.loginField)}"` : "";
    const extraClass = options?.mono ? " is-mono" : "";
    return `
      <label class="sim-field">
        <span>${escapeHtml(t(labelKey))}</span>
        <input class="sim-input${extraClass}" type="${escapeHtml(inputType)}" value="${escapeHtml(value)}"${placeholder}${loginData} />
      </label>
    `;
  }

  function renderConnectionField(labelKey, field, value, options) {
    const inputType = options?.type || "text";
    const placeholder = options?.placeholder ? ` placeholder="${escapeHtml(options.placeholder)}"` : "";
    const extraClass = options?.mono ? " is-mono" : "";
    return `
      <label class="sim-field">
        <span>${escapeHtml(t(labelKey))}</span>
        <input class="sim-input${extraClass}" type="${escapeHtml(inputType)}" data-connection-field="${escapeHtml(field)}" value="${escapeHtml(value)}"${placeholder} />
      </label>
    `;
  }

  function renderConnectionSelect(labelKey, field, value, options) {
    return `
      <label class="sim-field is-select">
        <span>${escapeHtml(t(labelKey))}</span>
        <select class="sim-select" data-connection-field="${escapeHtml(field)}">
          ${options.map(([optionValue, optionLabel]) => `<option value="${escapeHtml(optionValue)}" ${optionValue === value ? "selected" : ""}>${escapeHtml(optionLabel)}</option>`).join("")}
        </select>
      </label>
    `;
  }

  function renderDriveSelect(draft) {
    const currentId = state.panel.mode === "edit" ? state.panel.connectionId : null;
    const options = Array.from(new Set([draft.drive_letter, ...DRIVE_POOL.filter((letter) => letter === draft.drive_letter || letter === nextAvailableDriveLetter(currentId) || !state.connections.some((connection) => connection.id !== currentId && connection.drive_letter === letter))]));
    return renderConnectionSelect("addedit.label.drive", "drive_letter", draft.drive_letter, options.map((letter) => [letter, letter]));
  }

  function renderConnectionCheckbox(field, label, checked) {
    return `
      <label class="sim-checkbox">
        <input type="checkbox" data-connection-field="${escapeHtml(field)}" ${checked ? "checked" : ""} />
        <span class="sim-checkbox-indicator${checked ? " is-checked" : ""}" aria-hidden="true"></span>
        <span>${escapeHtml(label)}</span>
      </label>
    `;
  }

  function renderUserField(labelKey, field, value, options) {
    const inputType = options?.type || "text";
    return `
      <label class="sim-field">
        <span>${escapeHtml(t(labelKey))}</span>
        <input class="sim-input" type="${escapeHtml(inputType)}" data-user-field="${escapeHtml(field)}" value="${escapeHtml(value)}" />
      </label>
    `;
  }

  function renderUserCheckbox(field, label, checked) {
    return `
      <label class="sim-checkbox">
        <input type="checkbox" data-user-field="${escapeHtml(field)}" ${checked ? "checked" : ""} />
        <span class="sim-checkbox-indicator${checked ? " is-checked" : ""}" aria-hidden="true"></span>
        <span>${escapeHtml(label)}</span>
      </label>
    `;
  }

  function renderPasswordField(labelKey, field, value) {
    return `
      <label class="sim-field">
        <span>${escapeHtml(t(labelKey))}</span>
        <input class="sim-input" type="password" data-password-field="${escapeHtml(field)}" value="${escapeHtml(value)}" />
      </label>
    `;
  }

  function renderReadOnlyField(label, value, mono) {
    return `
      <label class="sim-field">
        <span>${escapeHtml(label)}</span>
        <input class="sim-input${mono ? " is-mono" : ""}" type="text" value="${escapeHtml(value)}" readonly />
      </label>
    `;
  }

  function renderSettingsField(labelKey, field, value, options) {
    const type = options?.type || "text";
    const extraClass = options?.mono ? " is-mono" : "";
    return `
      <label class="sim-field">
        <span>${escapeHtml(t(labelKey))}</span>
        <input class="sim-input${extraClass}" type="${escapeHtml(type)}" data-settings-field="${escapeHtml(field)}" value="${escapeHtml(value)}" />
      </label>
    `;
  }

  function renderSettingsSelect(labelKey, field, value, options) {
    return `
      <label class="sim-field is-select">
        <span>${escapeHtml(t(labelKey))}</span>
        <select class="sim-select" data-settings-field="${escapeHtml(field)}">
          ${options.map(([optionValue, optionLabel]) => `<option value="${escapeHtml(optionValue)}" ${optionValue === value ? "selected" : ""}>${escapeHtml(optionLabel)}</option>`).join("")}
        </select>
      </label>
    `;
  }

  function renderSettingsCheckbox(field, label, checked) {
    return `
      <label class="sim-checkbox">
        <input type="checkbox" data-settings-field="${escapeHtml(field)}" ${checked ? "checked" : ""} />
        <span class="sim-checkbox-indicator${checked ? " is-checked" : ""}" aria-hidden="true"></span>
        <span>${escapeHtml(label)}</span>
      </label>
    `;
  }

  function renderInlineMessage(message) {
    return `
      <div class="sim-inline-message ${message.tone === "info" ? "is-info" : ""}">
        <strong>${escapeHtml(message.title)}</strong>
        <p>${escapeHtml(message.body)}</p>
      </div>
    `;
  }

  function renderPopup() {
    const connection = getConnection(state.popup.connectionId);
    if (!connection) return "";
    return `
      <div class="sim-popup">
        <div class="sim-popup-head">
          <span>${escapeHtml(t("sim.popup.title", { name: connection.name }))}</span>
          <button type="button" class="sim-icon-btn" data-action="close-popup" title="${escapeHtml(t("dialog.close"))}">${ICONS.close}</button>
        </div>
        <div class="sim-popup-body">
          <p><span class="sim-popup-accent">$</span> ${escapeHtml(`${state.popup.backend === "PuTTY" ? "putty" : "ssh"} ${connection.user}@${connection.host} -p ${connection.port}`)}</p>
          <p>${escapeHtml(t("sim.popup.body"))}</p>
          <p>${escapeHtml(t("sim.popup.future"))}</p>
        </div>
      </div>
    `;
  }

  function resolveModalText(key, text, params) {
    if (text) return text;
    if (key) return t(key, params);
    return "";
  }

  function renderModal() {
    const modal = state.modal;
    if (!modal) return "";

    if (modal.type === "notice") {
      return `
        <div class="sim-overlay">
          <div class="sim-modal">
            <div class="sim-modal-head"><h3>${escapeHtml(resolveModalText(modal.titleKey, modal.titleText))}</h3></div>
            <div class="sim-modal-body">${escapeHtml(resolveModalText(modal.bodyKey, modal.bodyText, modal.bodyParams))}</div>
            <div class="sim-modal-actions">
              <button type="button" class="sim-btn sim-btn-primary" data-action="modal-confirm">${escapeHtml(t("dialog.ok"))}</button>
            </div>
          </div>
        </div>
      `;
    }

    if (modal.type === "confirm") {
      return `
        <div class="sim-overlay">
          <div class="sim-modal">
            <div class="sim-modal-head"><h3>${escapeHtml(t(modal.titleKey))}</h3></div>
            <div class="sim-modal-body">${escapeHtml(t(modal.bodyKey, modal.bodyParams))}</div>
            <div class="sim-modal-actions">
              <button type="button" class="sim-btn" data-action="modal-cancel">${escapeHtml(t("dialog.no"))}</button>
              <button type="button" class="sim-btn ${modal.confirmVariant === "danger" ? "sim-btn-danger" : "sim-btn-primary"}" data-action="modal-confirm">${escapeHtml(t("dialog.yes"))}</button>
            </div>
          </div>
        </div>
      `;
    }

    if (modal.type === "mount-failed") {
      const connection = getConnection(modal.connectionId);
      const body = `${t("mount.failed.main", { name: connection?.name || "?" })}${t("mount.failed.troubleshoot", { host: connection?.host || "?", port: connection?.port || "?" })}${t("mount.failed.details", { msg: modal.details })}`;
      return `
        <div class="sim-overlay">
          <div class="sim-modal">
            <div class="sim-modal-head"><h3>${escapeHtml(t("mount.failed.title"))}</h3></div>
            <div class="sim-modal-body">${escapeHtml(body)}</div>
            <div class="sim-modal-actions">
              <button type="button" class="sim-btn" data-action="modal-cancel">${escapeHtml(t("dialog.ok"))}</button>
              <button type="button" class="sim-btn sim-btn-primary" data-action="modal-retry">${escapeHtml(t("mount.failed.retry"))}</button>
            </div>
          </div>
        </div>
      `;
    }

    if (modal.type === "auth-choice") {
      const connection = getConnection(modal.connectionId);
      return `
        <div class="sim-overlay">
          <div class="sim-modal">
            <div class="sim-modal-head"><h3>${escapeHtml(t("addedit.auth.ask.title"))}</h3></div>
            <div class="sim-modal-body">
              ${escapeHtml(t("addedit.auth.ask.prompt", { name: connection?.name || "?" }))}
              <div class="sim-radio-group">
                <label class="sim-radio"><input type="radio" name="sim-auth-method" data-modal-field="auth-method" value="password" ${modal.selectedMethod === "password" ? "checked" : ""} /> <span>${escapeHtml(t("addedit.auth.password"))}</span></label>
                <label class="sim-radio"><input type="radio" name="sim-auth-method" data-modal-field="auth-method" value="key" ${modal.selectedMethod === "key" ? "checked" : ""} /> <span>${escapeHtml(t("addedit.auth.key"))}</span></label>
              </div>
            </div>
            <div class="sim-modal-actions">
              <button type="button" class="sim-btn" data-action="modal-cancel">${escapeHtml(t("dialog.cancel"))}</button>
              <button type="button" class="sim-btn sim-btn-primary" data-action="modal-confirm">${escapeHtml(t("dialog.ok"))}</button>
            </div>
          </div>
        </div>
      `;
    }

    if (modal.type === "password-prompt") {
      const connection = getConnection(modal.connectionId);
      return `
        <div class="sim-overlay">
          <div class="sim-modal">
            <div class="sim-modal-head"><h3>${escapeHtml(t("auth.enter_password.title"))}</h3></div>
            <div class="sim-modal-body">
              <p>${escapeHtml(t("auth.enter_password.prompt", { name: connection?.name || "?" }))}</p>
              <input class="sim-input" type="password" data-modal-field="password" value="${escapeHtml(modal.value || "")}" />
            </div>
            <div class="sim-modal-actions">
              <button type="button" class="sim-btn" data-action="modal-cancel">${escapeHtml(t("dialog.cancel"))}</button>
              <button type="button" class="sim-btn sim-btn-primary" data-action="modal-confirm">${escapeHtml(t("dialog.ok"))}</button>
            </div>
          </div>
        </div>
      `;
    }

    return "";
  }

  function renderBadgeText() {
    return `${t("badge.n_active", { n: state.connections.length })} · ${t("badge.n_mounted", { n: getMountedCount() })}`;
  }

  function renderMountCountLabel() {
    const mounted = getMountedCount();
    if (mounted === 1) return t("sim.mounts.one");
    if (mounted > 1) return t("sim.mounts.many", { n: mounted });
    return "";
  }
})();