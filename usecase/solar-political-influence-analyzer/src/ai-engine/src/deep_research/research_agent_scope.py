import os 
from datetime import datetime
from dotenv import load_dotenv

from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage, get_buffer_string

from deep_research.prompts import transform_messages_into_research_topic_prompt
from deep_research.state_scope import AgentState, ResearchQuestion


def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")


load_dotenv()

model = ChatUpstage(api_key=os.getenv("UPSTAGE_API_KEY"), model="solar-pro2", temperature=0)


def research_brief_planner(state: AgentState):
    """
    Transform the conversation history into a comprehensive research brief.

    Uses structured output to ensure the brief follows the required format
    and contains all necessary details for effective research.
    """

    structured_output_model = model.with_structured_output(ResearchQuestion)

    response = structured_output_model.invoke([
        HumanMessage(content=transform_messages_into_research_topic_prompt.format(
            messages=get_buffer_string(state.get("messages", [])),
            date=get_today_str()
        ))
    ])

    return {
        "research_brief": response.research_brief,
        "supervisor_messages": [HumanMessage(content=f"{response.research_brief}.")]
    }
