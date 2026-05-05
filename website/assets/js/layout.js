/**
 * layout.js — Injects shared topbar, footer, and docs-sidebar markup so every
 * page has identical chrome without duplicating ~150 lines per file.
 *
 * Pages opt-in by including:
 *   <div data-layout="topbar" data-pathprefix=""></div>
 *   <div data-layout="footer" data-pathprefix=""></div>
 *   <div data-layout="docs-sidebar" data-pathprefix=""></div>
 *
 * `data-pathprefix` is the relative path back to the website root
 * (empty string for root pages, "../" for /docs, "../../" for /docs/developer).
 *
 * After injection, `window.neoI18n.apply()` is called so freshly-injected
 * [data-i18n] nodes get translated immediately.
 */

(function () {
  "use strict";

  /**
   * Build the topbar HTML.
   * @param {string} prefix Relative path back to the website root.
   * @returns {string}
   */
  function topbar(prefix) {
    return `
      <header class="topbar">
        <div class="container topbar-inner">
          <a href="${prefix}index.html" class="brand" aria-label="NEO SSH-Win Manager">
            <img class="brand-mark" src="${prefix}assets/app_icon_only.png" alt="" width="32" height="32" />
            <span class="brand-name"><b>NEO</b> <span>SSH-Win Manager</span></span>
          </a>
          <nav class="nav" data-nav>
            <a href="${prefix}index.html" data-i18n="nav.overview">Übersicht</a>
            <a href="${prefix}app.html" data-i18n="nav.demo">Live-App</a>
            <a href="${prefix}features.html" data-i18n="nav.features">Features</a>
            <a href="${prefix}download.html" data-i18n="nav.download">Download</a>
            <a href="${prefix}docs/getting-started.html" data-i18n="nav.docs">Dokumentation</a>
            <a href="${prefix}changelog.html" data-i18n="nav.changelog">Changelog</a>
          </nav>
          <div class="topbar-actions">
            <div class="lang-switch" role="group" aria-label="Language" data-i18n-attr="aria-label:btn.lang">
              <button data-lang="de" type="button">DE</button>
              <button data-lang="en" type="button">EN</button>
            </div>
            <button class="icon-btn" data-theme-toggle aria-label="Toggle theme" data-i18n-attr="aria-label:btn.theme">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            </button>
            <a class="btn btn-sm" href="https://github.com/gregorkrebs/neosshwinmanager" target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 .5C5.7.5.5 5.7.5 12c0 5.1 3.3 9.4 7.8 10.9.6.1.8-.2.8-.6v-2.1c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.7 1.3 3.4 1 .1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.3 1.2.9-.3 2-.4 3-.4s2.1.1 3 .4c2.3-1.5 3.3-1.2 3.3-1.2.7 1.6.2 2.8.1 3.1.8.8 1.2 1.9 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6 4.5-1.5 7.8-5.8 7.8-10.9C23.5 5.7 18.3.5 12 .5z"/></svg>
              <span data-i18n="btn.github">GitHub</span>
            </a>
            <button class="icon-btn menu-btn" data-menu-toggle aria-label="Menu" data-i18n-attr="aria-label:btn.menu">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
            </button>
          </div>
        </div>
      </header>`;
  }

  /**
   * Build the footer HTML.
   * @param {string} prefix Relative path back to the website root.
   * @returns {string}
   */
  function footer(prefix) {
    return `
      <footer class="footer">
        <div class="container">
          <div class="footer-grid">
            <div>
              <a href="${prefix}index.html" class="brand">
                <img class="brand-mark" src="${prefix}assets/app_icon_only.png" alt="" width="32" height="32" />
                <span class="brand-name"><b>NEO</b> <span>SSH-Win Manager</span></span>
              </a>
              <p style="margin:10px 0 0; max-width:340px" data-i18n="footer.tagline">
                Kostenloser Open-Source-SSHFS-Client für Windows.
              </p>
            </div>
            <div>
              <h4 data-i18n="footer.product">Produkt</h4>
              <ul>
                <li><a href="${prefix}app.html" data-i18n="footer.demo">Live-App</a></li>
                <li><a href="${prefix}features.html" data-i18n="nav.features">Features</a></li>
                <li><a href="${prefix}download.html" data-i18n="nav.download">Download</a></li>
                <li><a href="${prefix}changelog.html" data-i18n="nav.changelog">Changelog</a></li>
              </ul>
            </div>
            <div>
              <h4 data-i18n="footer.docs">Dokumentation</h4>
              <ul>
                <li><a href="${prefix}docs/getting-started.html" data-i18n="footer.gettingStarted">Erster Start</a></li>
                <li><a href="${prefix}docs/cli.html" data-i18n="footer.cli">CLI-Companion</a></li>
                <li><a href="${prefix}docs/configuration.html" data-i18n="footer.config">Einstellungen</a></li>
                <li><a href="${prefix}docs/troubleshooting.html" data-i18n="footer.troubleshooting">Troubleshooting</a></li>
              </ul>
            </div>
            <div>
              <h4 data-i18n="footer.developers">Entwickler</h4>
              <ul>
                <li><a href="${prefix}docs/developer/project-structure.html" data-i18n="footer.projectStructure">Projektstruktur</a></li>
                <li><a href="${prefix}docs/developer/api.html" data-i18n="footer.apiReference">API-Referenz</a></li>
                <li><a href="https://github.com/gregorkrebs/neosshwinmanager" target="_blank" rel="noopener" data-i18n="btn.github">GitHub</a></li>
              </ul>
            </div>
          </div>
          <div class="footer-bottom">
            <span data-i18n="footer.license">© 2026 NEO SSH-Win Manager · MIT-Lizenz</span>
            <span><span data-i18n="footer.builton">Aufsetzend auf</span>
              <a href="https://github.com/winfsp/sshfs-win" target="_blank" rel="noopener">sshfs-win</a>
              &amp;
              <a href="https://github.com/winfsp/winfsp" target="_blank" rel="noopener">WinFsp</a>.
            </span>
          </div>
        </div>
      </footer>`;
  }

  /**
   * Build the docs sidebar HTML.
   * @param {string} prefix Relative path back to the website root.
   * @returns {string}
   */
  function docsSidebar(prefix) {
    return `
      <aside class="docs-side" data-nav>
        <div class="group">
          <p class="group-title" data-i18n="side.firstSteps">Erste Schritte</p>
          <a href="${prefix}docs/getting-started.html" data-i18n="side.installFirstStart">Installation &amp; erster Start</a>
          <a href="${prefix}docs/connections.html" data-i18n="side.connections">Verbindungen anlegen</a>
          <a href="${prefix}docs/authentication.html" data-i18n="side.auth">Authentifizierung</a>
          <a href="${prefix}docs/cli.html" data-i18n="side.cli">CLI-Companion</a>
        </div>
        <div class="group">
          <p class="group-title" data-i18n="side.configuration">Konfiguration</p>
          <a href="${prefix}docs/configuration.html" data-i18n="side.settingsTheme">Einstellungen &amp; Theme</a>
          <a href="${prefix}docs/troubleshooting.html" data-i18n="side.troubleshooting">Troubleshooting</a>
        </div>
        <div class="group">
          <p class="group-title" data-i18n="side.developer">Entwickler</p>
          <a href="${prefix}docs/developer/project-structure.html" data-i18n="side.projectStructure">Projektstruktur</a>
          <a href="${prefix}docs/developer/api.html" data-i18n="side.apiReference">API-Referenz</a>
        </div>
      </aside>`;
  }

  /**
   * Wire up the language switch buttons to neoI18n.
   * Highlights the active language and reacts to changes from elsewhere.
   */
  function wireLangSwitch() {
    const groups = document.querySelectorAll(".lang-switch");
    if (!groups.length || !window.neoI18n) return;

    function paint() {
      const cur = window.neoI18n.getLang();
      groups.forEach((g) => {
        g.querySelectorAll("button[data-lang]").forEach((b) => {
          b.classList.toggle("active", b.dataset.lang === cur);
          b.setAttribute("aria-pressed", b.dataset.lang === cur ? "true" : "false");
        });
      });
    }
    groups.forEach((g) => {
      g.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-lang]");
        if (!btn) return;
        window.neoI18n.setLang(btn.dataset.lang);
      });
    });
    window.neoI18n.onChange(paint);
    paint();
  }

  // Inject everything synchronously (the script is loaded with `defer`,
  // so the DOM is ready by the time we run).
  document.querySelectorAll("[data-layout]").forEach((el) => {
    const prefix = el.dataset.pathprefix || "";
    const kind = el.dataset.layout;
    if (kind === "topbar") el.outerHTML = topbar(prefix);
    else if (kind === "footer") el.outerHTML = footer(prefix);
    else if (kind === "docs-sidebar") el.outerHTML = docsSidebar(prefix);
  });

  // Translate the freshly-injected chrome.
  if (window.neoI18n) window.neoI18n.apply(document);
  wireLangSwitch();
})();
