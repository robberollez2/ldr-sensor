import paho.mqtt.client as mqtt  # MQTT client library
import config  # Eigen config met API keys en endpoints
import matplotlib  # Plotting backend
matplotlib.use("TkAgg")  # Tkinter-backend kiezen voor Matplotlib
import matplotlib.pyplot as plt  # Plotting functionaliteit

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # Canvas voor Tk
import tkinter as tk  # GUI toolkit
from datetime import datetime, timedelta  # Tijdsfuncties
from threading import Lock  # Voor thread-safe data toegang

import pandas as pd  # Dataverwerking in tabellen
import requests  # HTTP requests naar de API


# -------------------------------------------------------------
# Basisklasse voor LDR history ophalen
# -------------------------------------------------------------
class SensorHistory:
    def __init__(self, hours_back: int):
        self.hours_back = hours_back  # Bewaar aantal uren terug

    def build_interval(self):
        # Huidig tijdstip
        end = datetime.now()  
        # Starttijd
        begin = end - timedelta(hours=self.hours_back)  
        return (
            begin.strftime(config.TIME_FORMAT),
            end.strftime(config.TIME_FORMAT),
        )

    # Implementeren in afgeleide klasse
    def build_url(self, begin: str, end: str) -> str:
        raise NotImplementedError()  

    def fetch(self) -> pd.DataFrame:
        # Tijdvenster bepalen
        begin, end = self.build_interval()  
        # API URL opbouwen
        url = self.build_url(begin, end)  
        # Auth header
        headers = {"X-Api-Key": config.API_KEY}  
        # HTTP call
        response = requests.get(url, headers=headers)  
        # Fout bij niet-200
        response.raise_for_status()  

        # JSON -> DF
        df = pd.DataFrame.from_dict(response.json()["records"])  
        # Timestamps
        df["timestamp"] = pd.to_datetime(df["timestamp"])  
        # DataFrame teruggeven
        return df  


class LdrHistory(SensorHistory):
    # Init base met tijdsvenster
    def __init__(self, hours_back=48):
        super().__init__(hours_back)  
        # Queryparameter voor LDR
        self.param = "ldr"  

    def build_url(self, begin: str, end: str):
        # Final API URL
        return f"{config.BASE_URL}?params={self.param}&begin={begin}&end={end}"  


# -------------------------------------------------------------
# MQTT data buffers
# -------------------------------------------------------------
times = []  # Tijdstippen van MQTT metingen
temps = []  # Waarden van MQTT metingen
data_lock = Lock()  # Lock voor thread-safe toegang


def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Verbonden met broker:", reason_code)  
    client.subscribe(config.MQTT_TOPIC)  


def on_message(client, userdata, msg):
    try:
        value = float(msg.payload.decode())  # Payload naar float
    except ValueError:
        print("Ongeldige MQTT waarde:", msg.payload)  # Foutafhandeling
        return  # Stop bij invalid

    # Huidige timestamp
    now = datetime.now() 
    # Met lock zodat alleen één thread tegelijk in de buffer schrijft
    with data_lock:  
        times.append(now)  # Tijd opslaan
        temps.append(value)  # Waarde opslaan
        if len(times) > 200:  # Buffer beperken
            times.pop(0)  # Oudste tijd weg
            temps.pop(0)  # Oudste temperatuur weg


# -------------------------------------------------------------
# GUI met twee grafieken onder elkaar
# -------------------------------------------------------------
def make_gui(df_history):
    root = tk.Tk()  # Hoofdvenster
    root.title("LDR Historiek (boven) + MQTT Temperatuur (onder)")  # Titel

    # Twee grafieken onder elkaar
    fig, (ax_hist, ax_mqtt) = plt.subplots(nrows=2, ncols=1, figsize=(10, 7))  # Twee subplots
    plt.tight_layout()  # Layout netjes

    canvas = FigureCanvasTkAgg(fig, master=root)  # Matplotlib in Tk
    canvas_widget = canvas.get_tk_widget()  # Canvas widget
    canvas_widget.pack(fill=tk.BOTH, expand=True)  # Uitrekken in venster

    # ---- Bovenste grafiek (statisch) ----
    def draw_history():
        ax_hist.clear()  # Reset as voor historiek
        if df_history is not None and not df_history.empty:  # Data aanwezig
            ax_hist.plot(df_history["timestamp"], df_history["ldr"], color="blue")  # Lijnplot
            ax_hist.set_title(f"LDR logging – laatste {history.hours_back}u")  # Titel
            ax_hist.set_xlabel("Tijd")  # X-label
            ax_hist.set_ylabel("LDR-waarde")  # Y-label
            ax_hist.grid(True, linestyle="--", alpha=0.4)  # Raster
        else:  # Geen data
            ax_hist.text(0.5, 0.5, "Geen LDR data gevonden...",
                         ha="center", va="center", transform=ax_hist.transAxes)  # Placeholder tekst

    # ---- Onderste grafiek (MQTT auto-refresh) ----
    def refresh_mqtt_graph():
        with data_lock:  # Thread-safe copy
            t_copy = list(times)  # Kopie van tijdstempels
            temp_copy = list(temps)  # Kopie van waarden

        ax_mqtt.clear()  # Reset MQTT plot
        if t_copy:  # Als er data is
            ax_mqtt.plot(t_copy, temp_copy, marker="o", color="red")  # Lijn/points
            ax_mqtt.set_title("MQTT Temperatuur (live)")  # Titel
            ax_mqtt.set_xlabel("Tijd")  # X-label
            ax_mqtt.set_ylabel("°C")  # Y-label
            fig.autofmt_xdate()  # Datum labels kantelen
        else:  # Geen data ontvangen
            ax_mqtt.text(0.5, 0.5, "Nog geen MQTT data ontvangen...",
                         ha="center", va="center", transform=ax_mqtt.transAxes)  # Placeholder

        canvas.draw()  # Canvas bijwerken

    def auto_refresh():
        refresh_mqtt_graph()  # Herteken MQTT grafiek
        root.after(1000, auto_refresh)  # elke 1s refresh

    # eerste keer tekenen
    draw_history()  # Eerste historiek plot
    canvas.draw()  # Canvas tonen

    # auto-refresh starten
    auto_refresh()  # Start interval

    return root  # Geef Tk root terug


# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------
def main():
    global history

    # --- LDR data ophalen ---
    history = LdrHistory(hours_back=48)  # Historiek over 48u
    try:
        df_history = history.fetch()  # Data laden
    except Exception as e:
        print("Fout bij ophalen LDR data:", e)  # Foutmelding
        df_history = pd.DataFrame()  # Lege DF bij fout

    # --- MQTT opzetten ---
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # Nieuwe client
    client.on_connect = on_connect  # Callback connect
    client.on_message = on_message  # Callback messages
    client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)  # Auth
    client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)  # Verbinden
    client.loop_start()  # Start async loop

    # --- GUI starten ---
    root = make_gui(df_history)  # Bouw GUI
    root.mainloop()  # Start event loop

    client.loop_stop()  # Stop MQTT loop
    client.disconnect()  # Netjes afsluiten


if __name__ == "__main__":
    main()
