# Supply Chain RAG System

A Retrieval-Augmented Generation (RAG) system for analyzing **Supply Chain Performance** and **Procurement Policy** documents using semantic search, vector databases, and Large Language Models.

The system retrieves relevant information from the supplied documents and generates **grounded answers with document and page-level citations**.

It is designed to handle **cross-document questions**, where the answer requires information from both the Supply Chain Performance Review and the Procurement Policy Handbook.

---

##  Project Overview

Traditional document search often relies on exact keywords. This project uses **semantic search** to understand the meaning of a question and retrieve the most relevant sections from the documents.

### Example

A user asks:

> "Kaveri Metals had poor delivery performance. Which policy clauses does this trigger?"

The system can retrieve:

```text
Supply Chain Performance Review
        ↓
Kaveri Metals performance data

        +

Procurement Policy Handbook
        ↓
Applicable policy rules

        ↓
       GPT-4o
        ↓
Grounded Answer + Sources
```

The system is designed to answer **only from the retrieved document context** and refuse questions when the required information is not available.

---

#  Architecture

```text
                    ┌──────────────────────┐
                    │      PDF Documents   │
                    │                      │
                    │  Performance Review  │
                    │  Procurement Policy  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    PDF Extraction    │
                    │      PyMuPDF         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Chunking        │
                    │ Recursive Splitter   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Embeddings      │
                    │ text-embedding-3-    │
                    │       small          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      ChromaDB        │
                    │ Persistent Vector DB │
                    └──────────┬───────────┘
                               │
                      User Question
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Retrieval       │
                    │  Semantic Search +   │
                    │ Cross-Document Logic │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Retrieved Context │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │        LLM           │
                    │     GPT-4o/Ollama    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Answer + Citations   │
                    └──────────────────────┘
```

---

#  Project Structure

```text
supply-chain-rag/
│
├── api/
│   ├── __init__.py
│   └── main.py
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── loader.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── retriever.py
│   ├── generator.py
│   └── pipeline.py
│
├── data/
│   ├── Meridian_Supply_Chain_Review_Q1_FY2025-26.pdf
│   └── Meridian_Procurement_Policy_Handbook_v4.2.pdf
│
├── chroma_db/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

#  Documents

The application works with two primary documents.

### 1. Supply Chain Performance Review

Contains information such as:

* Supplier performance
* Supplier spending
* On-time delivery
* Inventory
* Quality data
* Defects
* Freight costs
* Line stoppages
* Operational risks

### 2. Procurement Policy Handbook

Contains rules related to:

* Supplier classification
* Purchase-order approval
* Procurement requirements
* Penalties
* Safety-stock calculations
* Escalation procedures

The key purpose of the project is to connect information from these two documents when answering questions.

---

#  Technology Stack

| Technology              | Purpose                               |
| ----------------------- | ------------------------------------- |
| Python                  | Core programming language             |
| PyMuPDF                 | PDF text extraction                   |
| LangChain Text Splitter | Document chunking                     |
| OpenAI                  | Embeddings and GPT-4o                 |
| Ollama                  | Optional local LLM/embedding provider |
| ChromaDB                | Vector database                       |
| FastAPI                 | Backend API                           |
| Uvicorn                 | API server                            |
| python-dotenv           | Environment configuration             |
| Git                     | Version control                       |

---

#  Requirements

* Python 3.10+
* Git
* OpenAI API key **OR**
* Ollama running locally

For OpenAI:

```text
text-embedding-3-small
GPT-4o
```

For Ollama, the project can use locally available models depending on the configured provider.

---

#  Installation

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd supply-chain-rag
```

---

## 2. Create a virtual environment

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

#  Environment Configuration

Create a `.env` file in the project root.

### OpenAI configuration

```env
OPENAI_API_KEY=your_openai_api_key

LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
```

Do **not** commit `.env` to Git.

---

#  Ollama Configuration

The project also supports Ollama for local inference.

First install Ollama and make sure it is running.

Check:

```bash
ollama --version
```

Check installed models:

```bash
ollama list
```

Check the local API:

```text
http://localhost:11434
```

For example, you can use:

```bash
ollama pull llama3
ollama pull nomic-embed-text
```

Then configure:

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama

OLLAMA_HOST=http://localhost:11434
OLLAMA_LLM_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

The existing architecture supports both OpenAI and Ollama providers.

---

#  Document Ingestion

Documents should be placed inside:

```text
data/
```

The ingestion pipeline performs:

```text
PDF
 ↓
Page-level text extraction
 ↓
Metadata attachment
 ↓
Chunking
 ↓
Embeddings
 ↓
ChromaDB
```

Each chunk maintains:

* Source filename
* Page number
* Document type
* Chunk ID

---

#  Chunking Strategy

The project uses recursive character splitting.

Current configuration:

```text
Chunk Size: 1200
Chunk Overlap: 150
```

The overlap helps prevent important sentences or policy clauses from being split across chunk boundaries.

The assignment recommends a chunk size of approximately 800–1200 characters and an overlap of 100–200 characters.

---

#  Embeddings

The default OpenAI embedding model is:

```text
text-embedding-3-small
```

The same embedding model must be used for both:

* Document chunks
* User queries

This allows semantic similarity search to work correctly.

---

#  ChromaDB

ChromaDB is used as the persistent vector database.

Both documents are stored in the **same collection**.

Each stored chunk contains:

```text
Embedding
Text
Source
Page
Document Type
```

The database is persisted locally:

```text
chroma_db/
```

This means the application can restart without requiring the documents to be indexed again.

---

#  Retrieval

The retrieval process works as follows:

```text
User Question
      ↓
Question Embedding
      ↓
ChromaDB Similarity Search
      ↓
Top-K Relevant Chunks
      ↓
Check Document Diversity
      ↓
Cross-Document Fallback
      ↓
Final Context
```

The current implementation uses a default retrieval value of approximately:

```text
top_k = 6
```

The retriever also contains cross-document fallback logic to help ensure that relevant information from both document types can be retrieved when required.

---

#  Cross-Document Retrieval

Cross-document retrieval is the most important feature of this assignment.

For example:

```text
Question:
"Kaveri Metals had 88.1% on-time delivery.
Which policy clause does this trigger?"
```

The system may need:

```text
Performance Review
        ↓
88.1% delivery

        +

Procurement Policy
        ↓
Applicable threshold/penalty

        ↓
       GPT-4o
        ↓
Grounded Answer
```

If initial retrieval returns only one document type, the retriever performs an additional retrieval process to obtain relevant chunks from the other document.

---

#  Answer Generation

The system supports:

### OpenAI

```text
GPT-4o
```

### Ollama

A locally running Ollama model can be used when configured.

The generator is instructed to:

* Use only retrieved context
* Avoid hallucination
* Preserve numerical values
* Explain applicable rules
* Refuse unsupported questions
* Provide source information

The existing generator supports both OpenAI and Ollama implementations.

---

#  Citations

Answers should include document-level and page-level sources.

Example:

```text
Answer:
Kaveri Metals triggers the applicable performance clause
because its delivery performance is below the required threshold.

Sources:
- Meridian_Supply_Chain_Review_Q1_FY2025-26.pdf — Page 4
- Meridian_Procurement_Policy_Handbook_v4.2.pdf — Page 12
```

The source information is taken from the metadata associated with retrieved chunks.

---

#  FastAPI API

The backend exposes three main endpoints.

## POST `/ingest`

Used to upload and index PDFs.

Example response:

```json
{
  "files_processed": 2,
  "chunks_indexed": 84
}
```

---

## POST `/ask`

Used to ask questions.

Example request:

```json
{
  "question": "Which supplier had the highest spend?",
  "top_k": 5
}
```

Example response:

```json
{
  "answer": "....",
  "sources": [
    {
      "file": "Meridian_Supply_Chain_Review_Q1_FY2025-26.pdf",
      "page": 4
    }
  ]
}
```

---

## GET `/stats`

Returns vector-store information.

Example:

```json
{
  "collection_name": "supply_chain_rag",
  "total_chunks": 84
}
```

---

#  Running the API

Start the FastAPI server:

```bash
uvicorn api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

FastAPI provides an interactive Swagger interface for testing the endpoints.

---

#  Testing

The system should be tested using the assignment's ten questions:

1. Highest spend supplier and its on-time delivery
2. Line stoppages, downtime, causes
3. Approval authority for ₹1.4 crore
4. Supplier classification categories
5. Kaveri Metals — clauses triggered
6. Single-source microcontrollers — policy requirement
7. Safety stock for a 46-day imported part
8. Trident 640 PPM — cost consequence
9. Suppliers below B band — escalation path
10. Trap question — must be refused

Special attention should be given to questions requiring information from both documents.

---

#  Hallucination Prevention

The system should refuse to answer when the requested information is not present in the supplied documents.

Expected behavior:

```text
I cannot answer this question from the provided documents
because the required information was not found in the retrieved context.
```

The system must not invent:

* Numbers
* Policy clauses
* Suppliers
* Page numbers
* Penalties
* Approval limits

---

#  Security

Never commit:

```text
.env
API keys
Access tokens
Secrets
```

The `.gitignore` should include:

```text
.env
venv/
__pycache__/
*.pyc
chroma_db/
```

---

#  Current Architecture

```text
FastAPI
   │
   ├── /ingest
   │       │
   │       ▼
   │   PDF Loader
   │       ↓
   │   Chunker
   │       ↓
   │   Embeddings
   │       ↓
   │   ChromaDB
   │
   └── /ask
           │
           ▼
       Retriever
           │
           ▼
    Cross-Document
       Retrieval
           │
           ▼
      Context Builder
           │
           ▼
       GPT-4o/Ollama
           │
           ▼
     Answer + Sources
```

The current project already implements the core pipeline from document loading through retrieval and generation.

---

#  Project Status

### Core RAG

* [x] PDF extraction
* [x] Page metadata
* [x] Chunking
* [x] Embeddings
* [x] ChromaDB
* [x] Persistent storage
* [x] Duplicate protection
* [x] Semantic retrieval
* [x] Cross-document retrieval
* [x] LLM generation
* [x] Source metadata

### Backend

* [x] FastAPI
* [x] `/ingest`
* [x] `/ask`
* [x] `/stats`

### Configuration

* [ ] Verify `.env`
* [ ] Verify `requirements.txt`
* [ ] Verify package initialization
* [ ] Verify provider configuration

### Testing

* [ ] Index both PDFs
* [ ] Test persistence
* [ ] Test all 10 questions
* [ ] Verify cross-document answers
* [ ] Verify citations
* [ ] Verify trap question refusal

### Documentation

* [x] README
* [ ] Add screenshots
* [ ] Add final test results
* [ ] Add demo video

---

#  Known Issues to Verify

Before considering the project complete, verify:

1. `top_k` supplied through the API actually changes retrieval.
2. Retrieval errors are not silently suppressed.
3. Metadata access is safe.
4. PDFs with no extractable text are rejected.
5. Environment configuration works.
6. ChromaDB persistence survives restart.
7. Duplicate ingestion does not duplicate chunks.
8. Cross-document retrieval works.
9. Citations match actual retrieved pages.
10. Unsupported questions are refused.

---

#  Future Improvements

Possible future improvements include:

* Hybrid keyword + semantic search
* Re-ranking
* Better table extraction
* OCR support for scanned PDFs
* Authentication
* Web-based frontend
* Monitoring and logging
* Automated evaluation
* Docker deployment
* Cloud deployment
* Advanced document versioning

---

#  Assignment Objective

The primary objective is to demonstrate a working **Retrieval-Augmented Generation system** that can:

1. Read supply-chain documents.
2. Convert documents into searchable chunks.
3. Generate semantic embeddings.
4. Store embeddings in ChromaDB.
5. Retrieve relevant information.
6. Retrieve information across multiple documents.
7. Generate grounded answers using an LLM.
8. Provide source citations.
9. Refuse unsupported questions.
10. Expose the functionality through an API.

---

#  Author

**Vayu Nandan Tripathi**

B.Tech Computer Science & Engineering
Specialization: Artificial Intelligence & Machine Learning

---

##  Project Summary

> **Supply Chain RAG System** is an AI-powered document question-answering system that combines semantic retrieval, ChromaDB, and LLMs to analyze supply-chain performance and procurement policies while providing grounded, page-level source citations.
