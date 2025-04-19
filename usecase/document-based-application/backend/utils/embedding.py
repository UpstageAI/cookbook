import pickle
from langchain_upstage import UpstageEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List
import dotenv
import os

dotenv.load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
if not UPSTAGE_API_KEY:
    raise ValueError("UPSTAGE_API_KEY not found in environment variables.")

# Models
embedding_model = UpstageEmbeddings(
    model="embedding-passage",
    upstage_api_key=UPSTAGE_API_KEY
)

query_model = UpstageEmbeddings(
    model="embedding-query",
    upstage_api_key=UPSTAGE_API_KEY
)

def embed_text(chunks: List[Document], is_query: bool = False, embedding_store_path: str = "vector_store/embedding_store.pkl") -> List[List[float]]:
    model = query_model if is_query else embedding_model

    if is_query:
        return model.embed_documents([doc.page_content for doc in chunks])[0]

    # Embed and store passages
    embeddings = model.embed_documents([doc.page_content for doc in chunks])
    if os.path.exists(embedding_store_path):
        with open(embedding_store_path, "rb") as f:
            stored_data = pickle.load(f)
    else:
        stored_data = []
    for embedding, doc in zip(embeddings, chunks):
        stored_data.append({
            "embedding": embedding,
            "content": doc.page_content,
            "metadata": doc.metadata
        })

    # Save using pickle
    os.makedirs(os.path.dirname(embedding_store_path), exist_ok=True)
    with open(embedding_store_path, "wb") as f:
        pickle.dump(stored_data, f)

    return stored_data
