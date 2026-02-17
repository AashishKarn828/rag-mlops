"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""

    query: str
    top_k: Optional[int] = 3
    session_id: Optional[str] = None  # NEW: Optional session ID for conversation memory


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""

    answer: str
    sources: List[str]
    session_id: str  # NEW: Return session_id so client can maintain context


class IndexResponse(BaseModel):
    """Response model for index endpoint"""

    status: str
    filename: str
    chunks_indexed: int
    message: str


class HealthResponse(BaseModel):
    """Response model for health check"""

    status: str
    models_loaded: bool
