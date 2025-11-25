import paho.mqtt.client as mqtt
import config
import matplotlib
matplotlib.use("TkAgg")  # Tkinter-backend voor matplotlib
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from datetime import datetime
from threading import Lock

# ====== Data-buffer ======
times = []
temps = []
data_lock = Lock()   # om thread-safe te werken tussen MQTT en GUI

# ====== MQTT callbacks ======
def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Verbonden met broker. Result code:", reason_code)
    client.subscribe(config.MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        value = float(msg.payload.decode())
    except ValueError:
        print("Ongeldige waarde:", msg.payload)
        return

    print(f"[{msg.topic}] {value}")

    now = datetime.now()
    with data_lock:
        times.append(now)
        temps.append(value)
        # optioneel: alleen laatste 100 punten
        if len(times) > 100:
            times.pop(0)
            temps.pop(0)


# ====== UI + grafiek ======
def make_gui():
    root = tk.Tk()
    root.title("MQTT Temperatuur Viewer (auto refresh)")

    fig, ax = plt.subplots(figsize=(6, 4))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def refresh_graph():
        # kopie maken zodat we lock maar kort vasthouden
        with data_lock:
            t_copy = list(times)
            temp_copy = list(temps)

        ax.clear()

        if t_copy:
            ax.plot(t_copy, temp_copy, marker="o")
            ax.set_title("Temperatuur via MQTT")
            ax.set_xlabel("Tijd")
            ax.set_ylabel("°C")
            fig.autofmt_xdate()
        else:
            ax.text(0.5, 0.5, "Nog geen data ontvangen...", ha="center",
                    va="center", transform=ax.transAxes)

        canvas.draw()

    def auto_refresh():
        refresh_graph()
        # elke 1000 ms (1 seconde) opnieuw
        root.after(1000, auto_refresh)

    # auto-refresh starten
    auto_refresh()

    return root


# ====== Main ======
def main():
    # MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
    client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)

    # MQTT-loop in achtergrondthread
    client.loop_start()

    # GUI starten
    root = make_gui()
    root.mainloop()

    # netjes stoppen als venster sluit
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()
