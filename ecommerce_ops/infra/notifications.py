import logging
from typing import Optional
from datetime import datetime

from ecommerce_ops.config import settings
from ecommerce_ops.api.ws import ws_manager

logger = logging.getLogger("ecommerce_ops.infra.notifications")


async def notify_hitl_request(
    agent: str,
    action_id: str,
    action_type: str,
    risk_level: str,
    confidence: float,
):
    msg = (
        f"[HITL] {agent} — {action_type} (risk: {risk_level}, conf: {confidence:.2f})\n"
        f"Action ID: {action_id}"
    )
    logger.info("NOTIFY: %s", msg)
    await _send_slack(msg) if settings.SLACK_BOT_TOKEN else None
    await ws_manager.broadcast({
        "type": "notification",
        "payload": {
            "kind": "hitl_request",
            "agent": agent,
            "action_id": action_id,
            "action_type": action_type,
            "risk_level": risk_level,
            "confidence": confidence,
            "message": msg,
        },
    })


async def notify_pipeline_failed(
    run_id: str,
    error: str,
):
    msg = f"[FAIL] Pipeline {run_id} failed: {error}"
    logger.error("NOTIFY: %s", msg)
    await _send_slack(msg) if settings.SLACK_BOT_TOKEN else None
    await ws_manager.broadcast({
        "type": "notification",
        "payload": {"kind": "pipeline_failed", "run_id": run_id, "error": error, "message": msg},
    })


async def notify_agent_graduated(
    agent: str,
    new_level: str,
    streak: int,
):
    msg = f"[GRADUATE] {agent} promoted to {new_level} (streak: {streak})"
    logger.info("NOTIFY: %s", msg)
    await _send_slack(msg) if settings.SLACK_BOT_TOKEN else None
    await ws_manager.broadcast({
        "type": "notification",
        "payload": {
            "kind": "agent_graduated",
            "agent": agent,
            "new_level": new_level,
            "streak": streak,
            "message": msg,
        },
    })


async def notify_daily_summary(stats: dict):
    msg = (
        f"[DAILY] Pipeline runs: {stats.get('runs', 0)}, "
        f"decisions: {stats.get('decisions', 0)}, "
        f"pending HITL: {stats.get('pending_hitl', 0)}"
    )
    logger.info("NOTIFY: %s", msg)
    await _send_slack(msg) if settings.SLACK_BOT_TOKEN else None


async def _send_slack(message: str):
    if not settings.SLACK_BOT_TOKEN:
        return
    try:
        token = settings.SLACK_BOT_TOKEN.get_secret_value()
        channel = settings.SLACK_CHANNEL or "#general"
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"channel": channel, "text": message},
            )
    except Exception as e:
        logger.warning("Slack notification failed: %s", e)
