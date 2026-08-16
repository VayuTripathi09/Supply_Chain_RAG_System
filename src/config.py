import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Workspace paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

# Ingestion settings
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150

# ChromaDB settings
COLLECTION_NAME = "supply_chain_rag"

# Provider selection: 'openai' or 'ollama'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai").lower()

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Ollama settings
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3").strip()
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text").strip()

# Retrieval settings
RETRIEVAL_TOP_K = 6