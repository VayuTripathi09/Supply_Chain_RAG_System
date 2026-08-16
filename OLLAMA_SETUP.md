# 🚀 SETUP OLLAMA - LOCAL LLM FOR SUPPLY CHAIN RAG

## Step 1: Install Ollama
Download and install from: **https://ollama.ai**
- Choose the version for your OS (Windows, Mac, Linux)
- Run the installer
- Restart your computer after installation

## Step 2: Verify Installation
Open PowerShell and run:
```powershell
ollama --version
```
Should output something like: `ollama version 0.x.x`

## Step 3: Pull Required Models
Run these commands in PowerShell (one at a time):

```powershell
# Download the LLM model (llama2 is ~4GB)
ollama pull llama2

# Download the embedding model (nomic-embed-text is ~275MB)
ollama pull nomic-embed-text
```

This will take 5-10 minutes depending on your internet speed.

## Step 4: Start Ollama
Ollama runs as a background service and is usually started automatically.
To verify it's running, try this in PowerShell:
```powershell
curl http://localhost:11434/api/tags
```

Should return a list of available models.

## Step 5: Verify Configuration
Check that your `.env` file has:
```
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_LLM_MODEL=llama2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## Step 6: Continue Testing
Once Ollama is running, I'll:
1. Restart the FastAPI server
2. Test PDF ingestion
3. Run queries and verify answers

---

**Once you've completed steps 1-5, let me know and we'll continue!** ✋
