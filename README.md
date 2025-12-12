# ldr-sensor

Licht- en temperatuurmetingen met MQTT en een eenvoudige Tk/Matplotlib GUI. Er zijn twee stromen:

1. LDR-historiek ophalen via de Rubu IoT API en tonen in een desktop GUI.
2. TC74-temperatuur via I2C op een Raspberry Pi uitlezen, publiceren op MQTT en live tonen (web en LED-strip).

## Repo-overzicht

- `scripts/main.py` – Tk GUI met twee grafieken: boven LDR-historiek (API), onder live MQTT-temperature feed.
- `scripts/ledstrip_micropython.py` – ESP32/APA102-strip die MQTT-temperatuur omzet in kleuren + opstartanimatie.
- `RPI/temp_test.py` – Raspberry Pi script dat de TC74 via I2C leest en naar MQTT publiceert.
- `tc74/public_html/` – Kleine webmonitor die via MQTT.js live temperaturen toont (gauge + lijnplot) met thematoggle.

## LDR GUI (scripts/main.py)

- Haalt laatste N uur LDR-data op (`LdrHistory(hours_back=48)` standaard).
- API-call met `requests`, pandas-parsing, Tk/Matplotlib voor de grafiek.
- Onderste grafiek toont live MQTT-temperaturen (zelfde broker/topic als TC74).

### Config (`scripts/config.py`)

| Key             | Betekenis                    |
| --------------- | ---------------------------- |
| `API_KEY`       | Rubu IoT API key             |
| `BASE_URL`      | Endpoint voor LDR API        |
| `TIME_FORMAT`   | Tijdformaat voor begin/einde |
| `MQTT_BROKER`   | Broker hostnaam              |
| `MQTT_PORT`     | Broker poort                 |
| `MQTT_TOPIC`    | Topic voor temperaturen      |
| `MQTT_USERNAME` | Broker user                  |
| `MQTT_PASSWORD` | Broker wachtwoord            |

Aanpassen van het tijdsvenster: wijzig `LdrHistory(hours_back=...)` in `main.py`.

### Run (desktop)

```pwsh
pip install pandas matplotlib requests paho-mqtt
python .\scripts\main.py
```

Tk opent met twee grafieken; de onderste vult zich zodra MQTT-berichten binnenkomen.

## TC74-keten (temperatuur)

### Raspberry Pi publisher (`RPI/temp_test.py`)

- Leest TC74 via I2C bus 1 (`TC74_ADDR=0x48`, register `0x00`).
- Publiceert elke 2s de integer temperatuur naar `MQTT_TOPIC` met `paho.mqtt.client`.
- Start `client.loop_start()` en logt publish-status. Bij leesfout wordt een melding geprint.

Benodigd: `smbus2`, `RPi.GPIO`, `paho-mqtt`. Voorbeeldinstallatie:

```pwsh
pip install smbus2 RPi.GPIO paho-mqtt
```

Run op de Pi:

```pwsh
python ./RPI/temp_test.py
```

### Webmonitor (`tc74/public_html`)

- `index.html` + `app.js` gebruiken MQTT.js + Google Charts.
- Config komt uit `mqtt-config.php` dat `.env` leest (naast `public_html`).
- `.env` moet bevatten: `MQTT_BROKER_URL`, `MQTT_TOPIC`, optioneel `MQTT_USERNAME`, `MQTT_PASSWORD`.
- UI toont live waarde, gauge en max 25 punten geschiedenis; heeft dark/light toggle.

### LED-strip client (`scripts/ledstrip_micropython.py`)

- Richt zich op een ESP32 met APA102 strip (DATA=18, CLOCK=5, 60 leds).
- WiFi connect, daarna MQTT subscribe op hetzelfde topic.
- Opstart: regenbooganimatie; bij connect groen knipperen; WiFi-fout rood.
- Payload wordt naar float geparsed; kleurmapping: <10 wit, 10-17 lichtblauw, 18-22 groen, 23-30 oranje, >30 rood.
- Animaties via eenvoudige SPI `apa102_write` functie.

Flash naar de ESP32 met MicroPython tooling (bijv. `mpremote cp scripts/ledstrip_micropython.py :main.py`).

## Troubleshooting

- API-fout of lege LDR-data: controleer `API_KEY`, `BASE_URL` en `hours_back`.
- Geen MQTT data in GUI/web/LED: check broker host/port/credentials en of `temp_test.py` draait.
- Webmonitor leeg: controleer `.env` pad/inhoud en CORS/hosting (PHP moet `.env` kunnen lezen).
