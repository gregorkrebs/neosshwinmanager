/**
 * site.js — Shared client-side helpers for the NEO SSH-Win Manager website.
 *
 * Responsibilities:
 *  - Persist + apply the dark/light theme preference.
 *  - Toggle the mobile navigation menu.
 *  - Highlight the active navigation link.
 *  - Resolve the latest GitHub release URL for download buttons.
 */

(function () {
  "use strict";

  const STORAGE_KEY = "nswm.theme";
  const REPO = "gregorkrebs/neosshwinmanager";

  /* -----------------------------------------------------------
   * Theme handling
   * --------------------------------------------------------- */

  /**
   * Read the persisted theme preference, falling back to the OS preference.
   * @returns {"dark"|"light"} The resolved theme.
   */
  function getPreferredTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "dark" || stored === "light") return stored;
    return window.matchMedia("(prefers-color-scheme: light)").matches
      ? "light"
      : "dark";
  }

  /** Return a localized theme-toggle label for the current theme. */
  function getThemeToggleLabel(theme) {
    const key = theme === "dark" ? "btn.theme.toLight" : "btn.theme.toDark";
    return window.neoI18n?.t(key) || (theme === "dark"
      ? "Zu hellem Theme wechseln"
      : "Zu dunklem Theme wechseln");
  }

  /**
   * Apply a theme to the document and persist it.
   * @param {"dark"|"light"} theme
   */
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
    const btn = document.querySelector("[data-theme-toggle]");
    if (btn) {
      btn.setAttribute("aria-label", getThemeToggleLabel(theme));
      btn.dataset.themeState = theme;
    }
  }

  /** Wire up the theme toggle button. */
  function initThemeToggle() {
    const btn = document.querySelector("[data-theme-toggle]");
    if (!btn) return;
    btn.setAttribute("aria-label",
      getThemeToggleLabel(document.documentElement.getAttribute("data-theme") || "dark"));
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      applyTheme(current === "dark" ? "light" : "dark");
    });
    window.neoI18n?.onChange(() => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      btn.setAttribute("aria-label", getThemeToggleLabel(current));
    });
  }

  /* -----------------------------------------------------------
   * Navigation
   * --------------------------------------------------------- */

  /** Highlight the nav link matching the current page. */
  function markActiveNav() {
    const path = location.pathname.replace(/index\.html$/, "");
    document.querySelectorAll("[data-nav] a").forEach((a) => {
      const href = a.getAttribute("href") || "";
      const cleanHref = href.replace(/index\.html$/, "");
      if (cleanHref && (path.endsWith(cleanHref) || path === cleanHref)) {
        a.classList.add("active");
      }
    });
  }

  /** Wire up the mobile menu toggle. */
  function initMobileMenu() {
    const btn = document.querySelector("[data-menu-toggle]");
    const nav = document.querySelector("[data-nav]");
    if (!btn || !nav) return;
    btn.addEventListener("click", () => {
      nav.classList.toggle("open");
    });
  }

  /* -----------------------------------------------------------
   * GitHub release links
   * --------------------------------------------------------- */

  /**
   * Update buttons marked with `data-release` to point at the latest release.
   * Falls back gracefully to /releases/latest if the API is unreachable.
   */
  async function resolveLatestRelease() {
    const targets = document.querySelectorAll("[data-release]");
    if (!targets.length) return;
    try {
      const res = await fetch(`https://api.github.com/repos/${REPO}/releases/latest`, {
        headers: { Accept: "application/vnd.github+json" },
      });
      if (!res.ok) return;
      const data = await res.json();
      const tag = data.tag_name || "latest";
      const versionEl = document.querySelector("[data-release-version]");
      if (versionEl) versionEl.textContent = tag;
      targets.forEach((el) => {
        const kind = el.dataset.release;
        const exe = kind === "cli"
          ? "NeoSSHWinManager-cli.exe"
          : "NeoSSHWinManager.exe";
        const asset = (data.assets || []).find((a) => a.name === exe);
        if (asset) el.setAttribute("href", asset.browser_download_url);
      });
    } catch (_) {
      /* offline — links keep their static fallback */
    }
  }

  /* -----------------------------------------------------------
   * Boot
   * --------------------------------------------------------- */

  // Apply theme as early as possible to avoid a flash.
  applyTheme(getPreferredTheme());

  document.addEventListener("DOMContentLoaded", () => {
    initThemeToggle();
    initMobileMenu();
    markActiveNav();
    resolveLatestRelease();
  });
})();
