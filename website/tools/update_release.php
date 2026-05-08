<?php
/**
 * update_release.php — Fetches the latest release info from GitHub and updates
 * the website: version numbers, changelog entries, and i18n keys.
 *
 * Usage:
 *   php tools/update_release.php [--root /path/to/website]
 *
 * What it updates:
 *   - changelog.html  : auto-generated release block (<li> elements carry data-i18n)
 *   - index.html      : version badge in the app mockup
 *   - i18n.js         : version strings + any missing changelog.vXXX.liN keys
 *                       (only adds missing keys — never overwrites existing ones)
 */

// ─── Config ──────────────────────────────────────────────────────────────────

const GITHUB_REPO = 'gregorkrebs/neosshwinmanager';
const GITHUB_API  = 'https://api.github.com/repos/' . GITHUB_REPO . '/releases';
const GITHUB_UA   = 'NEO-SSH-Win-Manager-Website-Updater/1.0';

const FILE_CHANGELOG = 'changelog.html';
const FILE_INDEX     = 'index.html';
const FILE_I18N      = 'assets/js/i18n.js';

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
        'method'        => 'GET',
        'header'        => "User-Agent: " . GITHUB_UA . "\r\nAccept: application/vnd.github+json\r\n",
        'timeout'       => 15,
        'ignore_errors' => true,
    ],
    'ssl' => ['verify_peer' => true],
]);

$json = @file_get_contents(GITHUB_API, false, $ctx);
if ($json === false) {
    die("[ERROR] Could not connect to GitHub API. Check internet connection.\n");
}

$releases = json_decode($json, true);
if (!is_array($releases) || empty($releases)) {
    die("[ERROR] GitHub API returned unexpected data: " . substr($json, 0, 200) . "\n");
}

$published = array_values(array_filter($releases, fn($r) => !$r['draft'] && !$r['prerelease']));
if (empty($published)) {
    $published = array_values(array_filter($releases, fn($r) => !$r['draft']));
}
if (empty($published)) {
    die("[ERROR] No published releases found in the repository.\n");
}

$latestTag     = ltrim($published[0]['tag_name'], 'v');
$latestVersion = 'v' . $latestTag;

echo "[INFO] Latest release: {$latestVersion}\n";
echo "[INFO] Total releases: " . count($published) . "\n";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatBytes(int $bytes): string {
    if ($bytes >= 1048576) return round($bytes / 1048576, 1) . ' MB';
    if ($bytes >= 1024)    return round($bytes / 1024)       . ' KB';
    return $bytes . ' B';
}

/**
 * Convert a version tag to a changelog i18n key prefix.
 * "v1.3.0" → "changelog.v130"
 */
function tagToKeyPrefix(string $tag): string {
    $digits = preg_replace('/[^0-9]/', '', $tag);
    return 'changelog.v' . $digits;
}

/**
 * Parse a GitHub Markdown release body into plain-text list items.
 * Strips bold/italic markers and inline code.
 */
function parseReleaseBody(string $body): array {
    $items = [];
    foreach (explode("\n", $body) as $line) {
        $line = trim($line);
        if (!preg_match('/^[-*]\s+(.+)/', $line, $m)) {
            continue;
        }
        $text = trim($m[1]);
        // Strip markdown bold (**text**, __text__) and italic (*text*, _text_)
        $text = preg_replace('/\*\*(.+?)\*\*/', '$1', $text);
        $text = preg_replace('/__(.+?)__/',     '$1', $text);
        $text = preg_replace('/\*(.+?)\*/',     '$1', $text);
        $text = preg_replace('/_(.+?)_/',       '$1', $text);
        // Strip inline code (`text`)
        $text = preg_replace('/`([^`]+)`/', '$1', $text);
        $items[] = trim($text);
    }
    return $items;
}

/**
 * Build HTML for one release block. Returns [html, keyMap] where
 * keyMap maps each generated i18n key to its English fallback text.
 *
 * @return array{0: string, 1: array<string, string>}
 */
function buildReleaseHtml(array $release, bool $isLatest): array {
    $tag       = htmlspecialchars($release['tag_name']);
    $relUrl    = 'https://github.com/' . GITHUB_REPO . '/releases/tag/' . $tag;
    $keyPrefix = tagToKeyPrefix($release['tag_name']);

    $body   = trim($release['body'] ?? '');
    $items  = parseReleaseBody($body);
    $assets = $release['assets'] ?? [];
    $keyMap = [];

    $latestBadge = $isLatest
        ? '            <span class="badge accent" data-i18n="changelog.latest">Latest</span>' . "\n"
        : '';

    // List items — each carries its own data-i18n key
    $listHtml = '';
    if (empty($items)) {
        $listHtml = '            <li>See <a href="' . htmlspecialchars($relUrl)
            . '" target="_blank" rel="noopener">' . htmlspecialchars($tag)
            . ' release notes</a> on GitHub.</li>' . "\n";
    } else {
        foreach ($items as $n => $text) {
            $key          = $keyPrefix . '.li' . ($n + 1);
            $keyMap[$key] = $text;
            $esc          = htmlspecialchars($text);
            $listHtml    .= '            <li data-i18n="' . $key . '">' . $esc . "</li>\n";
        }
    }

    // Assets table rows
    $guiAsset = $cliAsset = null;
    foreach ($assets as $asset) {
        $name = $asset['name'];
        if (stripos($name, ASSET_CLI) !== false)     $cliAsset = $asset;
        elseif (stripos($name, ASSET_GUI) !== false) $guiAsset = $asset;
    }
    $rowsHtml = '';
    foreach (array_filter([$guiAsset, $cliAsset]) as $asset) {
        $name     = htmlspecialchars($asset['name']);
        $dlUrl    = htmlspecialchars($asset['browser_download_url']);
        $size     = formatBytes((int)($asset['size'] ?? 0));
        $rowsHtml .= <<<HTML
              <tr>
                <td><a href="{$dlUrl}">{$name}</a></td>
                <td class="size">{$size}</td>
              </tr>

HTML;
    }

    $html = <<<HTML

        <article class="release">
          <div class="release-head">
            <span class="release-tag">{$tag}</span>
{$latestBadge}            <a class="release-date" href="{$relUrl}" target="_blank" rel="noopener">github.com/releases/{$tag}</a>
          </div>
          <ul class="release-list">
{$listHtml}          </ul>
          <table class="assets-table">
            <thead>
              <tr>
                <th data-i18n="changelog.col.asset">File</th>
                <th data-i18n="changelog.col.size">Size</th>
              </tr>
            </thead>
            <tbody>
{$rowsHtml}            </tbody>
          </table>
        </article>

HTML;

    return [$html, $keyMap];
}

/**
 * Insert any missing changelog list-item keys into both the DE and EN
 * sections of i18n.js. Each key is added just before the "// ─── docs:"
 * section comment. Existing keys are never touched.
 *
 * @param array<string, string> $newKeys  i18n key → English fallback text
 */
function patchI18nKeys(string $i18n, array $newKeys): string {
    // The DE and EN objects are separated by this exact marker
    $enMarker = "\n\n    en: {";
    $sepPos   = strpos($i18n, $enMarker);
    if ($sepPos === false) {
        echo "[WARN] DE/EN boundary not found in i18n.js — key insertion skipped.\n";
        return $i18n;
    }

    $dePart = substr($i18n, 0, $sepPos);
    $enPart = substr($i18n, $sepPos);

    // Insertion anchor: the first "// ─── docs:" comment in each section
    $docsMarker = '// ─── docs:';
    $inserted   = 0;

    foreach ($newKeys as $key => $text) {
        $keyJson  = json_encode($key,  JSON_UNESCAPED_UNICODE);
        $textJson = json_encode($text, JSON_UNESCAPED_UNICODE);
        $entry    = "      {$keyJson}: {$textJson},\n";

        // DE section
        if (strpos($dePart, $keyJson) === false) {
            $pos = strpos($dePart, $docsMarker);
            if ($pos !== false) {
                $dePart = substr($dePart, 0, $pos) . $entry . substr($dePart, $pos);
                $inserted++;
            }
        }
        // EN section
        if (strpos($enPart, $keyJson) === false) {
            $pos = strpos($enPart, $docsMarker);
            if ($pos !== false) {
                $enPart = substr($enPart, 0, $pos) . $entry . substr($enPart, $pos);
                $inserted++;
            }
        }
    }

    echo $inserted > 0
        ? "[INFO]   Inserted {$inserted} key/language pairs into i18n.js.\n"
        : "[INFO]   All changelog keys already present — nothing inserted.\n";

    return $dePart . $enPart;
}

// ─── Build all release HTML blocks ───────────────────────────────────────────

$releasesHtml = '';
$allNewKeys   = [];
foreach ($published as $i => $release) {
    echo "[INFO]   Building block for " . $release['tag_name'] . "...\n";
    [$html, $keyMap] = buildReleaseHtml($release, $i === 0);
    $releasesHtml   .= $html;
    $allNewKeys      = array_merge($allNewKeys, $keyMap);
}

// ─── Patch changelog.html ─────────────────────────────────────────────────────

$changelogFile = $root . '/' . FILE_CHANGELOG;
if (!file_exists($changelogFile)) {
    die("[ERROR] changelog.html not found: {$changelogFile}\n");
}

$changelogHtml = file_get_contents($changelogFile);

// Replace content between the wrapper div and the end-comment
$pattern  = '/(<div data-changelog-releases>).*?(<\/div>\s*<!-- End auto-generated block -->)/s';
$replaced = preg_replace($pattern,
    '$1' . "\n" . $releasesHtml . '      $2',
    $changelogHtml
);

if ($replaced === null || $replaced === $changelogHtml) {
    echo "[WARN] Auto-generated block not found in changelog.html — no changes made.\n";
} else {
    $changelogHtml = $replaced;
    // Keep the generator comment current
    $changelogHtml = preg_replace(
        '/<!-- Auto-generated by [^\-]+ — do not edit by  -->/',
        '<!-- Auto-generated by tools/update_release.php — do not edit by  -->',
        $changelogHtml
    );
    file_put_contents($changelogFile, $changelogHtml);
    echo "[OK]  changelog.html updated.\n";
}

// ─── Patch i18n.js ────────────────────────────────────────────────────────────

$i18nFile = $root . '/' . FILE_I18N;
if (!file_exists($i18nFile)) {
    echo "[WARN] i18n.js not found — skipping.\n";
} else {
    $i18n = file_get_contents($i18nFile);

    // Update version in hero.eyebrow (DE and EN)
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

    // Insert any missing changelog list-item keys into both language sections
    if (!empty($allNewKeys)) {
        echo "[INFO] Checking " . count($allNewKeys) . " changelog key(s) in i18n.js...\n";
        $i18n = patchI18nKeys($i18n, $allNewKeys);
    }

    file_put_contents($i18nFile, $i18n);
    echo "[OK]  i18n.js updated.\n";
}

// ─── Patch index.html ─────────────────────────────────────────────────────────

$indexFile = $root . '/' . FILE_INDEX;
if (!file_exists($indexFile)) {
    echo "[WARN] index.html not found — skipping.\n";
} else {
    $indexHtml = file_get_contents($indexFile);
    $indexHtml = preg_replace(
        '/(<span>)v[\d.]+(<\/span>\s*<\/div>\s*<\/div>\s*<\/div>\s*<\/section>\s*<!--.*?FEATURES)/s',
        '${1}' . $latestVersion . '${2}',
        $indexHtml
    );
    file_put_contents($indexFile, $indexHtml);
    echo "[OK]  index.html version badge updated to {$latestVersion}.\n";
}

// ─── Done ─────────────────────────────────────────────────────────────────────

echo "\n[DONE] Website updated to {$latestVersion}.\n";
echo "       Files patched:\n";
echo "         - {$changelogFile}\n";
if (file_exists($i18nFile))  echo "         - {$i18nFile}\n";
if (file_exists($indexFile)) echo "         - {$indexFile}\n";
echo "\n";
echo "       Next steps:\n";
echo "         1. Review DE translations for new changelog entries in i18n.js.\n";
echo "            (New keys are inserted with English text as placeholder.)\n";
echo "         2. git diff  →  inspect changes.\n";
echo "         3. git add -A && git commit -m \"chore: update to {$latestVersion}\"\n";
echo "         4. Deploy.\n\n";
