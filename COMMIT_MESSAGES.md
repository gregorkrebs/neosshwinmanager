# Commit Messages für die aktuellen Änderungen

## Vorschlag für GitHub-Commits

### 1. Passwort-Logging in PuTTY-Start verhindern
**Commit-Message:**
`fix(security): redact PuTTY password from debug logs`

**Enthaltene Änderungen:**
- `src/ssh_launcher.py`
- Maskierung des `-pw` Werts im Log

### 2. Einmalpasswörter sicher im Speicher halten
**Commit-Message:**
`fix(security): store askpass tokens as SecureBytes`

**Enthaltene Änderungen:**
- `src/askpass_manager.py`
- Speicherung des Passworts als `SecureBytes`
- Wipe nach Verwendung und beim Cleanup

### 3. Passwort-Mindestlänge erhöhen
**Commit-Message:**
`fix(security): require minimum password length of 8 characters`

**Enthaltene Änderungen:**
- `src/ui/dialogs/login_dialog.py`
- `src/ui/main_window.py`
- Anpassung der Passwortprüfung von 6 auf 8 Zeichen

### 4. Crash-Reports absichern
**Commit-Message:**
`fix(security): restrict crash report permissions`

**Enthaltene Änderungen:**
- `main.py`
- Anwendung der sicheren Dateiberechtigungen auf `crash_report.txt`

### 5. Security CI hinzufügen
**Commit-Message:**
`ci: add security workflow for dependency and static scans`

**Enthaltene Änderungen:**
- `.github/workflows/security.yml`
- `pip-audit`, `bandit`, `pip check`, `pytest`

## Empfohlene Reihenfolge
1. `fix(security): redact PuTTY password from debug logs`
2. `fix(security): store askpass tokens as SecureBytes`
3. `fix(security): require minimum password length of 8 characters`
4. `fix(security): restrict crash report permissions`
5. `ci: add security workflow for dependency and static scans`

## Hinweis
`SECURITY_AUDIT.md` ist als lokale Notiz markiert und soll nicht committed werden.
