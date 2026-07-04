"""Tests for pipeline/runner.py and pipeline/builder.py."""
import uuid
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from ecommerce_ops.pipeline.builder import build_payload_and_evidence
from ecommerce_ops.pipeline.runner import (
    DECISION_TYPE_MAP,
    execute_shop_action,
    update_agent_streak,
)


# ── builder.py tests ───────────────────────────────────────


def _make_decision(agent_id, action_data=None, reasoning="test reasoning"):
    return SimpleNamespace(
        agent_id=agent_id,
        action_data=action_data or {},
        reasoning=reasoning,
    )


class TestBuildPayloadAndEvidence:
    def test_fraud_agent_payload(self):
        d = _make_decision("FraudAgent", {"order_id": "ORD-123", "risk_score": 90})
        payload, evidence = build_payload_and_evidence(d, [])
        assert payload["order_id"] == "ORD-123"
        assert payload["fraud_score"] == 90
        assert payload["recommended_action"] == "hold"
        assert len(evidence) == 2
        assert evidence[0]["label"] == "Risk Score"

    def test_fraud_agent_default_order_id(self):
        d = _make_decision("FraudAgent", {})
        payload, _ = build_payload_and_evidence(d, [])
        assert payload["order_id"] == "ORD-UNKNOWN"

    def test_inventory_agent_payload(self):
        d = _make_decision("InventoryAgent", {"sku": "SKU-1", "quantity_to_order": 100})
        payload, evidence = build_payload_and_evidence(d, [])
        assert payload["sku"] == "SKU-1"
        assert payload["reorder_quantity"] == 100
        assert payload["total_po_value"] == 1500.0

    def test_inventory_agent_default_qty(self):
        d = _make_decision("InventoryAgent", {})
        payload, _ = build_payload_and_evidence(d, [])
        assert payload["reorder_quantity"] == 75

    def test_pricing_agent_payload(self):
        d = _make_decision("PricingAgent", {"sku": "SKU-2", "old_price": 50, "new_price": 45})
        payload, evidence = build_payload_and_evidence(d, [])
        assert payload["sku"] == "SKU-2"
        assert payload["current_price"] == 50
        assert payload["proposed_price"] == 45

    def test_reviews_agent_with_reviews(self):
        d = _make_decision("ReviewsAgent", {"review_id": "rev-1", "sentiment": "negative"})
        reviews = [{"content": "Bad product", "rating": 2}]
        payload, evidence = build_payload_and_evidence(d, reviews)
        assert payload["review_id"] == "rev-1"
        assert payload["rating"] == 2
        assert payload["review_text"] == "Bad product"

    def test_reviews_agent_no_reviews(self):
        d = _make_decision("ReviewsAgent", {})
        payload, _ = build_payload_and_evidence(d, [])
        assert payload["rating"] == 3

    def test_marketing_agent_fallback(self):
        d = _make_decision("MarketingAgent", {"sku": "SKU-3", "draft_copy": "Buy now!"})
        payload, evidence = build_payload_and_evidence(d, [])
        assert payload["campaign_name"] == "Campaign for SKU-3"
        assert payload["discount_percent"] == 15.0
        assert len(evidence) == 2

    def test_unknown_agent_uses_marketing_fallback(self):
        d = _make_decision("UnknownAgent", {"sku": "SKU-X"})
        payload, _ = build_payload_and_evidence(d, [])
        assert "campaign_name" in payload


# ── runner.py tests ────────────────────────────────────────


class TestDecisonTypeMap:
    def test_all_keys_mapped(self):
        expected = {"HOLD_ORDER", "DRAFT_PO", "UPDATE_PRICE", "POST_REVIEW_RESPONSE", "DRAFT_MARKETING_CAMPAIGN"}
        assert set(DECISION_TYPE_MAP.keys()) == expected

    def test_all_values_are_strings(self):
        for v in DECISION_TYPE_MAP.values():
            assert isinstance(v, str)


class TestExecuteShopAction:
    @pytest.mark.asyncio
    async def test_shadow_mode_returns_true(self):
        action = MagicMock()
        action.shadow_mode = True
        action.action_type = "fraud_hold"
        action.id = "test-id"
        success, msg = await execute_shop_action(action)
        assert success is True
        assert "Shadow" in msg

    @pytest.mark.asyncio
    async def test_live_mode_returns_true(self):
        action = MagicMock()
        action.shadow_mode = False
        action.action_type = "price_change"
        action.id = "test-id"
        success, msg = await execute_shop_action(action)
        assert success is True
        assert "Executed" in msg


class TestUpdateAgentStreak:
    @pytest.mark.asyncio
    async def test_approved_increments_streak(self):
        session = AsyncMock()
        status = MagicMock()
        status.total_decisions = 10
        status.total_approvals = 8
        status.total_rejections = 2
        status.streak = 5
        status.autonomy_level = "supervised"
        status.avg_confidence = 0.85

        result = MagicMock()
        result.scalar_one_or_none.return_value = status
        session.execute.return_value = result

        await update_agent_streak("FraudAgent", True, 0.96, session)

        assert status.total_decisions == 11
        assert status.total_approvals == 9
        assert status.streak == 6
        session.add.assert_called_once_with(status)

    @pytest.mark.asyncio
    async def test_rejected_resets_streak(self):
        session = AsyncMock()
        status = MagicMock()
        status.total_decisions = 10
        status.total_approvals = 8
        status.total_rejections = 2
        status.streak = 5
        status.autonomy_level = "supervised"
        status.avg_confidence = 0.85

        result = MagicMock()
        result.scalar_one_or_none.return_value = status
        session.execute.return_value = result

        await update_agent_streak("FraudAgent", False, 0.5, session)

        assert status.total_rejections == 3
        assert status.streak == 0
        assert status.autonomy_level == "supervised"

    @pytest.mark.asyncio
    async def test_graduation_to_autonomous(self):
        session = AsyncMock()
        status = MagicMock()
        status.total_decisions = 49
        status.total_approvals = 48
        status.streak = 49
        status.autonomy_level = "supervised"
        status.avg_confidence = 0.90

        result = MagicMock()
        result.scalar_one_or_none.return_value = status
        session.execute.return_value = result

        with patch("ecommerce_ops.pipeline.runner.notify_agent_graduated", new_callable=AsyncMock):
            await update_agent_streak("FraudAgent", True, 0.99, session)

        assert status.streak == 50
        assert status.autonomy_level == "autonomous"

    @pytest.mark.asyncio
    async def test_nonexistent_agent_does_nothing(self):
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session.execute.return_value = result

        await update_agent_streak("NonexistentAgent", True, 0.9, session)
        session.add.assert_not_called()
