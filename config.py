"""
config.py
Bevat alle configuratie-instellingen voor het LDR-project.
"""

from datetime import timedelta

# Vul hier je echte API-key in
API_KEY: str = "api-key-placeholder"

# Basis-URL van de API 
BASE_URL: str = "https://www.rubu.be/iot/co2/api.php"

# Formaat voor begin/eind in de URL
TIME_FORMAT: str = "%Y-%m-%d %H:%M"

# MongoDB instellingen 
MONGO_URI: str = "mongodb://localhost:27017"
DB_NAME: str = "ldr_project"
COLLECTION_NAME: str = "ldr_readings"