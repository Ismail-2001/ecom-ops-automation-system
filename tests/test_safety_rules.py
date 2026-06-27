import pytest
from ecommerce_ops.safety.safety_rules import evaluate_action_safety
from ecommerce_ops.models.db import StoreSettings


@pytest.fixture
def settings():
    return StoreSettings(
        id=1,
        shadow_mode=False,
        fraud_threshold=70,
        po_limit=1000.0,
        pricing_limit=5.0,
        reviews_rating_threshold=4,
    )


class TestFraudSafety:
    def test_fraud_always_requires_hitl(self, settings):
        requires_hitl, risk_level, impact = evaluate_action_safety(
            agent_id="FraudAgent",
            action_type="fraud_hold",
            action_data={"order_total": 500.0},
            confidence=0.9,
            settings=settings,
        )
        assert requires_hitl is True
        assert risk_level == "high"
        assert impact == 500.0

    def test_fraud_impact_from_order_total(self, settings):
        _, _, impact = evaluate_action_safety(
            agent_id="FraudAgent",
            action_type="fraud_hold",
            action_data={"order_total": 2500.0},
            confidence=0.95,
            settings=settings,
        )
        assert impact == 2500.0


class TestInventorySafety:
    def test_po_below_limit_auto_approves(self, settings):
        requires_hitl, risk_level, impact = evaluate_action_safety(
            agent_id="InventoryAgent",
            action_type="purchase_order",
            action_data={"total_po_value": 500.0},
            confidence=0.85,
            settings=settings,
        )
        assert requires_hitl is False
        assert risk_level == "low"
        assert impact == -500.0

    def test_po_above_limit_requires_hitl(self, settings):
        requires_hitl, risk_level, impact = evaluate_action_safety(
            agent_id="InventoryAgent",
            action_type="purchase_order",
            action_data={"total_po_value": 1500.0},
            confidence=0.85,
            settings=settings,
        )
        assert requires_hitl is True
        assert risk_level == "medium"

    def test_po_well_above_limit_is_high_risk(self, settings):
        requires_hitl, risk_level, _ = evaluate_action_safety(
            agent_id="InventoryAgent",
            action_type="purchase_order",
            action_data={"total_po_value": 6000.0},
            confidence=0.85,
            settings=settings,
        )
        assert requires_hitl is True
        assert risk_level == "high"

    def test_po_falls_back_to_qty_times_cost(self, settings):
        _, _, impact = evaluate_action_safety(
            agent_id="InventoryAgent",
            action_type="purchase_order",
            action_data={"quantity_to_order": 100},
            confidence=0.85,
            settings=settings,
        )
        assert impact == -2000.0


class TestPricingSafety:
    def test_small_change_auto_approves(self, settings):
        requires_hitl, risk_level, _ = evaluate_action_safety(
            agent_id="PricingAgent",
            action_type="price_change",
            action_data={"old_price": 100.0, "new_price": 103.0},
            confidence=0.85,
            settings=settings,
        )
        assert requires_hitl is False
        assert risk_level == "low"

    def test_moderate_change_requires_hitl(self, settings):
        requires_hitl, risk_level, _ = evaluate_action_safety(
            agent_id="PricingAgent",
            action_type="price_change",
            action_data={"old_price": 100.0, "new_price": 110.0},
            confidence=0.85,
            settings=settings,
        )
        assert requires_hitl is True
        assert risk_level == "medium"

    def test_large_change_is_high_risk(self, settings):
        requires_hitl, risk_level, _ = evaluate_action_safety(
            agent_id="PricingAgent",
            action_type="price_change",
            action_data={"old_price": 100.0, "new_price": 120.0},
            confidence=0.85,
            settings=settings,
        )
        assert requires_hitl is True
        assert risk_level == "high"

    def test_extreme_change_is_critical(self, settings):
        requires_hitl, risk_level, _ = evaluate_action_safety(
            agent_id="PricingAgent",
            action_type="price_change",
            action_data={"old_price": 100.0, "new_price": 130.0},
            confidence=0.85,
            settings=settings,
        )
        assert requires_hitl is True
        assert risk_level == "critical"


class TestReviewsSafety:
    def test_high_rating_auto_approves(self, settings):
        requires_hitl, risk_level, _ = evaluate_action_safety(
            agent_id="ReviewsAgent",
            action_type="review_response",
            action_data={"rating": 5},
            confidence=0.95,
            settings=settings,
        )
        assert requires_hitl is False
        assert risk_level == "low"

    def test_low_rating_requires_hitl(self, settings):
        requires_hitl, risk_level, _ = evaluate_action_safety(
            agent_id="ReviewsAgent",
            action_type="review_response",
            action_data={"rating": 2},
            confidence=0.95,
            settings=settings,
        )
        assert requires_hitl is True
        assert risk_level == "medium"


class TestMarketingSafety:
    def test_marketing_always_requires_hitl(self, settings):
        requires_hitl, risk_level, impact = evaluate_action_safety(
            agent_id="MarketingAgent",
            action_type="marketing_campaign",
            action_data={},
            confidence=0.85,
            settings=settings,
        )
        assert requires_hitl is True
        assert risk_level == "medium"
        assert impact == 0.0


class TestLowConfidenceEscalation:
    def test_low_confidence_escalates_low_risk(self, settings):
        requires_hitl, risk_level, _ = evaluate_action_safety(
            agent_id="PricingAgent",
            action_type="price_change",
            action_data={"old_price": 100.0, "new_price": 101.0},
            confidence=0.5,
            settings=settings,
        )
        assert risk_level == "medium"


class TestShadowModeOverrides:
    def test_shadow_mode_forces_hitl(self, settings):
        settings.shadow_mode = True
        requires_hitl, _, _ = evaluate_action_safety(
            agent_id="PricingAgent",
            action_type="price_change",
            action_data={"old_price": 100.0, "new_price": 101.0},
            confidence=0.95,
            settings=settings,
        )
        assert requires_hitl is True
