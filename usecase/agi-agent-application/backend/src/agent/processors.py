import json
import logging
from typing import Dict, Any
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_formatted_cases(formatted_case):
    """Extract structured data from a formatted case text"""
    logger.info("Processing formatted case text")
    
    # Default values
    title = ""
    summary = ""
    key_points = ""
    judge_result = ""
    
    try:
        # Check if it's already a dictionary
        if isinstance(formatted_case, dict):
            return {
                "type": "cases",
                "response": {
                    "title": formatted_case.get("title", ""),
                    "summary": formatted_case.get("summary", ""),
                    "key points": formatted_case.get("key_points", ""),
                    "judge result": formatted_case.get("judgment", formatted_case.get("result", ""))
                },
                "status": "success",
                "message": "Response Successful"
            }
            
        # Parse text format
        if "제목:" in formatted_case:
            parts = formatted_case.split("제목:", 1)
            if len(parts) > 1:
                title_part = parts[1].split("\n", 1)
                if title_part:
                    title = title_part[0].strip()
        
        if "요약:" in formatted_case:
            parts = formatted_case.split("요약:", 1)
            if len(parts) > 1:
                summary_part = parts[1].split("\n\n", 1)
                if summary_part:
                    summary = summary_part[0].strip()
                else:
                    # Try with single newline
                    summary_part = parts[1].split("\n", 1)
                    if summary_part:
                        summary = summary_part[0].strip()
        
        if "주요 쟁점:" in formatted_case:
            parts = formatted_case.split("주요 쟁점:", 1)
            if len(parts) > 1:
                key_points_part = parts[1].split("\n\n", 1)
                if key_points_part:
                    key_points = key_points_part[0].strip()
                else:
                    # Try with single newline
                    key_points_part = parts[1].split("\n", 1)
                    if key_points_part:
                        key_points = key_points_part[0].strip()
        
        if "판결:" in formatted_case:
            parts = formatted_case.split("판결:", 1)
            if len(parts) > 1:
                judge_result = parts[1].strip()
                
        # If we still don't have data, try to parse the whole text
        if not (title or summary or key_points or judge_result):
            logger.info("Trying alternative parsing")
            # Just use the entire text as summary if we can't parse it
            summary = formatted_case
                
        return {
            "type": "cases",
            "response": {
                "title": title,
                "summary": summary,
                "key points": key_points,
                "judge result": judge_result
            },
            "status": "success",
            "message": "Response Successful"
        }
    except Exception as e:
        logger.error(f"Error processing formatted case: {e}")
        return {
            "type": "simple_dialogue",
            "response": formatted_case,  # Return the raw text as fallback
            "status": "success",
            "message": "Showing raw case data"
        }

def extract_response_from_messages(final_messages, logger=logger):
    """Extract appropriate response data from the agent's final messages"""
    
    if not final_messages:
        return {"type": "error", "response": "응답을 생성하지 못했습니다.", "status": "error", "message": "No response generated"}
    
    # Enhanced logging
    logger.info("=" * 50)
    logger.info("Processing final messages:")
    for i, msg in enumerate(final_messages):
        logger.info(f"Message {i}:")
        logger.info(f"Type: {type(msg)}")
        logger.info(f"Class name: {msg.__class__.__name__ if hasattr(msg, '__class__') else 'No class'}")
        if hasattr(msg, 'content'):
            logger.info(f"Content: {msg.content[:100]}...")
        elif isinstance(msg, dict) and 'content' in msg:  # Fixed: Changed 'message' to 'msg'
            logger.info(f"Content: {msg['content'][:100]}...")
    logger.info("="*50)
    
    # First, check if there's a direct simple response from the assistant 
    # This should have priority for simple queries
    for message in final_messages:
        role = None
        content = None
        
        if hasattr(message, "role"):
            role = message.role
        elif isinstance(message, dict):
            role = message.get("role")
        
        if hasattr(message, "content"):
            content = message.content
        elif isinstance(message, dict) and "content" in message:
            content = message.get("content")
        
        # If it's a direct assistant message that's not formatted as a case, it should be prioritized
        if role == "assistant" and content:
            # Check if the content doesn't look like a formatted case (no "제목:" or "요약:")
            if "제목:" not in content and "요약:" not in content:
                logger.info(f"Found direct assistant response: {content[:50]}...")
                return {
                    "type": "simple_dialogue", 
                    "message": content, 
                    "status": "success", 
                    "dummy": "Direct Response"
                }
    
    # Look for ToolMessage with content as it contains the actual results
    for message in reversed(final_messages):
        if isinstance(message, object) and hasattr(message, "__class__"):
            logger.info(f"Processing message of type: {message.__class__.__name__}")
            
        if isinstance(message, object) and hasattr(message, "__class__") and message.__class__.__name__ == "ToolMessage":
            if hasattr(message, "content") and message.content:
                tool_name = message.name if hasattr(message, "name") else "unknown"
                logger.info(f"Found ToolMessage with name: {tool_name}")
                
                # Parse the content as JSON if possible
                try:
                    content_str = message.content
                    content = json.loads(content_str)
                    
                    print("=Content"*50)
                    print(content)
                    
                    # Handle different tool types
                    if tool_name == "find_case_tool":
                        return process_find_case_result(content)
                    elif tool_name == "simulate_dispute_tool":
                        return process_simulation_result(content)
                    elif tool_name == "web_search_tool":
                        return process_web_search_result(content)
                    elif tool_name == "find_toxic_clauses_tool":
                        return content
                    
                    # Default format
                    return {
                        "type": "simple_dialogue", 
                        "response": json.dumps(content, indent=2, ensure_ascii=False), 
                        "status": "success", 
                        "message": "Response Successful"
                    }
                        
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON: {message.content[:100]}...")
                    # If not JSON, try to parse as formatted case directly
                    return process_formatted_cases(message.content)
    
    # If no ToolMessage with content, check for assistant messages with improved detection
    for message in reversed(final_messages):
        logger.info(f"Checking message type: {type(message)}")
        
        # Check for AIMessage class directly
        if hasattr(message, "__class__") and message.__class__.__name__ in ["AIMessage", "HumanMessage"]:
            if message.__class__.__name__ == "AIMessage" and hasattr(message, "content"):
                logger.info(f"Found AIMessage with content: {message.content[:50]}...")
                return {
                    "type": "no_tool_chat", 
                    "response": message.content, 
                    "status": "success", 
                    "message": "Response Successful"
                }
        
        # Handle both dictionary-like objects and other message types
        role = None
        content = None
        
        if hasattr(message, "role"):
            role = message.role
        elif isinstance(message, dict):
            role = message.get("role")
        
        if hasattr(message, "content"):
            content = message.content
        elif isinstance(message, dict) and "content" in message:
            content = message.get("content")
            
        if role == "assistant" and content:
            logger.info(f"Found assistant message with content: {content[:50]}...")
            return {
                "type": "simple_dialogue", 
                "response": content, 
                "status": "success", 
                "message": "Response Successful"
            }
    
    # As a fallback, just return the last message content if any exists
    for message in reversed(final_messages):
        if hasattr(message, "content") and message.content:
            logger.info(f"Fallback: using message content: {message.content[:50]}...")
            return {
                "type": "simple_dialogue", 
                "response": message.content, 
                "status": "success", 
                "message": "Response Successful (fallback)"
            }
    
    # If we reach here, we couldn't find any useful content
    logger.error("No valid response content found in any message")
    return {
        "type": "simple_dialogue", 
        "response": "응답을 생성하지 못했습니다. 다른 질문을 시도하거나, 계약서 관련 질문인 경우 '계약 해지 조항 분석해줘'와 같이 더 구체적으로 질문해 보세요.", 
        "status": "error", 
        "message": "No valid response content found"
    }

def process_find_case_result(content):
    """Process find_case_tool results and format into a standardized dialogue format"""
    try:
        # Convert content to string if it's not already
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, ensure_ascii=False)
        else:
            content_str = str(content)
            
        print(content)
        print("="*50)
        print(content_str)

        # Define regex pattern for case details
        pattern = r'제목:\s*(.*?)(?:\s*\n)\s*요약:\s*(.*?)(?:\s*\n)\s*핵심 포인트:\s*(.*?)(?:\s*\n)\s*판결 결과:\s*(.*?)$'
        
        # Find case details using regex
        match = re.search(pattern, content_str, re.DOTALL)
        
        if match:
            title = match.group(1).strip()
            summary = match.group(2).strip()
            key_points = match.group(3).strip()
            judgment = match.group(4).strip()
            
            return {
            "type": "cases",
            "disputes": [{
                "title": title if title else "",
                "summary": summary if summary else "",
                "key points": key_points if key_points else "",
                "judge result": judgment if judgment else "",   
            }],
            "status": "success",
            "message": "금융 분쟁 사례들입니다."
            }
            
        else:
            raise ValueError("Cannot parse the case details from the content")
            
    except Exception as e:
        logger.error(f"Error processing find case result: {str(e)}")
        return {
            "type": "simple_dialogue",
            "response": "판례 처리 중 오류가 발생했습니다.",
            "status": "error",
            "message": str(e)
        }

def process_simulation_result(content):
    """Process simulate_dispute_tool results"""
    simulations = content.get("simulations", [])
    print(simulations)
    if not simulations:
        return {
            "type": "simple_dialogue", 
            "response": "시뮬레이션 결과가 없습니다.", 
            "status": "error", 
            "message": "No simulation results"
        }
        
    formatted_simulations = []
    for i, simulation in enumerate(simulations):
        # Default values
        situation = ""
        user_part = ""
        agent_part = ""
        
        # Remove ``` from start and end of the text if present
        simulation = simulation.strip()
        simulation = simulation.replace("```", "")
        
        pattern = r'상황:\s*(.*?)\s*사용자:\s*"?(.*?)"?\s*상담원:\s*"?(.*?)"?\s*$'
        match = re.search(pattern, simulation, re.DOTALL)
        
        formatted_simulations.append({
            "id": i,
            "situation": match.group(1).strip() if match else "",
            "user": match.group(2).strip() if match else "",
            "consultant": match.group(3).strip() if match else ""
        })
    
    return {
        "type": "simulation", 
        "simulations": formatted_simulations,
        "status": "success", 
        "message": "Response Successful"
    }

def process_web_search_result(content):
    """Process web_search_tool results"""
    results = content.get("results", [])
    if not results:
        return {
            "type": "simple_dialogue", 
            "message": "검색 결과가 없습니다.", 
            "status": "error"
        }
    
    # Combine results into a coherent response
    response_text = ""
    for result in results:
        title = result.get("title", "")
        content_text = result.get("content", "")
        if title and content_text:
            response_text += f"{title}:\n{content_text}\n\n"
    
    return {
        "type": "simple_dialogue", 
        "message": response_text or json.dumps(content, ensure_ascii=False), 
        "status": "success"
    }
