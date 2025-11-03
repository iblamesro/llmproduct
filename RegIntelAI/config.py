"""
Configuration for RegIntel AI
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini"  # Fast reasoning, bilingual
EMBEDDING_MODEL = "text-embedding-3-small"  # Cheap and multilingual

# Vector Store Configuration
CHROMA_DB_DIR = "./chroma_db"
COLLECTION_NAME = "regulatory_documents"

# RAG Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 5

# UI Configuration
APP_TITLE = "RegIntel AI"
APP_SUBTITLE = "AI-Driven Regulatory & Compliance Copilot"
APP_ICON = "🏦"

# Suggested Prompts
SUGGESTED_PROMPTS = [
    "Compare this internal policy to EU AI Act Article 9",
    "Highlight regulatory gaps in this document against EBA guidelines",
    "What are the key compliance requirements from this regulation?",
    "Perform a gap analysis between our current policies and GDPR Article 35",
    "Summarize the main obligations from this ECB regulation"
]
