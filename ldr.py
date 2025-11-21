import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

API_KEY = "api-key-placeholder"

begin = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
end = datetime.now().strftime("%Y-%m-%d %H:%M")

url = f"https://www.rubu.be/iot/co2/api.php?params=ldr&begin={begin}&end={end}"

header = {"X-Api-Key" : API_KEY}

response = requests.get(url, headers=header)

if response.status_code == 200:
    data = response.json()
    recordsDataFrame = pd.DataFrame.from_dict(data["records"])
    print(recordsDataFrame)
    print()

    datetimes = pd.to_datetime(recordsDataFrame["timestamp"])
    recordsDataFrame["timestamp"] = datetimes
    recordsDataFrame.info()

    recordsDataFrame.plot(x="timestamp", y=["ldr"], figsize=(10,6),
                          title=f"LDR Logging T1.18", xlabel="Datetime")
    plt.show()