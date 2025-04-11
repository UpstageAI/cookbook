import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, TypedDict
from dotenv import load_dotenv
from openai import OpenAI

# LangGraph imports
from langgraph.graph import StateGraph, START, END
# Remove tools_condition import
from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from src.config import FORMAT_PROMPT_PATH

import boto3
from botocore.config import Config

# Local imports
from .state import AgentState
from .processors import extract_response_from_messages

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'wetube-gwanwoo')
s3 = boto3.client('s3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name='ap-northeast-2',
    config=Config(signature_version='s3v4')
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomToolNode:
    """Custom implementation of ToolNode that properly handles file IDs"""
    
    def __init__(self, tools: list) -> None:
        self.tools = tools
        self.tools_dict = {tool.name: tool for tool in tools}
        # Initialize OpenAI client for formatting web search results
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def format_web_search_results(self, raw_results: str) -> str:
        """Format web search results into a conversational response"""
        try:
            # Load the formatting prompt
            with open(FORMAT_PROMPT_PATH, 'r', encoding='utf-8') as f:
                format_prompt = f.read()
            
            # Create a special prompt for web search formatting
            web_search_format_prompt = """
            You are a helpful financial assistant. Format the following web search results into a natural, 
            conversational response. Organize information clearly and present it as if you're directly 
            answering the user's query. Remove any raw data formatting, URLs, or metadata that would 
            make the response seem unnatural. 
            
            The response should be in Korean and should not include any disclaimers or unnecessary information.

            Here are the web search results to format:
            """
            
            messages_for_formatting = [
                {"role": "system", "content": web_search_format_prompt},
                {"role": "user", "content": raw_results}
            ]
            
            logger.info("Formatting web search results...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_for_formatting,
                temperature=0.3,
            )
            
            formatted_response = response.choices[0].message.content.strip()
            logger.info("Successfully formatted web search results")
            return formatted_response
        except Exception as e:
            logger.error(f"Error formatting web search results: {e}")
            return f"검색 결과: {raw_results}"
            
    def __call__(self, state):
        # Get the messages and file ID from the state
        messages = state.get("messages", [])
        file_id = state.get("file_id")
        
        if not messages:
            return state
            
        # Get the last message which should contain tool calls
        message = messages[-1]
        
        # Check if there are no tool calls
        if (not hasattr(message, "tool_calls") and 
            not (isinstance(message, dict) and message.get("tool_calls"))):
            return state
            
        # Extract tool calls
        tool_calls = (message.tool_calls if hasattr(message, "tool_calls") 
                     else message.get("tool_calls", []))
        
        # No tool calls found
        if not tool_calls:
            return state
            
        # Process each tool call
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name") if isinstance(tool_call, dict) else tool_call.name
            tool_args = tool_call.get("args") if isinstance(tool_call, dict) else tool_call.args
            tool_id = tool_call.get("id") if isinstance(tool_call, dict) else tool_call.id
            
            logger.info(f"Executing tool: {tool_name}")
            
            # Find the right tool
            tool = self.tools_dict.get(tool_name)
            
            if not tool:
                logger.error(f"Tool not found: {tool_name}")
                continue
                
            try:
                # Create a copy of args to avoid modifying the original
                final_args = dict(tool_args) if isinstance(tool_args, dict) else {}
                
                # Special handling for tools that need file ID
                if tool_name == "simulate_dispute_tool" and file_id:
                    logger.info("Adding file_id to simulation tool arguments")
                    final_args["file_id"] = file_id
                    
                    # Make sure query is in args
                    if "query" not in final_args and isinstance(tool_args, dict):
                        final_args["query"] = tool_args.get("query", "계약서 시뮬레이션")
                        
                    result = tool.invoke(final_args)
                elif tool_name == "find_toxic_clauses_tool" and file_id:
                    logger.info("Adding file_id to toxic clauses tool arguments")
                    final_args["file_id"] = file_id
                    
                    # Make sure query is in args
                    if "query" not in final_args and isinstance(tool_args, dict):
                        final_args["query"] = tool_args.get("query", "독소조항 분석")
                        
                    result = tool.invoke(final_args)
                else:
                    result = tool.invoke(tool_args)
                
                # For web search tool, format the results before returning
                if tool_name == "web_search_tool":
                    logger.info("Formatting web search results through LLM")
                    # Convert result to string for formatting
                    result_str = json.dumps(result, ensure_ascii=False)
                    # Format the results through LLM
                    formatted_result = self.format_web_search_results(result_str)
                    # Create a tool message with formatted results
                    results.append(
                        ToolMessage(
                            content=formatted_result,
                            name=tool_name,
                            tool_call_id=tool_id,
                        )
                    )
                    # Also append an assistant message to make it more conversational
                    results.append({
                        "role": "assistant", 
                        "content": formatted_result
                    })
                else:
                    # Create a regular tool message for other tools
                    results.append(
                        ToolMessage(
                            content=json.dumps(result, ensure_ascii=False),
                            name=tool_name,
                            tool_call_id=tool_id,
                        )
                    )
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Handle specific tool errors
                if tool_name == "simulate_dispute_tool":
                    error_msg = {
                        "simulations": [
                            f"계약서 분석 중 오류가 발생했습니다: {str(e)}",
                            "파일이 올바르게 업로드되었는지 확인하시고, 다시 시도해 주세요."
                        ]
                    }
                    results.append(
                        ToolMessage(
                            content=json.dumps(error_msg, ensure_ascii=False),
                            name=tool_name,
                            tool_call_id=tool_id,
                        )
                    )
                elif tool_name == "web_search_tool":
                    error_msg = f"검색 중 오류가 발생했습니다: {str(e)}"
                    results.append(
                        ToolMessage(
                            content=error_msg,
                            name=tool_name,
                            tool_call_id=tool_id,
                        )
                    )
                    # Add assistant message for better UX
                    results.append({
                        "role": "assistant", 
                        "content": error_msg
                    })
                elif tool_name == "find_toxic_clauses_tool":
                    error_msg = [{"error": f"독소조항 분석 중 오류가 발생했습니다: {str(e)}"}]
                    results.append(
                        ToolMessage(
                            content=json.dumps(error_msg, ensure_ascii=False),
                            name=tool_name,
                            tool_call_id=tool_id,
                        )
                    )
                else:
                    results.append(
                        ToolMessage(
                            content=f"Error: {str(e)}",
                            name=tool_name,
                            tool_call_id=tool_id,
                        )
                    )
        
        return {"messages": results}

def create_formatter(format_prompt_path=FORMAT_PROMPT_PATH):
    """Create a response formatter function"""
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Load format prompt from file
    try:
        with open(format_prompt_path, 'r', encoding='utf-8') as f:
            format_prompt = f.read()
        logger.info(f"Successfully loaded format prompt from {format_prompt_path}")
    except Exception as e:
        logger.error(f"Failed to load format prompt: {e}")
        format_prompt = "Summarize the following information in a clear, concise manner:"
    
    def format_response(state: AgentState) -> AgentState:
        """Format the final response"""
        if state.get("error"):
            return state
            
        try:
            logger.info("Formatting final response...")
            messages = state["messages"]
            
            # If the last message doesn't have tool results, return as is without formatting
            last_message = messages[-1] if messages else None
            if not last_message:
                logger.info("No messages to format, returning as is")
                return state
                
            # Check if this is a tool message that needs formatting
            is_tool_message = (hasattr(last_message, "__class__") and 
                              last_message.__class__.__name__ == "ToolMessage")
                
            # If it's NOT a tool message OR doesn't have content, return as is
            if not is_tool_message:
                content = getattr(last_message, "content", None)
                if isinstance(last_message, dict):
                    content = last_message.get("content")
                    
                if not content or len(content.strip()) < 5:
                    logger.info("Last message has no meaningful content to format")
                    return state
                    
                # If it's a direct chatbot response (not tool output), never format it
                if (hasattr(last_message, "role") and last_message.role == "assistant") or \
                   (isinstance(last_message, dict) and last_message.get("role") == "assistant"):
                    logger.info("Direct assistant response, skipping formatting")
                    return state
            
            # Only format if we have valid tool output to process 
            last_message_content = messages[-1].content if hasattr(messages[-1], "content") else ""
            if not last_message_content or len(last_message_content.strip()) < 5:
                logger.info("No substantial content to format, returning as is")
                return state
                
            # At this point, we know we have substantial tool output that should be formatted
            try:
                messages_for_formatting = [
                    {"role": "system", "content": format_prompt},
                    {"role": "user", "content": last_message_content}
                ]
                
                summary_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages_for_formatting,
                    temperature=0.1,
                )
                
                formatted_response = summary_response.choices[0].message.content.strip()
                # Don't append if we already have a direct chatbot response
                messages.append({"role": "assistant", "content": formatted_response})
                logger.info("Successfully formatted response")
            except Exception as e:
                logger.error(f"Error formatting response: {e}")
                messages.append({"role": "assistant", "content": f"결과 포맷팅 실패: {str(e)}"})
            
            return {"messages": messages}
        except Exception as e:
            logger.error(f"Error in format_response: {e}")
            state["error"] = f"포맷팅 오류: {str(e)}"
            state["messages"].append({"role": "assistant", "content": "응답 생성 중 오류가 발생했습니다."})
            return state
            
    return format_response

def llm_tool_router(state: AgentState):
    """
    Custom router function that uses LLM's judgment to determine next step.
    If the LLM's response contains tool calls, route to tools.
    Otherwise, route to formatter.
    """
    messages = state.get("messages", [])
    
    if not messages:
        return "chatbot"
    
    # Check the last message - if it contains tool calls, route to tools
    last_message = messages[-1]
    
    # Check if the message has tool_calls attribute or field
    has_tool_calls = False
    
    if hasattr(last_message, "tool_calls"):
        has_tool_calls = bool(last_message.tool_calls)
    elif isinstance(last_message, dict) and last_message.get("tool_calls"):
        has_tool_calls = bool(last_message.get("tool_calls"))
    
    logger.info(f"LLM tool router - Has tool calls: {has_tool_calls}")
    
    if has_tool_calls:
        return "tools"
    else:
        return "formatter"

def create_chatbot_node(tools):
    """Create the chatbot node for the agent"""
    
    # Create LangChain ChatOpenAI instance with lower temperature for more reliable tool selection
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.05,  # Lower temperature for more reliable tool selection
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Create detailed tool descriptions
    tool_descriptions = []
    for tool in tools:
        name = tool.name
        description = tool.description
        
        # For tools that require files, add an explicit note
        requires_file = ""
        if name in ["simulate_dispute_tool", "find_toxic_clauses_tool"]:
            requires_file = " (참고: 이 도구는 업로드된 계약서 파일이 필요합니다)"
        
        tool_descriptions.append(f"- {name}: {description}{requires_file}")
    
    # Create a more detailed and structured system prompt to guide the LLM
    tool_selection_prompt = """
    You are a legal assistant AI specialized in analyzing financial contracts. Your task is to analyze the user's question and choose the most appropriate tool to respond.

    **Available Tools:**  
    {tool_list}

    **Tool Selection Guidelines:**

    1. **Toxic Clause Analysis Tool (`find_toxic_clauses_tool`)**  
    - When to use: When the user asks to find toxic, unfair, disadvantageous, or risky clauses in the contract.  
    - Example questions:  
        - "Are there any toxic clauses in this contract?"  
        - "Can you point out any unfair terms?"

    2. **Contract Dispute Simulation Tool (`simulate_dispute_tool`)**  
    - When to use: When the user wants to understand the consequences of termination, breach, or non-performance of a contract, or requests a dispute outcome simulation.  
    - Example questions:  
        - "What happens if I terminate the contract?"  
        - "Will I be liable for a penalty?"  
        - "What are the consequences of breaching this clause?"

    3. **Case Law Search Tool (`find_case_tool`)**  
    - When to use: When the user wants to find relevant precedents, court rulings, or legal decisions for a particular legal scenario.  
    - Example questions:  
        - "Are there any similar precedents?"  
        - "How have courts ruled in cases like this?"

    4. **Web Search Tool (`web_search_tool`)**  
    - When to use: Only when general or up-to-date information is needed that cannot be provided by the other tools.  
    - Example questions:  
        - "What are the recent amendments to financial law?"  
        - "What are the latest guidelines from the financial supervisory authority?"

    **Important Notes:**

    1. **Tools requiring a file**:  
    Both `simulate_dispute_tool` and `find_toxic_clauses_tool` require the contract file to be uploaded. Only use these tools if a file is available.

    2. **Only invoke a tool when necessary**:  
    If the user's question can be answered directly without using a tool, respond without invoking one.

    3. **Understand user intent clearly**:  
    Make sure to fully understand the user's intent before choosing a tool.

    4. **When using a tool, provide the required arguments (`args`) accurately.**
    """

    # Format the prompt with actual tool descriptions
    formatted_tool_selection_prompt = tool_selection_prompt.format(tool_list="\n".join(tool_descriptions))
    
    print(formatted_tool_selection_prompt)
    
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)
    
    def chatbot(state: AgentState):
        # Get user messages
        messages = state["messages"]
        file_id = state.get("file_id")
        
        # Log if file ID is present
        if (file_id):
            logger.info(f"File ID is present in chatbot node: {file_id}")
        else:
            logger.info("No file ID in chatbot node")
        
        # Get user's last message - improved extraction logic
        last_user_message = None
        for msg in reversed(messages):
            # Handle dictionary format
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
            # Handle object format
            elif hasattr(msg, "role") and msg.role == "user":
                if hasattr(msg, "content"):
                    last_user_message = msg.content
                    break
            # Direct string format (fallback)
            elif isinstance(msg, str):
                last_user_message = msg
                break
        
        # Use the first message if extraction failed
        if last_user_message is None and messages and len(messages) > 0:
            if isinstance(messages[0], dict) and "content" in messages[0]:
                last_user_message = messages[0]["content"]
            elif hasattr(messages[0], "content"):
                last_user_message = messages[0].content
            elif isinstance(messages[0], str):
                last_user_message = messages[0]
        
        # Log the message before processing
        logger.info(f"Processing message: {last_user_message}")
        # Add file context to the user message if available
        if file_id:
            file_context = "사용자가 계약서 파일을 업로드했습니다. 필요한 경우 계약서 분석 도구를 사용하세요."
        else:
            file_context = "사용자가 아직 계약서 파일을 업로드하지 않았습니다. 계약서 분석이 필요한 경우, 파일 업로드를 요청하세요."
        
        # Add system message with the tool selection prompt and file context
        system_msg = SystemMessage(content=f"{formatted_tool_selection_prompt}\n\n{file_context}")
        messages_with_system = [system_msg] + (messages if isinstance(messages, list) else [messages])
        
        # Use the LLM with the enhanced system prompt
        try:
            response = llm_with_tools.invoke(messages_with_system)
            # Log the response for debugging
            logger.info("LLM Response:")
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response content: {response.content if hasattr(response, 'content') else response}")
            if hasattr(response, "tool_calls"):
                logger.info(f"Tool calls: {response.tool_calls}")
        except Exception as e:
            logger.error(f"Error invoking LLM: {e}")
            response = {"content": "처리 중 오류가 발생했습니다. 다시 시도해 주세요."}
        
        # Convert LangChain message format to the format expected by the state
        ai_message = {
            "role": "assistant",
            "content": response.content if hasattr(response, "content") else str(response),
        }
        
        # If there are tool calls, add them to the message
        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.info(f"Adding tool calls to message: {response.tool_calls}")
            ai_message["tool_calls"] = response.tool_calls
        else:
            logger.info("No tool calls in response")
        
        return {"messages": [ai_message]}
    
    return chatbot

def create_legal_assistant_agent(tools) -> StateGraph:
    """Create the LangGraph workflow for the legal assistant agent"""
    
    # Create nodes
    chatbot_node = create_chatbot_node(tools)
    tool_node = CustomToolNode(tools=tools)
    formatter_node = create_formatter()
    
    # Create the StateGraph with our updated AgentState that includes file_id
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("chatbot", chatbot_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("formatter", formatter_node)
    
    # Use our custom LLM-based router instead of tools_condition
    workflow.add_conditional_edges(
        "chatbot",
        llm_tool_router,  # Custom router that relies on LLM's decisions
        {
            "tools": "tools",
            "formatter": "formatter",
            "chatbot": "chatbot"  # Allow cycling back to chatbot if needed
        }
    )
    
    # Edge from tools to formatter
    workflow.add_edge("tools", "formatter")
    
    # Set entry point
    workflow.set_entry_point("chatbot")
    
    return workflow.compile()

def process_query(query: str, tools: List, file_id: Optional[str] = None) -> dict:
    """Process a user query and return the response in the appropriate format"""
    try:
        logger.info(f"Processing query: '{query}'")
        
        if file_id:
            logger.info(f"Using file ID: {file_id}")
            # Add additional debug log
            logger.info(f"File ID type: {type(file_id)}")
        
        # Create the agent
        agent = create_legal_assistant_agent(tools)
        
        # Initial state with messages and file_id
        # Make sure file_id is explicitly included
        initial_state = {
            "messages": [{"role": "user", "content": query}],
            "file_id": file_id,  # This is the important field that's not getting through
            "error": ""
        }
        
        # Debug log for initial state
        logger.info(f"Initial state: {initial_state}")
        
        # Run the agent
        result = agent.invoke(initial_state)
        logger.info(f"Agent execution completed, result keys: {result.keys()}")
        
        # Extract the final response
        return extract_response_from_messages(result.get("messages", []))
        
    except Exception as e:
        logger.error(f"Uncaught error during agent execution: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "type": "error", 
            "response": f"시스템 오류: {str(e)}", 
            "status": "error", 
            "message": str(e)
        }