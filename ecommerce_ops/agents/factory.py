"""
Agent Factory
Unified interface for LLM and rule-based agents with automatic fallback.
Tries LLM agent first; on failure, falls back to rule-based agent.
"""

import logging
import threading
import time
from typing import Any, Dict, Optional

from ecommerce_ops.agents._base import BaseAgent
from ecommerce_ops.agents.fraud import FraudAgent
from ecommerce_ops.agents.fraud_llm import FraudDetectionAgentLLM
from ecommerce_ops.agents.inventory import InventoryAgent
from ecommerce_ops.agents.inventory_llm import InventoryManagementAgentLLM
from ecommerce_ops.agents.marketing import MarketingAgent
from ecommerce_ops.agents.marketing_llm import MarketingAutomationAgentLLM
from ecommerce_ops.agents.pricing import PricingAgent
from ecommerce_ops.agents.reviews import ReviewsAgent

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
        self._lock = threading.Lock()

    def get_agent(self, name: str) -> "UnifiedAgent":
        """Get or create an agent instance, thread-safe with double-checked locking."""
        agent = self._agents.get(name)
        if agent is not None:
            return agent
        with self._lock:
            agent = self._agents.get(name)
            if agent is None:
                agent = self._create_unified(name)
                self._agents[name] = agent
        return agent

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
        """Select the single highest-value active order for fraud analysis.

        The LLM agent analyzes one order per call, so a list must never be
        passed as ``order_data``. Choosing the highest-value order ensures the
        riskiest order is always analyzed; the rule-based agent still handles
        the full order set in fallback.
        """
        orders = state.get("active_orders", [])
        if not orders:
            return None
        order = max(orders, key=lambda o: float(o.get("order_total") or 0))
        if not isinstance(order, dict):
            return None
        line_items = order.get("line_items") or []
        return {
            "id": order.get("id", ""),
            "customer_email": order.get("customer_email", ""),
            "total": float(order.get("order_total") or 0),
            "item_count": len(line_items),
            "line_items": line_items,
        }

    def _adapt_inventory_input(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map inventory state to a single product dict for the LLM agent.

        Real stock from the state is surfaced as ``current_stock`` so the LLM
        never sees an injected ``0``. The most urgent (lowest-stock) item is
        analyzed first; the rule-based agent covers the full catalog in fallback.
        """
        items = [i for i in state.get("inventory_data", []) if isinstance(i, dict) and i.get("sku")]
        if not items:
            return None
        item = min(items, key=lambda i: float(i.get("stock") or 0))
        stock = item.get("stock")
        if stock is None:
            stock = item.get("current_stock")
        return {
            "product_id": str(item.get("variant_id") or item.get("product_id") or item.get("sku")),
            "sku": item.get("sku"),
            "name": item.get("name") or item.get("sku"),
            "current_stock": int(stock or 0),
            "price": float(item.get("price") or 0),
            "unit_cost": float(item.get("unit_cost") or item.get("price") or 0),
            "daily_sales": float(item.get("daily_sales") or 0),
        }

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
        """Adapt inventory LLM result into a decision; never fabricate values.

        Confidence comes from the LLM (with approval derived from it), and a
        DRAFT_PO is only produced when all execution-critical values (sku,
        positive reorder quantity) are actually present. Otherwise None is
        returned so the pipeline falls back to the rule-based agent instead of
        inventing a purchase order.
        """
        if not llm_result:
            return None
        if llm_result.get("recommended_action") != "reorder":
            return None
        sku = llm_result.get("sku")
        reorder_quantity = llm_result.get("reorder_quantity")
        if not sku or not reorder_quantity or reorder_quantity <= 0:
            return None
        confidence = float(llm_result.get("confidence") or 0)
        return {
            "action_type": "DRAFT_PO",
            "reasoning": llm_result.get("reasoning") or "",
            "confidence": confidence,
            "requires_approval": confidence < 0.9,
            "data": {
                "sku": sku,
                "quantity_to_order": int(reorder_quantity),
                "product_id": llm_result.get("product_id") or "",
                "urgency": llm_result.get("urgency") or "medium",
                "demand_forecast": llm_result.get("demand_forecast") or {},
                "cost_impact": float(llm_result.get("cost_impact") or 0),
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
