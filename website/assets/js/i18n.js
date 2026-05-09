/**
 * i18n.js — Lightweight translation system for the NEO SSH-Win Manager site.
 *
 * Usage in HTML:
 *   <h1 data-i18n="hero.title">…fallback text…</h1>
 *   <p data-i18n="hero.lead">…</p>
 *   <input data-i18n-attr="placeholder:search.placeholder" />
 *
 * Activation:
 *   The translator runs automatically on DOMContentLoaded and again whenever
 *   layout.js injects new chrome. Language is persisted in localStorage under
 *   `neo-ssh-lang`. Default is German ("de").
 *
 * Public API on `window.neoI18n`:
 *   getLang()                  → "de" | "en"
 *   setLang(code)              → set language, re-translate, persist
 *   t(key, fallback?)          → look up a single key
 *   apply(root?)               → translate a subtree
 *   onChange(fn)               → subscribe to language changes
 */

(function () {
  "use strict";

  /** @type {Record<string, Record<string, string>>} */
  const DICT = {
    de: {
      // ─── chrome ──────────────────────────────────────────────
      "nav.overview": "Übersicht",
      "nav.demo": "Live-App",
      "nav.features": "Features",
      "nav.download": "Download",
      "nav.docs": "Dokumentation",
      "nav.changelog": "Changelog",
      "btn.github": "GitHub",
      "btn.menu": "Menü",
      "btn.theme": "Theme wechseln",
      "btn.theme.toLight": "Zu hellem Theme wechseln",
      "btn.theme.toDark": "Zu dunklem Theme wechseln",
      "btn.lang": "Sprache wechseln",

      "title.index": "NEO SSH-Win Manager — SSH-Laufwerke für Windows",
      "title.app": "Browser-Simulation — NEO SSH-Win Manager",
      "title.features": "Features — NEO SSH-Win Manager",
      "title.download": "Download — NEO SSH-Win Manager",
      "title.changelog": "Changelog — NEO SSH-Win Manager",
      "title.docs.gettingStarted": "Erster Start — NEO SSH-Win Manager",
      "title.docs.connections": "Verbindungen — NEO SSH-Win Manager",
      "title.docs.authentication": "Authentifizierung — NEO SSH-Win Manager",
      "title.docs.cli": "CLI-Companion — NEO SSH-Win Manager",
      "title.docs.configuration": "Einstellungen — NEO SSH-Win Manager",
      "title.docs.troubleshooting": "Troubleshooting — NEO SSH-Win Manager",
      "title.docs.projectStructure": "Projektstruktur — Entwickler — NEO SSH-Win Manager",
      "title.docs.api": "API-Referenz — Entwickler — NEO SSH-Win Manager",
      "meta.index.description":
        "Kostenloser Windows-Desktop-Client für SSHFS. Remote-Ordner als Laufwerk einbinden, mehrere Benutzer, verschlüsselte Zugangsdaten, PuTTY- und OpenSSH-Unterstützung, eingebautes Terminal.",
      "meta.app.description":
        "Interaktive Browser-Simulation der Windows-App. Klickbare Buttons, originale Statusmeldungen und komplette Frontend-Logik ohne echte SSH- oder Mount-Aktionen.",

      "footer.tagline":
        "Kostenloser Open-Source-SSHFS-Client für Windows. Showcase- und Portfolio-Projekt von Den4ik53 und Gregor Krebs.",
      "footer.product": "Produkt",
      "footer.demo": "Live-App",
      "footer.docs": "Dokumentation",
      "footer.developers": "Entwickler",
      "footer.builton": "Aufsetzend auf",
      "footer.license": "© 2026 NEO SSH-Win Manager · MIT-Lizenz",
      "footer.gettingStarted": "Erster Start",
      "footer.cli": "CLI-Companion",
      "footer.config": "Einstellungen",
      "footer.troubleshooting": "Troubleshooting",
      "footer.projectStructure": "Projektstruktur",
      "footer.apiReference": "API-Referenz",
      // ── Footer-Links (in jeder Seite sichtbar) ──
      "footer.imprint": "Impressum",
      "footer.privacy": "Datenschutz",

      // ── Header der Legal-Seite ──
      "legal.eyebrow": "Rechtliches",
      "legal.title": "Impressum & Datenschutz",
      "legal.lead":
        "Pflichtangaben gemäß § 5 DDG sowie Datenschutzhinweise zu diesem privaten Open-Source-Projekt.",
      "legal.meta.private": "Privates Projekt",
      "legal.meta.noncommercial": "Nicht kommerziell",
      "legal.meta.opensource": "Open Source · MIT",

      // ── TOC (linke Sidebar) ──
      "legal.toc.imprintGroup": "Impressum",
      "legal.toc.imprint": "Angaben gemäß § 5 DDG",
      "legal.toc.privacyGroup": "Datenschutz",
      "legal.toc.controller": "Verantwortlicher",
      "legal.toc.processing": "Verarbeitung",
      "legal.toc.externalLinks": "Externe Links",
      "legal.toc.rights": "Rechte Betroffener",
      "legal.toc.contact": "Kontakt",

      // ── Impressum-Block ──
      "legal.imprint.heading": "Impressum",
      "legal.imprint.intro": "Angaben gemäß § 5 DDG (Digitale-Dienste-Gesetz).",
      "legal.imprint.contactBlock": "Diensteanbieter",
      "legal.imprint.emailBlock": "E-Mail",
      "legal.imprint.note":
        "Dieses Projekt ist ein privates, nicht kommerzielles Open-Source-Projekt. Es werden weder Werbung noch entgeltliche Leistungen angeboten.",

      // ── Datenschutz ──
      "legal.privacy.heading": "Datenschutzerklärung",
      "legal.privacy.controllerTitle": "Verantwortlicher",
      "legal.privacy.controllerIntro":
        "Verantwortlich für die Datenverarbeitung im Sinne von Art. 4 Nr. 7 DSGVO ist:",
      "legal.privacy.addressBlock": "Anschrift",

      "legal.privacy.processingTitle": "Verarbeitung personenbezogener Daten",
      "legal.privacy.processingP1":
        "Nach unserem aktuellen Stand werden über diese Website keine personenbezogenen Zugriffslogs dauerhaft gespeichert oder ausgewertet.",
      "legal.privacy.processingP2":
        "Es werden keine Benutzerkonten, Kommentare, Analyse- oder Tracking-Tools, Werbedienste oder eingebettete Drittanbieter-Inhalte eingesetzt.",
      "legal.privacy.processingNote":
        "Technisch notwendige kurzfristige Verarbeitungen auf Infrastruktur- oder Netzwerkebene durch Hostinganbieter oder Netzwerkbetreiber können nicht vollständig ausgeschlossen werden.",

      "legal.privacy.externalTitle": "Externe Links",
      "legal.privacy.externalBody":
        "Diese Website kann Links zu externen Websites enthalten. Für deren Inhalte und Datenschutzpraktiken sind ausschließlich die jeweiligen Betreiber verantwortlich.",

      "legal.privacy.rightsTitle": "Rechte betroffener Personen",
      "legal.privacy.rightsIntro":
        "Soweit personenbezogene Daten verarbeitet werden, bestehen im Rahmen der gesetzlichen Vorschriften insbesondere folgende Rechte:",
      "legal.privacy.right.access": "Auskunft",
      "legal.privacy.right.rectify": "Berichtigung",
      "legal.privacy.right.erase": "Löschung",
      "legal.privacy.right.restrict": "Einschränkung",
      "legal.privacy.right.object": "Widerspruch",
      "legal.privacy.right.portability": "Datenübertragbarkeit",
      "legal.privacy.rightsAuthority":
        "Zudem besteht das Recht auf Beschwerde bei einer Datenschutzaufsichtsbehörde (Art. 77 DSGVO).",

      "legal.privacy.contactTitle": "Kontakt",
      "legal.privacy.contactBody":
        "Bei Fragen zum Datenschutz oder zur Geltendmachung Ihrer Rechte:",

      "legal.stand": "Stand",
      "legal.standDate": "Mai 2026",
      "legal.standNote": "Änderungen dieser Hinweise behalten wir uns vor.",

      // ─── docs sidebar ─────────────────────────────────────────
      "side.firstSteps": "Erste Schritte",
      "side.installFirstStart": "Installation & erster Start",
      "side.connections": "Verbindungen anlegen",
      "side.auth": "Authentifizierung",
      "side.cli": "CLI-Companion",
      "side.configuration": "Konfiguration",
      "side.settingsTheme": "Einstellungen & Theme",
      "side.troubleshooting": "Troubleshooting",
      "side.developer": "Entwickler",
      "side.projectStructure": "Projektstruktur",
      "side.apiReference": "API-Referenz",

      // ─── docs: authentication ─────────────────────────────────
      "auth.title": "Authentifizierung",
      "auth.lead": "Drei Methoden — Passwort, privater Schlüssel oder „jedes Mal fragen”. Hier siehst du, wie sie funktionieren und wo die Zugangsdaten liegen.",
      "auth.h.password": "Passwort speichern",
      "auth.password.body": "Du gibst das SSH-Passwort einmal ein. Es wird beim Mounten von Laufwerken automatisch verwendet. Im SSH-Terminal funktioniert automatische Passworteingabe <strong>nur mit PuTTY</strong> (Einstellungen → „PuTTY verwenden”). Beim nativen OpenSSH-Client musst du das Passwort aus Sicherheitsgründen manuell eintippen.",
      "auth.password.storage": "Das Passwort wird lokal in der SQLite-Datenbank gespeichert — pro App-Benutzer mit AES-256-GCM verschlüsselt und erst nach dem App-Login entschlüsselt.",
      "auth.h.key": "SSH-Key",
      "auth.key.body": "Gib den Pfad zu deinem privaten OpenSSH-Key an (z. B. <code>C:\\Users\\du\\.ssh\\id_ed25519</code>). Der Key wird beim Mounten und beim nativen SSH-Terminal automatisch verwendet. SSH-Zertifikate werden ebenfalls unterstützt.",
      "auth.key.note": "Der Key sollte keine Passphrase haben, damit der Mount automatisch im Hintergrund funktioniert.",
      "auth.h.ppk": "PuTTY-Key (.ppk)",
      "auth.ppk.body": "PuTTY erwartet Schlüssel im eigenen PPK-Format. Hinterlege den Pfad zur <code>.ppk</code>-Datei im Verbindungs-Editor unter <em>„PuTTY-Key-Pfad”</em>. OpenSSH-Keys (<code>id_ed25519</code>, <code>id_rsa</code>) werden dagegen im Feld <em>„SSH-Key-Pfad”</em> eingetragen und ausschließlich für den nativen SSH-Client und SSHFS-Win verwendet. Konvertierung zwischen beiden Formaten ist mit <strong>PuTTYgen</strong> möglich.",
      "auth.ppk.note": "Wenn ein PPK-Pfad hinterlegt ist, nutzt PuTTY diesen — andernfalls fällt es auf den OpenSSH-Key-Pfad zurück (mit Warnung, falls die Datei keine .ppk ist).",
      "auth.h.ask": "Jedes Mal fragen",
      "auth.ask.body": "Es wird kein Passwort gespeichert — bei jedem Verbindungsaufbau erscheint ein Eingabedialog. Sinnvoll für:",
      "auth.ask.li1": "Server, auf denen keine Zugangsdaten gespeichert werden sollen.",
      "auth.ask.li2": "Konten mit wechselnden Passwörtern.",
      "auth.ask.li3": "Server mit Zwei-Faktor-Authentifizierung.",
      "auth.h.encryption": "Wie werden Passwörter geschützt?",
      "auth.encryption.body": "Beim App-Login wird aus deinem Profilpasswort ein Schlüssel erzeugt, der nur im Arbeitsspeicher bleibt. Mit ihm werden alle SSH-Zugangsdaten lokal verschlüsselt. Beim Abmelden wird der Schlüssel sofort gelöscht.",
      "auth.key.unattended": "SSHFS-Win führt im Hintergrund einen unattended Mount aus — eine interaktive Passphrase-Abfrage hängt den Mount-Versuch sonst auf.",
      "auth.h.password.storage": "Wo liegt das Passwort?",
      "auth.password.li1": "Wenn <code>keyring</code> verfügbar ist (Standard): im <strong>Windows Credential Manager</strong>, DPAPI-verschlüsselt, gebunden an den Windows-Benutzer.",
      "auth.password.li2": "<code>config.json</code> enthält dann <em>kein</em> Klartext-Passwort, nur einen Marker <code>_has_password</code>.",
      "auth.password.li3": "In der Multi-User-DB liegt das Passwort zusätzlich symmetrisch verschlüsselt mit dem aus deinem Login-Passwort abgeleiteten Schlüssel.",
      "auth.key.mount": "Beim Mount wird der Pfad an <code>sshfs.exe</code> via <code>-oIdentityFile=…</code> übergeben. Zusätzlich werden gesetzt:",
      "auth.key.batchmode": "Damit fragt SSH bei fehlendem oder falschem Key nicht interaktiv nach einem Passwort, sondern bricht ab.",
      "auth.key.cert": "SSH-Zertifikate funktionieren genauso — der signierte Public-Key-Teil muss neben dem privaten Schlüssel als <code>&lt;key&gt;-cert.pub</code> liegen, OpenSSH und SSHFS-Win finden ihn automatisch.",

      // ─── hero (index) ─────────────────────────────────────────
      "hero.eyebrow": "v1.3.2 · Open Source · Windows · MIT",
      "hero.title": "Mehrere Server.",
      "hero.titleAccent": "Mehrere Admins.",
      "hero.titleEnd": "Ein Klick zum Mounten.",
      "hero.lead":
        "NEO SSH-Win Manager ist ein moderner Desktop-Client für SSHFS auf Windows — mit Multi-User-Konten, verschlüsselten Credentials, integriertem Terminal und einem CLI-Companion für Skripte und Automatisierungen. Komplett kostenlos und Open Source.",
      "hero.cta.download": "Download für Windows",
      "hero.cta.demo": "Live-App testen",
      "hero.cta.docs": "Dokumentation",
      "hero.meta.free": "Ist und bleibt kostenlos",
      "hero.meta.license": "MIT-Lizenz",
      "hero.meta.platform": "Windows 10 / 11",

      "simpage.eyebrow": "Browser-Simulation",
      "simpage.title": "Die Windows-App im Browser.",
      "simpage.lead": "Diese Demo bildet das Desktop-UX mit klickbaren Buttons, Statusmeldungen und Dialogen nach. Alles läuft rein im Frontend: keine SSH-Verbindung, kein Mount, kein Backend.",
      "simpage.reset": "Demo zurücksetzen",
      "simpage.noteTitle": "Frontend-only",
      "simpage.note": "SSH öffnet nur ein Platzhalter-Popup. Mounts, Explorer-Aktionen, Einstellungen und Formulare werden komplett im Browser simuliert.",

      // ─── mockup labels ────────────────────────────────────────
      "mock.titlebar": "NEO SSH-Win Manager — admin@workstation",
      "mock.connections": "Verbindungen",
      "mock.pill": "3 aktiv · 1 verbunden",
      "mock.system": "System · web-01",
      "mock.lastSeen": "Zuletzt gesehen",
      "mock.load": "Auslastung",
      "mock.uptime": "Betriebszeit",
      "mock.online": "Online · 1 Mount",

      // ─── feature section ──────────────────────────────────────
      "feat.eyebrow": "Funktionen",
      "feat.title": "Einfach. Sicher. Sofort einsatzbereit.",
      "feat.sub":
        "SSH-Laufwerke mit einem Klick einbinden, mehrere Benutzer verwalten, sicher einloggen — alles in einer App, ohne Kommandozeile.",

      "feat.mount.title": "One-Click Mount",
      "feat.mount.body":
        "Remote-Pfade als Windows-Laufwerksbuchstaben einbinden — über SSHFS-Win und WinFsp.",

      "feat.passwordless.title": "Passwortlos mounten — ohne SSH-Key",
      "feat.passwordless.body":
        "Einmal Passwort hinterlegen — danach wird es beim Mounten automatisch verwendet. Kein SSH-Key nötig. Für automatisches Passwort-Login im Terminal: PuTTY in den Einstellungen aktivieren.",

      "feat.terminal.title": "Eingebautes SSH-Terminal",
      "feat.terminal.body":
        "Direkt aus der App heraus mit jedem Server verbinden. Mit PuTTY wird das Passwort automatisch eingegeben; beim nativen SSH-Client erfolgt die Eingabe manuell im Terminal.",

      "feat.sysinfo.title": "Live-Systemstatus",
      "feat.sysinfo.body":
        "CPU, RAM, Disk, Uptime und Load pro Server — direkt in der Verbindungskarte sichtbar.",

      "feat.multiuser.title": "Mehrere Benutzer",
      "feat.multiuser.body":
        "Mehrere Profile auf einem PC. Jeder Benutzer hat eigene Verbindungen und Zugangsdaten — sicher voneinander getrennt.",

      "feat.cli.title": "CLI-Companion",
      "feat.cli.body":
        "Verbindungen aus Skripten oder Automatisierungen heraus nutzen — mit Access-Key, ohne Login-Dialog.",

      "feat.tray.title": "System-Tray",
      "feat.tray.body":
        "App im Hintergrund lassen, Laufwerke mit einem Klick ein- oder aushängen.",

      "feat.auth.title": "Passwort, Key oder Zertifikat",
      "feat.auth.body":
        "Drei Anmeldemethoden: gespeichertes Passwort, SSH-Key oder jedes Mal neu eingeben. Gespeicherte SSH-Passwörter liegen lokal verschlüsselt in der SQLite-Datenbank.",

      "feat.theme.title": "Modernes Design",
      "feat.theme.body":
        "Stilvolles modernes Interface — wahlweise hell oder dunkel. Pro Benutzer einstellbar, ebenso die Sprache.",

      // ─── how it works ─────────────────────────────────────────
      "how.eyebrow": "Funktionsweise",
      "how.title": "Native Windows-Laufwerke via SSH.",
      "how.sub":
        "Kein VPN, keine Kompromisse. NEO SSH-Win Manager verbindet sich sicher per SSH und hängt den Remote-Ordner direkt als Windows-Laufwerk ein — sichtbar im Explorer wie eine normale Festplatte.",
      "how.code.comment": "# Was die App im Hintergrund ausführt:",
      "how.cred.title": "Sichere Zugangsdaten-Speicherung",
      "how.cred.body":
        "SSH-Passwörter werden lokal in der SQLite-Datenbank gespeichert — pro App-Benutzer mit AES-256-GCM verschlüsselt. Der Schlüssel wird beim App-Login freigegeben und bleibt nur während der Sitzung im Arbeitsspeicher.",
      "how.multi.title": "Echte Mehrbenutzer-Trennung",
      "how.multi.body":
        "Mehrere Profile auf einem PC teilen keine Zugangsdaten. Jeder Benutzer hat seine eigenen Verbindungen, seine Sprache, sein Design — und sieht die Zugangsdaten der anderen nie.",

      // ─── CTA ──────────────────────────────────────────────────
      "cta.eyebrow": "Loslegen",
      "cta.title": "Lade dir die aktuelle Version herunter.",
      "cta.sub": "Aktuell v1.3.2 — kostenlos, ohne Tracking, ohne Account.",
      "cta.btn.download": "Zum Download",
      "cta.btn.source": "Quellcode auf GitHub",

      // ─── changelog ────────────────────────────────────────────
      "changelog.eyebrow": "Changelog",
      "changelog.title": "Was sich geändert hat.",
      "changelog.lead":
        "Alle veröffentlichten Versionen — direkt aus den GitHub-Releases. Vollständige Commit-Historie im",
      "changelog.history": "GitHub-Verlauf",
      "changelog.latest": "Aktuell",
      "changelog.col.asset": "Datei",
      "changelog.col.size": "Größe",
      "changelog.col.notes": "Hinweis",
      "changelog.source": "Quelle: GitHub-Releases. Aktualisierbar via",
      "changelog.v120.theme": "Hinzugefügt: persistente Light-/Dark-Theme-Unterstützung.",
      "changelog.v120.ask": "Hinzugefügt: „Jedes Mal fragen”-Authentifizierung für Verbindungen.",
      "changelog.v120.click": "Verbessert: Klick-Verhalten der Verbindungskarten beim Mounten.",
      "changelog.v120.icons": "Behoben: App-Icons im Login- und Hauptfenster.",
      "changelog.v120.bump": "Versions-Metadaten auf 1.2.0 aktualisiert.",
      "changelog.v110.first":
        "Erste Veröffentlichung des NEO SSH-Win Manager — moderner Windows-Desktop-Client zum Einbinden von SSH-Ordnern als Laufwerksbuchstaben.",
      "changelog.v110.gui": "GUI-Anwendung",
      "changelog.v110.cli": "CLI-Companion",

      // ─── v1.3.2 ──────────────────────────────────────────────
      "changelog.v132.li1": "Security: Argon2id als KDF für Schlüsselableitung; Windows Credential Manager (Keyring) für Master-Key.",
      "changelog.v132.li2": "Security: Sicheres Überschreiben sensibler Daten im Arbeitsspeicher (SecureBytes) und strikte Eingabevalidierung gegen Command-Injection.",
      "changelog.v132.li3": "Security: SSH-Host-Key-Verifikation gehärtet — unbekannte Hosts werden bei Mounts abgelehnt (kein accept-new mehr).",
      "changelog.v132.li4": "Security: SSH_PASSWORD-Umgebungsvariable entfernt — Passwort nicht mehr im Prozess-Environment sichtbar.",
      "changelog.v132.li5": "Authentifizierung: Separates Feld für PuTTY-Keys (.ppk).",
      "changelog.v132.li6": "Terminal: Native SSH-Sessions zuverlässig in isoliertem CMD-Fenster.",
      "changelog.v132.li7": "Stabilität: Massen-Disconnect-Bug durch Stabilisierung des SSHFS-Mount-Prozesses behoben.",
      "changelog.v132.li8": "UI/UX: Mausrad-Scroll-Verhalten in Formularen gefixt; strikte Live-Validierung für Pflichtfelder.",

      // ─── v1.3.1 ──────────────────────────────────────────────
      "changelog.v131.li1": "Agent-CLI-Key im Verbindungseditor direkt sichtbar statt maskiert.",
      "changelog.v131.li2": "Zwei sichtbare SVG-Aktionen für CLI-Key eingeführt: kopieren und neu generieren.",
      "changelog.v131.li3": "Copy-Feedback im Editor per Check-Icon ergänzt.",
      "changelog.v131.li4": "Versions- und Website-Metadaten auf 1.3.1 angehoben.",

      // ─── v1.3.0 ──────────────────────────────────────────────
      "changelog.v130.li1": "Einstellungen und Benutzerverwaltung als Vollbild-Panel via QStackedWidget",
      "changelog.v130.li2": "Sidebar-Navigation mit Hervorhebung des aktiven Eintrags",
      "changelog.v130.li3": "[i]-Schaltfläche öffnet ausschließlich das SSH-Live-Systeminfo-Panel",
      "changelog.v130.li4": "Bearbeiten-Schaltfläche immer sichtbar, deaktiviert wenn Verbindung eingehängt",
      "changelog.v130.li5": "Primäre Schaltflächen: Verlauf #00b4d8 → #0077b6, schwarzer Text",
      "changelog.v130.li6": "Titelleistenfarbe passt sich dem aktiven Design via DwmSetWindowAttribute (Windows 11+) an",
      "changelog.v130.li7": "Checkbox-Indikator: 14×14 px, weißer Haken auf türkisem Hintergrund",
      "changelog.v130.li8": "Panel-Header: 52 px Höhe, Kicker-Labels entfernt, Titel vertikal zentriert",
      "changelog.v130.li9": "Listenansicht mit 4-px-Farbbalken für CPU/RAM/Festplatte",
      "changelog.v130.li10": "Vollständige statische Website in website/ (Landing, Features, Docs, Changelog, Download)",
      "changelog.v130.li11": "Interaktive Browser-Simulation (website/app.html) in reinem HTML/CSS/JS",
      "changelog.v130.li12": "Keine Installation nötig, direkt über GitHub Pages bereitstellbar",
      "changelog.v130.li13": "Veraltetes credential_store.py entfernt",
      "changelog.v130.li14": "AppUserModelID-Präfix von dennis. auf neo. geändert",
      "changelog.v130.li15": "Versionserhöhung auf 1.3.0",

      // ─── docs: getting-started ────────────────────────────────
      "gs.title": "Installation & erster Start",
      "gs.lead": "Schritt für Schritt: von der Installation bis zum ersten eingehängten SSH-Laufwerk.",
      "gs.h.prereq": "1. Voraussetzungen installieren",
      "gs.prereq.intro": "NEO SSH-Win Manager benötigt zwei kostenlose Zusatzprogramme:",
      "gs.prereq.note": "Beide Installer mit Standardoptionen durchklicken. Fertig.",
      "gs.h.download": "2. App herunterladen",
      "gs.download.text": "Auf der",
      "gs.download.or": "oder direkt im",
      "gs.download.release": "GitHub-Release",
      "gs.download.text2": "die",
      "gs.download.text3": "herunterladen.",
      "gs.smartscreen.title": "SmartScreen-Hinweis",
      "gs.smartscreen.body": "Die App ist nicht signiert. Beim ersten Start „Weitere Informationen” → „Trotzdem ausführen” wählen.",
      "gs.h.firstrun": "3. Erster Start — Profil anlegen",
      "gs.firstrun.intro": "Beim ersten Start ist keine Datenbank vorhanden. Du wirst aufgefordert, ein Benutzerprofil mit Name und Passwort anzulegen. Dieses Passwort wird für zwei Dinge genutzt:",
      "gs.firstrun.li1": "Login in die App.",
      "gs.firstrun.li2": "Verschlüsselung deiner gespeicherten SSH-Zugangsdaten.",
      "gs.firstrun.warn": "Wichtig: Vergisst du das Passwort, sind die gespeicherten SSH-Zugangsdaten dieses Profils nicht wiederherstellbar. Es gibt keinen Reset.",
      "gs.h.login": "4. Login",
      "gs.login.body": "Nach dem Setup landest du im Login-Dialog. Optional kannst du in den Einstellungen <em>„Auto-Login mit Windows-Account”</em> aktivieren — dann entfällt der Login-Schritt.",
      "gs.h.firstconn": "5. Erste Verbindung anlegen",
      "gs.firstconn.intro": "Im Hauptfenster oben rechts auf <strong>+ Verbindung</strong> klicken. Folgende Felder ausfüllen:",
      "gs.field.name": "<strong>Name</strong> — frei wählbar, wird als Laufwerksbezeichnung angezeigt.",
      "gs.field.host": "<strong>Host</strong> — Adresse oder IP des SSH-Servers.",
      "gs.field.user": "<strong>Benutzer</strong> — dein SSH-Benutzername.",
      "gs.field.port": "<strong>Port</strong> — Standard ist 22.",
      "gs.field.path": "<strong>Remote-Pfad</strong> — z. B. <code>/var/www</code> oder <code>/</code>.",
      "gs.field.letter": "<strong>Laufwerksbuchstabe</strong> — die App schlägt einen freien vor.",
      "gs.field.auth": "<strong>Anmeldung</strong> — Passwort, SSH-Key oder jedes Mal fragen.",
      "gs.firstconn.finish": "Speichern, dann den Toggle in der Verbindungskarte klicken. Bei Erfolg wird das Laufwerk grün und erscheint im Explorer.",
      "gs.h.next": "Nächste Schritte",

      // ─── docs: connections ────────────────────────────────────
      "conn.title": "Verbindungen anlegen",
      "conn.lead": "Alle Felder im Verbindungs-Dialog erklärt — und wie das Laufwerk danach eingehängt wird.",
      "conn.h.dialog": "Verbindungs-Dialog",
      "conn.th.field": "Feld",
      "conn.th.desc": "Beschreibung",
      "conn.th.default": "Standard",
      "conn.f.name": "Anzeigename, wird als Laufwerksbezeichnung gesetzt.",
      "conn.f.host": "Adresse oder IP des SSH-Servers.",
      "conn.f.user": "SSH-Benutzername auf dem Server.",
      "conn.f.port": "SSH-Port.",
      "conn.f.path": "Ordner auf dem Server, der als Laufwerk eingehängt werden soll.",
      "conn.f.letter": "Windows-Laufwerksbuchstabe (z. B. Z:).",
      "conn.f.auth": "<code>password</code>, <code>key</code> oder <code>ask</code>.",
      "conn.f.password": "Wird lokal verschlüsselt in der SQLite-Datenbank gespeichert.",
      "conn.f.keypath": "Pfad zum OpenSSH-Key (nur bei Methode „key”). Wird für Mounts (sshfs.exe) und den nativen SSH-Client verwendet.",
      "conn.f.puttykeypath": "Pfad zum PuTTY-Key im <code>.ppk</code>-Format. Wird ausschließlich für PuTTY-Terminal-Sessions verwendet. Konvertierung mit PuTTYgen.",
      "conn.f.cli": "Erlaubt Zugriff aus dem CLI-Companion.",
      "conn.h.mount": "Laufwerk einhängen",
      "conn.mount.body": "Den Toggle rechts in der Verbindungskarte klicken. Bei Erfolg wird der Toggle grün und das Laufwerk erscheint im Explorer.",
      "conn.h.unmount": "Laufwerk aushängen",
      "conn.unmount.body": "Nochmals auf den (nun grünen) Toggle klicken. Falls das fehlschlägt, werden automatisch Fallback-Methoden versucht.",
      "conn.h.tips": "Tipps",
      "conn.tip1": "<strong>Auto-Reconnect-Mounts beim Start</strong> in den Einstellungen aktivieren, damit Laufwerke beim nächsten App-Start automatisch wieder eingehängt werden.",
      "conn.tip2": "Bei <em>„mount point in use”</em>: Einstellungen → <em>Veraltete Mounts bereinigen</em>.",
      "conn.tip3": "Mehrere Verbindungen zum gleichen Server sind erlaubt — jeweils mit anderem Laufwerksbuchstaben.",

      // // ─── docs: authentication ─────────────────────────────────
      // "auth.title": "Anmeldung & Sicherheit",
      // "auth.lead": "Drei Methoden zur SSH-Anmeldung — wähle, was am besten zu deinem Workflow passt.",
      // "auth.h.password": "Passwort speichern (empfohlen)",
      // "auth.password.body": "Du gibst das SSH-Passwort einmal ein — danach läuft alles automatisch. Beim Mounten und im Terminal wird das Passwort im Hintergrund eingegeben. Kein SSH-Key nötig.",
      // "auth.password.storage": "Das Passwort wird lokal in der SQLite-Datenbank gespeichert — pro App-Benutzer mit AES-256-GCM verschlüsselt und erst nach dem App-Login entschlüsselt.",
      // "auth.h.key": "SSH-Key",
      // "auth.key.body": "Gib den Pfad zu deinem privaten SSH-Key an (z. B. <code>C:\\Users\\du\\.ssh\\id_ed25519</code>). Der Key wird beim Verbinden automatisch verwendet. SSH-Zertifikate werden ebenfalls unterstützt.",
      // "auth.key.note": "Der Key sollte keine Passphrase haben, damit der Mount automatisch im Hintergrund funktioniert.",
      // "auth.h.ask": "Jedes Mal fragen",
      // "auth.ask.body": "Es wird kein Passwort gespeichert — bei jedem Verbindungsaufbau erscheint ein Eingabedialog. Sinnvoll für:",
      // "auth.ask.li1": "Server, auf denen keine Zugangsdaten gespeichert werden sollen.",
      // "auth.ask.li2": "Konten mit wechselnden Passwörtern.",
      // "auth.ask.li3": "Server mit Zwei-Faktor-Authentifizierung.",
      // "auth.h.encryption": "Wie werden Passwörter geschützt?",
      // "auth.encryption.body": "Beim App-Login wird aus deinem Profilpasswort ein Schlüssel erzeugt, der nur im Arbeitsspeicher bleibt. Mit ihm werden alle SSH-Zugangsdaten lokal verschlüsselt. Beim Abmelden wird der Schlüssel sofort gelöscht.",

      // ─── docs: cli ────────────────────────────────────────────
      "cli.title": "CLI-Companion",
      "cli.lead": "SSH-Verbindungen aus Skripten oder Automatisierungen heraus nutzen — ohne Login-Dialog.",
      "cli.h.concept": "Wie funktioniert es?",
      "cli.concept.body": "<code>NeoSSHWinManager-cli.exe</code> ist eine separate Konsolen-App, die mit der laufenden Haupt-App kommuniziert. Du aktivierst CLI-Zugriff für eine Verbindung und bekommst einen Access-Key — damit kannst du dich aus jedem Skript heraus verbinden.",
      "cli.h.prereq": "Voraussetzungen",
      "cli.prereq.li1": "Die Haupt-App läuft und du bist eingeloggt.",
      "cli.prereq.li2": "In der Verbindung ist <strong>CLI-Zugriff</strong> aktiviert.",
      "cli.prereq.li3": "Du hast den Access-Key (in der Verbindungsbearbeitung einsehbar).",
      "cli.h.examples": "Beispiele",
      "cli.h.interactive": "Interaktive SSH-Session",
      "cli.h.command": "Einzelnes Kommando ausführen",
      "cli.h.flags": "Parameter",
      "cli.th.flag": "Parameter",
      "cli.th.desc": "Beschreibung",
      "cli.flag.connect": "Access-Key der Verbindung.",
      "cli.flag.alias": "Alias (alternative Schreibweise).",
      "cli.flag.exec": "Optional: Kommando ausführen statt interaktiver Shell.",
      "cli.h.exit": "Exit-Codes",
      "cli.exit.0": "<code>0</code> — Erfolgreich.",
      "cli.exit.1": "<code>1</code> — Fehler (App nicht aktiv, kein Login, ungültiger Key).",
      "cli.exit.2": "<code>2</code> — Fehlende Parameter.",
      "cli.security.title": "Sicherheitshinweis",
      "cli.security.body": "Der Access-Key wird nur lokal übertragen — nicht über das Netzwerk. Lege Keys nicht in Klartext in Skripte oder Repositories, sondern lese sie aus einer lokalen <code>.env</code>-Datei oder dem Credential Manager.",

      // ─── docs: configuration ─────────────────────────────────
      "cfg.title": "Einstellungen",
      "cfg.lead": "Alles, was im Einstellungs-Dialog konfigurierbar ist.",
      "cfg.h.location": "Speicherort",
      "cfg.location.body": "Einstellungen werden in <code>%APPDATA%\\SSHWinManager\\config.json</code> gespeichert. Verbindungen und Benutzerprofile liegen in einer separaten Datenbank im selben Ordner.",
      "cfg.h.general": "Allgemein",
      "cfg.th.setting": "Einstellung",
      "cfg.th.default": "Standard",
      "cfg.th.effect": "Effekt",
      "cfg.s.startup": "Mit Windows starten",
      "cfg.s.startup.d": "aus",
      "cfg.s.startup.e": "App startet automatisch beim Windows-Login.",
      "cfg.s.tray": "In Tray minimieren",
      "cfg.s.tray.d": "an",
      "cfg.s.tray.e": "Schließen minimiert die App ins System-Tray statt sie zu beenden.",
      "cfg.s.autologin": "Auto-Login mit Windows-Account",
      "cfg.s.autologin.d": "aus",
      "cfg.s.autologin.e": "Login wird übersprungen, wenn Windows-Benutzer mit App-Profil übereinstimmt.",
      "cfg.s.reconnect": "Auto-Reconnect",
      "cfg.s.reconnect.d": "aus",
      "cfg.s.reconnect.e": "Unterbrochene Laufwerke werden automatisch neu verbunden.",
      "cfg.s.reconnectstart": "Laufwerke beim Start wiederherstellen",
      "cfg.s.reconnectstart.d": "an",
      "cfg.s.reconnectstart.e": "Beim App-Start werden zuletzt aktive Laufwerke automatisch eingehängt.",
      "cfg.s.interval": "Check-Intervall",
      "cfg.s.interval.d": "30 s",
      "cfg.s.interval.e": "Wie oft der Verbindungsstatus geprüft wird.",
      "cfg.s.debug": "Debug-Modus",
      "cfg.s.debug.d": "aus",
      "cfg.s.debug.e": "Aktiviert ausführliches Logging und ein Live-Log-Fenster.",
      "cfg.s.putty": "PuTTY verwenden",
      "cfg.s.putty.d": "aus",
      "cfg.s.putty.e": "PuTTY statt OpenSSH für SSH-Terminal-Sessions verwenden. <strong>Nur PuTTY</strong> unterstützt automatische Passworteingabe im Terminal und PPK-Schlüssel. Aus Sicherheitsgründen ist automatischer Passwort-Login im nativen SSH-Client deaktiviert.",
      "cfg.s.puttypath": "PuTTY-Pfad",
      "cfg.s.puttypath.d": "Standard-Pfad",
      "cfg.s.puttypath.e": "Pfad zur putty.exe-Installation.",
      "cfg.h.theme": "Design wechseln",
      "cfg.theme.body": "Im Einstellungs-Dialog → <em>Erscheinungsbild</em> → <em>Hell</em> oder <em>Dunkel</em>. Pro Benutzer gespeichert, wirkt sofort.",
      "cfg.h.lang": "Sprache wechseln",
      "cfg.lang.body": "Einstellungen → <em>Sprache</em>. Verfügbar: <strong>Deutsch</strong> und <strong>Englisch</strong>. Die Sprache ändert sich nach Neustart.",
      "cfg.h.debug": "Debug-Modus",
      "cfg.debug.body": "Aktiviert detailliertes Logging in <code>%APPDATA%\\SSHWinManager\\app.log</code> und ein Live-Log-Fenster. Hilfreich bei Verbindungsproblemen.",

      "ts.eyebrow": "Docs",
      "ts.title": "Troubleshooting",
      "ts.lead": "Die häufigsten Fehlermeldungen mit ihrer Ursache und Lösung.",
      "ts.h.nosshfs": "„sshfs.exe nicht gefunden\”",
      "ts.nosshfs.body": "SSHFS-Win ist nicht installiert oder liegt an einem unüblichen Pfad. Lösung: Installer von winfsp/sshfs-win laufen lassen. Die App sucht in:",
      "ts.nosshfs.note": "Auch PATH wird durchsucht.",
      "ts.h.mountpoint": "„mount point in use\”",
      "ts.mountpoint.body": "Der gewählte Laufwerksbuchstabe ist noch von einem alten Mount belegt. Schritte:",
      "ts.mountpoint.li1": "Anderen Buchstaben wählen, oder",
      "ts.mountpoint.li2": "Settings → Stale Mounts bereinigen ausführen, oder",
      "ts.mountpoint.li3": "Im Explorer das alte Laufwerk trennen, oder",
      "ts.mountpoint.li4": "Als letzter Ausweg: Windows neu starten.",
      "ts.h.authfail": "„Authentifizierung fehlgeschlagen”",
      "ts.authfail.li1": "Passwort prüfen — Edit → Passwort neu setzen.",
      "ts.authfail.li2": "Bei Key-Auth: Pfad zum privaten Schlüssel korrekt? Hat die Datei keine Passphrase?",
      "ts.authfail.li3": "Auf dem Server: ~/.ssh/authorized_keys enthält den Public-Key?",
      "ts.authfail.li4": "Server-Config: PasswordAuthentication bzw. PubkeyAuthentication in sshd_config aktiv?",
      "ts.h.connrefused": "„Verbindung abgelehnt”",
      "ts.connrefused.body": "SSH-Daemon läuft nicht oder Firewall blockt. Test:",
      "ts.connrefused.note": "Aus PowerShell. Wenn das auch fehlschlägt, ist es kein App-Problem.",
      "ts.h.accessdenied": "Laufwerk taucht im Explorer auf, aber „Zugriff verweigert”",
      "ts.accessdenied.body": "WinFsp-Berechtigungsproblem. Die App setzt bereits:",
      "ts.accessdenied.note": "Falls das Problem trotzdem auftritt: SSHFS-Win neu installieren und prüfen, ob der WinFsp-Dienst läuft (services.msc).",
      "ts.h.nostart": "App startet nicht oder bringt nichts in den Vordergrund",
      "ts.nostart.body": "Single-Instance-Lock per Windows-Mutex aktiv. Eine zweite Instanz beendet sich sofort und versucht, das vorhandene Fenster zu fokussieren. Falls das Fenster nicht erscheint:",
      "ts.nostart.li1": "Tray prüfen — App ist evtl. minimiert.",
      "ts.nostart.li2": "Im Taskmanager nach NeoSSHWinManager.exe suchen und beenden.",
      "ts.h.logs": "Logs einsehen",
      "ts.logs.body": "Settings → Debug-Modus aktivieren. Logs landen in %APPDATA%\\SSHWinManager\\app.log. Bei Mount-Problemen ist der vollständige sshfs.exe-stderr enthalten.",

      // ─── docs: developer / project-structure ─────────────────
      "dev.ps.title": "Projektstruktur",
      "dev.ps.lead": "Überblick über das Repository für Mitwirkende und Interessierte.",
      "dev.ps.h.toplevel": "Verzeichnis-Übersicht",
      "dev.ps.h.modules": "Hauptmodule",
      "dev.ps.h.ui": "UI-Module",
      "dev.ps.th.file": "Datei",
      "dev.ps.th.role": "Aufgabe",
      "dev.ps.h.models": "Datenmodelle",
      "dev.ps.h.release": "Build- & Release-Prozess",
      "dev.ps.main.intro": "GUI entry point. In order, it:",
      "dev.ps.main.li1": "Loads the config (<code>config.AppSettings.load()</code>).",
      "dev.ps.main.li2": "Enforces single-instance mode (<code>SingleInstance(\"SSHWinManager_Mutex_v1\")</code>).",
      "dev.ps.main.li3": "Initializes <code>QApplication</code> with the saved theme.",
      "dev.ps.main.li4": "Shows the login window (unless auto-login applies) → main window.",
      "dev.ps.main.li5": "Starts <code>IPCServer</code> in a worker thread.",
      "dev.ps.cli.body": "Argparse CLI. Connects to <code>\\\\.\\pipe\\SSHWinManager_IPC_v1</code>, sends a JSON request <code>{op:\"connect\", key:\"…\", exec:\"…\"}</code>, receives credentials, then calls <code>ssh_launcher.spawn_session()</code>.",
      "dev.ps.config.li1": "<code>AppSettings</code> — dataclass with defaults (theme, language, PuTTY path, auto-reconnect, check interval, tray, debug, …).",
      "dev.ps.config.li2": "<code>load()</code>/<code>save()</code> — JSON in <code>%APPDATA%\\SSHWinManager\\config.json</code>.",
      "dev.ps.config.li3": "Migrations: missing keys are filled with defaults.",
      "dev.ps.db.li1": "SQLite, path: <code>%APPDATA%\\SSHWinManager\\app.db</code>.",
      "dev.ps.db.li2": "Tables: <code>users</code>, <code>connections</code>, <code>settings_per_user</code>.",
      "dev.ps.db.li3": "Schema version in <code>PRAGMA user_version</code>; <code>migrate()</code> adds new columns idempotently.",
      "dev.ps.auth.li1": "<code>UserManager</code> — create, sign in, change password, delete.",
      "dev.ps.auth.li2": "Password hash: PBKDF2-HMAC-SHA256, per-user salt, 200k iterations.",
      "dev.ps.auth.li3": "The session key is derived at sign-in and kept only in RAM.",
      "dev.ps.auth.li4": "<code>UserConnectionManager</code> — CRUD for connections, automatic encryption/decryption per user.",
      "dev.ps.sshfs.li1": "<code>SSHFSController.mount(connection, password=None)</code> — builds the argument list and starts <code>sshfs.exe</code> as a detached subprocess.",
      "dev.ps.sshfs.li2": "<code>unmount(letter)</code> — three strategies (see <a href=\"../connections.html\" data-i18n=\"side.connections\">Connections</a>).",
      "dev.ps.sshfs.li3": "<code>list_mounts()</code> — parses fsutil output.",
      "dev.ps.sshfs.li4": "<code>status_for(connection)</code> — returns <code>\"mounted\"</code>, <code>\"unmounted\"</code>, or <code>\"stale\"</code>.",
      "dev.ps.launcher.body": "Starts an interactive SSH session. Chooses OpenSSH or PuTTY based on <code>AppSettings.use_putty</code>. Passes the key or password securely.",
      "dev.ps.ipc.body": "Worker thread with a named-pipe server. Accepts JSON requests, validates the access key against the database, and returns decrypted credentials.",
      "dev.ps.ui.login": "Login form and first-profile setup wizard.",
      "dev.ps.ui.main": "Main window: sidebar + connection list + status bar.",
      "dev.ps.ui.tray": "System tray icon with quick-access menu.",
      "dev.ps.ui.card": "One card per connection with a mount toggle.",
      "dev.ps.ui.toggle": "Custom switch with cyan/green states and spinner.",
      "dev.ps.ui.addedit": "Create / edit a connection.",
      "dev.ps.ui.settings": "App-wide settings.",
      "dev.ps.ui.ask": "Password prompt for “Ask each time”.",
      "dev.ps.ui.debug": "Live log viewer with filter.",
      "dev.ps.release.li1": "Bump the version in <code>file_version_info.txt</code>, README, and <code>changelog.html</code>.",
      "dev.ps.release.li2": "Run <code>.\\build_dual.ps1</code> — builds GUI and CLI EXEs with PyInstaller into <code>dist/</code>.",
      "dev.ps.release.li3": "Test both EXEs locally (login, one mount, one CLI call).",
      "dev.ps.release.li4": "Create the tag: <code>git tag v1.x.0 &amp;&amp; git push --tags</code>.",
      "dev.ps.release.li5": "Create a new GitHub release, attach both EXEs, and add the changelog.",

      // ─── docs: developer / api ────────────────────────────────
      "dev.api.title": "API-Referenz",
      "dev.api.lead": "Wichtige Klassen und Methoden für Entwickler und Mitwirkende.",
      "dev.api.h.auth": "Authentifizierungs-Ablauf",
      "dev.api.h.mount": "Mount- / Unmount-Ablauf",
      "dev.api.h.cli": "CLI-IPC-Ablauf",
      "dev.api.h.pipe": "Pipe-Protokoll",
      "dev.api.h.settings": "Einstellungs-Ablauf",
      "dev.api.h.public": "Öffentliche Klassen & Methoden",
      "dev.api.th.method": "Methode",
      "dev.api.th.desc": "Beschreibung",
      "dev.api.h.gendoc": "Generierte API-Dokumentation (optional)",
      "dev.api.auth.li1": "User gibt im Login-Fenster Username + Passwort ein.",
      "dev.api.auth.li2": "<code>UserManager.authenticate(username, password)</code> vergleicht den Hash, leitet bei Erfolg den Session-Key ab und gibt ihn zurück.",
      "dev.api.auth.li3": "Session-Key wird in <code>UserConnectionManager</code> übergeben und nur in dessen Instanz gehalten.",
      "dev.api.auth.li4": "Beim Lesen einer Verbindung wird das verschlüsselte Passwort mit dem Session-Key entschlüsselt.",
      "dev.api.auth.li5": "Beim Logout: <code>UserConnectionManager.dispose()</code> löscht den Schlüssel aus dem RAM.",
      "dev.api.mount.li1": "UI ruft <code>SSHFSController.mount(connection)</code> in einem Worker-Thread auf.",
      "dev.api.mount.li2": "Bei <code>auth_method=\"ask\"</code>: Modal-Dialog für Passwort, sonst <code>connection.password</code> oder <code>connection.key_path</code>.",
      "dev.api.mount.li3": "Argument-Liste wird gebaut, <code>sshfs.exe</code> als detached Subprocess gestartet.",
      "dev.api.mount.li4": "Nach 3 s wird per <code>list_mounts()</code> validiert, ob das Laufwerk verfügbar ist.",
      "dev.api.mount.li5": "UI bekommt ein Signal <code>mount_state_changed(connection_id, \"mounted\"|\"failed\", error_text)</code>.",
      "dev.api.mount.li6": "Unmount: <code>SSHFSController.unmount(letter)</code> mit Fallback-Kette.",
      "dev.api.settings.li1": "Settings-Dialog ändert <code>AppSettings</code>-Instanz.",
      "dev.api.settings.li2": "<code>AppSettings.save()</code> schreibt JSON.",
      "dev.api.settings.li3": "Signal <code>settings_changed</code> wird ausgegeben.",
      "dev.api.settings.li4": "Theme: <code>QApplication.setStyleSheet(load_theme(name))</code> — kein Neustart nötig.",
      "dev.api.settings.li5": "Sprache: <code>i18n.set_locale(code)</code>; alle Widgets re-rendern via <code>retranslate_ui()</code>.",
      "dev.api.desc.load": "Liest <code>config.json</code>, merged mit Defaults, gibt Instanz zurück.",
      "dev.api.desc.save": "Schreibt aktuelle Werte als JSON.",
      "dev.api.desc.reset": "Setzt alles auf Default und persistiert.",
      "dev.api.desc.createUser": "Legt neuen User an, hasht Passwort.",
      "dev.api.desc.authenticate": "Login. Gibt bei Erfolg den abgeleiteten Session-Key zurück.",
      "dev.api.desc.changePassword": "Re-encryptet alle Verbindungs-Passwörter mit neuem Session-Key.",
      "dev.api.desc.deleteUser": "Cascade-löscht Verbindungen.",
      "dev.api.desc.list": "Alle Verbindungen des aktuellen Users.",
      "dev.api.desc.get": "Eine Verbindung — Passwort entschlüsselt.",
      "dev.api.desc.createConn": "Anlegen, Passwort verschlüsselt persistieren. Gibt ID zurück.",
      "dev.api.desc.updateConn": "Re-encrypt &amp; persist.",
      "dev.api.desc.deleteConn": "Löschen.",
      "dev.api.desc.byAccessKey": "Vom IPC-Server für CLI-Lookup verwendet.",
      "dev.api.desc.mount": "Startet Mount. Gibt Status + ggf. stderr zurück.",
      "dev.api.desc.unmount": "Trennt sauber, mit Fallback-Strategien.",
      "dev.api.desc.listMounts": "Aktuelle Mounts.",
      "dev.api.desc.statusFor": "<code>\"mounted\" / \"unmounted\" / \"stale\"</code>.",
      "dev.api.desc.cleanup": "Räumt verwaiste Mountpoints auf.",
      "dev.api.variant.pdoc": "Variante A — pdoc",
      "dev.api.variant.mkdocs": "Variante B — MkDocs Material + mkdocstrings",

      // ─── features page ────────────────────────────────────────
      "fp.hero.title": "Alles, was die App kann.",
      "fp.hero.lead": "Eine Übersicht aller Funktionen in NEO SSH-Win Manager — einfach erklärt.",
      "fp.s1.eyebrow": "SSH-Laufwerke",
      "fp.s1.title": "Remote-Ordner als Windows-Laufwerk.",
      "fp.s1.sub": "Einen Klick — und der Server-Ordner erscheint wie eine lokale Festplatte im Explorer.",
      "fp.oneclick.title": "One-Click Mount",
      "fp.oneclick.body": "Mit einem Klick wird der Remote-Ordner als Windows-Laufwerksbuchstabe eingehängt — kein Kommandozeilenwissen nötig.",
      "fp.autoletter.title": "Automatischer Laufwerksbuchstabe",
      "fp.autoletter.body": "Die App erkennt freie Buchstaben und vermeidet Konflikte mit bestehenden Laufwerken automatisch.",
      "fp.unmount.title": "Sicheres Trennen",
      "fp.unmount.body": "Laufwerke werden sauber getrennt. Falls nötig, werden automatisch mehrere Methoden versucht.",
      "fp.label.title": "Laufwerks-Bezeichnung",
      "fp.label.body": "Der Verbindungsname erscheint direkt als Laufwerks-Label im Explorer.",
      "fp.reconnect.title": "Auto-Reconnect",
      "fp.reconnect.body": "Unterbrochene Verbindungen werden automatisch wiederhergestellt — z. B. nach einem kurzen Netzausfall.",
      "fp.startup.title": "Laufwerke beim Start wiederherstellen",
      "fp.startup.body": "Die App merkt sich aktive Laufwerke und hängt sie nach dem Neustart automatisch wieder ein.",
      "fp.s2.eyebrow": "Anmeldung & Sicherheit",
      "fp.s2.title": "Sicher und bequem.",
      "fp.pw.title": "Passwortlos mounten — ohne SSH-Key",
      "fp.pw.body": "Passwort einmal eingeben — es wird automatisch beim Mounten von Laufwerken verwendet. Kein SSH-Key nötig. Im SSH-Terminal funktioniert automatische Passworteingabe nur mit PuTTY.",
      "fp.key.title": "SSH-Key & Zertifikat",
      "fp.key.body": "Standard-SSH-Keys und -Zertifikate werden unterstützt und automatisch beim Verbinden verwendet.",
      "fp.ask.title": "Jedes Mal fragen",
      "fp.ask.body": "Für Server, auf denen kein Passwort gespeichert werden soll — ein Dialog erscheint beim Verbinden.",
      "fp.crypto.title": "Verschlüsselte Zugangsdaten",
      "fp.crypto.body": "Alle gespeicherten SSH-Passwörter sind lokal verschlüsselt — der Schlüssel kommt aus deinem App-Login.",
      "fp.singleinstance.title": "Einmalig geöffnet",
      "fp.singleinstance.body": "Die App läuft immer nur einmal — ein zweiter Start bringt das vorhandene Fenster in den Vordergrund.",
      "fp.multiuser.title": "Mehrere Profile",
      "fp.multiuser.body": "Mehrere Benutzer auf einem PC, jeder mit eigenen Verbindungen und Zugangsdaten.",
      "fp.s3.eyebrow": "Bedienung & Design",
      "fp.s3.title": "Einfach zu bedienen. Angenehm anzusehen.",
      "fp.terminal.title": "Eingebautes Terminal",
      "fp.terminal.body": "Mit einem Klick eine SSH-Session öffnen — OpenSSH oder PuTTY. Mit PuTTY wird das Passwort automatisch eingegeben; beim nativen SSH-Client manuell eintippen.",
      "fp.sysinfo.title": "Live-Systemstatus",
      "fp.sysinfo.body": "CPU, RAM, Disk, Uptime und Load direkt in der Verbindungskarte — ohne extra Tools.",
      "fp.tray.title": "System-Tray",
      "fp.tray.body": "Die App läuft diskret im Tray. Laufwerke ein- oder aushängen ohne das Hauptfenster zu öffnen.",
      "fp.theme.title": "Modernes Design",
      "fp.theme.body": "Stilvolles Interface mit hellem und dunklem Theme — pro Benutzer einstellbar.",
      "fp.lang.title": "Deutsch & Englisch",
      "fp.lang.body": "Sprache pro Benutzer wählbar. Die Sprache ändert sich nach Neustart.",
      "fp.autostart.title": "Mit Windows starten",
      "fp.autostart.body": "Die App startet optional automatisch beim Windows-Login — als Tray-App im Hintergrund.",
      "fp.s4.eyebrow": "Automatisierung",
      "fp.s4.title": "CLI-Companion für Skripte.",
      "fp.s4.sub": "Verbindungen aus Skripten oder Automationen heraus nutzen — mit einem Access-Key, ohne Login-Dialog.",
      "fp.cli.note": "CLI-Zugriff in der Verbindungseinstellung aktivieren und Access-Key generieren.",

      // ─── download page ────────────────────────────────────────
      "dl.eyebrow": "Aktuelle Version:",
      "dl.title": "Download.",
      "dl.lead": "NEO SSH-Win Manager ist kostenlos und Open Source. Einfach herunterladen und starten — keine Installation.",
      "dl.gui.badge": "Empfohlen",
      "dl.gui.title": "NeoSSHWinManager.exe",
      "dl.gui.desc": "Die Hauptanwendung mit allem: Verbindungsverwaltung, Tray, mehrere Benutzerprofile, Live-Systemstatus.",
      "dl.gui.size": "~25 MB · Windows 10 / 11 (x64)",
      "dl.gui.btn": "GUI herunterladen",
      "dl.cli.badge": "Optional",
      "dl.cli.title": "NeoSSHWinManager-cli.exe",
      "dl.cli.desc": "Konsolen-Companion für Skripte und Automatisierungen. Nutzt die Verbindungen der laufenden Hauptanwendung.",
      "dl.cli.size": "~10 MB · erfordert laufende GUI",
      "dl.cli.btn": "CLI herunterladen",
      "dl.smartscreen.title": "Windows SmartScreen",
      "dl.smartscreen.body": "Die App ist nicht code-signiert (Open-Source-Projekt). Windows zeigt beim ersten Start möglicherweise eine Warnung. „Weitere Informationen” → <em>Trotzdem ausführen</em> klicken. Lade die App ausschließlich aus dem offiziellen",
      "dl.smartscreen.body2": "herunter.",
      "dl.prereq.eyebrow": "Voraussetzungen",
      "dl.prereq.title": "Zwei kostenlose Programme werden benötigt.",
      "dl.prereq.sub": "Diese erledigen das SSH-Mounting im Hintergrund — NEO SSH-Win Manager ist die Bedienoberfläche.",
      "dl.prereq.th.comp": "Programm",
      "dl.prereq.th.what": "Wozu",
      "dl.prereq.th.dl": "Download",
      "dl.prereq.winfsp.what": "Stellt das Dateisystem-Interface für Windows bereit.",
      "dl.prereq.sshfswin.what": "Verbindet SSH mit dem Dateisystem.",
      "dl.prereq.win.what": "x64. Andere Versionen werden nicht getestet.",
      "dl.prereq.win.dl": "—",
      "dl.prereq.openssh.what": "Optional, für die eingebaute Terminal-Funktion.",
      "dl.prereq.openssh.dl": "Windows-Feature (vorinstalliert)",
      "dl.order.title": "Installationsreihenfolge",
      "dl.order.li1": "WinFsp installieren.",
      "dl.order.li2": "SSHFS-Win installieren.",
      "dl.order.li3": "<code>NeoSSHWinManager.exe</code> herunterladen — keine Installation nötig, einfach starten.",
      "dl.order.li4": "App starten, Benutzerprofil anlegen, erste Verbindung hinzufügen.",
      "dl.src.eyebrow": "Aus Quellcode bauen",
      "dl.src.title": "Selbst kompilieren.",
      "dl.src.sub": "Mit Python 3.11+ und PyInstaller.",
      "dl.src.run": "# Direkt aus Quellcode starten",
      "dl.src.build": "# Beide EXE-Dateien bauen (GUI + CLI)",
      "dl.src.note": "EXE-Dateien werden im <code>dist/</code>-Ordner gespeichert.",
    },

    en: {
      // ─── chrome ──────────────────────────────────────────────
      "nav.overview": "Overview",
      "nav.demo": "Live app",
      "nav.features": "Features",
      "nav.download": "Download",
      "nav.docs": "Documentation",
      "nav.changelog": "Changelog",
      "btn.github": "GitHub",
      "btn.menu": "Menu",
      "btn.theme": "Toggle theme",
      "btn.theme.toLight": "Switch to light theme",
      "btn.theme.toDark": "Switch to dark theme",
      "btn.lang": "Switch language",

      "title.index": "NEO SSH-Win Manager — SSH drives for Windows",
      "title.app": "Browser simulator — NEO SSH-Win Manager",
      "title.features": "Features — NEO SSH-Win Manager",
      "title.download": "Download — NEO SSH-Win Manager",
      "title.changelog": "Changelog — NEO SSH-Win Manager",
      "title.docs.gettingStarted": "Getting started — NEO SSH-Win Manager",
      "title.docs.connections": "Connections — NEO SSH-Win Manager",
      "title.docs.authentication": "Authentication — NEO SSH-Win Manager",
      "title.docs.cli": "CLI companion — NEO SSH-Win Manager",
      "title.docs.configuration": "Settings — NEO SSH-Win Manager",
      "title.docs.troubleshooting": "Troubleshooting — NEO SSH-Win Manager",
      "title.docs.projectStructure": "Project structure — Developers — NEO SSH-Win Manager",
      "title.docs.api": "API reference — Developers — NEO SSH-Win Manager",
      "meta.index.description":
        "Free Windows desktop client for SSHFS. Mount remote folders as drives, manage multiple users, encrypted credentials, PuTTY and OpenSSH support, and a built-in terminal.",
      "meta.app.description":
        "Interactive browser simulation of the Windows app. Clickable buttons, original status messages and frontend-only logic without any real SSH or mount actions.",

      "footer.tagline":
        "A free, open-source SSHFS client for Windows. Showcase and portfolio project by Den4ik53 and Gregor Krebs.",
      "footer.product": "Product",
      "footer.demo": "Live app",
      "footer.docs": "Documentation",
      "footer.developers": "Developers",
      "footer.builton": "Built on",
      "footer.license": "© 2026 NEO SSH-Win Manager · MIT licence",
      "footer.gettingStarted": "Getting started",
      "footer.cli": "CLI companion",
      "footer.config": "Settings",
      "footer.troubleshooting": "Troubleshooting",
      "footer.projectStructure": "Project structure",
      "footer.apiReference": "API reference",
      // ── Footer links (visible on every page) ──
      "footer.imprint": "Imprint",
      "footer.privacy": "Privacy",

      // ── Footer links (visible on every page) ──
      "footer.imprint": "Imprint",
      "footer.privacy": "Privacy",

      // ── Legal page header ──
      "legal.eyebrow": "Legal",
      "legal.title": "Imprint & Privacy Policy",
      "legal.lead":
        "Mandatory information pursuant to § 5 DDG and the privacy notice for this private open-source project.",
      "legal.meta.private": "Private project",
      "legal.meta.noncommercial": "Non-commercial",
      "legal.meta.opensource": "Open source · MIT",

      // ── TOC (left sidebar) ──
      "legal.toc.imprintGroup": "Imprint",
      "legal.toc.imprint": "Information per § 5 DDG",
      "legal.toc.privacyGroup": "Privacy",
      "legal.toc.controller": "Controller",
      "legal.toc.processing": "Processing",
      "legal.toc.externalLinks": "External links",
      "legal.toc.rights": "Data subject rights",
      "legal.toc.contact": "Contact",

      // ── Imprint block ──
      "legal.imprint.heading": "Imprint",
      "legal.imprint.intro": "Mandatory information pursuant to § 5 of the German Digital Services Act (DDG).",
      "legal.imprint.contactBlock": "Service provider",
      "legal.imprint.emailBlock": "Email",
      "legal.imprint.note":
        "This project is a private, non-commercial open-source project. Neither advertising nor paid services are offered.",

      // ── Privacy ──
      "legal.privacy.heading": "Privacy policy",
      "legal.privacy.controllerTitle": "Controller",
      "legal.privacy.controllerIntro":
        "The controller responsible for data processing within the meaning of Art. 4(7) GDPR is:",
      "legal.privacy.addressBlock": "Address",

      "legal.privacy.processingTitle": "Processing of personal data",
      "legal.privacy.processingP1":
        "To the best of our current knowledge, no personal access logs from this website are permanently stored or analysed.",
      "legal.privacy.processingP2":
        "No user accounts, comments, analytics or tracking tools, advertising services or embedded third-party content are used.",
      "legal.privacy.processingNote":
        "Technically necessary short-term processing on infrastructure or network level by hosting providers or network operators cannot be entirely ruled out.",

      "legal.privacy.externalTitle": "External links",
      "legal.privacy.externalBody":
        "This website may contain links to external sites. Their content and privacy practices are the sole responsibility of the respective operators.",

      "legal.privacy.rightsTitle": "Data subject rights",
      "legal.privacy.rightsIntro":
        "Where personal data is processed, you have the following rights under applicable law in particular:",
      "legal.privacy.right.access": "Access",
      "legal.privacy.right.rectify": "Rectification",
      "legal.privacy.right.erase": "Erasure",
      "legal.privacy.right.restrict": "Restriction",
      "legal.privacy.right.object": "Objection",
      "legal.privacy.right.portability": "Data portability",
      "legal.privacy.rightsAuthority":
        "You also have the right to lodge a complaint with a data protection supervisory authority (Art. 77 GDPR).",

      "legal.privacy.contactTitle": "Contact",
      "legal.privacy.contactBody":
        "For questions about data protection or to exercise your rights:",

      "legal.stand": "As of",
      "legal.standDate": "May 2026",
      "legal.standNote": "We reserve the right to amend this notice.",


      // ── Legal page header ──
      "legal.eyebrow": "Legal",
      "legal.title": "Imprint & Privacy Policy",
      "legal.lead":
        "Mandatory information pursuant to § 5 DDG and the privacy notice for this private open-source project.",
      "legal.meta.private": "Private project",
      "legal.meta.noncommercial": "Non-commercial",
      "legal.meta.opensource": "Open source · MIT",

      // ── TOC (left sidebar) ──
      "legal.toc.imprintGroup": "Imprint",
      "legal.toc.imprint": "Information per § 5 DDG",
      "legal.toc.privacyGroup": "Privacy",
      "legal.toc.controller": "Controller",
      "legal.toc.processing": "Processing",
      "legal.toc.externalLinks": "External links",
      "legal.toc.rights": "Data subject rights",
      "legal.toc.contact": "Contact",

      // ── Imprint block ──
      "legal.imprint.heading": "Imprint",
      "legal.imprint.intro":
        "Mandatory information pursuant to § 5 of the German Digital Services Act (DDG).",
      "legal.imprint.contactBlock": "Service provider",
      "legal.imprint.emailBlock": "Email",
      "legal.imprint.note":
        "This project is a private, non-commercial open-source project. Neither advertising nor paid services are offered.",

      // ── Privacy ──
      "legal.privacy.heading": "Privacy policy",
      "legal.privacy.controllerTitle": "Controller",
      "legal.privacy.controllerIntro":
        "The controller responsible for data processing within the meaning of Art. 4(7) GDPR is:",
      "legal.privacy.addressBlock": "Address",

      "legal.privacy.processingTitle": "Processing of personal data",
      "legal.privacy.processingP1":
        "To the best of our current knowledge, no personal access logs from this website are permanently stored or analysed.",
      "legal.privacy.processingP2":
        "No user accounts, comments, analytics or tracking tools, advertising services or embedded third-party content are used.",
      "legal.privacy.processingNote":
        "Technically necessary short-term processing on infrastructure or network level by hosting providers or network operators cannot be entirely ruled out.",

      "legal.privacy.externalTitle": "External links",
      "legal.privacy.externalBody":
        "This website may contain links to external sites. Their content and privacy practices are the sole responsibility of the respective operators.",

      "legal.privacy.rightsTitle": "Data subject rights",
      "legal.privacy.rightsIntro":
        "Where personal data is processed, you have the following rights under applicable law in particular:",
      "legal.privacy.right.access": "Access",
      "legal.privacy.right.rectify": "Rectification",
      "legal.privacy.right.erase": "Erasure",
      "legal.privacy.right.restrict": "Restriction",
      "legal.privacy.right.object": "Objection",
      "legal.privacy.right.portability": "Data portability",
      "legal.privacy.rightsAuthority":
        "You also have the right to lodge a complaint with a data protection supervisory authority (Art. 77 GDPR).",

      "legal.privacy.contactTitle": "Contact",
      "legal.privacy.contactBody":
        "For questions about data protection or to exercise your rights:",

      "legal.stand": "As of",
      "legal.standDate": "May 2026",
      "legal.standNote": "We reserve the right to amend this notice.",

      // ─── docs sidebar ─────────────────────────────────────────
      "side.firstSteps": "First steps",
      "side.installFirstStart": "Install & first run",
      "side.connections": "Adding connections",
      "side.auth": "Authentication",
      "side.cli": "CLI companion",
      "side.configuration": "Configuration",
      "side.settingsTheme": "Settings & appearance",
      "side.troubleshooting": "Troubleshooting",
      "side.developer": "Developers",
      "side.projectStructure": "Project structure",
      "side.apiReference": "API reference",

      // ─── hero ─────────────────────────────────────────────────
      "hero.eyebrow": "v1.3.2 · Open Source · Windows · MIT",
      "hero.title": "Multiple servers.",
      "hero.titleAccent": "Multiple users.",
      "hero.titleEnd": "One click to mount.",
      "hero.lead":
        "NEO SSH-Win Manager is a modern Windows desktop app for SSHFS — mount remote folders as drive letters, manage multiple profiles, and connect without typing passwords. Completely free and open source.",
      "hero.cta.download": "Download for Windows",
      "hero.cta.demo": "Open live app",
      "hero.cta.docs": "Documentation",
      "hero.meta.free": "Free and stays free",
      "hero.meta.license": "MIT licence",
      "hero.meta.platform": "Windows 10 / 11",

      "simpage.eyebrow": "Browser simulator",
      "simpage.title": "The Windows app in your browser.",
      "simpage.lead": "This demo mirrors the desktop UX with clickable buttons, status messages and dialog flows. Everything runs in the frontend only: no SSH session, no drive mount, no backend.",
      "simpage.reset": "Reset demo",
      "simpage.noteTitle": "Frontend-only",
      "simpage.note": "SSH only opens a placeholder popup. Mounts, Explorer actions, settings and forms are fully simulated in the browser.",

      // ─── mockup labels ────────────────────────────────────────
      "mock.titlebar": "NEO SSH-Win Manager — admin@workstation",
      "mock.connections": "Connections",
      "mock.pill": "3 active · 1 mounted",
      "mock.system": "System · web-01",
      "mock.lastSeen": "Last seen",
      "mock.load": "Load",
      "mock.uptime": "Uptime",
      "mock.online": "Online · 1 mount",

      // ─── feature section ──────────────────────────────────────
      "feat.eyebrow": "Features",
      "feat.title": "Simple. Secure. Ready to go.",
      "feat.sub":
        "Mount SSH drives with one click, manage multiple users, and log in without passwords — all in one app, no command line needed.",

      "feat.mount.title": "One-click mount",
      "feat.mount.body":
        "Mount remote folders as Windows drive letters — visible in Explorer like any other drive.",

      "feat.passwordless.title": "Passwordless mounts — no SSH key required",
      "feat.passwordless.body":
        "Save your password once — it is used automatically when mounting drives. No SSH key needed. For automatic password login in the terminal, enable PuTTY in Settings.",

      "feat.terminal.title": "Built-in SSH terminal",
      "feat.terminal.body":
        "Connect to any server directly from the app. With PuTTY, the password is entered automatically. With the native SSH client, type the password manually in the terminal.",

      "feat.sysinfo.title": "Live system info",
      "feat.sysinfo.body":
        "CPU, RAM, disk, uptime and load per server — shown right in the connection card.",

      "feat.multiuser.title": "Multiple users",
      "feat.multiuser.body":
        "Multiple profiles on one PC. Each user has their own connections and credentials — securely separated.",

      "feat.cli.title": "CLI companion",
      "feat.cli.body":
        "Use connections from scripts or automations — with an access key, no login dialog needed.",

      "feat.tray.title": "System tray",
      "feat.tray.body":
        "Keep the app running in the background and mount or unmount drives with one click.",

      "feat.auth.title": "Password, key or certificate",
      "feat.auth.body":
        "Three sign-in methods: saved password, SSH key, or prompt each time. Saved SSH passwords are stored locally in the encrypted SQLite database.",

      "feat.theme.title": "Modern design",
      "feat.theme.body":
        "A polished modern interface — choose light or dark. Per-user preference, just like the language.",

      // ─── how it works ─────────────────────────────────────────
      "how.eyebrow": "How it works",
      "how.title": "Native Windows drives over SSH.",
      "how.sub":
        "No VPN, no compromises. NEO SSH-Win Manager connects securely via SSH and mounts the remote folder as a Windows drive — visible in Explorer like a regular disk.",
      "how.code.comment": "# What the app runs in the background:",
      "how.cred.title": "Secure credential storage",
      "how.cred.body":
        "SSH passwords are stored locally in the SQLite database — encrypted per app user with AES-256-GCM. The key is unlocked during app sign-in and kept only in memory for the session.",
      "how.multi.title": "Real multi-user separation",
      "how.multi.body":
        "Multiple profiles on one PC share no credentials. Each user has their own connections, language, and appearance — and never sees anyone else's passwords.",

      // ─── CTA ──────────────────────────────────────────────────
      "cta.eyebrow": "Get started",
      "cta.title": "Download the latest release.",
      "cta.sub": "Currently v1.3.2 — free, no tracking, no account required.",
      "cta.btn.download": "Go to download",
      "cta.btn.source": "Source on GitHub",

      // ─── changelog ────────────────────────────────────────────
      "changelog.eyebrow": "Changelog",
      "changelog.title": "What's changed.",
      "changelog.lead":
        "All published releases — straight from GitHub. Full commit history on",
      "changelog.history": "GitHub history",
      "changelog.latest": "Latest",
      "changelog.col.asset": "File",
      "changelog.col.size": "Size",
      "changelog.col.notes": "Notes",
      "changelog.source": "Source: GitHub releases. Refresh via",
      "changelog.v120.theme": "Added: persistent light / dark theme support.",
      "changelog.v120.ask": "Added: “Ask each time” authentication method for connections.",
      "changelog.v120.click": "Improved: connection card click behaviour while mounting.",
      "changelog.v120.icons": "Fixed: app icons in the login and main windows.",
      "changelog.v120.bump": "Version metadata updated to 1.2.0.",
      "changelog.v110.first":
        "First release of NEO SSH-Win Manager — a modern Windows desktop app for mounting SSH folders as drive letters.",
      "changelog.v110.gui": "GUI application",
      "changelog.v110.cli": "CLI companion",

      // ─── v1.3.2 ──────────────────────────────────────────────
      "changelog.v132.li1": "Security: Argon2id key derivation and Windows Credential Manager (Keyring) for master key storage.",
      "changelog.v132.li2": "Security: Secure memory wiping (SecureBytes) and strict input validation against command injection.",
      "changelog.v132.li3": "Security: SSH host key verification hardened — unknown hosts are rejected on mount (no more silent accept-new).",
      "changelog.v132.li4": "Security: SSH_PASSWORD environment variable removed — password no longer exposed in process environment.",
      "changelog.v132.li5": "Auth: Separate field for PuTTY keys (.ppk format).",
      "changelog.v132.li6": "Terminal: Native SSH sessions reliably open in an isolated CMD window.",
      "changelog.v132.li7": "Stability: Mass-disconnect bug fixed by stabilising the SSHFS mount process.",
      "changelog.v132.li8": "UI/UX: Fixed unwanted mouse-wheel scroll in forms; added strict live validation for required fields.",

      // ─── v1.3.1 ──────────────────────────────────────────────
      "changelog.v131.li1": "Agent CLI key is now directly visible in the connection editor instead of being masked.",
      "changelog.v131.li2": "Added two visible SVG actions for the CLI key: copy and regenerate.",
      "changelog.v131.li3": "Added check-icon feedback after copying the key.",
      "changelog.v131.li4": "Bumped version and website metadata to 1.3.1.",

      // ─── v1.3.0 ──────────────────────────────────────────────
      "changelog.v130.li1": "Full-screen Settings and User Management panels via QStackedWidget",
      "changelog.v130.li2": "Sidebar navigation with active-state highlighting",
      "changelog.v130.li3": "[i] button exclusively opens the SSH live system-info panel",
      "changelog.v130.li4": "Edit button always visible, disabled when connection is mounted",
      "changelog.v130.li5": "Primary buttons: gradient #00b4d8 → #0077b6, black text",
      "changelog.v130.li6": "Title bar colour adapts to active theme via DwmSetWindowAttribute (Windows 11+)",
      "changelog.v130.li7": "Checkbox indicator: 14×14 px, white checkmark on teal background",
      "changelog.v130.li8": "Panel headers: 52 px height, kicker labels removed, titles vertically centred",
      "changelog.v130.li9": "List layout with 4 px colour-coded progress bars for CPU/RAM/Disk",
      "changelog.v130.li10": "Full static website in website/ (landing, features, docs, changelog, download)",
      "changelog.v130.li11": "Interactive browser simulation (website/app.html) in pure HTML/CSS/JS",
      "changelog.v130.li12": "No installation needed, deployable via GitHub Pages",
      "changelog.v130.li13": "Removed legacy credential_store.py",
      "changelog.v130.li14": "AppUserModelID prefix changed from dennis. to neo.",
      "changelog.v130.li15": "Version bump to 1.3.0",

      // ─── docs: getting-started ────────────────────────────────
      "gs.title": "Install & first run",
      "gs.lead": "Step by step: from installation to your first mounted SSH drive.",
      "gs.h.prereq": "1. Install prerequisites",
      "gs.prereq.intro": "NEO SSH-Win Manager needs two free companion programs:",
      "gs.prereq.note": "Run both installers with the default options. That's it.",
      "gs.h.download": "2. Download the app",
      "gs.download.text": "Go to the",
      "gs.download.or": "or directly to the",
      "gs.download.release": "GitHub release",
      "gs.download.text2": "and download",
      "gs.download.text3": ".",
      "gs.smartscreen.title": "Windows SmartScreen notice",
      "gs.smartscreen.body": "The app is not code-signed. On first run, click “More info” → “Run anyway”.",
      "gs.h.firstrun": "3. First run — create your profile",
      "gs.firstrun.intro": "On first launch, no database exists yet. You will be asked to create a user profile with a name and password. This password is used for two things:",
      "gs.firstrun.li1": "Signing in to the app.",
      "gs.firstrun.li2": "Encrypting your saved SSH credentials.",
      "gs.firstrun.warn": "Important: if you forget this password, your saved SSH credentials for this profile cannot be recovered. There is no reset.",
      "gs.h.login": "4. Sign in",
      "gs.login.body": "After setup, you land on the login screen. You can optionally enable <em>“Auto-login with Windows account”</em> in Settings — this skips the login step.",
      "gs.h.firstconn": "5. Add your first connection",
      "gs.firstconn.intro": "Click <strong>+ Connection</strong> in the top-right of the main window and fill in these fields:",
      "gs.field.name": "<strong>Name</strong> — anything you like; shown as the drive label.",
      "gs.field.host": "<strong>Host</strong> — address or IP of your SSH server.",
      "gs.field.user": "<strong>User</strong> — your SSH username.",
      "gs.field.port": "<strong>Port</strong> — default is 22.",
      "gs.field.path": "<strong>Remote path</strong> — e.g. <code>/var/www</code> or <code>/</code>.",
      "gs.field.letter": "<strong>Drive letter</strong> — the app suggests a free one.",
      "gs.field.auth": "<strong>Sign-in method</strong> — password, SSH key, or ask each time.",
      "gs.firstconn.finish": "Save, then click the toggle in the connection card. If everything is correct, the drive turns green and appears in Explorer.",
      "gs.h.next": "Next steps",

      // ─── docs: connections ────────────────────────────────────
      "conn.title": "Adding connections",
      "conn.lead": "All fields in the connection dialog explained — and how the drive gets mounted.",
      "conn.h.dialog": "Connection dialog",
      "conn.th.field": "Field",
      "conn.th.desc": "Description",
      "conn.th.default": "Default",
      "conn.f.name": "Display name, also used as the drive label.",
      "conn.f.host": "Hostname or IP address of the SSH server.",
      "conn.f.user": "SSH username on the remote server.",
      "conn.f.port": "SSH port.",
      "conn.f.path": "The folder on the server to mount as a drive.",
      "conn.f.letter": "Windows drive letter (e.g. Z:).",
      "conn.f.auth": "<code>password</code>, <code>key</code>, or <code>ask</code>.",
      "conn.f.password": "Stored locally in the encrypted SQLite database.",
      "conn.f.keypath": "Path to your OpenSSH key file (only for the “key” method). Used for mounts (sshfs.exe) and the native SSH client.",
      "conn.f.puttykeypath": "Path to your PuTTY key in <code>.ppk</code> format. Used exclusively for PuTTY terminal sessions. Convert with PuTTYgen.",
      "conn.f.cli": "Allows access from the CLI companion.",
      "conn.h.mount": "Mounting a drive",
      "conn.mount.body": "Click the toggle on the right side of the connection card. When successful, the toggle turns green and the drive appears in Explorer.",
      "conn.h.unmount": "Unmounting a drive",
      "conn.unmount.body": "Click the (now green) toggle again. If that fails, fallback methods are tried automatically.",
      "conn.h.tips": "Tips",
      "conn.tip1": "Enable <strong>Restore mounts on start</strong> in Settings so your drives reconnect automatically when you open the app.",
      "conn.tip2": "If you see <em>“mount point in use”</em>: Settings → <em>Clean up stale mounts</em>.",
      "conn.tip3": "Multiple connections to the same server are allowed — just use a different drive letter for each.",

      // ─── docs: authentication ─────────────────────────────────
      "auth.title": "Authentication",
      "auth.lead": "Three SSH sign-in methods — password, private key, or ask each time. This section shows how they work and where credentials are stored.",
      "auth.h.password": "Save password",
      "auth.password.body": "Enter your SSH password once. It is used automatically when mounting drives. In the SSH terminal, automatic password entry is <strong>only supported with PuTTY</strong> (Settings → \"Use PuTTY\"). With the native OpenSSH client you must type the password manually — this is a deliberate security restriction.",
      "auth.password.storage": "The password is stored locally in the SQLite database — encrypted per app user with AES-256-GCM and decrypted only after app sign-in.",
      "auth.h.key": "SSH key",
      "auth.key.body": "Provide the path to your private OpenSSH key (e.g. <code>C:\\Users\\you\\.ssh\\id_ed25519</code>). The key is used automatically when mounting drives and when using the native SSH terminal. SSH certificates are also supported.",
      "auth.key.note": "The key should not have a passphrase so that mounts can run automatically in the background.",
      "auth.h.ppk": "PuTTY key (.ppk)",
      "auth.ppk.body": "PuTTY expects keys in its own PPK format. Enter the path to your <code>.ppk</code> file in the connection editor under <em>\"PuTTY key path\"</em>. OpenSSH keys (<code>id_ed25519</code>, <code>id_rsa</code>) go in the <em>\"SSH key path\"</em> field and are only used for the native SSH client and SSHFS-Win. You can convert between formats using <strong>PuTTYgen</strong>.",
      "auth.ppk.note": "If a PPK path is set, PuTTY uses it. Otherwise it falls back to the OpenSSH key path — with a log warning if the file does not end in .ppk.",
      "auth.h.ask": "Ask each time",
      "auth.ask.body": "No password is stored — a prompt appears every time you connect. Useful for:",
      "auth.ask.li1": "Servers where you don't want credentials stored locally.",
      "auth.ask.li2": "Accounts with rotating passwords.",
      "auth.ask.li3": "Servers with two-factor authentication.",
      "auth.h.encryption": "How are passwords protected?",
      "auth.encryption.body": "When you sign in to the app, a key is derived from your profile password and kept only in memory. All SSH credentials are encrypted with this key. When you sign out, the key is immediately discarded.",
      "auth.key.unattended": "For unattended use (e.g. auto-mount on startup), use the SSH key method with a key that has no passphrase.",
      "auth.h.password.storage": "Where is the password stored?",
      "auth.password.li1": "If <code>keyring</code> is available (default): in the <strong>Windows Credential Manager</strong>, DPAPI-encrypted and tied to the Windows user.",
      "auth.password.li2": "<code>config.json</code> then contains <em>no</em> plain-text password — only a marker <code>_has_password</code>.",
      "auth.password.li3": "In the multi-user database the password is additionally stored symmetrically encrypted with a key derived from your login password.",
      "auth.key.mount": "When mounting, the path is passed to <code>sshfs.exe</code> via <code>-oIdentityFile=…</code>. The following options are also set:",
      "auth.key.batchmode": "This prevents SSH from prompting interactively for a password if the key is missing or incorrect — it aborts instead.",
      "auth.key.cert": "SSH certificates work the same way — the signed public key must be placed next to the private key as <code>&lt;key&gt;-cert.pub</code>; OpenSSH and SSHFS-Win find it automatically.",

      // ─── docs: cli ────────────────────────────────────────────
      "cli.title": "CLI companion",
      "cli.lead": "Use SSH connections from scripts or automations — no login dialog needed.",
      "cli.h.concept": "How does it work?",
      "cli.concept.body": "<code>NeoSSHWinManager-cli.exe</code> is a separate console app that communicates with the running main app. Enable CLI access for a connection and get an access key — use it from any script to connect instantly.",
      "cli.h.prereq": "Requirements",
      "cli.prereq.li1": "The main app is running and you are signed in.",
      "cli.prereq.li2": "<strong>CLI access</strong> is enabled for the connection.",
      "cli.prereq.li3": "You have the access key (visible in the connection editor).",
      "cli.h.examples": "Examples",
      "cli.h.interactive": "Interactive SSH session",
      "cli.h.command": "Run a single command",
      "cli.h.flags": "Options",
      "cli.th.flag": "Option",
      "cli.th.desc": "Description",
      "cli.flag.connect": "Access key for the connection.",
      "cli.flag.alias": "Alias (alternative spelling).",
      "cli.flag.exec": "Optional: run a command instead of an interactive shell.",
      "cli.h.exit": "Exit codes",
      "cli.exit.0": "<code>0</code> — Success.",
      "cli.exit.1": "<code>1</code> — Error (app not running, not signed in, invalid key).",
      "cli.exit.2": "<code>2</code> — Missing arguments.",
      "cli.security.title": "Security note",
      "cli.security.body": "The access key is only transferred locally — never over the network. Don't put keys in plain text in scripts or repositories; read them from a local <code>.env</code> file or the Credential Manager instead.",

      // ─── docs: configuration ─────────────────────────────────
      "cfg.title": "Settings",
      "cfg.lead": "Everything you can configure in the Settings dialog.",
      "cfg.h.location": "Where settings are stored",
      "cfg.location.body": "Settings are saved in <code>%APPDATA%\\SSHWinManager\\config.json</code>. Connections and user profiles are stored in a separate database in the same folder.",
      "cfg.h.general": "General",
      "cfg.th.setting": "Setting",
      "cfg.th.default": "Default",
      "cfg.th.effect": "Effect",
      "cfg.s.startup": "Start with Windows",
      "cfg.s.startup.d": "off",
      "cfg.s.startup.e": "The app launches automatically when you sign in to Windows.",
      "cfg.s.tray": "Minimise to tray",
      "cfg.s.tray.d": "on",
      "cfg.s.tray.e": "Closing the window minimises to the system tray instead of quitting.",
      "cfg.s.autologin": "Auto-login with Windows account",
      "cfg.s.autologin.d": "off",
      "cfg.s.autologin.e": "Skips the login screen when your Windows user matches your app profile.",
      "cfg.s.reconnect": "Auto-reconnect",
      "cfg.s.reconnect.d": "off",
      "cfg.s.reconnect.e": "Dropped drives are reconnected automatically.",
      "cfg.s.reconnectstart": "Restore mounts on start",
      "cfg.s.reconnectstart.d": "on",
      "cfg.s.reconnectstart.e": "Previously active drives are automatically mounted when the app starts.",
      "cfg.s.interval": "Check interval",
      "cfg.s.interval.d": "30 s",
      "cfg.s.interval.e": "How often the connection status is checked.",
      "cfg.s.debug": "Debug mode",
      "cfg.s.debug.d": "off",
      "cfg.s.debug.e": "Enables detailed logging and a live log window.",
      "cfg.s.putty": "Use PuTTY",
      "cfg.s.putty.d": "off",
      "cfg.s.putty.e": "Use PuTTY instead of OpenSSH for SSH terminal sessions. <strong>Only PuTTY</strong> supports automatic password entry in the terminal and PPK keys. For security reasons, automatic password login is disabled in the native SSH client.",
      "cfg.s.puttypath": "PuTTY path",
      "cfg.s.puttypath.d": "Default path",
      "cfg.s.puttypath.e": "Path to your putty.exe installation.",
      "cfg.h.theme": "Change appearance",
      "cfg.theme.body": "Settings → <em>Appearance</em> → <em>Light</em> or <em>Dark</em>. Saved per user, takes effect immediately.",
      "cfg.h.lang": "Change language",
      "cfg.lang.body": "Settings → <em>Language</em>. Available: <strong>English</strong> and <strong>German</strong>. The interface switches after restart.",
      "cfg.h.debug": "Debug mode",
      "cfg.debug.body": "Enables detailed logging to <code>%APPDATA%\\SSHWinManager\\app.log</code> and a live log window. Helpful when troubleshooting connection issues.",

      // ─── docs: troubleshooting ────────────────────────────────
      "ts.eyebrow": "Docs",
      "ts.title": "Troubleshooting",
      "ts.lead": "The most common issues with their cause and fix.",
      "ts.h.nosshfs": "\"sshfs.exe not found\"",
      "ts.nosshfs.body": "SSHFS-Win is not installed or not in the expected location. Fix: download and run the installer from",
      "ts.nosshfs.body2": ".",
      "ts.nosshfs.note": "PATH is also searched.",
      "ts.h.mountpoint": "\"mount point in use\"",
      "ts.mountpoint.body": "The selected drive letter is still occupied by an old mount.",
      "ts.mountpoint.li1": "Choose a different drive letter, or",
      "ts.mountpoint.li2": "Settings → <em>Clean up stale mounts</em>, or",
      "ts.mountpoint.li3": "Disconnect the old drive in Explorer, or",
      "ts.mountpoint.li4": "Restart Windows.",
      "ts.h.authfail": "\"Authentication failed\"",
      "ts.authfail.li1": "Check your password — edit the connection and re-enter it.",
      "ts.authfail.li2": "For SSH key: is the path correct? Does the key have a passphrase?",
      "ts.authfail.li3": "On the server: is your public key in <code>~/.ssh/authorized_keys</code>?",
      "ts.authfail.li4": "Server config: is PasswordAuthentication / PubkeyAuthentication enabled in sshd_config?",
      "ts.h.connrefused": "\"Connection refused\"",
      "ts.connrefused.body": "The SSH service is not running or a firewall is blocking the connection. Test:",
      "ts.connrefused.body2": "If this also fails, it is not an app issue.",
      "ts.connrefused.note": "From PowerShell. If this also fails, it is not an app issue.",
      "ts.h.accessdenied": "Drive appears but \"Access denied\"",
      "ts.accessdenied.body": "Reinstall SSHFS-Win and verify that the WinFsp service is running (Services → WinFsp).",
      "ts.accessdenied.note": "If the issue persists: reinstall SSHFS-Win and verify that the WinFsp service is running (services.msc).",
      "ts.h.nostart": "App doesn’t start or doesn’t come to the foreground",
      "ts.nostart.body": "Another instance is already running. Check the system tray — the app may be minimised. If not, end it in Task Manager and restart.",
      "ts.nostart.li1": "Check the tray — the app may be minimised.",
      "ts.nostart.li2": "Find NeoSSHWinManager.exe in Task Manager and end it.",
      "ts.h.logs": "View logs",
      "ts.logs.body": "Enable Debug mode in Settings. Logs are saved to <code>%APPDATA%\\SSHWinManager\\app.log</code>.",

      // ─── docs: developer / project-structure ─────────────────
      "dev.ps.title": "Project structure",
      "dev.ps.lead": "A tour of the repository for contributors and curious readers.",
      "dev.ps.h.toplevel": "Directory overview",
      "dev.ps.h.modules": "Main modules",
      "dev.ps.h.ui": "UI modules",
      "dev.ps.th.file": "File",
      "dev.ps.th.role": "Responsibility",
      "dev.ps.h.models": "Data models",
      "dev.ps.h.release": "Build & release process",
      "dev.ps.main.intro": "Entry-Point der GUI. Tut der Reihe nach:",
      "dev.ps.main.li1": "Lädt die Konfig (<code>config.AppSettings.load()</code>).",
      "dev.ps.main.li2": "Erzwingt Single-Instance (<code>SingleInstance(\"SSHWinManager_Mutex_v1\")</code>).",
      "dev.ps.main.li3": "Initialisiert <code>QApplication</code> mit dem gespeicherten Theme.",
      "dev.ps.main.li4": "Zeigt Login-Window (außer Auto-Login greift) → Hauptfenster.",
      "dev.ps.main.li5": "Startet <code>IPCServer</code> in einem Worker-Thread.",
      "dev.ps.cli.body": "Argparse-CLI. Verbindet sich mit <code>\\\\.\\pipe\\SSHWinManager_IPC_v1</code>, sendet einen JSON-Request <code>{op:\"connect\", key:\"…\", exec:\"…\"}</code>, erhält Credentials zurück und ruft dann <code>ssh_launcher.spawn_session()</code> auf.",
      "dev.ps.config.li1": "<code>AppSettings</code> — Dataclass mit Defaults (Theme, Sprache, PuTTY-Pfad, Auto-Reconnect, Check-Intervall, Tray, Debug, …).",
      "dev.ps.config.li2": "<code>load()</code>/<code>save()</code> — JSON in <code>%APPDATA%\\SSHWinManager\\config.json</code>.",
      "dev.ps.config.li3": "Migrations: fehlende Keys werden mit Defaults aufgefüllt.",
      "dev.ps.db.li1": "SQLite, Pfad: <code>%APPDATA%\\SSHWinManager\\app.db</code>.",
      "dev.ps.db.li2": "Tabellen: <code>users</code>, <code>connections</code>, <code>settings_per_user</code>.",
      "dev.ps.db.li3": "Schema-Version in <code>PRAGMA user_version</code>; <code>migrate()</code> fügt neue Spalten idempotent hinzu.",
      "dev.ps.auth.li1": "<code>UserManager</code> — anlegen, einloggen, Passwort ändern, löschen.",
      "dev.ps.auth.li2": "Passwort-Hash: PBKDF2-HMAC-SHA256, per-User Salt, 200k Iterations.",
      "dev.ps.auth.li3": "Session-Key wird beim Login abgeleitet und hält nur im RAM.",
      "dev.ps.auth.li4": "<code>UserConnectionManager</code> — CRUD für Verbindungen, automatische En/Decryption pro User.",
      "dev.ps.sshfs.li1": "<code>SSHFSController.mount(connection, password=None)</code> — baut die Argumentliste, startet <code>sshfs.exe</code> als detached Subprocess.",
      "dev.ps.sshfs.li2": "<code>unmount(letter)</code> — drei Strategien (siehe <a href=\"../connections.html\" data-i18n=\"side.connections\">Verbindungen</a>).",
      "dev.ps.sshfs.li3": "<code>list_mounts()</code> — parst fsutil-Output.",
      "dev.ps.sshfs.li4": "<code>status_for(connection)</code> — gibt <code>\"mounted\"</code>, <code>\"unmounted\"</code> oder <code>\"stale\"</code> zurück.",
      "dev.ps.launcher.body": "Startet eine interaktive SSH-Session. Wählt OpenSSH oder PuTTY je nach <code>AppSettings.use_putty</code>. Übergibt Key oder Passwort sicher.",
      "dev.ps.ipc.body": "Worker-Thread mit Named-Pipe-Server. Akzeptiert JSON-Requests, validiert Access-Key gegen die DB, gibt entschlüsselte Credentials zurück.",
      "dev.ps.ui.login": "Login-Form, Setup-Wizard für Erstprofil.",
      "dev.ps.ui.main": "Hauptfenster: Sidebar + Verbindungsliste + Statusbar.",
      "dev.ps.ui.tray": "System-Tray-Icon mit Schnellzugriff-Menü.",
      "dev.ps.ui.card": "Kachel pro Verbindung mit Mount-Toggle.",
      "dev.ps.ui.toggle": "Custom Switch mit Cyan/Grün-States + Spinner.",
      "dev.ps.ui.addedit": "Verbindung anlegen / bearbeiten.",
      "dev.ps.ui.settings": "App-weite Einstellungen.",
      "dev.ps.ui.ask": "Passwort-Abfrage für „Jedes Mal fragen”.",
      "dev.ps.ui.debug": "Live-Log-Viewer mit Filter.",
      "dev.ps.release.li1": "Version in <code>file_version_info.txt</code>, README und <code>changelog.html</code> erhöhen.",
      "dev.ps.release.li2": "<code>.\\build_dual.ps1</code> ausführen — baut GUI- und CLI-EXE per PyInstaller in <code>dist/</code>.",
      "dev.ps.release.li3": "Beide EXEs lokal testen (Login, ein Mount, ein CLI-Aufruf).",
      "dev.ps.release.li4": "Tag setzen: <code>git tag v1.x.0 &amp;&amp; git push --tags</code>.",
      "dev.ps.release.li5": "Auf GitHub neues Release anlegen, beide EXEs anhängen, Changelog einfügen.",

      // ─── docs: developer / api ────────────────────────────────
      "dev.api.title": "API reference",
      "dev.api.lead": "Key classes and methods for contributors and developers.",
      "dev.api.h.auth": "Authentication flow",
      "dev.api.h.mount": "Mount / unmount flow",
      "dev.api.h.cli": "CLI IPC flow",
      "dev.api.h.pipe": "Pipe protocol",
      "dev.api.h.settings": "Settings flow",
      "dev.api.h.public": "Public classes & methods",
      "dev.api.th.method": "Method",
      "dev.api.th.desc": "Description",
      "dev.api.h.gendoc": "Generated API docs (optional)",
      "dev.api.auth.li1": "The user enters username + password in the login window.",
      "dev.api.auth.li2": "<code>UserManager.authenticate(username, password)</code> compares the hash, derives the session key on success, and returns it.",
      "dev.api.auth.li3": "The session key is passed into <code>UserConnectionManager</code> and kept only in that instance.",
      "dev.api.auth.li4": "When a connection is read, the encrypted password is decrypted with the session key.",
      "dev.api.auth.li5": "On logout: <code>UserConnectionManager.dispose()</code> removes the key from RAM.",
      "dev.api.mount.li1": "The UI calls <code>SSHFSController.mount(connection)</code> in a worker thread.",
      "dev.api.mount.li2": "For <code>auth_method=\"ask\"</code>: password modal; otherwise <code>connection.password</code> or <code>connection.key_path</code>.",
      "dev.api.mount.li3": "The argument list is built and <code>sshfs.exe</code> is started as a detached subprocess.",
      "dev.api.mount.li4": "After 3 s, <code>list_mounts()</code> validates whether the drive is available.",
      "dev.api.mount.li5": "The UI receives a <code>mount_state_changed(connection_id, \"mounted\"|\"failed\", error_text)</code> signal.",
      "dev.api.mount.li6": "Unmount: <code>SSHFSController.unmount(letter)</code> with the fallback chain.",
      "dev.api.settings.li1": "The settings dialog modifies the <code>AppSettings</code> instance.",
      "dev.api.settings.li2": "<code>AppSettings.save()</code> writes JSON.",
      "dev.api.settings.li3": "The <code>settings_changed</code> signal is emitted.",
      "dev.api.settings.li4": "Theme: <code>QApplication.setStyleSheet(load_theme(name))</code> — no restart needed.",
      "dev.api.settings.li5": "Language: <code>i18n.set_locale(code)</code>; all widgets re-render through <code>retranslate_ui()</code>.",
      "dev.api.desc.load": "Reads <code>config.json</code>, merges it with defaults, and returns an instance.",
      "dev.api.desc.save": "Writes current values as JSON.",
      "dev.api.desc.reset": "Resets everything to defaults and persists it.",
      "dev.api.desc.createUser": "Creates a new user and hashes the password.",
      "dev.api.desc.authenticate": "Login. Returns the derived session key on success.",
      "dev.api.desc.changePassword": "Re-encrypts all connection passwords with the new session key.",
      "dev.api.desc.deleteUser": "Cascade-deletes connections.",
      "dev.api.desc.list": "All connections for the current user.",
      "dev.api.desc.get": "One connection — password decrypted.",
      "dev.api.desc.createConn": "Creates and persists the encrypted password. Returns the ID.",
      "dev.api.desc.updateConn": "Re-encrypt &amp; persist.",
      "dev.api.desc.deleteConn": "Delete.",
      "dev.api.desc.byAccessKey": "Used by the IPC server for CLI lookup.",
      "dev.api.desc.mount": "Starts a mount. Returns status plus stderr if present.",
      "dev.api.desc.unmount": "Unmounts cleanly, with fallback strategies.",
      "dev.api.desc.listMounts": "Current mounts.",
      "dev.api.desc.statusFor": "<code>\"mounted\" / \"unmounted\" / \"stale\"</code>.",
      "dev.api.desc.cleanup": "Cleans up stale mount points.",
      "dev.api.variant.pdoc": "Option A — pdoc",
      "dev.api.variant.mkdocs": "Option B — MkDocs Material + mkdocstrings",

      // ─── features page ────────────────────────────────────────
      "fp.hero.title": "Everything the app can do.",
      "fp.hero.lead": "A full overview of all features in NEO SSH-Win Manager — simply explained.",
      "fp.s1.eyebrow": "SSH drives",
      "fp.s1.title": "Remote folder as a Windows drive.",
      "fp.s1.sub": "One click — and the server folder appears like a local disk in Explorer.",
      "fp.oneclick.title": "One-click mount",
      "fp.oneclick.body": "One click mounts the remote folder as a Windows drive letter — no command-line knowledge needed.",
      "fp.autoletter.title": "Automatic drive letter",
      "fp.autoletter.body": "The app finds a free letter and avoids conflicts with existing drives automatically.",
      "fp.unmount.title": "Clean unmount",
      "fp.unmount.body": "Drives are disconnected cleanly. If that fails, fallback methods are tried automatically.",
      "fp.label.title": "Drive label",
      "fp.label.body": "The connection name appears directly as the drive label in Explorer.",
      "fp.reconnect.title": "Auto-reconnect",
      "fp.reconnect.body": "Dropped connections are restored automatically — e.g. after a brief network outage.",
      "fp.startup.title": "Restore drives on start",
      "fp.startup.body": "The app remembers active drives and mounts them again automatically after a restart.",
      "fp.s2.eyebrow": "Authentication & security",
      "fp.s2.title": "Secure and effortless.",
      "fp.pw.title": "Passwordless mounts — no SSH key needed",
      "fp.pw.body": "Enter your password once — it is used automatically when mounting drives. No SSH key needed. For automatic password login in the terminal, enable PuTTY in Settings.",
      "fp.key.title": "SSH key & certificate",
      "fp.key.body": "Standard SSH keys and certificates are supported and used automatically when connecting.",
      "fp.ask.title": "Ask each time",
      "fp.ask.body": "For servers where no password should be stored — a prompt appears on each connection.",
      "fp.crypto.title": "Encrypted credentials",
      "fp.crypto.body": "All saved SSH passwords are encrypted locally — the key comes from your app login.",
      "fp.singleinstance.title": "Single instance",
      "fp.singleinstance.body": "The app only runs once — a second launch brings the existing window to the front.",
      "fp.multiuser.title": "Multiple profiles",
      "fp.multiuser.body": "Multiple users on one PC, each with their own connections and credentials.",
      "fp.s3.eyebrow": "Interface & design",
      "fp.s3.title": "Easy to use. Enjoyable to look at.",
      "fp.terminal.title": "Built-in terminal",
      "fp.terminal.body": "Open an SSH session with one click — OpenSSH or PuTTY. With PuTTY the password is entered automatically; with the native SSH client, type it manually in the terminal.",
      "fp.sysinfo.title": "Live system info",
      "fp.sysinfo.body": "CPU, RAM, disk, uptime and load right in the connection card — no extra tools.",
      "fp.tray.title": "System tray",
      "fp.tray.body": "The app runs quietly in the tray. Mount or unmount drives without opening the main window.",
      "fp.theme.title": "Modern design",
      "fp.theme.body": "A polished interface with light and dark themes — per-user preference.",
      "fp.lang.title": "German & English",
      "fp.lang.body": "Language per user. The interface switches after restart.",
      "fp.autostart.title": "Start with Windows",
      "fp.autostart.body": "The app can start automatically at Windows login — as a tray app in the background.",
      "fp.s4.eyebrow": "Automation",
      "fp.s4.title": "CLI companion for scripts.",
      "fp.s4.sub": "Use connections from scripts or automations — with an access key, no login dialog needed.",
      "fp.cli.note": "Enable CLI access in the connection settings and generate an access key.",

      // ─── download page ────────────────────────────────────────
      "dl.eyebrow": "Latest version:",
      "dl.title": "Download.",
      "dl.lead": "NEO SSH-Win Manager is free and open source. Just download and run — no installation needed.",
      "dl.gui.badge": "Recommended",
      "dl.gui.title": "NeoSSHWinManager.exe",
      "dl.gui.desc": "The main application with everything: connection manager, tray, multiple user profiles, live system info.",
      "dl.gui.size": "~25 MB · Windows 10 / 11 (x64)",
      "dl.gui.btn": "Download GUI",
      "dl.cli.badge": "Optional",
      "dl.cli.title": "NeoSSHWinManager-cli.exe",
      "dl.cli.desc": "Console companion for scripts and automations. Uses connections from the running main app.",
      "dl.cli.size": "~10 MB · requires running GUI",
      "dl.cli.btn": "Download CLI",
      "dl.smartscreen.title": "Windows SmartScreen",
      "dl.smartscreen.body": "The app is not code-signed (open-source project). Windows may show a warning on first run. Click “More info” → <em>Run anyway</em>. Only download from the official",
      "dl.smartscreen.body2": ".",
      "dl.prereq.eyebrow": "Prerequisites",
      "dl.prereq.title": "Two free programs are required.",
      "dl.prereq.sub": "These handle SSH mounting in the background — NEO SSH-Win Manager is the user interface on top.",
      "dl.prereq.th.comp": "Program",
      "dl.prereq.th.what": "Purpose",
      "dl.prereq.th.dl": "Download",
      "dl.prereq.winfsp.what": "Provides the filesystem interface for Windows.",
      "dl.prereq.sshfswin.what": "Connects SSH to the filesystem.",
      "dl.prereq.win.what": "x64. Other versions are not tested.",
      "dl.prereq.win.dl": "—",
      "dl.prereq.openssh.what": "Optional, for the built-in terminal feature.",
      "dl.prereq.openssh.dl": "Windows feature (pre-installed)",
      "dl.order.title": "Installation order",
      "dl.order.li1": "Install WinFsp.",
      "dl.order.li2": "Install SSHFS-Win.",
      "dl.order.li3": "Download <code>NeoSSHWinManager.exe</code> — no setup needed, just run it.",
      "dl.order.li4": "Launch the app, create a user profile, and add your first connection.",
      "dl.src.eyebrow": "Build from source",
      "dl.src.title": "Compile it yourself.",
      "dl.src.sub": "With Python 3.11+ and PyInstaller.",
      "dl.src.run": "# Run directly from source",
      "dl.src.build": "# Build both EXE files (GUI + CLI)",
      "dl.src.note": "Output files are in the <code>dist/</code> folder.",
    },
  };

  const STORAGE_KEY = "neo-ssh-lang";
  const DEFAULT = "de";
  const SUPPORTED = ["de", "en"];

  /** @type {Set<(lang: string) => void>} */
  const listeners = new Set();

  // In-memory cache so language changes survive localStorage being blocked
  // (e.g. file:// protocol). Initialised once from storage on first load.
  let _lang = (() => {
    try {
      const s = localStorage.getItem(STORAGE_KEY);
      return s && SUPPORTED.includes(s) ? s : DEFAULT;
    } catch {
      return DEFAULT;
    }
  })();

  /** @returns {string} */
  function getLang() {
    return _lang;
  }

  /**
   * Look up a translation string.
   * @param {string} key Dot-notation key, e.g. "hero.title".
   * @param {string} [fallback] Fallback if the key is missing in current lang.
   * @returns {string}
   */
  function t(key, fallback) {
    const lang = getLang();
    return DICT[lang]?.[key] ?? DICT[DEFAULT]?.[key] ?? fallback ?? key;
  }

  /**
   * Translate every [data-i18n] / [data-i18n-attr] node under `root`.
   * @param {ParentNode} [root=document]
   */
  function apply(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!key) return;
      const val = t(key, el.textContent);
      // Allow simple inline HTML (e.g. <code>) inside translations.
      if (/[<>]/.test(val)) el.innerHTML = val;
      else el.textContent = val;
    });
    scope.querySelectorAll("[data-i18n-attr]").forEach((el) => {
      const spec = el.getAttribute("data-i18n-attr") || "";
      // Format: "attr1:key1;attr2:key2"
      spec.split(";").forEach((pair) => {
        const [attr, key] = pair.split(":").map((s) => s && s.trim());
        if (attr && key) el.setAttribute(attr, t(key, el.getAttribute(attr) || ""));
      });
    });
    // Update <html lang> for assistive tech.
    document.documentElement.setAttribute("lang", getLang());
  }

  /**
   * Set a new language, persist it, and re-translate the whole page.
   * @param {string} code
   */
  function setLang(code) {
    if (!SUPPORTED.includes(code)) return;
    _lang = code;
    try {
      localStorage.setItem(STORAGE_KEY, code);
    } catch {}
    apply(document);
    listeners.forEach((fn) => {
      try {
        fn(code);
      } catch {}
    });
  }

  /**
   * Subscribe to language changes.
   * @param {(code: string) => void} fn
   */
  function onChange(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  }

  // Apply once on first paint and again on full DOM ready.
  apply(document);
  document.addEventListener("DOMContentLoaded", () => apply(document));

  window.neoI18n = { getLang, setLang, t, apply, onChange, SUPPORTED };
})();

