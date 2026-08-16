import os
from pypdf import PdfReader

class Document:
    """Represents a page extracted from a PDF with its associated metadata."""
    def __init__(self, text, metadata):
        self.text = text
        self.metadata = metadata

    def to_dict(self):
        return {
            "text": self.text,
            "metadata": self.metadata
        }

    def __repr__(self):
        return f"Document(page={self.metadata.get('page')}, source={self.metadata.get('filename')})"


def get_document_type(filename):
    """Determines the document type based on the filename."""
    fname_lower = filename.lower()
    if "policy" in fname_lower or "handbook" in fname_lower:
        return "policy"
    elif "review" in fname_lower or "performance" in fname_lower:
        return "review"
    return "unknown"


def load_pdf(file_path):
    """Loads a single PDF and extracts text page-by-page.
    
    Returns a list of Document objects with metadata:
    - filename: name of the file
    - page: 1-indexed page number
    - document_type: 'policy' or 'review'
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at {file_path}")
        
    filename = os.path.basename(file_path)
    doc_type = get_document_type(filename)
    
    reader = PdfReader(file_path)
    documents = []
    
    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        text = page.extract_text() or ""
        
        metadata = {
            "filename": filename,
            "page": page_num,
            "document_type": doc_type
        }
        
        documents.append(Document(text=text, metadata=metadata))
        
    return documents


def load_all_from_directory(directory_path):
    """Loads all PDF documents from the specified directory.
    
    Returns a list of Document objects.
    """
    all_documents = []
    if not os.path.exists(directory_path):
        print(f"Directory {directory_path} does not exist.")
        return all_documents
        
    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            full_path = os.path.join(directory_path, filename)
            try:
                docs = load_pdf(full_path)
                all_documents.extend(docs)
                print(f"Loaded {filename}: {len(docs)} pages.")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                
    return all_documents