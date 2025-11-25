import time
import smbus2
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

# === GPIO ===
GPIO.setmode(GPIO.BCM)
INPUT_PIN = 18
GPIO.setup(INPUT_PIN, GPIO.IN)

# === TC74 ===
I2C_BUS = 1
TC74_ADDR = 0x48
TEMP_REG = 0x00

# === MQTT ===
MQTT_BROKER = "mqtt.rubu.be"    
MQTT_PORT = 1884
MQTT_TOPIC = "rollezrobbe/temp"   
MQTT_USERNAME = "rollezrobbe"
MQTT_PASSWORD = "vm2qdu"

bus = smbus2.SMBus(I2C_BUS)

# ==== MQTT callbacks ====
def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Verbonden met MQTT broker, result code:", reason_code)

def on_disconnect(client, userdata, reason_code, properties=None):
    print("MQTT verbinding verbroken, code:", reason_code)

def read_temp_value():
    try:
        temp = bus.read_byte_data(TC74_ADDR, TEMP_REG)
        return temp
    except Exception as e:
        print("Fout bij lezen TC74:", e)
        return None

def main():
    # MQTT client aanmaken
    client = mqtt.Client(client_id="rollezrobbe")  # or mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # Verbind met broker
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()   # start netwerkloop in achtergrondthread

    try:
        while True:
            temp = read_temp_value()
            if temp is not None:
                # publiceer als integer
                payload = str(temp)
                print(f"Publiceer {payload} naar topic {MQTT_TOPIC}")
                result = client.publish(MQTT_TOPIC, payload, qos=0, retain=False)
                #check status:
                status = result[0]
                if status != mqtt.MQTT_ERR_SUCCESS:
                    print("Fout bij publish:", status)
            else:
                print("Geen geldige temperatuur gelezen.")

            time.sleep(2)  
    except KeyboardInterrupt:
        print("Afsluiten...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()