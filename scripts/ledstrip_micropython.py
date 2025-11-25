import network
import time
from machine import Pin, SPI
from umqtt.simple import MQTTClient

# ------- WIFI INSTELLINGEN -------
WIFI_SSID = "A118_IWT_TEMPORARY"
WIFI_PASSWORD = "VIVES_ELOICT"

# ------- MQTT INSTELLINGEN -------
MQTT_BROKER = "mqtt.rubu.be"
MQTT_PORT = 1884

MQTT_TOPIC = b"rollezrobbe/temp"

MQTT_USERNAME = "rollezrobbe"
MQTT_PASSWORD = "vm2qdu"

# ------- LED STRIP INSTELLINGEN -------
DATA_PIN = 18
CLOCK_PIN = 5
NUM_LEDS = 60

spi = SPI(
    1,
    baudrate=4_000_000,
    polarity=0,
    phase=0,
    sck=Pin(CLOCK_PIN),
    mosi=Pin(DATA_PIN),
)

brightness_level = 31

# -------------------------------------------------
# APA102 basis
# -------------------------------------------------
def apa102_write(pixels):
    spi.write(b"\x00\x00\x00\x00")
    for r, g, b in pixels:
        spi.write(bytes([0b11100000 | int(brightness_level), b, g, r]))
    spi.write(b"\xFF\xFF\xFF\xFF")

def clear_strip():
    apa102_write([(0, 0, 0)] * NUM_LEDS)

# -------------------------------------------------
# HULPFUNCTIES VOOR KLEUREN + ANIMATIES
# -------------------------------------------------
def wheel(pos):
    """0-255 -> (r,g,b) regenboogkleur."""
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    else:
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)

def rainbow_startup(duration_ms=2000):
    """🌈 Regenbooganimatie bij systeemstart (duur = exact 2 sec)."""
    print("Startanimatie...")

    start = time.ticks_ms()
    step = 0

    while time.ticks_diff(time.ticks_ms(), start) < duration_ms:
        pixels = []
        for i in range(NUM_LEDS):
            color = wheel((i * 256 // NUM_LEDS + step) & 255)
            pixels.append(color)

        apa102_write(pixels)
        step = (step + 5) & 255   # snelheid van de animatie

        time.sleep_ms(50)         # kleine delay om CPU vrij te laten

    clear_strip()


def blink_color(color, times=3, on_ms=200, off_ms=200):
    """Laat de hele strip in een bepaalde kleur knipperen."""
    for _ in range(times):
        apa102_write([color] * NUM_LEDS)
        time.sleep_ms(on_ms)
        clear_strip()
        time.sleep_ms(off_ms)

def wifi_error_animation():
    print("❌ WiFi fout – rood knipperen")
    blink_color((255, 0, 0), times=5, on_ms=150, off_ms=150)

def mqtt_connected_animation():
    print("MQTT verbonden – groen knipperen")
    blink_color((0, 255, 0), times=3, on_ms=200, off_ms=200)

# -------------------------------------------------
# WIFI CONNECT (met wit knipperen tijdens connect)
# -------------------------------------------------
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    print("Verbinden met WiFi...", end="")
    blink = False
    start = time.ticks_ms()

    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.3)

        # Wit knipperen zolang nog geen WiFi
        blink = not blink
        if blink:
            apa102_write([(255, 255, 255)] * NUM_LEDS)  # wit
        else:
            clear_strip()

        # (optioneel) timeout na 20 seconden
        if time.ticks_diff(time.ticks_ms(), start) > 20000:
            print("\nWiFi timeout!")
            wifi_error_animation()
            # je kunt hier eventueel resetten of returnen
            break

    if wlan.isconnected():
        print("\nVerbonden:", wlan.ifconfig())
        clear_strip()

# ------------- TEMP → KLEUR -------------
def temp_to_color(t):
    if t < 10:
        return (255, 255, 255)          # wit
    elif 10 <= t <= 17:
        return (0, 150, 255)            # lichtblauw
    elif 18 <= t <= 22:
        return (0, 255, 0)              # groen
    elif 23 <= t <= 30:
        return (255, 140, 0)            # oranje
    else:  # > 30
        return (255, 0, 0)              # rood

def show_temp_color(temp_value):
    color = temp_to_color(temp_value)
    pixels = [color] * NUM_LEDS
    apa102_write(pixels)

# ------- MQTT CALLBACK -------
def callback(topic, msg):
    #print("🔔 MQTT bericht ontvangen:")
    #print("  Topic:", topic)
    #print("  Payload:", msg)

    try:
        temp = float(msg.decode())   # b'22' -> "22" -> 22.0
    except ValueError:
        print("⚠ Kon temperatuur niet parsen uit payload:", msg)
        # fout in payload → kort rood knipperen
        blink_color((255, 0, 0), times=2, on_ms=150, off_ms=150)
        return

    print("  Temperatuur:", temp)
    show_temp_color(temp)

# ------------- MAIN -------------
def main():
    # 🌈 SYSTEEMSTART ANIMATIE
    rainbow_startup()

    # 🔗 WIFI VERBINDEN (met wit knipperen)
    wifi_connect()

    # MQTT CLIENT
    client = MQTTClient(
        client_id="esp32_ledbar",
        server=MQTT_BROKER,
        port=MQTT_PORT,
        user=MQTT_USERNAME,
        password=MQTT_PASSWORD,
    )

    # MQTT CONNECT + STATUSANIMATIES
    try:
        client.set_callback(callback)
        client.connect()
        print("Verbonden met MQTT broker")
        mqtt_connected_animation()      # ✅ groen knipperen bij succesvolle connect
        client.subscribe(MQTT_TOPIC)
        print("Geabonneerd op", MQTT_TOPIC)
    except Exception as e:
        print("❌ MQTT verbindingsfout:", e)
        wifi_error_animation()          # rood knipperen bij fout
        return

    # Daarna normale werking: kleur volgens temperatuur
    while True:
        try:
            client.wait_msg()  # blokkeert tot bericht binnenkomt → callback()
        except Exception as e:
            print("❌ MQTT fout tijdens wait_msg:", e)
            wifi_error_animation()
            # kleine pauze, dan eventueel opnieuw proberen:
            time.sleep(2)

main()
