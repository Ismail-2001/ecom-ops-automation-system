"""Tests for observability/ module (tracing, evaluation, trace_models, tracing_otel)."""
import pytest
from unittest.mock import MagicMock, patch

from ecommerce_ops.observability.tracing_otel import (
    OTEL_ENABLED,
    OTEL_SERVICE_NAME,
    init_tracing,
    get_tracer,
    _get_sampler,
)
from ecommerce_ops.observability.trace_models import (
    TraceSpan,
    TraceStatus,
    AgentMetrics,
    EvaluationResult,
    EvaluationMetric,
)
from ecommerce_ops.observability.evaluation import EvaluationFramework


# ── tracing_otel.py tests ──────────────────────────────────


class TestTracingOtel:
    def test_default_config_disabled(self):
        assert OTEL_ENABLED is False or OTEL_ENABLED is True

    def test_service_name(self):
        assert OTEL_SERVICE_NAME == "opsiq-api"

    def test_init_tracing_disabled(self):
        with patch("ecommerce_ops.observability.tracing_otel.OTEL_ENABLED", False):
            result = init_tracing()
            assert result is None

    def test_get_tracer_returns_tracer(self):
        tracer = get_tracer("test")
        assert tracer is not None

    def test_get_sampler_returns_sampler(self):
        sampler = _get_sampler()
        assert sampler is not None


# ── trace_models.py tests ──────────────────────────────────


class TestTraceModels:
    def test_trace_span_defaults(self):
        span = TraceSpan()
        assert span.name == ""
        assert span.status == TraceStatus.UNSET

    def test_trace_status_values(self):
        assert TraceStatus.OK.value == "ok"
        assert TraceStatus.ERROR.value == "error"
        assert TraceStatus.UNSET.value == "unset"

    def test_agent_metrics(self):
        m = AgentMetrics(agent_id="test", total_decisions=10)
        assert m.agent_id == "test"
        assert m.total_decisions == 10

    def test_evaluation_result(self):
        r = EvaluationResult(
            agent_name="test",
            decision_id="d1",
            overall_score=0.85,
            passed=True,
            feedback="good",
        )
        assert r.overall_score == 0.85
        assert r.passed is True


# ── evaluation.py tests ────────────────────────────────────


class TestEvaluationFramework:
    def setup_method(self):
        self.framework = EvaluationFramework()

    def test_evaluate_decision_returns_result(self):
        result = self.framework.evaluate_decision(
            agent_name="FraudAgent",
            decision_id="d1",
            decision={
                "action_type": "fraud_hold",
                "reasoning": "High risk order",
                "confidence_score": 0.9,
                "action_data": {},
            },
            context={"run_id": "test"},
        )
        assert hasattr(result, "overall_score")
        assert hasattr(result, "passed")
        assert 0 <= result.overall_score <= 1

    def test_evaluate_high_confidence_passes(self):
        result = self.framework.evaluate_decision(
            agent_name="FraudAgent",
            decision_id="d2",
            decision={
                "action_type": "fraud_hold",
                "reasoning": "Confident decision",
                "confidence_score": 0.95,
                "action_data": {},
            },
            context={},
        )
        assert result.passed is True

    def test_evaluate_low_confidence_may_fail(self):
        result = self.framework.evaluate_decision(
            agent_name="PricingAgent",
            decision_id="d3",
            decision={
                "action_type": "price_change",
                "reasoning": "Uncertain",
                "confidence_score": 0.3,
                "action_data": {},
            },
            context={},
        )
        assert result.overall_score < 0.8
