# NEO SSH-Win Manager

A modern, dark-themed Windows desktop app for mounting remote SSH filesystems as Windows drive letters — built on top of [**sshfs-win**](https://github.com/winfsp/sshfs-win) and [**WinFsp**](https://github.com/winfsp/winfsp).

Manage multiple SSH connections, mount them with one click, switch languages per user, and browse remote paths in Windows Explorer as if they were local drives.

## Credits / History

The idea for this tool was inspired by the original **SSHWinManager**, which was written in JavaScript / Electron by a different author.

**NEO SSH-Win Manager is a complete, from-scratch rewrite in Python (PyQt6)** developed jointly by [**Den4ik53**](https://github.com/Den4ik53) and [**Gregor Krebs**](https://github.com/gregorkrebs). No code from the original project is reused. The goals, scope and architecture have changed substantially:

- Native Python / PyQt6 stack instead of Electron
- Multi-user support with per-user encrypted SSH credential storage (SQLite + cryptography)
- Per-user language preference (English / German, easily extensible)
- Per-connection system info panel (CPU, RAM, disk, load, uptime via SSH)
- Optional CLI access key for agent/automation integration
- System tray with quick mount toggles
- Optional PuTTY / OpenSSH terminal launch per connection

## Features

- Add / edit / delete SSH connections with full form validation
- One-click mount / unmount per connection — appears in Windows Explorer instantly
- Password or SSH private key authentication (passwords encrypted at rest with a user-derived key)
- Per-user accounts with login, password change and user management
- Auto drive-letter detection (free letters only)
- Live system info panel per connection (OS, CPU, memory, disk, uptime, temperature)
- System tray with quick mount toggles, minimize to tray
- "Start with Windows" and "Auto-reconnect on connection loss" options
- Ghost-drive cleanup and Explorer restart helpers
- Translation system (English / German) selectable per user
- Optional CLI companion executable for scripting / agents

## Prerequisites

Install these before running the app:

| Tool | Download |
|------|----------|
| **WinFsp** | https://github.com/winfsp/winfsp/releases |
| **SSHFS-Win** | https://github.com/winfsp/sshfs-win/releases |
| **Python 3.11+** (for running from source) | https://www.python.org/downloads/ |

## Quick Start (Development)

```bat
git clone https://github.com/<your-user>/neosshwinmanager.git
cd neosshwinmanager

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

On first launch you will be prompted to create an admin user. All SSH credentials you enter afterwards are encrypted with a key derived from that user's password.

## Build as .exe

A PyInstaller spec file (`NeoSSHWinManager.spec`) and a PowerShell build script (`build_dual.ps1`) are included. The dual build produces both:

- `NeoSSHWinManager.exe` — the GUI app (windowed subsystem)
- `NeoSSHWinManager-cli.exe` — the CLI companion (console subsystem) used for scripted CLI access

```powershell
.\build_dual.ps1
```

Outputs land in `dist/`.

## Project Layout

```
neosshwinmanager/
├── main.py                        # GUI entry point
├── cli_main.py                    # CLI entry point (companion exe)
├── requirements.txt
├── NeoSSHWinManager.spec            # PyInstaller spec
├── build_dual.ps1                 # Dual-build helper (GUI + CLI exe)
├── assets/                        # App icons
├── src/
│   ├── config.py                  # Data models + JSON config
│   ├── database.py                # SQLite schema + migrations
│   ├── auth_manager.py            # Users, sessions, encrypted credentials
│   ├── connection_manager.py      # Connection CRUD
│   ├── sshfs_controller.py        # Mount / unmount via net use
│   ├── drive_utils.py             # Drive letter helpers
│   ├── i18n.py                    # Translation loader
│   ├── translations/
│   │   ├── en.json                # English (default)
│   │   └── de.json                # German
│   └── ui/
│       ├── main_window.py
│       ├── connection_card.py
│       ├── system_info_panel.py
│       ├── system_tray.py
│       ├── theme.py
│       └── dialogs/
│           ├── add_edit_dialog.py
│           ├── settings_dialog.py
│           ├── about_dialog.py
│           ├── login_dialog.py
│           └── system_info_dialog.py
└── tests/
    └── test_config.py
```

## How Mounting Works

sshfs-win exposes remote SSH paths under a UNC format that Windows `net use` understands:

```
net use X: \\sshfs.r\user@host!22\var\www /persistent:no
```

The app builds this command automatically from the connection settings and tracks mount state via drive enumeration.

## Languages

Language is stored per user. To add a new language:

1. Copy `src/translations/en.json` to `src/translations/<code>.json` and translate the values.
2. Add the code to `_SUPPORTED` in `src/i18n.py` and the label map in `src/ui/dialogs/settings_dialog.py`.
3. Restart the app.

Missing keys automatically fall back to English.

## Run Tests

```bat
python -m pytest tests/ -v
```

## License

[MIT](LICENSE) — do whatever you want with it. Attribution is appreciated but not required.
