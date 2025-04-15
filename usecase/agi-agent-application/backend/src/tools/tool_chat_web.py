import requests
from flask import Flask, request, jsonify, Response
import langgraph
import json
import os
from src.tools.basic import *
from langchain_openai import ChatOpenAI
from langchain_teddynote.tools.tavily import TavilySearch
from typing import Annotated, Dict, Any, Optional, List
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from werkzeug.utils import secure_filename
from langchain_core.messages import ToolMessage
from langchain_teddynote.messages import display_message_tree
from dotenv import load_dotenv
from langchain.tools import tool
from pydantic import BaseModel, Field

from tavily import TavilyClient
from ..config import FORMAT_PROMPT_PATH

load_dotenv()


global_LLm = None

class State(TypedDict):
    # 메시지 정의(list type 이며 add_messages 함수를 사용하여 메시지를 추가)
    messages: Annotated[list, add_messages]

class GraphAgent:
    def __init__(self):
        # Initialize the LangGraph agent with a configuration file.
        # Replace 'langgraph_config.yaml' with the path to your LangGraph configuration file.
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_completion_tokens=1024)
        self.graph = StateGraph(State)
    
    def add_node(self, name, func):
        self.graph.add_node(name, func)

    def add_conditional(self,source,path,path_map):
        self.graph.add_conditional_edges(source, path, path_map)

    def add_edge_start(self, name, chatbot):
        self.graph.add_edge(name, chatbot)

    def add_edge_general(self, func1, func2):
        self.graph.add_edge(func1, func2)

    def add_edge_end(self, chatbot, name):
        self.graph.add_edge(chatbot, name)

    def graph_compile(self):
        return self.graph.compile()

    def getGraph(self):
        return self.graph
    
class Tavily:
    def __init__(self, tool):
        # get_api_key("conf.d/config.yaml")
        self.llm = ChatOpenAI(model="gpt-4o-mini", max_completion_tokens=1024)
        self.tool = tool
        self.API_KEY = os.getenv('TAVILY_API_KEY')
        self.tools = []
    
    def add_tool(self):
        self.tools.append(self.tool)

    def implement(self, content):
        self.tool.invoke(content)

    def bind_tools(self):
        return self.llm.bind_tools(self.tools)


class BasicToolNode:
    """Run tools requested in the last AIMessage node"""

    def __init__(self, tools: list) -> None:
        # 도구 리스트
        self.tools_list = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        # 메시지가 존재할 경우 가장 최근 메시지 1개 추출
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")

        # 도구 호출 결과
        outputs = []
        for tool_call in message.tool_calls:
            # 도구 호출 후 결과 저장
            tool_result = self.tools_list[tool_call["name"]].invoke(tool_call["args"])
            outputs.append(
                # 도구 호출 결과를 메시지로 저장
                ToolMessage(
                    content=json.dumps(
                        tool_result, ensure_ascii=False
                    ),  # 도구 호출 결과를 문자열로 변환
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

        return {"messages": outputs}

# Flask 웹 서버 생성
app = Flask(__name__)


def route_tools(
    state: State,
):
    if messages := state.get("messages", []):
        # 가장 최근 AI 메시지 추출
        ai_message = messages[-1]
    else:
        # 입력 상태에 메시지가 없는 경우 예외 발생
        raise ValueError(f"No messages found in input state to tool_edge: {state}")

    # AI 메시지에 도구 호출이 있는 경우 "tools" 반환
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        # 도구 호출이 있는 경우 "tools" 반환
        return "tools"
    # 도구 호출이 없는 경우 "END" 반환
    return END


@app.route('/query', methods=['POST'])
def query_agent():
    global global_LLm
    # Accept JSON or form data for the user's query
    if request.is_json:
        data = request.get_json()
        query = data.get("query")
    else:
        query = request.form.get("query")

    # 노드 추가
    llm = ChatOpenAI(model="gpt-4o-mini")

    tool = TavilySearch(max_results=3)
    Tavily_agent = Tavily(tool)
    Tavily_agent.add_tool()
    llm_w_tools = Tavily_agent.bind_tools()
    global_LLm = llm_w_tools
    tool_node = BasicToolNode(tools=[tool])
    # 그래프에 도구 노드 추가

    agent = GraphAgent()
    
    agent.add_node("chatbot", chatbot)
    agent.add_node("tools", tool_node)

    agent.add_conditional(
        source="chatbot",
        path=route_tools,
        # route_tools 의 반환값이 "tools" 인 경우 "tools" 노드로, 그렇지 않으면 END 노드로 라우팅
        path_map={"tools": "tools", END: END},
    )

    # tools > chatbot
    agent.add_edge_general("tools", "chatbot")

    # START > chatbot
    agent.add_edge_start(START, "chatbot")

    graph = agent.graph_compile()
    res = []
    for event in graph.stream({"messages": [("user", query)]}):
        for key, value in event.items():
            print(f"\n==============\nSTEP: {key}\n==============\n")
            res.append({"key" : key, "content" : value["messages"][0].content})

    if not query:
        return jsonify({"error": "Query not provided"}), 400
    
    try:
        response_data = json.dumps({"response": res}, ensure_ascii=False)
        return Response(response_data, content_type="application/json; charset=utf-8")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def chatbot(state: State):
    answer =  global_LLm.invoke(state["messages"])
    # 메시지 목록 반환
    return {"messages": [answer]}

# Load format prompt from file
with open(FORMAT_PROMPT_PATH, 'r', encoding='utf-8') as f:
    format_prompt = f.read()

# Define schema for the web search tool
class WebSearchToolSchema(BaseModel):
    query: str = Field(..., description="Search query to look up information on the web")

@tool(args_schema=WebSearchToolSchema, description="Searches the web for up-to-date information in response to the user's query, particularly when current events, recent data, or dynamic content are needed.")
def web_search_tool(query: str) -> Dict[str, Any]:
    """
    Search the web for information using the Tavily search engine.
    
    Args:
        query (str): The search query string to look up on the web
        
    Returns:
        Dict[str, Any]: A dictionary containing search results with titles, snippets, and URLs
    """
    try:
        tavily_client = TavilyClient(api_key=os.environ.get('TAVILY_API_KEY'))
        search_results = tavily_client.search(
            query=query,
            search_depth="advanced",
            include_images=False,
            include_raw_content=False,
            max_results=2
        )
        
        # Format the results for easier consumption
        formatted_results = {
            "query": query,
            "results": []
        }
        
        if "results" in search_results and isinstance(search_results["results"], list):
            for result in search_results["results"]:
                formatted_results["results"].append({
                    "title": result.get("title", "No title"),
                    "url": result.get("url", "No URL"),
                    "content": result.get("content", "No content")
                })
        
        return formatted_results
    except Exception as e:
        return {
            "error": f"Web search failed: {str(e)}",
            "query": query,
            "results": []
        }



if __name__ == "__main__":
    app.run(debug=True)