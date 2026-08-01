from __future__ import annotations

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
)
from policy_attribution_consistency import (
    PolicyAttributionState,
    PolicyAttributionResult,
)
from eval_tools import URLScraper
from eval_prompt import gold_compare



class CombinedEvalState(TypedDict, total=False):
    """
    Shared state used to run:
    - Impact Evidence Faithfulness
    - Policy Attribution Consistency
    - Gold vs Model report comparison
    for a single influence chain or report.
    """

    politician: Optional[str]
    policy: Optional[str]
    question: Optional[str]

    industry_or_sector: str
    companies: List[str]
    impact_description: str

    evidence: List[EvidenceItem]

    scraped_pages: List[Dict[str, Any]]

    impact_result: ImpactEvidenceResult
    attribution_result: PolicyAttributionResult

    gold_report: Optional[Dict[str, Any]]
    model_report: Optional[Dict[str, Any]]
    gold_eval: Optional[Dict[str, Any]]

    combined_summary: Dict[str, Any]



load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

gold_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=API_KEY,
    temperature=0.0,
    convert_system_message_to_human=True,
)



class GoldCompareResult(BaseModel):
    """Structured output for comparing gold_report and model_report."""

    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score between 0.0 and 1.0.",
    )
    reasoning: str = Field(
        ...,
        description="Short Korean explanation of how the two reports were compared.",
    )
    model_unique_points: List[str] = Field(
        default_factory=list,
        description="Key points that appear only in the model_report.",
    )
    gold_unique_points: List[str] = Field(
        default_factory=list,
        description="Key points that appear only in the gold_report.",
    )


gold_prompt = ChatPromptTemplate.from_template(gold_compare)
gold_structured_llm = gold_llm.with_structured_output(GoldCompareResult, strict=True)
gold_chain = gold_prompt | gold_structured_llm


async def evaluate_gold_node(state: CombinedEvalState) -> CombinedEvalState:
    """
    Compare `gold_report` and `model_report` using an LLM-as-judge.

    This node expects:
    - state["question"]
    - state["gold_report"]
    - state["model_report"]

    If either gold_report or model_report is missing, this node
    simply returns the state unchanged.
    """
    question = state.get("question", "") or ""
    gold_report = state.get("gold_report")
    model_report = state.get("model_report")

    if gold_report is None or model_report is None:
        return state

    result: GoldCompareResult = await gold_chain.ainvoke(
        {
            "question": question,
            "gold_report": gold_report,
            "model_report": model_report,
        }
    )

    return {
        "gold_eval": result.model_dump(),
    }


