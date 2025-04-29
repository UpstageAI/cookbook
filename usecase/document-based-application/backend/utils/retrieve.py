import numpy as np
import os
import pickle

def retrieve_similar_chunks(query_embedding, embedding_store_path="vector_store/embedding_store.pkl", k=4):
    """
    Retrieves the top-k most similar chunks using dot product similarity.

    Parameters:
    - query_embedding: List[float] - the query embedding vector
    - embedding_store_path: str - path to the saved embedding store
    - k: int - number of most similar chunks to return

    Returns:
    - List[str] - contents of the most similar chunks
    """
    if not os.path.exists(embedding_store_path):
        raise FileNotFoundError(f"Embedding store not found at '{embedding_store_path}'")

    # Load stored passages and their embeddings
    with open(embedding_store_path, "rb") as f:
        data = pickle.load(f)  # expects a list of dicts: [{'embedding': ..., 'content': ..., 'metadata': ...}, ...]

    similarity_list = []
    for item in data:
        passage_embedding = item["embedding"]
        similarity = np.dot(passage_embedding, query_embedding)
        similarity_list.append((similarity, item))

    # Sort by similarity, descending
    similarity_list.sort(key=lambda x: x[0], reverse=True)

    # Get top-k results
    top_k_items = [item["content"] for _, item in similarity_list[:k]]

    return top_k_items
