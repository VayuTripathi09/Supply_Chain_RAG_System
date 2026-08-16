import requests
from openai import OpenAI
from src.config import (
    EMBEDDING_PROVIDER,
    OPENAI_API_KEY,
    OLLAMA_HOST,
    OLLAMA_EMBEDDING_MODEL
)

class OpenAIEmbeddingFunction:
    def __init__(self, api_key=None):
        # Delay API key loading to allow startup without key
        self.api_key = api_key or OPENAI_API_KEY
        self.client = None
        self.model = "text-embedding-3-small"

    def name(self):
        return "openai"

    def embed_query(self, input):
        """ChromaDB query embedding method."""
        return self(input)

    def __call__(self, input):
        """Generates embeddings for a string or list of strings.
        
        Always returns a list of embeddings (list of lists of floats).
        """
        # Validate key availability on-call
        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Please set OPENAI_API_KEY in your .env file.")
            
        if self.client is None:
            self.client = OpenAI(api_key=self.api_key)
            
        if isinstance(input, str):
            input = [input]
            
        embeddings = []
        batch_size = 100
        for i in range(0, len(input), batch_size):
            batch = input[i:i+batch_size]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            embeddings.extend([data.embedding for data in response.data])
        return embeddings


class OllamaEmbeddingFunction:
    def __init__(self, host=OLLAMA_HOST, model=OLLAMA_EMBEDDING_MODEL):
        self.host = host.rstrip("/")
        self.model = model

    def name(self):
        return "ollama"

    def check_ollama_availability(self):
        """Checks if Ollama is running and the model is available."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=3)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                if any(self.model in m for m in models):
                    return True
                print(f"Warning: Ollama is running but model '{self.model}' was not found in: {models}")
                return False
            return False
        except Exception:
            return False

    def embed_query(self, input):
        """ChromaDB query embedding method."""
        return self(input)

    def __call__(self, input):
        """Generates embeddings for a string or list of strings using Ollama.
        
        Always returns a list of embeddings (list of lists of floats).
        """
        if isinstance(input, str):
            input = [input]
            
        # Try batch embedding if supported
        try:
            response = requests.post(
                f"{self.host}/api/embed",
                json={"model": self.model, "input": input},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["embeddings"]
        except Exception:
            pass
            
        # Fallback: embed one-by-one
        embeddings = []
        for text in input:
            try:
                response = requests.post(
                    f"{self.host}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                    timeout=10
                )
                if response.status_code == 200:
                    embeddings.append(response.json()["embedding"])
                else:
                    raise ValueError(f"Ollama embedding failed with status {response.status_code}: {response.text}")
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Ollama at {self.host}: {e}")
        return embeddings


def get_embedding_function():
    """Returns the embedding function based on the configuration."""
    if EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddingFunction()
    elif EMBEDDING_PROVIDER == "ollama":
        return OllamaEmbeddingFunction()
    else:
        raise ValueError(f"Unknown embedding provider: {EMBEDDING_PROVIDER}")