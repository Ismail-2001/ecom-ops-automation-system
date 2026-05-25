from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from ecommerce_ops.graph.state import OverallState, ExecutionPlan, ReflectionFeedback
from ecommerce_ops.agents.inventory import InventoryAgent
from ecommerce_ops.agents.pricing import PricingAgent
from ecommerce_ops.agents.reviews import ReviewsAgent
from ecommerce_ops.agents.fraud import FraudAgent
from ecommerce_ops.agents.marketing import MarketingAgent
from ecommerce_ops.agents.reflection import ReflectionAgent
import logging

logger = logging.getLogger("ecommerce_ops.graph.supervisor")

AGENTS = {
    "fraud": FraudAgent(),
    "inventory": InventoryAgent(),
    "pricing": PricingAgent(),
    "reviews": ReviewsAgent(),
    "marketing": MarketingAgent(),
}

DEFAULT_PLAN = ["fraud", "inventory", "pricing", "reviews", "marketing"]


async def planner(state: Dict[str, Any]) -> Dict[str, Any]:
    plan = []
    if state.get("active_orders"):
        plan.append("fraud")
    if state.get("inventory_data"):
        plan.append("inventory")
        plan.append("pricing")
    if state.get("reviews_data"):
        plan.append("reviews")
    plan.append("marketing")

    if not plan:
        plan = DEFAULT_PLAN

    state["execution_plan"] = ExecutionPlan(agents_to_run=plan, rationale="dynamic")
    state["_step_index"] = 0
    logger.info("Execution plan: %s", plan)
    return state


async def run_agent(node_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    agent = AGENTS.get(node_name)
    if agent is None:
        logger.warning("Unknown agent node: %s", node_name)
        return state
    try:
        result = await agent.run(state)
        idx = state.get("_step_index", 0)
        result["_step_index"] = idx + 1
        return result
    except Exception as e:
        logger.exception("Agent %s failed: %s", node_name, e)
        errors = state.get("errors", [])
        errors.append({"agent": node_name, "error": str(e)})
        state["errors"] = errors
        state["_step_index"] = state.get("_step_index", 0) + 1
        return state


async def router(state: Dict[str, Any]) -> str:
    plan: ExecutionPlan = state.get("execution_plan")
    if plan is None:
        return END
    idx = state.get("_step_index", 0)
    if idx >= len(plan.agents_to_run):
        return "reflection"
    next_agent = plan.agents_to_run[idx]
    return next_agent if next_agent in AGENTS else "reflection"


async def reflection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    decisions = state.get("decisions", [])
    if not decisions:
        return state

    reflection = ReflectionAgent()
    feedback = await reflection.run(decisions)

    corrected = []
    for d, fb in zip(decisions, feedback):
        c = await reflection.correct_decision(d, fb)
        corrected.append(c)

    state["decisions"] = corrected
    state["reflection_feedback"] = state.get("reflection_feedback", []) + feedback

    passed = sum(1 for fb in feedback if fb.passed)
    logger.info("Reflection: %d/%d decisions passed validation", passed, len(feedback))
    return state


class Supervisor:
    def __init__(self):
        self.builder = StateGraph(OverallState)
        self._setup_graph()

    def _setup_graph(self):
        self.builder.add_node("planner", planner)
        self.builder.add_node("reflection", reflection_node)

        for name in AGENTS:
            self.builder.add_node(
                name, lambda state, n=name: run_agent(n, state)
            )

        all_nodes = list(AGENTS.keys()) + ["reflection", END]
        self.builder.set_conditional_entry_point(
            lambda s: "planner" if s.get("execution_plan") is None else DEFAULT_PLAN[0],
            {"planner": "planner", DEFAULT_PLAN[0]: DEFAULT_PLAN[0]},
        )

        self.builder.add_edge("planner", DEFAULT_PLAN[0])

        for name in AGENTS:
            self.builder.add_conditional_edges(
                name,
                router,
                {n: n for n in all_nodes},
            )

        self.builder.add_edge("reflection", END)

        self.graph = self.builder.compile()

    async def run(self, input_state: Dict[str, Any]) -> Dict[str, Any]:
        if "memory_context" not in input_state:
            input_state["memory_context"] = {}
        if "reflection_feedback" not in input_state:
            input_state["reflection_feedback"] = []
        if "_step_index" not in input_state:
            input_state["_step_index"] = 0
        return await self.graph.ainvoke(input_state)
