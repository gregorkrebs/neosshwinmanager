# Commit-Plan für v1.3.0

## Commit 1 — feat: add missing Lucide SVG icon assets
**Dateien:** `assets/icons/x.svg`, `assets/icons/arrow-right.svg`, `assets/icons/minus.svg`

```
feat: add missing Lucide SVG icon assets

x, arrow-right and minus icons were referenced by the UI but not present
in the repository, causing a FileNotFoundError on startup.
```

---

## Commit 2 — chore: remove credential_store module, clean up config
**Dateien:** `src/credential_store.py` (gelöscht), `src/config.py`

```
chore: remove legacy credential_store module

Passwords are now stored AES-GCM encrypted in the SQLite database.
credential_store.py was only used in the old JSON-based flow.
config.py docstring and imports updated accordingly.
```

---

## Commit 3 — feat: bump version to 1.3.0, neutralize AppUserModelID
**Dateien:** `main.py`, `src/single_instance.py`, `src/ui/dialogs/about_dialog.py`

```
feat: bump version to 1.3.0 and neutralize AppUserModelID

Version reflects the full UI architecture overhaul (inline panels,
full-screen settings/users, sidebar active states).
AppUserModelID prefix changed from "dennis." to "neo." for a
vendor-neutral identifier.
```

---

## Commit 4 — feat: update translations for new UI strings
**Dateien:** `src/translations/de.json`, `src/translations/en.json`

```
feat: add translation keys for inline user management and settings panels

New keys cover section headers, field labels, and status messages
introduced by the full-screen settings/users panel redesign.
```

---

## Commit 5 — feat: full-screen settings and user management panels (v1.3.0 UI overhaul)
**Dateien:** `src/ui/main_window.py`, `src/ui/connection_card.py`, `src/ui/system_info_panel.py`, `src/ui/theme.py`

```
feat: redesign UI with full-screen settings/users panels and sidebar states

- Settings and Users now open full-screen (whole window minus sidebar)
  using a QStackedWidget; clicking a sidebar icon activates it (blue)
  and switches the view; clicking again or Home returns to connections
- [i] button exclusively opens the SSH system-info panel; card click
  always shows connection details in the right panel
- Edit button is always visible in the info panel, disabled (not hidden)
  when the connection is mounted
- Connection card: transparent background behind title/path text,
  mount button reduced to 34×34 with vertically centred icon
- Right panel: fully responsive with min-width 300px, horizontal
  scrollbar only when needed; QComboBox dropdowns styled with solid
  background and correct item height
- Field value rows get subtle background/padding; rpValue transparent
  in light mode matching the label background
- System-info panel fully rewritten: list-style layout with 4px
  colour-coded progress bars for CPU/RAM/Disk
```

---

## Commit 6 — feat: add project website
**Dateien:** `website/` (alle neuen Dateien)

```
feat: add static project website

Includes landing page, feature overview, documentation pages
(getting started, connections, authentication, CLI, configuration,
troubleshooting), changelog, download page, and a PHP release-update
tool.  Fully internationalised (de/en) via assets/js/i18n.js.
```
