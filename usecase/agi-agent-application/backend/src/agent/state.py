from typing import Dict, List, Any, TypedDict, Optional

class AgentState(TypedDict, total=False):
    """State for the legal assistant agent."""
    messages: List[Any]  # List of message objects or dicts
    error: str  # Error message if any
    file_id: Optional[Any]  # File ID for accessing S3 files
