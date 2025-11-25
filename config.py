"""
config.py
Bevat alle configuratie-instellingen voor het LDR-project.
"""

from datetime import timedelta

# Vul hier je echte API-key in
API_KEY: str = "api-key-placeholder"

# Basis-URL van de API 
BASE_URL = "api-url"
MQTT_BROKER = "your-broker"
MQTT_PORT = 1884
MQTT_TOPIC = "your-topic"
MQTT_USERNAME = "your-username"
MQTT_PASSWORD = "your-password"

# Formaat voor begin/eind in de URL
TIME_FORMAT: str = "%Y-%m-%d %H:%M"