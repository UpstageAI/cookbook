import os
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from langchain_upstage import ChatUpstage

from dotenv import load_dotenv
load_dotenv()

from deep_research.utils import get_today_str
from deep_research.prompts import generate_influence_report_prompt
from deep_research.state_scope import AgentState, AgentInputState
from deep_research.research_agent_scope import research_brief_planner
from deep_research.multi_agent_supervisor import supervisor_agent

from pydantic import BaseModel
from typing import List, Optional

class Evidence(BaseModel):
    source_title: str
    url: str

class InfluenceChain(BaseModel):
    politician: str
    policy: str
    industry_or_sector: str
    companies: List[str]
    impact_description: str
    evidence: List[Evidence]

class InfluenceReport(BaseModel):
    report_title: str
    time_range: str
    question_answer: str
    influence_chains: List[InfluenceChain]
    notes: Optional[str] = ""


writer_model = ChatUpstage(api_key=os.getenv("UPSTAGE_API_KEY"), model="solar-pro2", temperature=0).with_structured_output(InfluenceReport)



async def generate_influence_report(state: AgentState):
    """
    Final report generation node.

    Synthesizes all research findings into a comprehensive final report
    """

    notes = state.get("notes", [])

    findings = "\n".join(notes)

    final_report_prompt = generate_influence_report_prompt.format(
        research_brief=state.get("research_brief", ""),
        findings=findings,
        date=get_today_str()
    )

    final_report = await writer_model.ainvoke([HumanMessage(content=final_report_prompt)])

    data = final_report.model_dump()

    return {
        "final_report": data,
    }

deep_researcher_builder = StateGraph(AgentState, input_schema=AgentInputState)

deep_researcher_builder.add_node("research_brief_planner", research_brief_planner)
deep_researcher_builder.add_node("supervisor_subgraph", supervisor_agent)
deep_researcher_builder.add_node("generate_influence_report", generate_influence_report)

deep_researcher_builder.add_edge(START, "research_brief_planner")
deep_researcher_builder.add_edge("research_brief_planner", "supervisor_subgraph")
deep_researcher_builder.add_edge("supervisor_subgraph", "generate_influence_report")
deep_researcher_builder.add_edge("generate_influence_report", END)

agent = deep_researcher_builder.compile()
