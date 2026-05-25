from prometheus_client import Counter, Histogram

METRIC_HTTP_REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
METRIC_HTTP_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)
METRIC_DECISIONS_CREATED = Counter(
    "agent_decisions_total", "Total agent decisions created", ["agent", "action_type"]
)
METRIC_DECISIONS_APPROVED = Counter(
    "agent_decisions_approved_total", "Total decisions approved", ["agent"]
)
METRIC_DECISIONS_REJECTED = Counter(
    "agent_decisions_rejected_total", "Total decisions rejected", ["agent"]
)
METRIC_PIPELINE_RUNS = Counter(
    "pipeline_runs_total", "Total pipeline runs", ["status"]
)
METRIC_LLM_CALL_DURATION = Histogram(
    "llm_call_duration_seconds", "LLM call duration", ["agent"]
)
