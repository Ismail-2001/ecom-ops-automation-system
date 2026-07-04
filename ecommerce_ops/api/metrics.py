from prometheus_client import Counter, Histogram, Gauge

METRIC_HTTP_REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
METRIC_HTTP_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration (seconds)", ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
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
METRIC_DECISIONS_AUTO_APPROVED = Counter(
    "agent_decisions_auto_approved_total", "Total decisions auto-approved", ["agent"]
)
METRIC_PIPELINE_RUNS = Counter(
    "pipeline_runs_total", "Total pipeline runs", ["status"]
)
METRIC_LLM_CALL_DURATION = Histogram(
    "llm_call_duration_seconds", "LLM call duration (seconds)", ["agent"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)
METRIC_LLM_CALLS = Counter(
    "llm_calls_total", "Total LLM calls", ["agent", "model"]
)
METRIC_ACTIVE_AGENTS = Gauge(
    "agent_active_total", "Number of active agents", ["agent"]
)
METRIC_DB_CONNECTION_POOL = Gauge(
    "db_connection_pool_size", "Database connection pool size"
)
METRIC_CACHE_HIT_RATIO = Gauge(
    "cache_hit_ratio", "Cache hit ratio (0-1)"
)
METRIC_QUEUE_DEPTH = Gauge(
    "task_queue_depth", "Current task queue depth"
)
METRIC_RATE_LIMIT_REJECTED = Counter(
    "rate_limit_rejected_total", "Total requests rejected by rate limiter"
)
METRIC_AGENT_CONFIDENCE_AVG = Gauge(
    "agent_decisions_confidence_avg", "Average confidence score per agent", ["agent"]
)
METRIC_HITL_QUEUE_DEPTH = Gauge(
    "hitl_queue_depth", "Current HITL queue depth"
)
METRIC_FINANCIAL_IMPACT = Counter(
    "financial_impact_total_dollars", "Total financial impact in dollars", ["agent", "action_type"]
)
METRIC_LLM_TOKENS_INPUT = Counter(
    "llm_tokens_input_total", "Total LLM input tokens consumed", ["agent", "model"]
)
METRIC_LLM_TOKENS_OUTPUT = Counter(
    "llm_tokens_output_total", "Total LLM output tokens consumed", ["agent", "model"]
)
METRIC_LLM_COST_DOLLARS = Counter(
    "llm_cost_dollars_total", "Total LLM API cost in USD", ["agent", "model"]
)
METRIC_LLM_DAILY_COST = Gauge(
    "llm_daily_cost_dollars", "Current day LLM spend in USD"
)
