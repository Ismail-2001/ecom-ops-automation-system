import abc
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from ecommerce_ops.config import settings, Environment
from ecommerce_ops.graph.state import AgentDecision
from ecommerce_ops.memory.agent_memory import store_decision_memory, get_recent_memories, get_pattern_insight
import structlog

logger = structlog.get_logger(__name__)


class BaseAgent(abc.ABC):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        google_key = settings.GOOGLE_API_KEY.get_secret_value() if settings.GOOGLE_API_KEY else None
        deepseek_key = settings.DEEPSEEK_API_KEY.get_secret_value() if settings.DEEPSEEK_API_KEY else None
        if google_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=google_key,
                temperature=0,
                timeout=30,
            )
        elif deepseek_key:
            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                openai_api_key=deepseek_key,
                openai_api_base=settings.DEEPSEEK_BASE_URL,
                temperature=0,
                timeout=30,
            )
        else:
            if settings.ENV == Environment.PRODUCTION:
                raise RuntimeError(f"No API key configured for agent {agent_name}")
            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                openai_api_key="sk-dummy-key",
                openai_api_base=settings.DEEPSEEK_BASE_URL,
                temperature=0,
                timeout=30,
            )

    @abc.abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass

    async def load_memory_context(self, state: Dict[str, Any]) -> str:
        recent = await get_recent_memories(self.agent_name, 5)
        insight = await get_pattern_insight(self.agent_name)
        lines = []
        if recent:
            lines.append("Recent decisions from this agent:")
            for m in recent:
                lines.append(
                    f"  - {m.get('action_type')} | conf={m.get('confidence')} | "
                    f"approval={'needed' if m.get('requires_approval') else 'auto'} | "
                    f"{m.get('reasoning', '')[:80]}"
                )
        if insight:
            lines.append(f"Pattern insight: {insight}")
        return "\n".join(lines) if lines else ""

    async def persist_decision(self, decision: AgentDecision) -> None:
        await store_decision_memory(
            self.agent_name,
            {
                "action_type": decision.action_type,
                "confidence_score": decision.confidence_score,
                "reasoning": decision.reasoning,
                "requires_approval": decision.requires_approval,
            },
        )

    def create_decision(
        self,
        action_type: str,
        reasoning: str,
        data: Dict[str, Any],
        confidence: float,
        requires_approval: bool = True,
    ) -> AgentDecision:
        return AgentDecision(
            agent_id=self.agent_name,
            action_type=action_type,
            reasoning=reasoning,
            action_data=data,
            confidence_score=confidence,
            requires_approval=requires_approval,
        )
