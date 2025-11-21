import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
import config

# -------------------------------------------------------------
# Basisklasse voor het ophalen en verwerken van sensorhistorie
# -------------------------------------------------------------
class SensorHistory:
    def __init__(self, hours_back: int):
        # Slaat op hoeveel uur terug we data willen opvragen
        self.hours_back = hours_back

    def build_interval(self):
        # Bepaalt het tijdsinterval (begin en einde) op basis van het aantal uren terug
        end = datetime.now()  # Huidige tijd
        begin = end - timedelta(hours=self.hours_back)  # Tijd 'hours_back' uur geleden

        # Formatteert de tijden volgens het ingestelde formaat in config
        return (
            begin.strftime(config.TIME_FORMAT),
            end.strftime(config.TIME_FORMAT),
        )

    def build_url(self, begin: str, end: str) -> str:
        # Wordt overschreven in afgeleide klasses; hier moet de querystring worden gebouwd
        raise NotImplementedError("Derived class must provide the query params.")

    def fetch(self) -> pd.DataFrame:
        # Haalt de sensorwaarden op binnen het berekende interval
        begin, end = self.build_interval()
        url = self.build_url(begin, end)  # Bouwt de volledige API‑URL

        headers = {"X-Api-Key": config.API_KEY}  # Voegt API‑sleutel toe aan de request
        response = requests.get(url, headers=headers)  # Verstuurd request
        response.raise_for_status()  # Gooi fout als status niet 200 is

        # Zet het JSON‑antwoord om naar een pandas DataFrame
        frame = pd.DataFrame.from_dict(response.json()["records"])

        # Converteert 'timestamp' kolom naar een datetime object
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])

        return frame

    def plot(self, frame: pd.DataFrame):
        # Wordt overschreven in afgeleide klasses; hier moet de plot gestopt worden
        raise NotImplementedError("Derived class must implement plotting.")


# -------------------------------------------------------------
# Klasse specifiek voor het ophalen van LDR sensorhistorie
# -------------------------------------------------------------
class LdrHistory(SensorHistory):
    def __init__(self, hours_back: int = 48):
        # Roept constructor van de basisklasse aan
        super().__init__(hours_back)
        self.param = "ldr"  # Naam van de parameter zoals gebruikt in de API

    def build_url(self, begin: str, end: str) -> str:
        # Bouwt de URL volgens het API‑formaat, met begin‑ en eindtijd meegegeven
        return f"{config.BASE_URL}?params={self.param}&begin={begin}&end={end}"

    def plot(self, frame: pd.DataFrame, summary: pd.DataFrame | None = None):
        # Maakt een gecombineerde visualisatie (grafiek + tabel)
        if summary is None:
            summary = self.summarize(frame)

        fig, (ax_plot, ax_table) = plt.subplots(
            nrows=2,
            ncols=1,
            figsize=(11, 8),
            height_ratios=[3, 1.2],
        )

        frame.plot(
            x="timestamp",
            y=[self.param],
            ax=ax_plot,
            title=f"LDR Logging T1.18 -- Laatste {self.hours_back}u",
            xlabel="Datetime",
            ylabel="LDR waarde",
            legend=False,
        )
        ax_plot.grid(True, linestyle="--", alpha=0.4)

        ax_table.axis("off")
        table_data = summary.reset_index().rename(
            columns={"stat": "Stat", "waarde": "Waarde"}
        )
        stats = table_data["Stat"].tolist()
        values = [str(val) for val in table_data["Waarde"].tolist()]
        table_matrix = [["Stat"] + stats, ["Waarde"] + values]
        table = ax_table.table(
            cellText=table_matrix,
            cellLoc="center",
            loc="center",
            bbox=[0.1, 0.05, 0.8, 0.9],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(2, 1.4)

        for (row, col), cell in table.get_celld().items():
            cell.PAD = 0.2
            if row == 0:
                cell.set_text_props(weight="bold", style="normal")
            elif col == 0:
                cell.set_text_props(style="normal")
            else:
                cell.set_text_props(style="italic")

        plt.tight_layout()
        plt.show()  # Toon de grafiek en tabel

    def summarize(self, frame: pd.DataFrame) -> pd.DataFrame:
        # Bouwt een compacte tabel met kerncijfers over de gekozen periode
        values = frame[self.param]
        t_begin = frame["timestamp"].min()
        t_end = frame["timestamp"].max()
        duration_hours = round((t_end - t_begin).total_seconds() / 3600, 2)

        summary = pd.DataFrame(
            {
                "stat": [
                    "Gemiddelde",
                    "Minimum",
                    "Maximum",
                    "Mediaan",
                    "Standaarddeviatie",
                    "Aantal metingen",
                ],
                "waarde": [
                    round(values.mean(), 3),
                    round(values.min(), 3),
                    round(values.max(), 3),
                    round(values.median(), 3),
                    round(values.std(ddof=0), 3),
                    int(values.count()),
                ],
            }
        ).set_index("stat")

        abbreviations = {
            "Gemiddelde": "Gem",
            "Minimum": "Min",
            "Maximum": "Max",
            "Mediaan": "Med",
            "Standaarddeviatie": "Std",
            "Aantal metingen": "N",
        }
        summary.index = summary.index.to_series().map(lambda x: abbreviations.get(x, x))

        return summary

# -------------------------------------------------------------
# Uitvoeren wanneer het script direct wordt gestart
# -------------------------------------------------------------
if __name__ == "__main__":
    history = LdrHistory(hours_back=24)  # Maak een instantie voor laatste 12 uur
    df = history.fetch()  # Haal data op

    print(df, "\n")  # Print volledige DataFrame
    df.info()  # Geef informatie over het DataFrame
    summary_table = history.summarize(df)
    history.plot(df, summary_table)  # Toon grafiek + tabel in één figuur
