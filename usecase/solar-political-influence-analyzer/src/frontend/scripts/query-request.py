import os
import json
import asyncio
import uuid
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from deep_research.research_agent_full import deep_researcher_builder
from pydantic import BaseModel
from fastapi import HTTPException

load_dotenv()

app = FastAPI(title="Deep Research Server")

class QueryRequest(BaseModel):
    query: str

checkpointer = InMemorySaver()
full_agent = deep_researcher_builder.compile(checkpointer=checkpointer)

async def run_agent(query: str):
    """에이전트를 실행하고 결과(JSON) 반환"""
    thread = {"configurable": {"thread_id": str(uuid.uuid4()), "recursion_limit": 10}}
    result = await full_agent.ainvoke(
        {"messages": [HumanMessage(content=query)]},
        config=thread
    )
    data = result.get("final_report", {})
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    return json_str


@app.post("/generate")
async def generate_report(request: QueryRequest):
    """POST /generate { "query": "도널드 트럼프" }"""
    query = request.query

    if not query:
        raise HTTPException(400, "query field is required")

    result = await run_agent(query)
    return json.loads(result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("query-request:app", host="127.0.0.1", port=8000, reload=True)
