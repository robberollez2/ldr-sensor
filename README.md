# ldr-sensor

## Overzicht

Dit project haalt LDR-sensorwaarden op via de Rubu IoT API, zet de ruwe JSON om naar een pandas DataFrame en toont zowel een tijdreeksplot als een overzichtstabel met kernstatistieken (gemiddelde, minimum, maximum, mediaan, standaarddeviatie, aantal metingen en de exacte tijdsdekking). De code is opgezet met een basisklasse (`SensorHistory`) en een afgeleide klasse (`LdrHistory`).

## Belangrijkste functies

- Automatisch tijdsinterval bepalen op basis van de gevraagde historie (standaard 24 uur in `main.py`).
- Authenticated API-call (`requests`) met parsing naar pandas DataFrame.
- Gecombineerde matplotlib-figuur met grafiek + compacte statistiektabel.
- Polymorfe workflow (`render_history`).

## Vereisten

- Python 3.10 of hoger.
- Packages: `pandas`, `matplotlib`, `requests`.
- Geldige API-key voor de Rubu IoT endpoint.

## Installatie

1. Clone of download deze repository.
2. (Optioneel) Maak en activeer een virtual environment.
3. Installeer de benodigde pakketten:
   ```pwsh
   pip install pandas matplotlib requests
   ```
4. Vul in `config.py` je eigen `API_KEY` in als dat nog niet gebeurd is.

## Configuratie (`config.py`)

| Instelling    | Beschrijving                                                               |
| ------------- | -------------------------------------------------------------------------- |
| `API_KEY`     | Persoonlijke sleutel voor authenticatie bij de IoT-API.                    |
| `BASE_URL`    | Endpoint van de Rubu IoT-service.                                          |
| `TIME_FORMAT` | Datum/tijd-formaat dat zowel voor requests als voor output wordt gebruikt. |

Pas `LdrHistory(hours_back=...)` in `main.py` aan als je over een ander tijdsvenster wil rapporteren.

## Gebruik

1. Zorg dat de vereiste packages geïnstalleerd zijn en dat `config.py` correct is ingevuld.
2. Voer het script uit:
   ```pwsh
   python .\main.py
   ```
3. De console toont de ruwe DataFrame en metadata via `df.info()`. Daarna verschijnt een matplotlib-venster met de LDR-grafiek en daaronder de statistische tabel.

## Problemen oplossen

- **Geen data of HTTP-fout:** controleer `API_KEY`, netwerk en of `BASE_URL` bereikbaar is.
- **Lege grafiek:** mogelijk zijn er geen records in het gekozen tijdsvenster; verhoog `hours_back`.
