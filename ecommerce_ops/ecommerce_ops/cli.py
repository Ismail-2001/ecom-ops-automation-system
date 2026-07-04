import typer
import asyncio
from ecommerce_ops.graph.supervisor import Supervisor
from ecommerce_ops.config import settings
import structlog
from datetime import datetime
import uuid

app = typer.Typer()
logger = structlog.get_logger()

@app.command()
def run(shadow: bool = True):
    """Run a single manual cycle of the ecommerce-ops-agent."""
    typer.echo(f"🚀 Starting cycle (Shadow Mode: {shadow})")
    
    # In a real CLI, we would populate this from the connectors
    mock_state = {
        "inventory_data": [
            {"sku": "TSHIRT-BLUE-L", "stock": 5, "price": 25.0, "variant_id": "v1"},
            {"sku": "MUG-WHITE", "stock": 2, "price": 12.0, "variant_id": "v2"}
        ],
        "active_orders": [
            {"id": "o_suspicious", "line_items": [{"sku": "TSHIRT-BLUE-L", "quantity": 1}]}
        ],
        "reviews_data": [
            {"id": "r1", "content": "Great product!", "rating": 5}
        ],
        "decisions": [],
        "hitl_queue": [],
        "messages": [],
        "errors": [],
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow()
    }
    
    supervisor = Supervisor()
    asyncio.run(supervisor.run(mock_state))
    
    typer.echo(f"✅ Cycle complete. Run ID: {mock_state['run_id']}")
    typer.echo(f"📊 Decisions generated: {len(mock_state['decisions'])}")
    for d in mock_state['decisions']:
        typer.echo(f"  - [{d.agent_id}] {d.action_type}: {d.reasoning[:50]}...")

@app.command()
def pause():
    """Kill switch: Halts all autonomous actions."""
    typer.echo("🛑 Kill switch activated! All autonomous actions halted.")
    # In production, this would update a flag in Redis/DB

if __name__ == "__main__":
    app()
