from typing import Dict, Any, List
from datetime import datetime, timedelta
from ecommerce_ops.agents._base import BaseAgent
from ecommerce_ops.graph.state import AgentDecision
import structlog

logger = structlog.get_logger(__name__)

class InventoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("InventoryAgent")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the inventory analysis:
        1. Process current inventory snapshot.
        2. Calculate velocity for each SKU.
        3. Predict stockout dates.
        4. Generate PO drafts for items nearing stockout.
        """
        inventory = state.get("inventory_data", [])
        decisions = []
        
        for item in inventory:
            sku = item.get("sku")
            current_stock = item.get("stock", 0)
            
            # Simple 30-day velocity calculation (mocked for now, usually from historical orders)
            # In a real scenario, we'd fetch order history for this SKU
            daily_velocity = self._calculate_velocity(sku, state.get("active_orders", []))
            
            if daily_velocity > 0:
                days_left = current_stock / daily_velocity
                if days_left < 14:  # Threshold: 2 weeks
                    decision = self.create_decision(
                        action_type="DRAFT_PO",
                        reasoning=f"SKU {sku} has {current_stock} units left with a daily velocity of {daily_velocity:.2f}. Predicted stockout in {days_left:.1f} days.",
                        data={
                            "sku": sku,
                            "quantity_to_order": int(daily_velocity * 30),  # Order 30 days of supply
                            "supplier_id": "DEFAULT",
                            "predicted_stockout_days": days_left
                        },
                        confidence=0.9 if days_left < 7 else 0.7
                    )
                    decisions.append(decision)
                    self.log_audit(decision)

        state["decisions"] = state.get("decisions", []) + decisions
        return state

    def _calculate_velocity(self, sku: str, orders: List[Dict]) -> float:
        """Calculate daily sales velocity over the last 30 days."""
        # This is a heuristic - in production we'd use a real rolling window
        # For now, we search the provided orders for this SKU
        total_qty = 0
        window_days = 30
        
        # Mock logic: if we don't have enough order history, return a default for testing
        if not orders:
            return 2.5 # Default benchmark for demo
            
        for order in orders:
            for line_item in order.get("line_items", []):
                if line_item.get("sku") == sku:
                    total_qty += line_item.get("quantity", 0)
        
        return total_qty / window_days
