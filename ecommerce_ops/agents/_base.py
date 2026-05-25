import abc
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from ecommerce_ops.config import settings, Environment
from ecommerce_ops.graph.state import AgentDecision
import structlog

logger = structlog.get_logger(__name__)

class BaseAgent(abc.ABC):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        api_key = settings.DEEPSEEK_API_KEY.get_secret_value() if settings.DEEPSEEK_API_KEY else None
        if not api_key:
            if settings.ENV == Environment.PRODUCTION:
                raise RuntimeError(f"DEEPSEEK_API_KEY is required in production for agent {agent_name}")
            api_key = "sk-dummy-key"
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=api_key,
            openai_api_base=settings.DEEPSEEK_BASE_URL,
            temperature=0,
            timeout=30,
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
