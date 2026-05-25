from typing import Annotated, Any, Dict, List, Optional, TypedDict, Union
from datetime import datetime
from pydantic import BaseModel, Field

class AgentDecision(BaseModel):
    agent_id: str
    action_type: str
    reasoning: str
    action_data: Dict
    requires_approval: bool = True
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HITLItem(BaseModel):
    id: str
    agent_id: str
    decision: AgentDecision
    status: str = "pending"  # pending, approved, rejected
    owner_feedback: Optional[str] = None

class StoreState(TypedDict):
    # Core Data Snapshots
    inventory_snapshot: Dict[str, Any]
    active_orders: List[Dict]
    recent_reviews: List[Dict]
    
    # Execution Context
    current_agent: str
    next_action: Optional[str]
    history: List[AgentDecision]
    
    # HITL Management
    hitl_queue: List[HITLItem]
    
    # Meta
    run_id: str
    timestamp: datetime

# For LangGraph integration, we'll likely need a State definition that supports reducers
from operator import add

def merge_lists(left: list, right: list) -> list:
    return left + right

class OverallState(TypedDict):
    inventory_data: Dict
    pricing_data: Dict
    reviews_data: List[Dict]
    fraud_alerts: List[Dict]
    decisions: Annotated[list, add]
    hitl_queue: Annotated[list, add]
    messages: Annotated[list, add]
    errors: Annotated[list, add]
