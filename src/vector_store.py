import os
import chromadb
from src.config import CHROMA_DIR, COLLECTION_NAME
from src.embeddings import get_embedding_function

class VectorStoreManager:
    def __init__(self, embedding_function=None):
        # Create directory if it doesn't exist
        os.makedirs(CHROMA_DIR, exist_ok=True)
        
        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        
        # Get the embedding function
        if embedding_function is not None:
            self.embedding_function = embedding_function
        else:
            self.embedding_function = get_embedding_function()
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_function
        )

    def is_file_indexed(self, filename):
        """Checks if a file has already been indexed in the collection."""
        try:
            results = self.collection.get(
                where={"filename": filename},
                limit=1
            )
            return len(results.get("ids", [])) > 0
        except Exception as e:
            print(f"Error checking indexing status for {filename}: {e}")
            return False

    def get_indexed_files(self):
        """Returns a set of all unique filenames currently indexed in the collection."""
        try:
            # Fetch all metadatas in the collection
            results = self.collection.get(include=["metadatas"])
            metadatas = results.get("metadatas", [])
            return {meta["filename"] for meta in metadatas if meta and "filename" in meta}
        except Exception as e:
            print(f"Error retrieving indexed files: {e}")
            return set()

    def add_chunks(self, chunks):
        """Adds a list of document chunks to the collection, with duplicate protection."""
        if not chunks:
            return 0
            
        # Group chunks by filename to check duplicate status per file
        by_file = {}
        for chunk in chunks:
            fname = chunk.metadata["filename"]
            if fname not in by_file:
                by_file[fname] = []
            by_file[fname].append(chunk)
            
        added_count = 0
        for filename, file_chunks in by_file.items():
            if self.is_file_indexed(filename):
                print(f"Skipping indexing for '{filename}': Already indexed in ChromaDB.")
                continue
                
            ids = [chunk.metadata["chunk_id"] for chunk in file_chunks]
            documents = [chunk.text for chunk in file_chunks]
            metadatas = [chunk.metadata for chunk in file_chunks]
            
            # Add to ChromaDB collection
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"Successfully indexed '{filename}': {len(file_chunks)} chunks added.")
            added_count += len(file_chunks)
            
        return added_count

    def clear_collection(self):
        """Deletes and recreates the collection, wiping all data."""
        try:
            self.client.delete_collection(COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embedding_function
            )
            print(f"Collection '{COLLECTION_NAME}' has been cleared.")
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False

    def get_chunk_count(self):
        """Returns the total number of chunks in the collection."""
        return self.collection.count()