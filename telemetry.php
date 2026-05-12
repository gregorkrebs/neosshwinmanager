<?php
/**
 * NEO SSH-Win Manager - Telemetry Counter
 * 
 * Empfängt Telemetrie-Ereignisse vom Client.
 * Serverseitiger Schutz via IP Rate-Limiting, da Open-Source-Clients keine Geheimnisse wahren können.
 */

define('DATA_FILE', __DIR__ . '/telemetry_data.json');
define('IP_LOG_FILE', __DIR__ . '/telemetry_ips.json');
define('MAX_LOG_ENTRIES', 500);

header('Content-Type: application/json');

$action = isset($_GET['action']) ? $_GET['action'] : '';
if (!in_array($action, ['install', 'login'])) {
    http_response_code(400);
    exit(json_encode(["status" => "error", "message" => "Invalid action"]));
}

// Einfacher Schutz vor primitiven Web-Scrapern
if (!isset($_SERVER['HTTP_USER_AGENT']) || strpos($_SERVER['HTTP_USER_AGENT'], 'NeoSSHWinManager') === false) {
    http_response_code(401);
    exit(json_encode(["status" => "error", "message" => "Invalid client"]));
}

// --- 1. IP Rate Limiting (Zero-Log mit täglichem Hash) ---
// Um PII (IP-Adressen) nicht zu speichern, wird ein gehashter Wert generiert.
// Dieser Hash ist unwiderruflich und wechselt um Mitternacht automatisch.
// SECURITY: Load salt from environment variable; never hardcode secrets in source.
$_salt = getenv('NEOSSH_RATE_LIMIT_SALT');
if (!$_salt) {
    http_response_code(500);
    exit(json_encode(["status" => "error", "message" => "Server misconfiguration"]));
}
define('RATE_LIMIT_SALT', $_salt);
$client_ip = $_SERVER['REMOTE_ADDR'] ?? '127.0.0.1';
$daily_salt = date('Y-m-d'); 
$anonymous_client_hash = hash('sha256', $client_ip . RATE_LIMIT_SALT . $daily_salt);

$current_time = time();

$limit_data = [];
if (file_exists(IP_LOG_FILE)) {
    $content = file_get_contents(IP_LOG_FILE);
    $limit_data = json_decode($content, true) ?: [];
}

// Eintrag initialisieren
if (!isset($limit_data[$anonymous_client_hash])) {
    $limit_data[$anonymous_client_hash] = ['last_install' => 0, 'logins' => []];
}

if ($action === 'install') {
    if ($current_time - $limit_data[$anonymous_client_hash]['last_install'] < 86400) {
        http_response_code(429);
        exit(json_encode(["status" => "error", "message" => "Rate limit exceeded for install"]));
    }
    $limit_data[$anonymous_client_hash]['last_install'] = $current_time;
} elseif ($action === 'login') {
    $recent_logins = array_filter($limit_data[$anonymous_client_hash]['logins'], function($t) use ($current_time) {
        return ($current_time - $t) < 3600;
    });
    if (count($recent_logins) >= 10) {
        http_response_code(429);
        exit(json_encode(["status" => "error", "message" => "Rate limit exceeded for logins"]));
    }
    $recent_logins[] = $current_time;
    $limit_data[$anonymous_client_hash]['logins'] = $recent_logins;
}

// Bereinigen
$limit_data = array_filter($limit_data, function($data) use ($current_time) {
    $recent_login = !empty($data['logins']) ? max($data['logins']) : 0;
    return ($current_time - $data['last_install'] < 86400) || ($current_time - $recent_login < 3600);
});

file_put_contents(IP_LOG_FILE, json_encode($limit_data));


// --- 2. Counter aktuallisieren ---
$data = ["installs" => 0, "logins" => 0, "recent_logs" => []];
if (file_exists(DATA_FILE)) {
    $data = json_decode(file_get_contents(DATA_FILE), true) ?: $data;
}

if ($action === 'install') {
    $data['installs']++;
} elseif ($action === 'login') {
    $data['logins']++;
}

array_unshift($data['recent_logs'], [
    "action" => $action,
    "time" => date("Y-m-d\TH:i:sP"),
]);
$data['recent_logs'] = array_slice($data['recent_logs'], 0, MAX_LOG_ENTRIES);

file_put_contents(DATA_FILE, json_encode($data, JSON_PRETTY_PRINT));

echo json_encode(["status" => "success", "message" => "Counter updated", "action" => $action]);
?>
