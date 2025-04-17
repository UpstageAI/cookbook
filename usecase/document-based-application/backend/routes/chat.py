from fastapi import APIRouter, HTTPException
from schemas.chat_payload import ChatPayload, Message
from utils.embedding import embed_text
from utils.retrieve import retrieve_similar_chunks
from langchain_core.documents import Document
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
chat_router = APIRouter()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
if not UPSTAGE_API_KEY:
    raise ValueError("Missing UPSTAGE_API_KEY")

client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1"
)

# System prompt template
SYSTEM_TEMPLATE = """You are a helpful assistant that answers questions based on the provided document excerpts.
Here are relevant excerpts:
{chunks}

Respond clearly and concisely based only on the given information unless instructed otherwise."""

@chat_router.post("/chat", tags=["Chat"])
async def chat_with_upstage(payload: ChatPayload):
    try:
        messages = payload.messages

        # Use the last user message to generate the query embedding
        last_user_message = next((m.content for m in reversed(messages) if m.role == "user"), None)

        if not last_user_message:
            raise HTTPException(status_code=400, detail="No user message found in history.")

        # Initialize context chunks
        context_chunks = []

        # Add document content if available
        if payload.documentContent:
            try:
                # Split document content into chunks if it's too long
                doc_chunks = [payload.documentContent[i:i+1000] for i in range(0, len(payload.documentContent), 1000)]
                context_chunks.extend(doc_chunks)
            except Exception as e:
                print(f"Error processing document content: {str(e)}")
                # Continue without document content if there's an error

        # Generate query embedding
        query_doc = Document(page_content=last_user_message)
        query_embedding = embed_text([query_doc], is_query=True)

        # Retrieve similar chunks
        try:
            similar_chunks = retrieve_similar_chunks(query_embedding)
            context_chunks.extend(similar_chunks)
        except Exception as e:
            print(f"Error retrieving similar chunks: {str(e)}")
            # Continue with just document content if retrieval fails

        # Format system message
        system_message = SYSTEM_TEMPLATE.format(chunks="\n\n".join(f"- {chunk}" for chunk in context_chunks))
        
        # Prepare conversation
        full_convo = [Message(role="system", content=system_message)] + messages

        # Call the model
        try:
            response = client.chat.completions.create(
                model="solar-pro",
                messages=[msg.dict() for msg in full_convo]
            )

            assistant_reply = response.choices[0].message.content
            updated_history = messages + [Message(role="assistant", content=assistant_reply)]

            return {"messages": updated_history}
        except Exception as e:
            print(f"Error calling LLM: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in chat_with_upstage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
