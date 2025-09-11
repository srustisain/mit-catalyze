
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# PubChem API settings
PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# App settings
APP_TITLE = "Catalyze - AI-Powered Chemistry Assistant"
APP_DESCRIPTION = "Transform research questions into lab protocols and automation scripts"




