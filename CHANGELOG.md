# Changelog

All notable changes to NEO SSH-Win Manager are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.3] — 2026-05-09

### Security
- **CWE-312 · Connection Metadata Encryption:** Host, username, connection name and remote path are now encrypted with AES-256-GCM (using the per-user `enc_key`) before being stored in the database. Existing entries are migrated automatically on first login. Plaintext columns are zeroed out after migration — the SQLite file no longer exposes server addresses or usernames at rest.
- **CWE-732 · Windows ACL hardened:** `win32security` is now a hard module-level import (was: optional with silent fallback). A missing `pywin32` installation now raises an explicit `ImportError` on startup rather than leaving the database file world-readable. 5 new unit tests verify ACL correctness.
- **CWE-307 · Brute-Force Protection:** Login attempts are now rate-limited per username. After 5 consecutive failures the account is locked for 30 seconds; each subsequent block doubles the lockout window (exponential backoff). The counter resets on successful login.
- **CWE-362 · Session Race Condition fixed:** `Session._current_user` is now protected by a `threading.RLock`. The `enc_key` update after a password change is performed atomically via `Session.update_enc_key()` — concurrent access can no longer observe a partially updated session object.
- **CWE-591 · Memory-Lock failures now visible:** `mlock_memory()` / `munlock_memory()` previously returned `False` silently on failure. Both functions now emit a `WARNING` log entry explaining that secrets may be swapped to disk, allowing administrators to detect and fix privilege or system configuration issues.
- **CWE-214 · CLI Key via stdin:** `--connect-cli -` now reads the access key from stdin instead of the command line, preventing exposure in process listings and shell history. The argument form still works for backwards compatibility.
- **MITM Fix documented (v1.3.2 omission):** The change from `StrictHostKeyChecking=no` to `StrictHostKeyChecking=yes` in `ssh_launcher.py` was applied in v1.3.2 but not documented. This entry corrects that omission. Any installation running v1.3.1 or earlier is vulnerable to trivial MITM attacks on SSH connections — upgrade immediately.

---

## [1.3.2] — 2026-05-09

### Security
- **Comprehensive Security Audit:** Hardened credential storage, session handling, encryption routines and key derivation across `auth_manager`, `crypto`, `database`, `ssh_launcher` and `sshfs_controller`
- **CLI Keys Migration:** Plaintext CLI-access-keys are automatically encrypted on first login after the update — closes the legacy plaintext storage path
- **Shell Injection Prevention:** Removed unsafe shell interpolation in `ssh_launcher`; added `_is_safe_label()` validation in `sshfs_controller` to block injection via mount labels
- **SSH_ASKPASS for Password Auth:** Password-based SSH connections pass the password via the `SSH_ASKPASS` environment mechanism — the password is never exposed in the process list
- **Security Level Enforcement in SysInfo:** System info retrieval respects the configured security level — Level 0/1 requires an SSH key, Level 2 additionally permits password auth
- **Connection Name Validation:** Connection names are validated on save; names containing shell metacharacters are rejected before database insertion

### Features
- **PuTTY PPK Integration:** Auto-detection and configurable PPK key path for PuTTY-based connections
- **Native SSH Terminal Improvements:** Overhauled terminal launch logic in `main_window` for both PuTTY and native OpenSSH
- **SysInfo over Password:** System information can now be retrieved for password-authenticated connections using the `SSH_ASKPASS` protocol (non-interactive, secure)
- **SysInfo Auth Overlay:** When SysInfo retrieval is blocked by the security level, a 🤷 overlay is shown with a clear, neutral explanation; connection name and host info are hidden behind the overlay
- **About Dialog Redesign:** Card layout with grouped clickable link buttons for project, documentation, GitHub and author links
- **Sidebar About Button:** Persistent About button added to the sidebar (always visible between Debug and Logout)

### Fixed
- **SSHFS Mass Disconnect Bug:** Fixed a race condition in `sshfs_controller` that caused all mounted drives to disconnect simultaneously
- **Drive Unmount Crash:** Prevented a crash when a drive was unmounted while the UI still held a reference to it (#1)
- **QMessageBox Dark Mode:** Corrected background color of message boxes in dark mode (#3)
- **F2 Crash on Non-Standard Widgets:** Prevented crash when pressing F2 on widgets that don't support the debug inspector (#4)
- **Form Scroll Behavior:** Fixed scrolling in Add/Edit connection dialog on smaller screens
- **Copy Button in Error Popup:** Icon in the error popup copy button was misaligned due to incorrect CSS object name — fixed to use icon-only button style
- **PuTTY Error Messages in English:** PuTTY terminal error messages (password login disabled, password missing) are now fully translated and available in English and German

### Changed
- **SysInfo with PuTTY Active:** When PuTTY is active but the connection uses password-only auth (level 2), sysinfo falls back to native `ssh.exe` + `SSH_ASKPASS` instead of plink's `-pw` flag
- **Add/Edit Dialog:** Live validation and allowed-character hint for connection name field
- **Theme:** Extended styling for new UI components; corrected dark mode inconsistencies
- **Translations (EN/DE):** Added i18n keys for security level messages, PuTTY errors, About dialog and new overlay states
- **Removed:** Legacy build spec files (`NeoSSHWinManager-cli.spec`, `NeoSSHWinManager.spec`)

---

## [1.3.2] — Earlier

(Earlier releases documented separately if needed)
