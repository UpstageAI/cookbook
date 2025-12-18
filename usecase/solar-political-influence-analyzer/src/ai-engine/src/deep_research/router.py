# deep_research/router_agent.py (중요 부분만 수정 버전)

import json
import os
import uuid
from typing import Literal, Optional, Sequence

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from pydantic import BaseModel

from deep_research.state_scope import AgentState, AgentInputState
from deep_research.lite_researcher import LiteResearchState, lite_graph
from deep_research.research_agent_full import (
    agent as deep_agent,
    InfluenceReport,
    writer_model,
)
from deep_research.utils import get_today_str
from deep_research.prompts import generate_influence_report_prompt, route_prompt

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

router_llm = ChatUpstage(
    api_key=UPSTAGE_API_KEY,
    model="solar-pro2",
    temperature=0,
)


class RouteDecision(BaseModel):
    route: Literal["lite", "deep"]
    reason: str


def _extract_latest_user_question(messages: Sequence[BaseMessage]) -> str:
    """
    Helper to extract the latest user/human message content from AgentState.messages.
    """
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return str(msg.content)
    if messages:
        return str(messages[-1].content)
    return ""


def route_node(state: AgentState) -> dict:
    messages = state["messages"]
    question = _extract_latest_user_question(messages)

    structured_router = router_llm.with_structured_output(RouteDecision)
    decision: RouteDecision = structured_router.invoke(
        [
            HumanMessage(
                content=route_prompt.format(
                    question=question,
                )
            )
        ]
    )

    print(f"[ROUTER] route={decision.route}, reason={decision.reason}")
    return {"route": decision.route}


def lite_branch_node(state: AgentState) -> dict:
    """
    For 'lite' questions:

    1) Run the lite_graph to obtain:
       - raw_research: google_search_grounded output
       - findings: compressed research text (all info preserved)

    2) Feed (research_brief = question, findings = compressed text) into the
       existing generate_influence_report_prompt + writer_model to produce
       a full InfluenceReport JSON.

    This way we avoid information loss while keeping the pipeline lightweight.
    """
    messages = state["messages"]
    question = _extract_latest_user_question(messages)

    lite_state: LiteResearchState = lite_graph.invoke({"question": question})
    findings = lite_state["findings"]

    final_prompt = generate_influence_report_prompt.format(
        research_brief=question,
        findings=findings,
        date=get_today_str(),
    )

    report_obj: InfluenceReport = writer_model.invoke(
        [HumanMessage(content=final_prompt)]
    )
    report_data = report_obj.model_dump()

    return {
        "final_report": report_data,
    }


async def deep_branch_node(state: AgentState) -> dict:
    messages = state["messages"]
    deep_state: AgentState = await deep_agent.ainvoke({"messages": messages})

    final_report = deep_state.get("final_report")
    return {
        "final_report": final_report,
    }


router_builder = StateGraph(AgentState, input_schema=AgentInputState)

router_builder.add_node("route", route_node)
router_builder.add_node("lite_branch", lite_branch_node)
router_builder.add_node("deep_branch", deep_branch_node)

router_builder.add_edge(START, "route")


def route_selector(state: AgentState) -> str:
    route = state.get("route")
    if route == "deep":
        return "deep_branch"
    # Default to lite if anything is missing/invalid
    return "lite_branch"


router_builder.add_conditional_edges(
    "route",
    route_selector,
    {
        "lite_branch": "lite_branch",
        "deep_branch": "deep_branch",
    },
)

router_builder.add_edge("lite_branch", END)
router_builder.add_edge("deep_branch", END)

checkpointer = InMemorySaver()
full_agent: Runnable = router_builder.compile(checkpointer=checkpointer)
