from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.loader import Document
from src.config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_documents(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Splits a list of Document pages into smaller chunks.
    
    Each chunk is a Document object carrying the parent page's metadata
    along with chunk-specific info.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunked_docs = []
    
    for doc in documents:
        # Split the text of this specific page
        text_chunks = text_splitter.split_text(doc.text)
        
        for idx, text_chunk in enumerate(text_chunks):
            # Create a new metadata dictionary to avoid modifying the original by reference
            chunk_metadata = doc.metadata.copy()
            chunk_metadata["chunk_index"] = idx
            
            # Create a unique chunk ID using filename, page, and chunk index
            chunk_id = f"{chunk_metadata['filename']}_p{chunk_metadata['page']}_c{idx}"
            chunk_metadata["chunk_id"] = chunk_id
            
            chunked_docs.append(Document(text=text_chunk, metadata=chunk_metadata))
            
    return chunked_docs