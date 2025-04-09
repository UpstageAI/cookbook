"""Registry for all tools used by the agent"""

import importlib
import logging
import os
import sys
from typing import List

logger = logging.getLogger(__name__)

def get_registered_tools() -> List:
    """Get all registered tools for the agent"""
    tools = []
    
    # Make sure the backend directory is in the path
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
    
    # Tools to load (module.function_name format)
    tool_imports = [
        "src.tools.tool_dispute_simulator.simulate_dispute_tool",
        "src.tools.tool_find_case.find_case_tool",
        "src.tools.tool_chat_web.web_search_tool",
        "src.tools.tool_find_toxic.find_toxic_clauses_tool"  
    ]
    
    # Import tools dynamically
    for tool_import in tool_imports:
        try:
            module_name, function_name = tool_import.rsplit('.', 1)
            module = importlib.import_module(module_name)
            tool = getattr(module, function_name)
            tools.append(tool)
            logger.info(f"Successfully loaded tool: {tool_import}")
        except Exception as e:
            logger.error(f"Failed to load tool {tool_import}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    return tools
