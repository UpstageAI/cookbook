from fastapi import APIRouter, HTTPException
from langchain_core.documents import Document
from utils.embedding import embed_text
from utils.retrieve import retrieve_similar_chunks

query_router = APIRouter()

@query_router.post("/query", tags=["Query"])
async def query_documents(payload: str):
    try:
        # Wrap the payload in a Document
        query_doc = Document(page_content=payload)

        # Embed the query
        query_embeddings = embed_text([query_doc], is_query=True)

        # Retrieve similar chunks from FAISS index
        results = retrieve_similar_chunks(query_embeddings)

        return {
            "query": payload,
            "relevant_chunks": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
