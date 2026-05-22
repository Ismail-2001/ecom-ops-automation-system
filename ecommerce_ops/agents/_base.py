import abc
import json
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from ecommerce_ops.config import settings
from ecommerce_ops.graph.state import AgentDecision

class BaseAgent(abc.ABC):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.DEEPSEEK_API_KEY.get_secret_value() if settings.DEEPSEEK_API_KEY else "mock_key",
            openai_api_base=settings.DEEPSEEK_BASE_URL,
            temperature=0,
        )

    @abc.abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent's logic on the current state."""
        pass

    def create_decision(
        self, 
        action_type: str, 
        reasoning: str, 
        data: Dict[str, Any], 
        confidence: float,
        requires_approval: bool = True
    ) -> AgentDecision:
        """Helper to format a decision for the audit log and state."""
        return AgentDecision(
            agent_id=self.agent_name,
            action_type=action_type,
            reasoning=reasoning,
            action_data=data,
            confidence_score=confidence,
            requires_approval=requires_approval
        )

    def log_audit(self, decision: AgentDecision):
        """Write decision to immutable JSONL audit log."""
        log_entry = decision.model_dump_json()
        with open("audit_log.jsonl", "a") as f:
            f.write(log_entry + "\n")
