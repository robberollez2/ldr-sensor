"""
config.py
Bevat alle configuratie-instellingen voor het LDR-project.
"""

from datetime import timedelta

# Vul hier je echte API-key in
API_KEY: str = "api-key"

# Basis-URL van de API 
BASE_URL = "url"
MQTT_BROKER = "broker"
MQTT_PORT = 1885
MQTT_TOPIC = "topic"
MQTT_USERNAME = "username"
MQTT_PASSWORD = "password"

# Formaat voor begin/eind in de URL
TIME_FORMAT: str = "%Y-%m-%d %H:%M"