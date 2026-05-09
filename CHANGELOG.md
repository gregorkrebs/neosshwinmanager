# Changelog

All notable changes to NEO SSH-Win Manager are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.3] — 2026-05-09

### Security
- **CLI Keys Migration:** Plaintext CLI-access-keys are now automatically encrypted on first login after update (closes legacy plaintext path)
- **SSH Command Building:** Maintains `StrictHostKeyChecking=accept-new` and proper `known_hosts` verification
- **Security Level Enforcement in SysInfo:** System info retrieval now respects the configured security level — Level 0/1 requires an SSH key; Level 2 additionally permits password auth
- **Password via SSH_ASKPASS:** Password-based SysInfo always uses native `ssh.exe` + `SSH_ASKPASS` protocol, even when PuTTY is active — avoids exposing the password via plink's `-pw` flag in the process list

### Features
- **SysInfo over Password:** System information can now be retrieved for password-based SSH connections (via SSH_ASKPASS protocol)
- **Auto-Login over Password:** Works with both PuTTY and native SSH for password-authenticated connections
- **SysInfo Auth Denied Overlay:** When SysInfo retrieval is blocked by the security level, a 🤷 shrug overlay is shown with a neutral explanation instead of a generic error

### Fixed
- **Drive Unmount Crash:** Prevented crash when a drive was unmounted while the UI was still referencing it (#1)
- **QMessageBox Dark Mode:** Corrected background color of message boxes in dark mode (#3)
- **F2 Debug Crash:** Prevented crash when pressing F2 on non-standard widgets (#4)
- **SysInfo always showing "No SSH Key":** Settings were not passed to `SSHSystemInfoThread`, causing the security level to always default to 0 — now correctly forwarded
- **Auth error always showing "Level 0":** Fixed security level display in auth-denied overlay — now shows the actual configured level
- **PuTTY password error in English:** PuTTY terminal error messages (`pw_disabled`, `pw_missing`) are now available in English and German via i18n
- **Copy button not centered in error popup:** Icon in error popup copy button was offset due to wrong CSS object name (`actionBtn`) — switched to `rpHeaderBtn` with correct icon-only styling
- **Auth validation with password connections:** `_validate_auth` now uses `auth_method == "password"` (config intent) instead of `bool(conn.password)` (runtime value) — prevents false "no auth" errors when decryption returns empty string

### UX
- **Name Field Hint:** Add/Edit dialog now shows allowed characters for connection names
- **About Dialog:** New "What It Does" section; consistent 3-button layout for Project and Author links
- **Neutral auth error messages:** Auth-denied overlay messages no longer suggest raising the security level — only state what is missing and where to configure it
- **SysInfo error: clean overlay:** When the 🤷 overlay is shown, the hero card (connection name, host, path) is now hidden so no background text bleeds through

### Files Modified
- `src/auth_manager.py` – CLI key migration
- `src/database.py` – Permission logging
- `src/ui/dialogs/about_dialog.py` – About dialog improvements
- `src/ui/dialogs/add_edit_dialog.py` – Name field hint
- `src/ui/system_info_panel.py` – Security level enforcement, SSH_ASKPASS fallback, auth validation, overlay UX
- `src/ssh_launcher.py` – i18n for PuTTY error messages
- `src/ui/main_window.py` – Copy button fix in error popup
- `main.py` – SSH_ASKPASS helper activation
- `src/translations/en.json` – Auth level messages, PuTTY error messages
- `src/translations/de.json` – German translations for all new keys

---

## [1.3.2] — Earlier

(Earlier releases documented separately if needed)
