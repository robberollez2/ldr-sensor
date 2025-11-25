"""
config.py
Bevat alle configuratie-instellingen voor het LDR-project.
"""

from datetime import timedelta

# Vul hier je echte API-key in
API_KEY: str = "8e971ba20759cb779117a3593ede2e58068a76bc0f475fef4004c7d8bf1e311d"

# Basis-URL van de API 
BASE_URL = "https://www.rubu.be/iot/co2/api.php"
MQTT_BROKER = "mqtt.rubu.be"
MQTT_PORT = 1884
MQTT_TOPIC = "rollezrobbe/temp"
MQTT_USERNAME = "rollezrobbe"
MQTT_PASSWORD = "vm2qdu"

# Formaat voor begin/eind in de URL
TIME_FORMAT: str = "%Y-%m-%d %H:%M"