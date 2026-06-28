"""
Agent Factory
Unified interface for LLM and rule-based agents with automatic fallback.
Tries LLM agent first; on failure, falls back to rule-based agent.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from ecommerce_ops.agents._base import BaseAgent
from ecommerce_ops.agents.fraud import FraudAgent
from ecommerce_ops.agents.fraud_llm import FraudDetectionAgentLLM
from ecommerce_ops.agents.inventory import InventoryAgent
from ecommerce_ops.agents.inventory_llm import InventoryManagementAgentLLM
from ecommerce_ops.agents.pricing import PricingAgent
from ecommerce_ops.agents.reviews import ReviewsAgent
from ecommerce_ops.agents.marketing import MarketingAgent
from ecommerce_ops.agents.marketing_llm import MarketingAutomationAgentLLM

logger = logging.getLogger("ecommerce_ops.agents.factory")


class AgentFactory:
    """
    Factory that creates agent instances with LLM-first, rule-based fallback.
    
    Each agent node in the supervisor graph gets a UnifiedAgent that:
    1. Tries the LLM variant first (richer analysis, guardrails, message bus)
    2. On any LLM failure, silently falls back to the rule-based variant
    3. Returns decisions in the same format the supervisor expects
    """

    def __init__(self):
        self._agents: Dict[str, UnifiedAgent] = {}

    def get_agent(self, name: str) -> "UnifiedAgent":
        if name not in self._agents:
            self._agents[name] = self._create_unified(name)
        return self._agents[name]

    def _create_unified(self, name: str) -> "UnifiedAgent":
        if name == "fraud":
            return UnifiedAgent(
                name="fraud",
                llm_agent=FraudDetectionAgentLLM(),
                rule_agent=FraudAgent(),
                llm_method="analyze",
                rule_method="run",
                input_adapter=self._adapt_fraud_input,
                output_adapter=self._adapt_fraud_output,
            )
        elif name == "inventory":
            return UnifiedAgent(
                name="inventory",
                llm_agent=InventoryManagementAgentLLM(),
                rule_agent=InventoryAgent(),
                llm_method="analyze",
                rule_method="run",
                input_adapter=self._adapt_inventory_input,
                output_adapter=self._adapt_inventory_output,
            )
        elif name == "pricing":
            return UnifiedAgent(
                name="pricing",
                llm_agent=None,
                rule_agent=PricingAgent(),
                llm_method=None,
                rule_method="run",
                input_adapter=None,
                output_adapter=None,
            )
        elif name == "reviews":
            return UnifiedAgent(
                name="reviews",
                llm_agent=None,
                rule_agent=ReviewsAgent(),
                llm_method=None,
                rule_method="run",
                input_adapter=None,
                output_adapter=None,
            )
        elif name == "marketing":
            return UnifiedAgent(
                name="marketing",
                llm_agent=MarketingAutomationAgentLLM(),
                rule_agent=MarketingAgent(),
                llm_method="create_campaign",
                rule_method="run",
                input_adapter=self._adapt_marketing_input,
                output_adapter=self._adapt_marketing_output,
            )
        else:
            raise ValueError(f"Unknown agent: {name}")

    # ── Input Adapters (state → LLM agent format) ──────────

    def _adapt_fraud_input(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        orders = state.get("active_orders", [])
        if not orders:
            return None
        return orders[0] if len(orders) == 1 else orders

    def _adapt_inventory_input(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        items = state.get("inventory_data", [])
        if not items:
            return None
        return items[0] if len(items) == 1 else items

    def _adapt_marketing_input(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        items = state.get("inventory_data", [])
        if not items:
            return None
        low_stock = [i for i in items if 0 < i.get("stock", 0) < 20]
        if not low_stock:
            return None
        return {
            "trigger": "low_stock",
            "customer": {"segment": "all"},
            "cart_value": 0,
        }

    # ── Output Adapters (LLM result → state decisions) ─────

    def _adapt_fraud_output(self, llm_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not llm_result or llm_result.get("decision") == "approve":
            return None
        return {
            "action_type": "HOLD_ORDER",
            "reasoning": llm_result.get("reasoning", ""),
            "confidence": llm_result.get("confidence", 0.5),
            "requires_approval": llm_result.get("confidence", 0.5) < 0.9,
            "data": {
                "risk_score": llm_result.get("risk_score", 0.5),
                "risk_factors": llm_result.get("risk_factors", []),
                "recommended_actions": llm_result.get("recommended_actions", []),
            },
        }

    def _adapt_inventory_output(self, llm_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not llm_result:
            return None
        action = llm_result.get("recommended_action", "maintain")
        if action == "maintain":
            return None
        return {
            "action_type": "DRAFT_PO",
            "reasoning": llm_result.get("reasoning", ""),
            "confidence": 0.85,
            "requires_approval": False,
            "data": {
                "product_id": llm_result.get("product_id", ""),
                "reorder_quantity": llm_result.get("reorder_quantity", 0),
                "urgency": llm_result.get("urgency", "medium"),
                "demand_forecast": llm_result.get("demand_forecast", {}),
                "cost_impact": llm_result.get("cost_impact", 0),
            },
        }

    def _adapt_marketing_output(self, llm_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not llm_result:
            return None
        return {
            "action_type": "DRAFT_MARKETING_CAMPAIGN",
            "reasoning": llm_result.get("reasoning", ""),
            "confidence": 0.8,
            "requires_approval": True,
            "data": {
                "campaign_name": llm_result.get("campaign_name", ""),
                "campaign_type": llm_result.get("campaign_type", "email"),
                "target_audience": llm_result.get("target_audience", {}),
                "content": llm_result.get("content", {}),
                "estimated_reach": llm_result.get("estimated_reach", 0),
                "estimated_ctr": llm_result.get("estimated_ctr", 0),
                "estimated_revenue": llm_result.get("estimated_revenue", 0),
            },
        }


class UnifiedAgent:
    """
    Wraps an LLM agent and a rule-based agent into a single interface.
    Tries LLM first, falls back to rule-based on failure.
    """

    def __init__(
        self,
        name: str,
        llm_agent: Optional[BaseAgent],
        rule_agent: BaseAgent,
        llm_method: Optional[str],
        rule_method: str,
        input_adapter: Optional[Any],
        output_adapter: Optional[Any],
    ):
        self.name = name
        self.llm_agent = llm_agent
        self.rule_agent = rule_agent
        self.llm_method = llm_method
        self.rule_method = rule_method
        self.input_adapter = input_adapter
        self.output_adapter = output_adapter

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with LLM-first, rule-based fallback.
        Returns state with decisions appended.
        """
        start = time.monotonic()

        # Try LLM agent if available
        if self.llm_agent and self.llm_method:
            try:
                llm_input = self.input_adapter(state) if self.input_adapter else state
                if llm_input is not None:
                    llm_method = getattr(self.llm_agent, self.llm_method)
                    llm_result = await llm_method(llm_input)
                    adapted = self.output_adapter(llm_result) if self.output_adapter else None

                    if adapted:
                        decision = self.rule_agent.create_decision(
                            action_type=adapted["action_type"],
                            reasoning=adapted["reasoning"],
                            data=adapted.get("data", {}),
                            confidence=adapted.get("confidence", 0.5),
                            requires_approval=adapted.get("requires_approval", True),
                        )
                        decisions = state.get("decisions", []) + [decision]
                        state["decisions"] = decisions
                        elapsed = (time.monotonic() - start) * 1000
                        logger.info(
                            "Agent %s (LLM) completed in %.1fms",
                            self.name, elapsed,
                        )
                        return state

            except Exception as e:
                logger.warning(
                    "Agent %s LLM failed (%s), falling back to rule-based",
                    self.name, str(e),
                )

        # Fallback: rule-based agent
        try:
            result = await getattr(self.rule_agent, self.rule_method)(state)
            elapsed = (time.monotonic() - start) * 1000
            logger.info(
                "Agent %s (rule-based) completed in %.1fms",
                self.name, elapsed,
            )
            return result
        except Exception as e:
            logger.exception("Agent %s rule-based also failed: %s", self.name, e)
            errors = state.get("errors", [])
            errors.append({"agent": self.name, "error": str(e)})
            state["errors"] = errors
            return state


# Singleton
agent_factory = AgentFactory()
