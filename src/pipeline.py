import os
from src.loader import load_all_from_directory
from src.chunker import chunk_documents
from src.vector_store import VectorStoreManager
from src.retriever import Retriever
from src.generator import get_generator, format_context, SYSTEM_PROMPT

class RAGPipeline:
    def __init__(self, embedding_function=None):
        # Allow passing mock embedding function for testing
        self.vector_store = VectorStoreManager(embedding_function=embedding_function)
        self.retriever = Retriever(self.vector_store)
        
        # Generator is instantiated dynamically based on env config
        # We catch ValueError if the API key is not set yet, so we don't crash
        # until the user actually runs a query.
        self.generator = None
        try:
            self.generator = get_generator()
        except ValueError as e:
            self.generator_error = str(e)
        else:
            self.generator_error = None

    def index_data_directory(self, data_dir):
        """Loads and indexes all PDF files in the specified directory.
        
        Returns a tuple: (num_files_processed, num_chunks_indexed)
        """
        documents = load_all_from_directory(data_dir)
        if not documents:
            return 0, 0
            
        chunks = chunk_documents(documents)
        
        # Get count of unique files loaded
        unique_files = {doc.metadata["filename"] for doc in documents}
        
        # Add to vector store
        added_chunks = self.vector_store.add_chunks(chunks)
        
        return len(unique_files), added_chunks

    def ask(self, question: str, top_k: int = None):
        """Runs the complete RAG query pipeline.
        
        Args:
            question: The user's query
            top_k: Optional override for number of chunks to retrieve
        
        Returns a dict containing:
        - answer: LLM answer text
        - retrieved_chunks: list of dicts representing the raw retrieved chunks
        - sources: list of dicts with unique filenames and page numbers
        """
        if self.generator is None:
            # Try to initialize generator again in case env was updated
            try:
                self.generator = get_generator()
                self.generator_error = None
            except ValueError as e:
                return {
                    "answer": f"Error: Cannot initialize LLM provider. {str(e)}",
                    "retrieved_chunks": [],
                    "sources": []
                }

        # 1. Retrieve relevant chunks
        retrieve_kwargs = {"query": question}
        if top_k is not None:
            retrieve_kwargs["top_k"] = top_k
        chunks = self.retriever.retrieve(**retrieve_kwargs)
        
        if not chunks:
            return {
                "answer": "The database contains no indexed document context. Please index documents first.",
                "retrieved_chunks": [],
                "sources": []
            }

        # 2. Format context and system prompt
        context_str = format_context(chunks)
        sys_prompt = SYSTEM_PROMPT.format(context=context_str)

        # 3. Generate answer
        try:
            raw_answer = self.generator.generate(question, sys_prompt)
            import re
            # Try to extract the final answer block first
            match = re.search(r'\[?FINAL[-_ ]ANSWER\]?(.*?)\[?END[-_ ]FINAL[-_ ]ANSWER\]?', raw_answer, re.DOTALL | re.IGNORECASE)
            if match and match.group(1).strip():
                answer = match.group(1).strip()
            else:
                # Fallback: remove reasoning block
                answer = re.sub(r'\[?INTERNAL[-_ ]REASONING\]?.*?\[?END[-_ ]INTERNAL[-_ ]REASONING\]?', '', raw_answer, flags=re.DOTALL | re.IGNORECASE).strip()
            
            # Remove any residual tags that might leak
            answer = re.sub(r'\[?FINAL[-_ ]ANSWER\]?', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'\[?END[-_ ]FINAL[-_ ]ANSWER\]?', '', answer, flags=re.IGNORECASE)
            answer = answer.strip()
        except Exception as e:
            answer = f"Error during generation: {str(e)}"

        # 4. Extract unique source citations for the UI
        seen_sources = set()
        sources = []
        for chunk in chunks:
            fname = chunk["metadata"].get("filename", "unknown")
            page = chunk["metadata"].get("page", 0)
            src_key = (fname, page)
            if src_key not in seen_sources:
                seen_sources.add(src_key)
                sources.append({
                    "filename": fname,
                    "page": page,
                    "document_type": chunk["metadata"].get("document_type")
                })

        return {
            "answer": answer,
            "retrieved_chunks": chunks,
            "sources": sources
        }