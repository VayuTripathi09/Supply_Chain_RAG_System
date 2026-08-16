import os
import shutil
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from src.config import (
    DATA_DIR,
    COLLECTION_NAME,
    EMBEDDING_PROVIDER,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OLLAMA_LLM_MODEL,
    OLLAMA_EMBEDDING_MODEL
)
from src.pipeline import RAGPipeline

app = FastAPI(
    title="Meridian SCM RAG API",
    description="FastAPI Backend for Supply Chain RAG application",
    version="1.0"
)

# Initialize RAG Pipeline
# If the OpenAI key is missing, we don't crash the server start,
# but we will raise HTTPExceptions during requests if it fails.
pipeline = RAGPipeline()

class QueryRequest(BaseModel):
    question: str
    top_k: int = 4

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]

class StatsResponse(BaseModel):
    collection_name: str
    total_chunks: int
    embedding_provider: str
    embedding_model: str
    llm_provider: str
    llm_model: str

@app.post("/ingest")
async def ingest_files(files: List[UploadFile] = File(...)):
    """Receives one or more PDF files, saves them, and indexes them into ChromaDB."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    saved_files = 0
    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Only PDF files are allowed. Got {file.filename}")
            
        file_path = os.path.join(DATA_DIR, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files += 1
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file {file.filename}: {e}")
            
    try:
        # Index data folder
        files_indexed, chunks_indexed = pipeline.index_data_directory(DATA_DIR)
        return {
            "files": files_indexed,
            "chunks": chunks_indexed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")


@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Answers a question using the grounded RAG pipeline."""
    try:
        # Check if collection is empty
        count = pipeline.vector_store.get_chunk_count()
        if count == 0:
            raise HTTPException(status_code=400, detail="Database is empty. Please ingest documents first.")
            
        # Run query through pipeline with optional top_k override
        res = pipeline.ask(request.question, top_k=request.top_k)
        
        # Format sources for response: rename 'filename' to 'file'
        formatted_sources = []
        for src in res["sources"]:
            formatted_sources.append({
                "file": src["filename"],
                "page": src["page"]
            })
            
        return QueryResponse(
            answer=res["answer"],
            sources=formatted_sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG generation failed: {e}")


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Returns vector collection statistics and model metadata."""
    try:
        total_chunks = pipeline.vector_store.get_chunk_count()
    except Exception as e:
        total_chunks = 0
        print(f"Error reading chunk count for stats: {e}")
        
    embed_model = "text-embedding-3-small" if EMBEDDING_PROVIDER == "openai" else OLLAMA_EMBEDDING_MODEL
    llm_model = "gpt-4o" if LLM_PROVIDER == "openai" else OLLAMA_LLM_MODEL
    
    return StatsResponse(
        collection_name=COLLECTION_NAME,
        total_chunks=total_chunks,
        embedding_provider=EMBEDDING_PROVIDER,
        embedding_model=embed_model,
        llm_provider=LLM_PROVIDER,
        llm_model=llm_model
    )