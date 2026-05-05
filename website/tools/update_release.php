<?php
/**
 * update_release.php — Fetches the latest release info from GitHub and updates
 * the website: version numbers, changelog entries, and file sizes.
 *
 * Usage:
 *   php tools/update_release.php
 *
 * The script must be run from the website root directory, or pass --root:
 *   php tools/update_release.php --root /path/to/website
 *
 * What it updates:
 *   - changelog.html  : the auto-generated release block
 *   - index.html      : version in the CTA sub-text and hero eyebrow
 *   - i18n.js         : version strings in hero.eyebrow, cta.sub keys
 */

// ─── Config ──────────────────────────────────────────────────────────────────

const GITHUB_REPO   = 'gregorkrebs/neosshwinmanager';
const GITHUB_API    = 'https://api.github.com/repos/' . GITHUB_REPO . '/releases';
const GITHUB_UA     = 'NEO-SSH-Win-Manager-Website-Updater/1.0';

// Files to patch (relative to website root)
const FILE_CHANGELOG = 'changelog.html';
const FILE_INDEX     = 'index.html';
const FILE_I18N      = 'assets/js/i18n.js';

// SHA-256 assets to show in the changelog table (matched by filename substring)
const ASSET_GUI = 'NeoSSHWinManager.exe';
const ASSET_CLI = 'NeoSSHWinManager-cli.exe';

// ─── CLI args ─────────────────────────────────────────────────────────────────

$root = __DIR__ . '/..';
foreach ($argv as $i => $arg) {
    if ($arg === '--root' && isset($argv[$i + 1])) {
        $root = rtrim($argv[$i + 1], '/\\');
    }
}
$root = realpath($root);
if (!$root || !is_dir($root)) {
    die("[ERROR] Website root not found. Use --root /path/to/website\n");
}

// ─── Fetch releases from GitHub ───────────────────────────────────────────────

echo "[INFO] Fetching releases from GitHub API...\n";

$ctx = stream_context_create([
    'http' => [
        'method'          => 'GET',
        'header'          => "User-Agent: " . GITHUB_UA . "\r\nAccept: application/vnd.github+json\r\n",
        'timeout'         => 15,
        'ignore_errors'   => true,
    ],
    'ssl'  => ['verify_peer' => true],
]);

$json = @file_get_contents(GITHUB_API, false, $ctx);
if ($json === false) {
    die("[ERROR] Could not connect to GitHub API. Check your internet connection.\n");
}

$releases = json_decode($json, true);
if (!is_array($releases) || empty($releases)) {
    die("[ERROR] GitHub API returned unexpected data: " . substr($json, 0, 200) . "\n");
}

// Filter out drafts and pre-releases, keep published releases only
$published = array_values(array_filter($releases, fn($r) => !$r['draft'] && !$r['prerelease']));
if (empty($published)) {
    // Fall back to all releases if no stable ones exist
    $published = array_values(array_filter($releases, fn($r) => !$r['draft']));
}

if (empty($published)) {
    die("[ERROR] No published releases found in the repository.\n");
}

$latestTag     = ltrim($published[0]['tag_name'], 'v');
$latestVersion = 'v' . $latestTag;

echo "[INFO] Latest release: {$latestVersion}\n";
echo "[INFO] Total releases found: " . count($published) . "\n";

// ─── Build changelog HTML block ───────────────────────────────────────────────

function formatBytes(int $bytes): string {
    if ($bytes >= 1048576) return round($bytes / 1048576, 1) . ' MB';
    if ($bytes >= 1024)    return round($bytes / 1024)       . ' KB';
    return $bytes . ' B';
}

function buildReleaseHtml(array $release, bool $isLatest): string {
    $tag     = htmlspecialchars($release['tag_name']);
    $tagSlug = ltrim($tag, 'v');
    $repoUrl = 'https://github.com/' . GITHUB_REPO;
    $relUrl  = "{$repoUrl}/releases/tag/{$tag}";

    // Parse changelog body (GitHub Markdown → simple list items)
    $body    = trim($release['body'] ?? '');
    $items   = parseReleaseBody($body);

    // Assets
    $assets  = $release['assets'] ?? [];

    $latestBadge = $isLatest
        ? '<span class="badge accent" data-i18n="changelog.latest">Latest</span>'
        : '';

    $listItems = '';
    if (empty($items)) {
        // No body parsed — show a generic entry
        $listItems = '<li>See <a href="' . htmlspecialchars($relUrl) . '" target="_blank" rel="noopener">'
            . htmlspecialchars($tag) . ' release notes</a> on GitHub.</li>';
    } else {
        foreach ($items as $item) {
            $listItems .= '            <li>' . htmlspecialchars($item) . "</li>\n";
        }
    }

    $tableRows = '';
    $guiAsset  = null;
    $cliAsset  = null;
    foreach ($assets as $asset) {
        $name = $asset['name'];
        if (stripos($name, ASSET_CLI) !== false) {
            $cliAsset = $asset;
        } elseif (stripos($name, ASSET_GUI) !== false) {
            $guiAsset = $asset;
        }
    }
    foreach (array_filter([$guiAsset, $cliAsset]) as $asset) {
        $name    = htmlspecialchars($asset['name']);
        $dlUrl   = htmlspecialchars($asset['browser_download_url']);
        $size    = formatBytes((int)($asset['size'] ?? 0));
        $sha     = ''; // GitHub API does not expose SHA-256; left blank for manual update
        $shaHtml = $sha ? "\n                  <span class=\"sha\">sha256: {$sha}</span>" : '';

        $tableRows .= <<<HTML
              <tr>
                <td>
                  <a href="{$dlUrl}">{$name}</a>{$shaHtml}
                </td>
                <td class="size">{$size}</td>
              </tr>

HTML;
    }

    $colAsset = '<th data-i18n="changelog.col.asset">File</th>';
    $colSize  = '<th data-i18n="changelog.col.size">Size</th>';

    return <<<HTML

        <article class="release">
          <div class="release-head">
            <span class="release-tag">{$tag}</span>
            {$latestBadge}
            <a class="release-date" href="{$relUrl}" target="_blank" rel="noopener">github.com/releases/{$tag}</a>
          </div>
          <ul class="release-list">
{$listItems}          </ul>
          <table class="assets-table">
            <thead>
              <tr>{$colAsset}{$colSize}</tr>
            </thead>
            <tbody>
{$tableRows}            </tbody>
          </table>
        </article>

HTML;
}

/**
 * Parse a GitHub Markdown release body into plain-text list items.
 * Handles both "- item" and "* item" and "## Heading\n- item" patterns.
 */
function parseReleaseBody(string $body): array {
    $items = [];
    $lines = explode("\n", $body);
    foreach ($lines as $line) {
        $line = trim($line);
        if (preg_match('/^[-*]\s+(.+)/', $line, $m)) {
            $items[] = trim($m[1]);
        }
    }
    return $items;
}

// Build all release blocks
$releasesHtml = '';
foreach ($published as $i => $release) {
    echo "[INFO]   Building block for " . $release['tag_name'] . "...\n";
    $releasesHtml .= buildReleaseHtml($release, $i === 0);
}

// ─── Patch changelog.html ─────────────────────────────────────────────────────

$changelogFile = $root . '/' . FILE_CHANGELOG;
if (!file_exists($changelogFile)) {
    die("[ERROR] changelog.html not found at: {$changelogFile}\n");
}

$changelogHtml = file_get_contents($changelogFile);

// The auto-generated block is delimited by these comments:
$blockStart = '<!-- ============================================================ -->' . "\n"
    . '      <!-- Auto-generated by tools/fetch_changelog.py — do not edit by  -->' . "\n"
    . '      <!-- hand. Re-run the tool to refresh. Block start.               -->' . "\n"
    . '      <!-- ============================================================ -->' . "\n"
    . '      <div data-changelog-releases>';

$blockEnd   = '</div>' . "\n"
    . '      <!-- End auto-generated block -->';

$newBlock   = '<!-- ============================================================ -->' . "\n"
    . '      <!-- Auto-generated by tools/update_release.php — do not edit by  -->' . "\n"
    . '      <!-- hand. Re-run the tool to refresh. Block start.               -->' . "\n"
    . '      <!-- ============================================================ -->' . "\n"
    . '      <div data-changelog-releases>'
    . $releasesHtml
    . '      </div>' . "\n"
    . '      <!-- End auto-generated block -->';

// Try to find and replace the block
$patternStart = preg_quote($blockStart, '/');
$patternEnd   = preg_quote($blockEnd,   '/');
$pattern      = '/' . $patternStart . '.*?' . $patternEnd . '/s';

if (preg_match($pattern, $changelogHtml)) {
    $changelogHtml = preg_replace($pattern, $newBlock, $changelogHtml);
} else {
    // Fallback: look for just the wrapper div
    $pattern2 = '/<div data-changelog-releases>.*?<\/div>\s*<!-- End auto-generated block -->/s';
    if (preg_match($pattern2, $changelogHtml)) {
        $changelogHtml = preg_replace($pattern2,
            '<div data-changelog-releases>' . $releasesHtml . '      </div>' . "\n      <!-- End auto-generated block -->",
            $changelogHtml
        );
    } else {
        echo "[WARN] Could not find the auto-generated block in changelog.html. No changes made to release list.\n";
    }
}

// Also update the tool reference in the source note
$changelogHtml = preg_replace(
    '/(<code>)(python tools\/fetch_changelog\.py|php tools\/update_release\.php)(<\/code>)/',
    '${1}php tools/update_release.php${3}',
    $changelogHtml
);

file_put_contents($changelogFile, $changelogHtml);
echo "[OK]  changelog.html updated.\n";

// ─── Patch i18n.js ────────────────────────────────────────────────────────────

$i18nFile = $root . '/' . FILE_I18N;
if (!file_exists($i18nFile)) {
    echo "[WARN] i18n.js not found — skipping version string update in translations.\n";
} else {
    $i18n = file_get_contents($i18nFile);

    // Update version in hero.eyebrow (both DE and EN)
    $i18n = preg_replace(
        '/"hero\.eyebrow":\s*"v[\d.]+( · [^"]+)"/',
        '"hero.eyebrow": "' . $latestVersion . '$1"',
        $i18n
    );

    // Update version in cta.sub (DE)
    $i18n = preg_replace(
        '/"cta\.sub":\s*"Aktuell v[\d.]+ —/',
        '"cta.sub": "Aktuell ' . $latestVersion . ' —',
        $i18n
    );

    // Update version in cta.sub (EN)
    $i18n = preg_replace(
        '/"cta\.sub":\s*"Currently v[\d.]+ —/',
        '"cta.sub": "Currently ' . $latestVersion . ' —',
        $i18n
    );

    file_put_contents($i18nFile, $i18n);
    echo "[OK]  i18n.js version strings updated to {$latestVersion}.\n";
}

// ─── Patch index.html ─────────────────────────────────────────────────────────

$indexFile = $root . '/' . FILE_INDEX;
if (!file_exists($indexFile)) {
    echo "[WARN] index.html not found — skipping.\n";
} else {
    $indexHtml = file_get_contents($indexFile);

    // Update the statusbar version badge in the app mockup
    $indexHtml = preg_replace(
        '/(<span>)v[\d.]+(<\/span>\s*<\/div>\s*<\/div>\s*<\/div>\s*<\/section>\s*<!--.*?FEATURES)/s',
        '${1}' . $latestVersion . '${2}',
        $indexHtml
    );

    file_put_contents($indexFile, $indexHtml);
    echo "[OK]  index.html mockup version badge updated to {$latestVersion}.\n";
}

// ─── Done ─────────────────────────────────────────────────────────────────────

echo "\n[DONE] Website updated to {$latestVersion}.\n";
echo "       Files patched:\n";
echo "         - {$changelogFile}\n";
if (file_exists($i18nFile))  echo "         - {$i18nFile}\n";
if (file_exists($indexFile)) echo "         - {$indexFile}\n";
echo "\n";
echo "       Next steps:\n";
echo "         1. Review the changes (git diff).\n";
echo "         2. Commit: git add -A && git commit -m \"chore: update to {$latestVersion}\"\n";
echo "         3. Deploy.\n\n";
