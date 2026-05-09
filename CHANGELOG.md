# Changelog

All notable changes to NEO SSH-Win Manager are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.3] — 2026-05-09

### Security
- **CLI Keys Migration:** Plaintext CLI-access-keys are now automatically encrypted on first login after update (security: closes legacy plaintext path)
- **SSH Command Building:** Maintains `StrictHostKeyChecking=accept-new` and proper `known_hosts` verification

### Features
- **SysInfo over Password:** System information can now be retrieved for password-based SSH connections (via SSH_ASKPASS protocol)
- **Auto-Login over Password:** Works with both PuTTY and native SSH for password-authenticated connections

### UX Improvements
- **Name Field Hint:** Add/Edit dialog now shows allowed characters for connection names ("Letters, numbers, spaces, hyphens, underscores, dots")
- **About Dialog:** New "What It Does" section explaining app features; consistent 3-button layout for both Project and Author links
- **SysInfo Error Overlay:** Key-missing state now shows 🤷 shrug emoji and properly displays German translation (fixes cross-thread translation bug)

### Changed
- `sysinfo.key_required` message now indicates both SSH keys and passwords are supported
- `sysinfo.key_missing` title clarified as "Authentication Required"
- SSH native client now supports `BatchMode=no` for password auth (instead of enforcing `BatchMode=yes`)
- Password auth for SysInfo uses OpenSSH's official `SSH_ASKPASS` protocol (secure, non-interactive)

### Files Modified
- `src/auth_manager.py` – CLI key migration
- `src/database.py` – Permission logging
- `src/ui/dialogs/about_dialog.py` – About dialog improvements
- `src/ui/dialogs/add_edit_dialog.py` – Name field hint
- `src/ui/system_info_panel.py` – Password auth for SysInfo, error type detection
- `main.py` – SSH_ASKPASS helper activation
- `src/translations/en.json` – Messages for new features
- `src/translations/de.json` – German translations

---

## [1.3.2] — Earlier

(Earlier releases documented separately if needed)
