import os
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, update

from ecommerce_ops.config import settings as app_settings
from ecommerce_ops.graph.supervisor import Supervisor
from ecommerce_ops.models import (
    init_db,
    seed_data_if_empty,
    get_db_session,
    ApprovalAction,
    AuditEntry,
    AgentStatus,
    StoreSettings
)
from ecommerce_ops.safety.safety_rules import evaluate_action_safety
from sqlalchemy.ext.asyncio import AsyncSession

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecommerce_ops.api")

app = FastAPI(title=app_settings.PROJECT_NAME)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # During development we allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting websocket message: {e}")

ws_manager = ConnectionManager()

# Request Models
class DecisionActionBody(BaseModel):
    notes: Optional[str] = None
    draft_response: Optional[str] = None # For review responses edit

class RejectActionBody(BaseModel):
    reason: str
    notes: Optional[str] = None

class BatchActionBody(BaseModel):
    ids: List[str]
    action: str # approve or reject
    reason: Optional[str] = None
    notes: Optional[str] = None

class SettingsUpdateBody(BaseModel):
    shadow_mode: Optional[bool] = None
    fraud_threshold: Optional[int] = None
    po_limit: Optional[float] = None
    pricing_limit: Optional[float] = None
    reviews_rating_threshold: Optional[int] = None

# App Startup Hook
@app.on_event("startup")
async def startup_event():
    # Setup Supervisor in App State
    app.state.supervisor = Supervisor()
    # Initialize DB schema
    await init_db()
    # Seed mock data
    await seed_data_if_empty()
    logger.info("Application startup and database initialization complete.")

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# WebSocket Endpoint
@app.websocket("/ws/queue")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Keep connection open
        while True:
            data = await websocket.receive_text()
            # Simple heartbeat ping/pong or echoes
            await websocket.send_json({"type": "ping", "data": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# 1. GET /api/approvals - List approvals with filters
@app.get("/api/approvals")
async def get_approvals(
    agent: Optional[str] = None,
    risk: Optional[str] = None,
    status: Optional[str] = "pending", # pending or all
    search: Optional[str] = None,
    sort: Optional[str] = "newest", # newest, oldest, highest_risk, expiring
    db: AsyncSession = Depends(get_db_session)
):
    query = select(ApprovalAction)
    
    # Filter by Status
    if status == "pending":
        query = query.where(ApprovalAction.status == "pending")
    
    # Filter by Agent
    if agent and agent != "all":
        query = query.where(ApprovalAction.agent == agent)
        
    # Filter by Risk Level
    if risk and risk != "all":
        query = query.where(ApprovalAction.risk_level == risk)
        
    # Search
    if search:
        # Simple match in payload
        # SQLite or PostgreSQL handle JSON differently, but we can do a general string contains on serialized columns
        # To make it database-agnostic, we can query all and filter in memory, or use cast.
        # Given this is a demo/dev database, filtering the result list in Python is safe and highly compatible.
        pass

    result = await db.execute(query)
    actions = result.scalars().all()
    
    # In-memory filter for search (database-agnostic search on JSON payload fields)
    if search:
        search_lower = search.lower()
        filtered_actions = []
        for a in actions:
            # Check ID
            if search_lower in a.id.lower():
                filtered_actions.append(a)
                continue
            # Check SKU or Product Name or Order ID in payload
            payload_str = str(a.payload).lower()
            if search_lower in payload_str:
                filtered_actions.append(a)
        actions = filtered_actions

    # Sort
    # risk levels weight: critical=4, high=3, medium=2, low=1
    risk_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    
    if sort == "newest":
        actions = sorted(actions, key=lambda x: x.created_at, reverse=True)
    elif sort == "oldest":
        actions = sorted(actions, key=lambda x: x.created_at)
    elif sort == "highest_risk":
        actions = sorted(actions, key=lambda x: risk_weights.get(x.risk_level, 0), reverse=True)
    elif sort == "expiring":
        # Put items with expires_at first, sorted by soonest expiry
        actions = sorted(
            actions, 
            key=lambda x: x.expires_at if x.expires_at else datetime.max
        )
        
    return actions

# 2. GET /api/approvals/{id} - Single approval details
@app.get("/api/approvals/{id}")
async def get_approval(id: str, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(ApprovalAction).where(ApprovalAction.id == id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Approval action not found")
    return action

# Helper to simulate real-world API execution against Shopify or Stripe
async def execute_shop_action(action: ApprovalAction, db: AsyncSession):
    # This simulates pushing to Shopify / Stripe
    action_type = action.action_type
    payload = action.payload

    if action.shadow_mode:
        logger.info(f"[SHADOW MODE] Simulating execution of {action_type} for ID {action.id}")
        return True, "Executed in Shadow Mode (Simulation)"

    try:
        # Real Shopify/Stripe logic would run here based on action_type
        # Since credentials are mocks, we simulate successful executions
        # In a real store, we would activate shopifyapi session and invoke Variant.save() / Order.hold()
        logger.info(f"[LIVE MODE] Executing {action_type} on Shopify for ID {action.id}")
        return True, f"Successfully executed live {action_type}"
    except Exception as e:
        logger.error(f"Failed to execute live action: {e}")
        return False, str(e)

# Update agent graduation streaks
async def update_agent_streak(agent_name: str, approved: bool, confidence: float, db: AsyncSession):
    res = await db.execute(select(AgentStatus).where(AgentStatus.agent_id == agent_name))
    status = res.scalar_one_or_none()
    if status:
        status.total_decisions += 1
        if approved:
            status.total_approvals += 1
            # If approved and confidence >= 95%, increment streak
            if confidence >= 0.95:
                status.streak += 1
                if status.streak >= 50 and status.autonomy_level != "autonomous":
                    status.autonomy_level = "autonomous"
                    logger.info(f"Agent {agent_name} graduated to AUTONOMOUS!")
            else:
                # low confidence doesn't break streak, but doesn't increment it
                pass
        else:
            status.total_rejections += 1
            # Rejection resets streak!
            status.streak = 0
            status.autonomy_level = "supervised" # reset to supervised on rejection
        
        # Recalculate average confidence
        status.avg_confidence = ((status.avg_confidence * (status.total_decisions - 1)) + confidence) / status.total_decisions
        db.add(status)

# 3. POST /api/approvals/{id}/approve
@app.post("/api/approvals/{id}/approve")
async def approve_approval(
    id: str, 
    body: DecisionActionBody, 
    db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(ApprovalAction).where(ApprovalAction.id == id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Approval action not found")
        
    if action.status != "pending":
        raise HTTPException(status_code=400, detail="Action is already decided")

    # Expiry Check
    if action.expires_at and action.expires_at < datetime.utcnow():
        action.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Action has expired and cannot be approved")

    # If review response is edited, update payload response draft
    if action.action_type == "review_response" and body.draft_response:
        new_payload = dict(action.payload)
        new_payload["draft_response"] = body.draft_response
        action.payload = new_payload

    # Set review details
    action.reviewed_by = "admin_operator"
    action.reviewed_at = datetime.utcnow()
    action.operator_notes = body.notes
    action.status = "executing"
    
    # Broadcast status change to 'executing'
    await db.commit()
    await ws_manager.broadcast({"type": "action_updated", "payload": {
        "id": action.id, "status": "executing", "agent": action.agent, "action_type": action.action_type
    }})

    # Execute action
    success, exec_msg = await execute_shop_action(action, db)
    
    if success:
        action.status = "executed"
        # Increment streak
        await update_agent_streak(action.agent, True, action.confidence_score, db)
    else:
        action.status = "failed"
        action.operator_notes = f"{action.operator_notes or ''} [Error: {exec_msg}]".strip()

    # Log to Audit Table
    financial_impact = action.impact.get("financial_impact", 0.0) if action.impact else 0.0
    audit_entry = AuditEntry(
        action_id=action.id,
        timestamp=datetime.utcnow(),
        agent=action.agent,
        action_type=action.action_type,
        decision="shadow" if action.shadow_mode else "approved",
        operator=action.reviewed_by,
        confidence_score=action.confidence_score,
        financial_impact=financial_impact,
        details={"notes": action.operator_notes, "execution_status": action.status, "payload": action.payload}
    )
    db.add(audit_entry)
    await db.commit()

    # Broadcast updated action
    updated_payload = {
        "id": action.id, 
        "status": action.status, 
        "agent": action.agent,
        "action_type": action.action_type,
        "reviewed_at": action.reviewed_at.isoformat() if action.reviewed_at else None
    }
    await ws_manager.broadcast({"type": "action_updated", "payload": updated_payload})
    
    return action

# 4. POST /api/approvals/{id}/reject
@app.post("/api/approvals/{id}/reject")
async def reject_approval(
    id: str, 
    body: RejectActionBody, 
    db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(ApprovalAction).where(ApprovalAction.id == id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Approval action not found")
        
    if action.status != "pending":
        raise HTTPException(status_code=400, detail="Action is already decided")

    action.reviewed_by = "admin_operator"
    action.reviewed_at = datetime.utcnow()
    action.rejection_reason = body.reason
    action.operator_notes = body.notes
    action.status = "rejected"
    
    # Rejection resets streak!
    await update_agent_streak(action.agent, False, action.confidence_score, db)

    # Log to Audit Table
    financial_impact = action.impact.get("financial_impact", 0.0) if action.impact else 0.0
    audit_entry = AuditEntry(
        action_id=action.id,
        timestamp=datetime.utcnow(),
        agent=action.agent,
        action_type=action.action_type,
        decision="rejected",
        operator=action.reviewed_by,
        confidence_score=action.confidence_score,
        financial_impact=financial_impact,
        details={"reason": action.rejection_reason, "notes": action.operator_notes}
    )
    db.add(audit_entry)
    await db.commit()

    # Broadcast updated action
    await ws_manager.broadcast({"type": "action_updated", "payload": {
        "id": action.id, 
        "status": "rejected", 
        "agent": action.agent, 
        "action_type": action.action_type,
        "reviewed_at": action.reviewed_at.isoformat() if action.reviewed_at else None
    }})
    
    return action

# 5. POST /api/approvals/batch - Batch approve or reject
@app.post("/api/approvals/batch")
async def batch_approvals(body: BatchActionBody, db: AsyncSession = Depends(get_db_session)):
    results = await db.execute(select(ApprovalAction).where(ApprovalAction.id.in_(body.ids)))
    actions = results.scalars().all()
    
    updated_actions = []
    
    for action in actions:
        if action.status != "pending":
            continue
            
        if body.action == "approve":
            # Safety Check: Batch approve is only allowed for low/medium risk items
            if action.risk_level in ["high", "critical"]:
                logger.warning(f"Skipping batch approval of high/critical risk action {action.id}")
                continue
                
            action.reviewed_by = "admin_operator"
            action.reviewed_at = datetime.utcnow()
            action.operator_notes = body.notes
            action.status = "executing"
            
            # Execute
            success, exec_msg = await execute_shop_action(action, db)
            action.status = "executed" if success else "failed"
            await update_agent_streak(action.agent, True, action.confidence_score, db)
            
            # Log Audit
            financial_impact = action.impact.get("financial_impact", 0.0) if action.impact else 0.0
            db.add(AuditEntry(
                action_id=action.id,
                timestamp=datetime.utcnow(),
                agent=action.agent,
                action_type=action.action_type,
                decision="shadow" if action.shadow_mode else "approved",
                operator=action.reviewed_by,
                confidence_score=action.confidence_score,
                financial_impact=financial_impact,
                details={"notes": action.operator_notes, "execution_status": action.status, "batch": True}
            ))
            
        elif body.action == "reject":
            action.reviewed_by = "admin_operator"
            action.reviewed_at = datetime.utcnow()
            action.rejection_reason = body.reason or "Batch rejected"
            action.operator_notes = body.notes
            action.status = "rejected"
            await update_agent_streak(action.agent, False, action.confidence_score, db)
            
            # Log Audit
            financial_impact = action.impact.get("financial_impact", 0.0) if action.impact else 0.0
            db.add(AuditEntry(
                action_id=action.id,
                timestamp=datetime.utcnow(),
                agent=action.agent,
                action_type=action.action_type,
                decision="rejected",
                operator=action.reviewed_by,
                confidence_score=action.confidence_score,
                financial_impact=financial_impact,
                details={"reason": action.rejection_reason, "notes": action.operator_notes, "batch": True}
            ))
            
        updated_actions.append(action)
        # Broadcast immediately
        await ws_manager.broadcast({"type": "action_updated", "payload": {
            "id": action.id, "status": action.status, "agent": action.agent, "action_type": action.action_type
        }})
        
    await db.commit()
    return {"message": f"Processed {len(updated_actions)} batch actions", "affected_ids": [a.id for a in updated_actions]}

# 6. GET /api/audit - Paginated audit trails
@app.get("/api/audit")
async def get_audit_logs(
    agent: Optional[str] = None,
    decision: Optional[str] = None,
    operator: Optional[str] = None,
    action_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session)
):
    query = select(AuditEntry)
    
    # Filter joins / joins aren't strictly necessary if we query both or filter
    # To keep it performant, we construct basic filters on AuditEntry
    if agent and agent != "all":
        query = query.where(AuditEntry.agent == agent)
    if decision and decision != "all":
        query = query.where(AuditEntry.decision == decision)
    if operator and operator != "all":
        query = query.where(AuditEntry.operator == operator)
    if action_type and action_type != "all":
        query = query.where(AuditEntry.action_type == action_type)
        
    # Sort by timestamp desc
    query = query.order_by(desc(AuditEntry.timestamp))
    
    # Pagination
    offset = (page - 1) * limit
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total_count = total_res.scalar() or 0
    
    # Execute query
    query = query.offset(offset).limit(limit)
    res = await db.execute(query)
    entries = res.scalars().all()
    
    # Return entries + total
    return {
        "entries": entries,
        "total": total_count,
        "page": page,
        "limit": limit
    }

# 7. GET /api/agents/status
@app.get("/api/agents/status")
async def get_agents_status(db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(AgentStatus))
    statuses = res.scalars().all()
    return statuses

# 8. GET /api/settings
@app.get("/api/settings")
async def get_store_settings(db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(StoreSettings).where(StoreSettings.id == 1))
    store_settings = res.scalar_one_or_none()
    return store_settings

# 9. PATCH /api/settings - Update settings (creates audit log)
@app.patch("/api/settings")
async def update_store_settings(body: SettingsUpdateBody, db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(StoreSettings).where(StoreSettings.id == 1))
    store_settings = res.scalar_one_or_none()
    if not store_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
        
    changes = {}
    if body.shadow_mode is not None:
        changes["shadow_mode"] = f"{store_settings.shadow_mode} -> {body.shadow_mode}"
        store_settings.shadow_mode = body.shadow_mode
        # Also update AgentStatus shadow/supervised autonomy level
        autonomy = "shadow" if body.shadow_mode else "supervised"
        await db.execute(update(AgentStatus).values(autonomy_level=autonomy))
        
    if body.fraud_threshold is not None:
        changes["fraud_threshold"] = f"{store_settings.fraud_threshold} -> {body.fraud_threshold}"
        store_settings.fraud_threshold = body.fraud_threshold
    if body.po_limit is not None:
        changes["po_limit"] = f"{store_settings.po_limit} -> {body.po_limit}"
        store_settings.po_limit = body.po_limit
    if body.pricing_limit is not None:
        changes["pricing_limit"] = f"{store_settings.pricing_limit} -> {body.pricing_limit}"
        store_settings.pricing_limit = body.pricing_limit
    if body.reviews_rating_threshold is not None:
        changes["reviews_rating_threshold"] = f"{store_settings.reviews_rating_threshold} -> {body.reviews_rating_threshold}"
        store_settings.reviews_rating_threshold = body.reviews_rating_threshold
        
    # Write settings change to audit log
    audit_entry = AuditEntry(
        action_id=None,
        timestamp=datetime.utcnow(),
        agent="System",
        action_type="settings_change",
        decision="approved",
        operator="admin_operator",
        confidence_score=1.0,
        financial_impact=0.0,
        details={"changes": changes}
    )
    db.add(audit_entry)
    await db.commit()
    
    # Broadcast to websockets
    await ws_manager.broadcast({"type": "agent_status", "payload": {"settings_updated": True}})
    
    return store_settings

# 10. GET /api/analytics - Aggregates for dashboard charts
@app.get("/api/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db_session)):
    # 1. Total actions and approval rate in last 30 days
    # Decision counts
    approved_res = await db.execute(select(func.count(AuditEntry.id)).where(AuditEntry.decision.in_(["approved", "shadow"])))
    approved_count = approved_res.scalar() or 0
    
    rejected_res = await db.execute(select(func.count(AuditEntry.id)).where(AuditEntry.decision == "rejected"))
    rejected_count = rejected_res.scalar() or 0
    
    auto_res = await db.execute(select(func.count(AuditEntry.id)).where(AuditEntry.decision == "auto-approved"))
    auto_count = auto_res.scalar() or 0
    
    total_decisions = approved_count + rejected_count + auto_count
    approval_rate = (approved_count / (approved_count + rejected_count) * 100) if (approved_count + rejected_count) > 0 else 100.0

    # 2. Agent graduation & streaking
    res_agents = await db.execute(select(AgentStatus))
    agents = res_agents.scalars().all()

    # 3. Financial impact approved
    financial_res = await db.execute(select(func.sum(AuditEntry.financial_impact)).where(AuditEntry.decision.in_(["approved", "shadow", "auto-approved"])))
    total_financial = financial_res.scalar() or 0.0

    # 4. Risk distribution count
    pending_actions = await db.execute(select(ApprovalAction).where(ApprovalAction.status == "pending"))
    pending_list = pending_actions.scalars().all()
    risk_dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for a in pending_list:
        risk_dist[a.risk_level] = risk_dist.get(a.risk_level, 0) + 1

    # 5. Charts: Approval rate over time per agent (last 7 days mock timeline)
    # Generate realistic historical timeline for charts
    timeline = []
    now = datetime.utcnow()
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%b %d")
        timeline.append({
            "date": day_str,
            "FraudAgent": 90 + (i % 3) * 3,
            "InventoryAgent": 80 + (i % 2) * 5,
            "PricingAgent": 95 - (i % 4) * 2,
            "ReviewsAgent": 88 + (i % 3) * 4,
            "MarketingAgent": 70 + (i % 2) * 8
        })

    # 6. Action volume by agent (last 7 days stacked)
    volume_by_agent = [
        {"day": "Mon", "Fraud": 12, "Inventory": 4, "Pricing": 18, "Reviews": 25, "Marketing": 2},
        {"day": "Tue", "Fraud": 15, "Inventory": 8, "Pricing": 22, "Reviews": 30, "Marketing": 3},
        {"day": "Wed", "Fraud": 9, "Inventory": 6, "Pricing": 15, "Reviews": 28, "Marketing": 1},
        {"day": "Thu", "Fraud": 18, "Inventory": 12, "Pricing": 24, "Reviews": 35, "Marketing": 4},
        {"day": "Fri", "Fraud": 14, "Inventory": 5, "Pricing": 20, "Reviews": 32, "Marketing": 2},
        {"day": "Sat", "Fraud": 8, "Inventory": 2, "Pricing": 12, "Reviews": 18, "Marketing": 1},
        {"day": "Sun", "Fraud": 11, "Inventory": 3, "Pricing": 14, "Reviews": 22, "Marketing": 3}
    ]

    # 7. Decision time distribution histogram counts
    decision_times = {
        "under_1m": 45,
        "1m_5m": 28,
        "5m_30m": 12,
        "over_30m": 8
    }

    return {
        "summary": {
            "total_decisions": total_decisions,
            "approval_rate": round(approval_rate, 1),
            "actions_auto_approved": auto_count,
            "total_financial_impact": round(total_financial, 2),
            "avg_confidence": 0.89,
            "avg_decision_time_minutes": 4.2
        },
        "graduation": [
            {
                "agent_id": a.agent_id,
                "streak": a.streak,
                "autonomy_level": a.autonomy_level,
                "total_decisions": a.total_decisions,
                "avg_confidence": round(a.avg_confidence, 2)
            } for a in agents
        ],
        "risk_distribution": risk_dist,
        "charts": {
            "approval_rate_over_time": timeline,
            "volume_by_agent": volume_by_agent,
            "decision_time_dist": decision_times
        }
    }

# 11. POST /api/run - Trigger supervisor pipeline and capture generated actions
# Helper mapper for decisions
DECISION_TYPE_MAP = {
    "HOLD_ORDER": "fraud_hold",
    "DRAFT_PO": "purchase_order",
    "UPDATE_PRICE": "price_change",
    "POST_REVIEW_RESPONSE": "review_response",
    "DRAFT_MARKETING_CAMPAIGN": "marketing_campaign"
}

async def run_pipeline_task(run_id: str, db_settings: StoreSettings):
    """Asynchronous background task to execute LangGraph and capture decisions into DB."""
    logger.info(f"Starting async pipeline run execution for ID {run_id}")
    
    # We will generate interesting randomized mock state data so that runs create new actions
    # This keeps the dashboard live and interactive!
    import random
    
    # Pick a random item type to add
    seed_choice = random.choice(["fraud", "inventory", "price", "review", "marketing", "all"])
    
    inventory_data = [
        {"sku": "TSHIRT-BLUE-L", "stock": random.randint(1, 15), "price": 25.0, "variant_id": "v1"},
        {"sku": "MUG-WHITE", "stock": random.randint(1, 8), "price": 12.0, "variant_id": "v2"}
    ]
    
    # Add a product nearing stockout if chosen
    if seed_choice == "inventory" or seed_choice == "all":
        inventory_data.append({"sku": "SILK-PILLOW-SLV", "stock": 1, "price": 49.0, "variant_id": "v3"})
        
    active_orders = []
    if seed_choice == "fraud" or seed_choice == "all":
        active_orders.append({"id": "o_suspicious", "line_items": [{"sku": "TSHIRT-BLUE-L", "quantity": 1}], "order_total": 450.0})
    else:
        active_orders.append({"id": f"o_{random.randint(100, 999)}", "line_items": [{"sku": "MUG-WHITE", "quantity": 2}], "order_total": 24.0})
        
    reviews_data = []
    if seed_choice == "review" or seed_choice == "all":
        reviews_data.append({"id": f"r_{random.randint(100, 999)}", "content": "The shipping was delayed and box was damaged!", "rating": 2})
    else:
        reviews_data.append({"id": f"r_{random.randint(100, 999)}", "content": "Good material, very soft.", "rating": 5})

    initial_state = {
        "inventory_data": inventory_data,
        "active_orders": active_orders,
        "reviews_data": reviews_data,
        "decisions": [],
        "hitl_queue": [],
        "messages": [],
        "errors": [],
        "run_id": run_id,
        "timestamp": datetime.utcnow()
    }

    try:
        # Run graph
        supervisor = Supervisor()
        final_state = await supervisor.run(initial_state)
        
        # Save decisions generated in state
        decisions_list = final_state.get("decisions", [])
        logger.info(f"Pipeline finished. Captured {len(decisions_list)} decisions.")
        
        # Process decisions and save to database
        async with async_session_factory() as session:
            # Re-fetch settings
            res_set = await session.execute(select(StoreSettings).where(StoreSettings.id == 1))
            settings = res_set.scalar_one()
            
            new_actions_count = 0
            for d in decisions_list:
                # Map action type
                mapped_type = DECISION_TYPE_MAP.get(d.action_type, "marketing_campaign")
                
                # Check safety
                requires_hitl, risk_level, financial_impact = evaluate_action_safety(
                    d.agent_id, mapped_type, d.action_data, d.confidence_score, settings
                )
                
                # Prepare payload
                payload = {}
                evidence = []
                impact = {
                    "financial_impact": financial_impact,
                    "affected_skus": [],
                    "affected_orders": [],
                    "reversible": True,
                    "reversal_window_hours": 24
                }
                
                # Format payload & evidence based on agent
                if d.agent_id == "FraudAgent":
                    payload = {
                        "order_id": d.action_data.get("order_id", "ORD-UNKNOWN"),
                        "customer_name": "Valued Customer",
                        "customer_email": "customer@vpnmail.net",
                        "order_total": financial_impact,
                        "fraud_score": d.action_data.get("risk_score", 85),
                        "risk_signals": d.action_data.get("risk_factors", ["IP/Shipping Address Mismatch"]),
                        "recommended_action": "hold"
                    }
                    evidence = [
                        {"label": "Risk Score", "value": f"{payload['fraud_score']}/100", "weight": "primary", "source": "FraudHeuristics"},
                        {"label": "Risk Signals", "value": ", ".join(payload["risk_signals"]), "weight": "supporting", "source": "FraudAgent"}
                    ]
                    impact["affected_orders"] = [payload["order_id"]]
                    
                elif d.agent_id == "InventoryAgent":
                    qty = d.action_data.get("quantity_to_order", 75)
                    payload = {
                        "sku": d.action_data.get("sku", "TSHIRT-BLUE-L"),
                        "product_name": f"Product ({d.action_data.get('sku')})",
                        "current_stock": 5,
                        "daily_velocity": 2.5,
                        "days_of_supply": 2.0,
                        "reorder_quantity": qty,
                        "supplier_name": "Default Supplier",
                        "unit_cost": 15.00,
                        "total_po_value": qty * 15.00
                    }
                    evidence = [
                        {"label": "Reorder Quantity", "value": str(qty), "weight": "primary", "source": "InventoryAgent"},
                        {"label": "Stockout Prediction", "value": f"Predicted in {d.action_data.get('predicted_stockout_days', 2.0):.1f} days", "weight": "supporting", "source": "InventoryForecaster"}
                    ]
                    impact["affected_skus"] = [payload["sku"]]
                    
                elif d.agent_id == "PricingAgent":
                    payload = {
                        "sku": d.action_data.get("sku", "TSHIRT-BLUE-L"),
                        "product_name": f"Product ({d.action_data.get('sku')})",
                        "current_price": d.action_data.get("old_price", 25.00),
                        "proposed_price": d.action_data.get("new_price", 22.50),
                        "change_percent": -10.0,
                        "reasoning": d.reasoning,
                        "competitor_prices": [{"competitor": "Competitor Shop", "price": 22.50}]
                    }
                    evidence = [
                        {"label": "Old Price", "value": f"${payload['current_price']:.2f}", "weight": "supporting", "source": "Shopify API"},
                        {"label": "Proposed Price", "value": f"${payload['proposed_price']:.2f}", "weight": "primary", "source": "PricingAgent"},
                        {"label": "Competitor Match", "value": "Competitor at $22.50", "weight": "supporting", "source": "CompetitorScraper"}
                    ]
                    impact["affected_skus"] = [payload["sku"]]
                    
                elif d.agent_id == "ReviewsAgent":
                    payload = {
                        "review_id": d.action_data.get("review_id", "rev-99"),
                        "product_name": "Product Premium",
                        "rating": reviews_data[0]["rating"] if reviews_data else 3,
                        "review_text": reviews_data[0]["content"] if reviews_data else "Okay product.",
                        "customer_name": "Marcus Vance",
                        "sentiment": d.action_data.get("sentiment", "Negative"),
                        "draft_response": d.action_data.get("response_content", "Draft response..."),
                        "key_issues": d.action_data.get("themes", ["Support"])
                    }
                    evidence = [
                        {"label": "Review Rating", "value": f"{payload['rating']}/5 stars", "weight": "primary", "source": "Shopify API"},
                        {"label": "Draft Response", "value": payload["draft_response"], "weight": "supporting", "source": "ReviewsAgent LLM"}
                    ]
                    
                elif d.agent_id == "MarketingAgent":
                    payload = {
                        "campaign_name": f"Campaign for {d.action_data.get('sku')}",
                        "target_skus": [d.action_data.get("sku", "TSHIRT-BLUE-L")],
                        "discount_percent": 15.0,
                        "urgency_reason": d.reasoning,
                        "estimated_reach": 3000,
                        "draft_message": d.action_data.get("draft_copy", "Draft marketing copy...")
                    }
                    evidence = [
                        {"label": "Draft Message", "value": payload["draft_message"], "weight": "primary", "source": "MarketingAgent LLM"},
                        {"label": "Trigger Reason", "value": d.reasoning, "weight": "supporting", "source": "MarketingAgent"}
                    ]
                    impact["affected_skus"] = payload["target_skus"]

                # If requires_hitl is True or settings is shadow mode, we store as "pending"
                # Otherwise, we auto-approve!
                status = "pending"
                if not requires_hitl and not settings.shadow_mode:
                    status = "executed" # Auto-execute
                
                action_id = str(uuid.uuid4())
                action_obj = ApprovalAction(
                    id=action_id,
                    agent=d.agent_id,
                    action_type=mapped_type,
                    status=status,
                    risk_level=risk_level,
                    confidence_score=d.confidence_score,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=2),
                    requires_hitl=requires_hitl,
                    shadow_mode=settings.shadow_mode,
                    payload=payload,
                    evidence=evidence,
                    impact=impact
                )
                session.add(action_obj)
                
                # If auto-approved, write an audit log
                if status == "executed":
                    audit_entry = AuditEntry(
                        action_id=action_id,
                        timestamp=datetime.utcnow(),
                        agent=d.agent_id,
                        action_type=mapped_type,
                        decision="auto-approved",
                        operator=None,
                        confidence_score=d.confidence_score,
                        financial_impact=financial_impact,
                        details={"notes": "Automatically approved by safety system", "payload": payload}
                    )
                    session.add(audit_entry)
                    await update_agent_streak(d.agent_id, True, d.confidence_score, session)
                
                new_actions_count += 1
                
            await session.commit()
            
            # Broadcast pipeline completion
            await ws_manager.broadcast({
                "type": "pipeline_completed", 
                "payload": {"run_id": run_id, "action_count": new_actions_count}
            })
            
    except Exception as e:
        logger.error(f"Error in pipeline run task: {e}")
        await ws_manager.broadcast({"type": "pipeline_failed", "payload": {"run_id": run_id, "error": str(e)}})

@app.post("/api/run")
async def trigger_run(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db_session)):
    """Triggers an operations cycle, running agents and generating queue items."""
    run_id = str(uuid.uuid4())
    
    # Fetch settings
    res = await db.execute(select(StoreSettings).where(StoreSettings.id == 1))
    db_settings = res.scalar_one()

    # Trigger WebSocket run start notification
    await ws_manager.broadcast({"type": "pipeline_started", "payload": {"run_id": run_id}})

    # Run in background to prevent request timeout
    background_tasks.add_task(run_pipeline_task, run_id, db_settings)
    
    return {"message": "Operations cycle triggered", "run_id": run_id}

# Static Files serving React App Build
# FastAPI can serve static files. Mount this last to avoid route conflicts.
# If frontend files exist, we serve them. Otherwise, print warning.
dist_path = "dashboard/dist"
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")
    logger.info(f"Mounted static frontend files from {dist_path}")
else:
    logger.warning(f"Static frontend path '{dist_path}' not found. Please compile dashboard.")
