"""Pydantic schemas for API request and response data models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """User chat inquiry request payload."""
    query: str = Field(..., description="Kullanıcı bankacılık sorusu veya talebi", examples=["Geçen ay harcamalarım neden arttı ve nasıl tasarruf edebilirim?"])
    customer_number: str = Field(default="CUST-1001", description="Müşteri numarası", examples=["CUST-1001"])
    thread_id: Optional[str] = Field(default=None, description="Oturum takip kimliği (otomatik oluşturulur)")


class ChatResponse(BaseModel):
    """Response payload containing multi-agent answer, active agents, and details."""
    query: str
    customer_number: str
    thread_id: str
    response: str
    active_agents: List[str]
    agent_outputs: Dict[str, Any]


class AgentInfo(BaseModel):
    """Agent metadata description."""
    name: str
    role: str
    description: str
    tools: List[str]


class AgentListResponse(BaseModel):
    """List of available agents in the multi-agent system."""
    total_agents: int
    agents: List[AgentInfo]


class HealthResponse(BaseModel):
    """API health status payload."""
    status: str
    app_name: str
    version: str
    database: str
    agents_ready: bool
