from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from datetime import datetime

def chunk_text(text: str, filename: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[Document]:
    """
    Splits the input text into chunks with metadata.

    Parameters:
    - text: full text extracted from the uploaded file (HTML or plain)
    - filename: name of the uploaded file (used in metadata)
    - chunk_size: max tokens per chunk
    - chunk_overlap: token overlap between chunks

    Returns:
    - list of langchain Document objects with metadata
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = splitter.split_text(text)

    docs = []
    for i, chunk in enumerate(chunks):
        metadata = {
            "source": filename,
            "chunk_index": i,
            "upload_time": datetime.utcnow().isoformat()
        }
        docs.append(Document(page_content=chunk, metadata=metadata))

    return docs
