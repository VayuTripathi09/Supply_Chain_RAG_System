import logging
from src.config import RETRIEVAL_TOP_K
from src.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self, vector_store_manager: VectorStoreManager):
        self.manager = vector_store_manager
        self.collection = vector_store_manager.collection

    def retrieve(self, query: str, top_k: int = RETRIEVAL_TOP_K):
        """Retrieves relevant chunks for a query from ChromaDB.
        
        Implements a cross-document retrieval fix: if the initial retrieval
        contains chunks from only one document type, it falls back to a 
        metadata-filtered search to retrieve 3 chunks from each document type
        and combines them.
        """
        # 1. Initial query
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results into a list of dictionaries
        chunks = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            
            for idx in range(len(ids)):
                chunks.append({
                    "id": ids[idx],
                    "text": docs[idx],
                    "metadata": metadatas[idx],
                    "distance": distances[idx]
                })
                
        # Check if the query mentions a supplier and ensure Review Page 1 (scorecard) is retrieved
        supplier_names = ["Kaveri", "Shenzhen", "Trident", "Nexa", "Sunrise", "Baltic"]
        mentioned_suppliers = [s for s in supplier_names if s.lower() in query.lower()]
        if mentioned_suppliers:
            has_scorecard = any(
                "Supply_Chain_Review" in chunk["metadata"].get("filename", "") and chunk["metadata"].get("page") == 1
                for chunk in chunks
            )
            if not has_scorecard:
                supplier_query = f"{mentioned_suppliers[0]} supplier scorecard"
                supplier_chunks = self._retrieve_by_type(supplier_query, "review", 1)
                if supplier_chunks:
                    chunks = supplier_chunks + chunks

        # 2. Check document representation
        doc_types = {chunk["metadata"].get("document_type") for chunk in chunks}
        
        # If both are present, or we got nothing, return the initial result
        if len(doc_types) >= 2 or not chunks:
            return chunks
            
        # 3. Fallback: retrieve from both document types specifically
        print(f"Cross-document fallback triggered: Initial search returned only {list(doc_types)}.")
        half_k = max(2, top_k // 2)
        
        review_chunks = self._retrieve_by_type(query, "review", half_k)
        policy_chunks = self._retrieve_by_type(query, "policy", half_k)
        
        # Combine and return
        combined = review_chunks + policy_chunks
        # Sort by distance (ascending score is closer in default L2 distance)
        combined.sort(key=lambda x: x["distance"])
        return combined

    def _retrieve_by_type(self, query: str, doc_type: str, limit: int):
        """Helper to query with metadata filter for a specific document_type."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where={"document_type": doc_type},
                include=["documents", "metadatas", "distances"]
            )
            
            chunks = []
            if results and results.get("ids") and results["ids"][0]:
                ids = results["ids"][0]
                docs = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0]
                
                for idx in range(len(ids)):
                    chunks.append({
                        "id": ids[idx],
                        "text": docs[idx],
                        "metadata": metadatas[idx],
                        "distance": distances[idx]
                    })
            return chunks
        except Exception as e:
            logger.error(f"Error during metadata-filtered query for document type '{doc_type}': {type(e).__name__}: {e}")
            return []