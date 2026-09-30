from pydantic import BaseModel, Field
from typing import Any

class ChatRequest(BaseModel):
    message: str

class IntentResult(BaseModel):
    intent: str
    device_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    answer: str | None = None