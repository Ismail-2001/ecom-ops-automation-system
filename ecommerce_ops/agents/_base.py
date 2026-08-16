import abc
from typing import Any

import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from ecommerce_ops.config import Environment, settings
from ecommerce_ops.graph.state import AgentDecision
from ecommerce_ops.memory.agent_memory import (
    get_pattern_insight,
    get_recent_memories,
    store_decision_memory,
)

logger = structlog.get_logger(__name__)


class BaseAgent(abc.ABC):  # noqa: B024
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
                raise RuntimeError(f"No LLM API key configured for agent {agent_name}. Set GOOGLE_API_KEY or DEEPSEEK_API_KEY.")
            # Development fallback - uses settings.LLM_MODEL which defaults to gemini-2.0-flash
            # but requires a valid key. This will fail at first call if no key is set.
            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                openai_api_key="sk-dummy-key-do-not-use-in-prod",
                temperature=0,
                timeout=30,
            )

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement 'run' or use a custom method"
        )

    async def load_memory_context(self, state: dict[str, Any]) -> str:
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
        data: dict[str, Any],
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
