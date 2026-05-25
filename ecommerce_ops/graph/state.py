from typing import Annotated, Any, Dict, List, TypedDict
from datetime import datetime
from operator import add
from pydantic import BaseModel, Field


class AgentDecision(BaseModel):
    agent_id: str
    action_type: str
    reasoning: str
    action_data: Dict
    requires_approval: bool = True
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OverallState(TypedDict):
    inventory_data: Dict
    pricing_data: Dict
    reviews_data: List[Dict]
    fraud_alerts: List[Dict]
    decisions: Annotated[list, add]
    hitl_queue: Annotated[list, add]
    messages: Annotated[list, add]
    errors: Annotated[list, add]
