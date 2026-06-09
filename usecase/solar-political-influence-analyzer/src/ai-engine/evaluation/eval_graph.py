import os
from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from impact_evidence_faithfulness import (
    EvidenceItem,
    ImpactEvidenceState,
    ImpactEvidenceResult,
    evaluate_impact_node,
)
from policy_attribution_consistency import (
    PolicyAttributionState,
    PolicyAttributionResult,
    evaluate_policy_attribution_node,
)

from eval_tools import URLScraper
from eval_prompt import gold_compare
from gold_set_evaluation import evaluate_gold_node
from gold_set_evaluation import CombinedEvalState

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


async def scrape_urls_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch all evidence URLs using Playwright (via URLScraper)
    and attach the scraped page info to the state as `scraped_pages`.
    """
    evidence = state.get("evidence", [])
    urls = [ev["url"] for ev in evidence]

    scraper = URLScraper(
        headless=True,
        timeout_ms=20_000,
        wait_until="networkidle",
        max_chars=50_000,
    )

    if not urls:
        return {**state, "scraped_pages": []}

    results = await scraper.fetch_many(urls, concurrency=3)

    return {
        "scraped_pages": results,
    }





async def combine_node(state: CombinedEvalState) -> CombinedEvalState:
    """
    Merge the outputs from:
    - impact_evidence_faithfulness (per-chain, multi-source)
    - policy_attribution_consistency (per-chain, multi-source)
    - gold vs model report comparison

    into a single `combined_summary` object.
    """
    combined_summary: Dict[str, Any] = {
        "impact_result": state.get("impact_result"),
        "attribution_result": state.get("attribution_result"),
        "gold_eval": state.get("gold_eval"),
    }

    return {
        "combined_summary": combined_summary,
    }



workflow = StateGraph(CombinedEvalState)
workflow.add_node("scrape_urls", scrape_urls_node)
workflow.add_node("evaluate_impact", evaluate_impact_node)
workflow.add_node("evaluate_policy_attribution", evaluate_policy_attribution_node)
workflow.add_node("evaluate_gold", evaluate_gold_node)

workflow.add_node("combine", combine_node)

workflow.set_entry_point("scrape_urls")
workflow.add_edge("scrape_urls", "evaluate_impact")
workflow.add_edge("scrape_urls", "evaluate_policy_attribution")
workflow.add_edge("scrape_urls", "evaluate_gold")

workflow.add_edge("evaluate_impact", "combine")
workflow.add_edge("evaluate_policy_attribution", "combine")
workflow.add_edge("evaluate_gold", "combine")

workflow.add_edge("combine", END)

combined_eval_app = workflow.compile()
