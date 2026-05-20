from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from ecommerce_ops.graph.state import OverallState
from ecommerce_ops.agents.inventory import InventoryAgent
from ecommerce_ops.agents.pricing import PricingAgent
from ecommerce_ops.agents.reviews import ReviewsAgent
from ecommerce_ops.agents.fraud import FraudAgent
from ecommerce_ops.agents.marketing import MarketingAgent

class Supervisor:
    def __init__(self):
        self.builder = StateGraph(OverallState)
        self._setup_graph()

    def _setup_graph(self):
        # Initialize Agents
        nodes = {
            "inventory": InventoryAgent(),
            "pricing": PricingAgent(),
            "reviews": ReviewsAgent(),
            "fraud": FraudAgent(),
            "marketing": MarketingAgent()
        }
        
        # Add Nodes
        for name, agent in nodes.items():
            self.builder.add_node(name, agent.run)
        
        # Define Flow
        self.builder.set_entry_point("fraud") # Check fraud first
        self.builder.add_edge("fraud", "inventory")
        self.builder.add_edge("inventory", "pricing")
        self.builder.add_edge("pricing", "reviews")
        self.builder.add_edge("reviews", "marketing")
        self.builder.add_edge("marketing", END)

        # Compile
        self.graph = self.builder.compile()

    async def run(self, input_state: Dict[str, Any]):
        """Execute the multi-agent graph."""
        return await self.graph.ainvoke(input_state)
