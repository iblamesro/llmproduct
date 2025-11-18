import os

# UI
APP_TITLE = "RegIntel AI"
APP_SUBTITLE = "Regulatory Intelligence Assistant"

# Models
MODEL_NAME = os.getenv("GEN_MODEL", "gpt-4.1-mini")
EMBEDDING_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

# RAG params
CHUNK_SIZE = 1800
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 8  # un peu plus de rappel pour les regs

# Suggested prompts
SUGGESTED_PROMPTS = [
    "Can you introduce me to all the principles of BCBS 239?",
    "Perform a gap analysis between HexaBank – Data Management Procedure and BCBS 239.",
    "List the main governance requirements from BCBS 239",
]

# API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY env var is not set.")