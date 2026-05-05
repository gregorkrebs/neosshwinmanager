# NEO SSH-Win Manager — Website &amp; Dokumentation

Statische Showcase- und Doku-Website für **NEO SSH-Win Manager**. Kein Build-Step,
kein Framework, keine Toolchain — reines HTML, CSS und ein bisschen Vanilla-JS.

## Aufbau

```
website/
├── index.html               # Startseite (Hero + Features + Preview)
├── features.html            # Feature-Übersicht im Detail
├── download.html            # Download + Systemanforderungen + Sicherheitshinweise
├── changelog.html           # Versionshistorie
├── docs/
│   ├── getting-started.html # Installation &amp; erster Start
│   ├── connections.html     # Verbindungen anlegen
│   ├── authentication.html  # Auth-Methoden (Passwort, Key, Ask)
│   ├── configuration.html   # Settings, Theme, Sprache
│   ├── cli.html             # CLI-Companion
│   ├── troubleshooting.html # Häufige Probleme
│   └── developer/
│       ├── project-structure.html
│       └── api.html
└── assets/
    ├── css/site.css         # Komplettes Design-System
    ├── js/site.js           # Theme-Toggle, Mobile-Nav
    ├── js/layout.js         # Shared Topbar, Footer, Sidebar
    ├── icons/               # Inline-SVGs (übernommen aus Lucide-Style)
    ├── app_icon.png
    └── app_icon_only.png
```

## Lokal starten

Die Seite ist 100&nbsp;% statisch — du brauchst nur einen Mini-Webserver, damit
relative Pfade in Unter-Ordnern (`docs/`, `docs/developer/`) sauber auflösen.

### Python (überall vorhanden)

```bash
cd website
python -m http.server 4000
# http://localhost:4000
```

### Node

```bash
cd website
npx serve .
```

### VS Code

„Live Server"-Extension installieren, Rechtsklick auf `website/index.html` →
„Open with Live Server".

## Bauen

Es gibt nichts zu bauen. Die Seite ist deploy-ready, wie sie ist.

## Deployment auf GitHub Pages

1. Im Repository unter **Settings → Pages**:
   - **Source:** „Deploy from a branch"
   - **Branch:** `main` (oder der Branch deiner Wahl)
   - **Folder:** `/website`
2. Speichern. GitHub Pages serviert die Seite unter
   `https://&lt;username&gt;.github.io/&lt;repo&gt;/`.
3. Beim ersten Push aktualisiert sich die Seite automatisch.

### Eigenes Domain

`website/CNAME` mit der Domain anlegen (z.&nbsp;B. `neosshwm.example.com`),
DNS-CNAME auf `&lt;username&gt;.github.io` setzen.

### Alternative: Cloudflare Pages, Netlify, Vercel

Alle drei akzeptieren die Seite ohne Build-Command. Build Command leer lassen,
Output-Directory auf `website/` setzen.

## Inhalt aktualisieren

- **Top-/Footer-Navigation:** `website/assets/js/layout.js` (eine Quelle für alle Seiten).
- **Theme-Farben:** `website/assets/css/site.css` — die `:root` und `[data-theme="light"]`-Blöcke ganz oben.
- **Neue Doku-Seite:** Eine bestehende `docs/*.html` kopieren, Inhalt ersetzen,
  Eintrag in `layout.js` zur Sidebar (`docsSidebar()`-Funktion) hinzufügen.

## Theme &amp; Branding

Das Design folgt dem dunklen Cyber/Admin-Dashboard-Look der App:

- Akzentfarben **Cyan + Grün** wie der Mount-Toggle der App.
- JetBrains Mono für Code &amp; Labels, Inter für Body.
- Alle Farben sind als CSS Custom Properties definiert — Light- und Dark-Mode
  über `[data-theme="dark|light"]` am `<html>`-Tag, Toggle in der Topbar,
  Wahl in `localStorage`.

## i18n

Die Texte sind aktuell deutsch. Eine englische Version ist vorbereitet:

1. Dateien in `website/en/` mit denselben Pfaden anlegen.
2. In `layout.js` einen Sprachwechsel-Schalter ergänzen, der zwischen
   `/` und `/en/` umlinkt.
3. `<html lang="…">` und `data-pathprefix` entsprechend anpassen.

## Fehlende / gewünschte Screenshots

Die Seite zeigt aktuell ein gerendertes UI-Mockup. Sobald echte Screenshots
verfügbar sind, sollten sie folgende Pfade bekommen — sie sind in der README
und in der Doku referenziert:

- `assets/screenshots/main-window.png`
- `assets/screenshots/add-edit-dialog.png`
- `assets/screenshots/system-info.png`
- `assets/screenshots/tray.png`
- `assets/screenshots/login.png`

Empfohlen: 1600&nbsp;×&nbsp;1000&nbsp;px, PNG, **Dark-Theme** der App, identische
Cyan-Akzente.

## Lizenz

Wie das Hauptprojekt — siehe `../LICENSE` im Repo-Root.
