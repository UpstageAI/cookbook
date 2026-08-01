# deep_research/lite_researcher.py

import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage
from langchain_upstage import ChatUpstage
from langgraph.graph import END, StateGraph

from deep_research.utils import google_search_grounded, get_today_str, naver_search, tavily_search
from deep_research.prompts import compress_research_system_prompt

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

# LLM for compression step
compress_llm = ChatUpstage(
    api_key=UPSTAGE_API_KEY,
    model="solar-pro2",
    temperature=0.0,
)


class LiteResearchState(TypedDict):
    """
    State for the lightweight research pipeline.

    - question: original user question
    - raw_research: raw string output from google_search_grounded, naver_search, tavily_search tool
    - findings: cleaned & compressed findings text that preserves all relevant info
    """
    question: str
    raw_research: str
    findings: str


def lite_gather_node(state: LiteResearchState) -> LiteResearchState:
    """
    Run google_search_grounded, naver_search, tavily_search as a single research tool call and store
    the raw textual output (answer + sources + snippets).
    """
    question = state["question"]
    google_text = google_search_grounded.invoke({"question": question})
    naver_text = naver_search.invoke({"question": question})
    tavily_text = tavily_search.invoke({"query": question})

    combined = (
        "### [GOOGLE_SEARCH]\n"
        f"{google_text}\n\n"
        "### [TAVILY_SEARCH]\n"
        f"{tavily_text}\n\n"
        "### [NAVER_SEARCH]\n"
        f"{naver_text}\n"
    )
    
    return {"raw_research": combined}


def lite_compress_node(state: LiteResearchState) -> LiteResearchState:
    """
    Use compress_research_system_prompt to clean up and compress the raw research
    while preserving all relevant factual statements, relationships, and sources.
    """
    question = state["question"]
    raw_research = state["raw_research"]

    system_prompt = compress_research_system_prompt.format(
        date=get_today_str(),
    )

    content = (
        f"{system_prompt}\n\n"
        f"[Original Question]\n{question}\n\n"
        f"[Raw Research Messages]\n{raw_research}\n"
    )

    compressed = compress_llm.invoke(
        [HumanMessage(content=content)]
    ).content.strip()

    return {"findings": compressed}


lite_builder = StateGraph(LiteResearchState)
lite_builder.add_node("gather", lite_gather_node)
lite_builder.add_node("compress", lite_compress_node)

lite_builder.set_entry_point("gather")
lite_builder.add_edge("gather", "compress")
lite_builder.add_edge("compress", END)

lite_graph: Runnable = lite_builder.compile()
