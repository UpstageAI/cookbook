# policy_attribution_consistency.py
import os
from typing import Any, Dict, List, Literal, Optional

from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from eval_prompt import policy_attribution_prompt

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=API_KEY,
    temperature=0,
    convert_system_message_to_human=True,
)

RelationLabel = Literal[
    "HIGHLY_RELATED",
    "WEAKLY_RELATED",
    "UNRELATED",
    "NOT_ENOUGH_INFO",
]

ErrorType = Literal[
    "NONE",
    "PAGE_LOAD_ERROR",
    "LOGIN_REQUIRED",
    "REDIRECTED_TO_HOME",
    "TOO_SHORT",
    "OTHER",
]


class PolicyAttributionResult(BaseModel):
    """LLM-structured output for policy attribution consistency of a single chain (multi-source)."""

    label: RelationLabel = Field(
        ...,
        description="How strongly this chain's sources are related to (politician, policy).",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0.",
    )
    reasoning: str = Field(
        ...,
        description="Short explanation in Korean of how the sources relate to the politician and policy.",
    )
    evidence_spans: List[str] = Field(
        default_factory=list,
        description="Short spans from sources that show politician/policy relevance.",
    )
    error_type: ErrorType = Field(
        "NONE",
        description="Page loading or content error type.",
    )

    politician_mentioned: bool = Field(
        ...,
        description="True if the politician appears meaningfully in any of the sources.",
    )
    policy_topic_mentioned: bool = Field(
        ...,
        description="True if the specific policy or its core topic appears meaningfully in any of the sources.",
    )


class EvidenceItem(TypedDict):
    source_title: str
    url: str


class PolicyAttributionState(TypedDict, total=False):
    """
    State for evaluating policy attribution consistency
    of a single influence chain with multiple evidence URLs.
    """

    politician: str
    policy: str
    industry_or_sector: str
    companies: List[str]
    question: Optional[str]

    evidence: List[EvidenceItem]
    scraped_pages: List[Dict[str, Any]]
    attribution_result: PolicyAttributionResult


prompt = ChatPromptTemplate.from_template(policy_attribution_prompt)
structured_llm = llm.with_structured_output(PolicyAttributionResult, strict=True)
policy_chain = prompt | structured_llm


def _build_sources_block(
    evidence: List[EvidenceItem],
    scraped_pages: List[Dict[str, Any]],
    max_text_chars: int = 4000,
) -> str:
    """
    여러 evidence URL과 스크랩된 페이지들을 하나의 텍스트 블록으로 합치는 헬퍼 함수.
    """
    lines: List[str] = []
    for idx, (ev, page) in enumerate(zip(evidence, scraped_pages), start=1):
        url = ev["url"]
        title = ev.get("source_title") or page.get("title") or ""
        status = page.get("status")
        ok = page.get("ok")
        text = (page.get("text") or "")[:max_text_chars]

        lines.append(f"SOURCE {idx}:")
        lines.append(f"url: {url}")
        if title:
            lines.append(f"title: {title}")
        if status is not None:
            lines.append(f"http_status: {status}")
        if ok is not None:
            lines.append(f"ok: {ok}")
        lines.append("text:")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


async def evaluate_policy_attribution_node(
    state: PolicyAttributionState,
) -> PolicyAttributionState:
    """
    For a single influence chain:
    - Take all evidence URLs + scraped pages
    - Build one multi-source block
    - Call the LLM once to judge policy attribution consistency.
    """

    evidence = state.get("evidence", [])
    scraped_pages = state.get("scraped_pages", [])

    politician = state["politician"]
    policy = state["policy"]
    industry_or_sector = state["industry_or_sector"]
    companies = state["companies"]
    question = state.get("question", "") or ""

    if not evidence or not scraped_pages:
        result = PolicyAttributionResult(
            label="NOT_ENOUGH_INFO",
            score=0.0,
            reasoning="No usable evidence sources were available for this influence chain.",
            evidence_spans=[],
            error_type="TOO_SHORT",
            politician_mentioned=False,
            policy_topic_mentioned=False,
        )
        return {**state, "attribution_result": result}

    sources_block = _build_sources_block(evidence, scraped_pages)
    companies_str = ", ".join(companies) if companies else ""

    result: PolicyAttributionResult = await policy_chain.ainvoke(
        {
            "politician": politician,
            "policy": policy,
            "industry_or_sector": industry_or_sector,
            "companies": companies_str,
            "sources": sources_block,
            "question": question,
        }
    )

    return {
        "attribution_result": result,
    }
