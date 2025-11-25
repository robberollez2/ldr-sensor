import paho.mqtt.client as mqtt
import config
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from datetime import datetime, timedelta
from threading import Lock

import pandas as pd
import requests


# -------------------------------------------------------------
# Basisklasse voor LDR history ophalen
# -------------------------------------------------------------
class SensorHistory:
    def __init__(self, hours_back: int):
        self.hours_back = hours_back

    def build_interval(self):
        end = datetime.now()
        begin = end - timedelta(hours=self.hours_back)
        return (
            begin.strftime(config.TIME_FORMAT),
            end.strftime(config.TIME_FORMAT),
        )

    def build_url(self, begin: str, end: str) -> str:
        raise NotImplementedError()

    def fetch(self) -> pd.DataFrame:
        begin, end = self.build_interval()
        url = self.build_url(begin, end)
        headers = {"X-Api-Key": config.API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        df = pd.DataFrame.from_dict(response.json()["records"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df


class LdrHistory(SensorHistory):
    def __init__(self, hours_back=48):
        super().__init__(hours_back)
        self.param = "ldr"

    def build_url(self, begin: str, end: str):
        return f"{config.BASE_URL}?params={self.param}&begin={begin}&end={end}"


# -------------------------------------------------------------
# MQTT data buffers
# -------------------------------------------------------------
times = []
temps = []
data_lock = Lock()


def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Verbonden met broker:", reason_code)
    client.subscribe(config.MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        value = float(msg.payload.decode())
    except ValueError:
        print("Ongeldige MQTT waarde:", msg.payload)
        return

    now = datetime.now()
    with data_lock:
        times.append(now)
        temps.append(value)
        if len(times) > 200:
            times.pop(0)
            temps.pop(0)


# -------------------------------------------------------------
# GUI met twee grafieken onder elkaar
# -------------------------------------------------------------
def make_gui(df_history):
    root = tk.Tk()
    root.title("LDR Historiek (boven) + MQTT Temperatuur (onder)")

    # Twee grafieken onder elkaar
    fig, (ax_hist, ax_mqtt) = plt.subplots(nrows=2, ncols=1, figsize=(10, 7))
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True)

    # ---- Bovenste grafiek (statisch) ----
    def draw_history():
        ax_hist.clear()
        if df_history is not None and not df_history.empty:
            ax_hist.plot(df_history["timestamp"], df_history["ldr"], color="blue")
            ax_hist.set_title(f"LDR logging – laatste {history.hours_back}u")
            ax_hist.set_xlabel("Tijd")
            ax_hist.set_ylabel("LDR-waarde")
            ax_hist.grid(True, linestyle="--", alpha=0.4)
        else:
            ax_hist.text(0.5, 0.5, "Geen LDR data gevonden...",
                         ha="center", va="center", transform=ax_hist.transAxes)

    # ---- Onderste grafiek (MQTT auto-refresh) ----
    def refresh_mqtt_graph():
        with data_lock:
            t_copy = list(times)
            temp_copy = list(temps)

        ax_mqtt.clear()
        if t_copy:
            ax_mqtt.plot(t_copy, temp_copy, marker="o", color="red")
            ax_mqtt.set_title("MQTT Temperatuur (live)")
            ax_mqtt.set_xlabel("Tijd")
            ax_mqtt.set_ylabel("°C")
            fig.autofmt_xdate()
        else:
            ax_mqtt.text(0.5, 0.5, "Nog geen MQTT data ontvangen...",
                         ha="center", va="center", transform=ax_mqtt.transAxes)

        canvas.draw()

    def auto_refresh():
        refresh_mqtt_graph()
        root.after(1000, auto_refresh)  # elke 1s refresh

    # eerste keer tekenen
    draw_history()
    canvas.draw()

    # auto-refresh starten
    auto_refresh()

    return root


# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------
def main():
    global history

    # --- LDR data ophalen ---
    history = LdrHistory(hours_back=48)
    try:
        df_history = history.fetch()
    except Exception as e:
        print("Fout bij ophalen LDR data:", e)
        df_history = pd.DataFrame()

    # --- MQTT opzetten ---
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
    client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
    client.loop_start()

    # --- GUI starten ---
    root = make_gui(df_history)
    root.mainloop()

    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
