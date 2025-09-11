
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# LLM Provider settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # Default to openai

# Model settings
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL", "llama3.1-70b")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")

# PubChem API settings
PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# App settings
APP_TITLE = "Catalyze - AI-Powered Chemistry Assistant"
APP_DESCRIPTION = "Transform research questions into lab protocols and automation scripts"
