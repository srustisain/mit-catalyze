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

# ----------------------------------------------------------------------
# MCP SERVER REGISTRY
# ----------------------------------------------------------------------
# Supports both HTTP-based (streamable_http) and stdio-based MCP servers
# Format: {"server_name": {"transport": "stdio|streamable_http", ...}}
# 
# For stdio servers:
#   {"transport": "stdio", "command": "python", "args": ["/path/to/server.py"]}
#
# For HTTP servers:
#   {"transport": "streamable_http", "url": "http://localhost:8000"}
#
MCP_SERVERS = {
    # ChEMBL MCP Server (stdio-based)
    "chembl": {
        "transport": "stdio",
        "command": "node",
        "args": ["mcp_servers/chembl-mcp-server/build/index.js"]
    },
    
    # Opentrons MCP Server (stdio-based)
    "opentrons": {
        "transport": "stdio",
        "command": "node",
        "args": ["mcp_servers/opentrons-mcp-server/dist/index.js"]
    },
    
    # Example HTTP-based MCP servers (commented out for now)
    # "literature": {
    #     "transport": "streamable_http", 
    #     "url": "http://localhost:8001/mcp"
    # },
    # "knowledge_graph": {
    #     "transport": "streamable_http",
    #     "url": "http://localhost:8002/mcp"
    # },
    
    # Example stdio-based MCP servers
    # "local_math": {
    #     "transport": "stdio",
    #     "command": "python",
    #     "args": ["./examples/math_server.py"]
    # },
    # "local_chem": {
    #     "transport": "stdio", 
    #     "command": "python",
    #     "args": ["./examples/chem_server.py"]
    # }
}
