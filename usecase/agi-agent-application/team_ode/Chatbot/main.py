from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from langchain_upstage import ChatUpstage, UpstageEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_community.vectorstores import FAISS
import os
import json
from dotenv import load_dotenv

app = FastAPI()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

load_dotenv()

# Upstage API 키 설정
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")  # chat용
UPSTAGE_EMBEDDING_KEY = os.getenv("UPSTAGE_EMBEDDING_KEY")  # embedding용

# Upstage chat 모델
chat = ChatUpstage(api_key=UPSTAGE_API_KEY, model="solar-pro")

# 벡터 DB 경로
base_path = os.path.dirname(os.path.abspath(__file__))
vector_db_path = os.path.join(base_path, "vector_db", "Merged")

# ✅ Upstage 임베딩 모델 사용
embedding_model = UpstageEmbeddings(
    api_key=UPSTAGE_EMBEDDING_KEY,
    model="embedding-query"
)

# FAISS 벡터 스토어 로드
vectorstore = FAISS.load_local(
    vector_db_path,
    embeddings=embedding_model,
    allow_dangerous_deserialization=True  # 신뢰된 로컬 파일일 경우
)


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str

async def get_trade_response(messages: List[ChatMessage]) -> str:
    # 최신 user 메시지를 기준으로 유사 문서 검색
    user_messages = [msg.content for msg in messages if msg.role == "user"]
    if not user_messages:
        return "No user message found."

    query = user_messages[-1]
    docs = vectorstore.similarity_search(query, k=5)

    # 문서 내용 연결
    context = "\n---\n".join([doc.page_content for doc in docs])

    langchain_messages = [
        SystemMessage(content=f"""
        You are a specialized Trade and Customs Assistant.
        You have expertise in international trade procedures, HS codes,
        customs documentation, and regulations.

        Use the following trade knowledge context extracted from top relevant documents:
        다음은 연관된 통관 문제 사례들입니다.
        {context}
        
        Always provide accurate and helpful information about these topics, and respond in the same language as the user.
        만약 주어진 통관 문제 사례들을 사용자가 필요로 할 것 같은 경우, 언제든지 관련하여 조언을 주세요.
        """)
    ]

    for msg in messages:
        if msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            langchain_messages.append(AIMessage(content=msg.content))
    
    response = await chat.ainvoke(langchain_messages)

    return response.content

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response = await get_trade_response(request.messages)
        return ChatResponse(response=response)
    except Exception as e:
        return ChatResponse(response=f"Error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

