from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[str] = None


class ChatPayload(BaseModel):
    messages: List[Message] = Field(..., description="The message history including the user prompt")
    documentId: Optional[str] = None
    documentContent: Optional[str] = None
