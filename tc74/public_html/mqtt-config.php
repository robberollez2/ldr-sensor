<?php
header('Content-Type: application/json; charset=utf-8');

// Pad naar .env (één niveau hoger dan public_html)
$envPath = __DIR__ . '/../.env';

if (!file_exists($envPath)) {
    http_response_code(500);
    echo json_encode(['error' => '.env bestand niet gevonden']);
    exit;
}

// Eenvoudige .env parser
$vars = [];
$lines = file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);

foreach ($lines as $line) {
    $line = trim($line);
    if ($line === '' || $line[0] === '#') {
        continue; // comment of lege regel
    }

    $parts = explode('=', $line, 2);
    if (count($parts) !== 2) {
        continue;
    }

    $key = trim($parts[0]);
    $value = trim($parts[1]);

    // Quotes strippen
    $value = trim($value, "'\"");
    $vars[$key] = $value;
}

// Check verplichte waarden
if (empty($vars['MQTT_BROKER_URL']) || empty($vars['MQTT_TOPIC'])) {
    http_response_code(500);
    echo json_encode([
        'error' => 'MQTT_BROKER_URL en MQTT_TOPIC moeten in .env staan'
    ]);
    exit;
}

// JSON output naar front-end
echo json_encode([
    'brokerUrl' => $vars['MQTT_BROKER_URL'],
    'username' => $vars['MQTT_USERNAME'] ?? '',
    'password' => $vars['MQTT_PASSWORD'] ?? '',
    'topic' => $vars['MQTT_TOPIC'] ?? '',
]);
