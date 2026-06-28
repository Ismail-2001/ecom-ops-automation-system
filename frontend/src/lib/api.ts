const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, message: string, body?: unknown) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.body = body
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`
  const token =
    typeof window !== "undefined" ? localStorage.getItem("opsiq_api_key") : null

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  }

  const res = await fetch(url, { ...options, headers })

  if (!res.ok) {
    let body: unknown
    try {
      body = await res.json()
    } catch {
      body = await res.text()
    }
    throw new ApiError(res.status, `API ${res.status}: ${res.statusText}`, body)
  }

  const contentType = res.headers.get("content-type") || ""
  if (contentType.includes("application/json")) {
    return res.json() as Promise<T>
  }
  return res.text() as unknown as T
}

// ── Health ─────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  uptime_seconds: number
  version: string
  environment: string
  timestamp: string
  dependencies: Record<string, string>
  checks: Record<string, unknown>
}

export const healthApi = {
  check: () => request<HealthResponse>("/health"),
}

// ── Approvals ──────────────────────────────────────────────

export interface ApprovalAction {
  id: string
  action_type: string
  agent: string
  action: string
  rationale: string
  risk_level: string
  confidence: number
  financial_impact: number
  status: string
  shopify_entity_id: string | null
  shopify_entity_type: string | null
  suggested_response: string | null
  draft_response: string | null
  execution_result: string | null
  error_message: string | null
  executed_at: string | null
  expires_at: string | null
  metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ApprovalsQuery {
  agent?: string
  risk?: string
  status?: string
  search?: string
  sort?: string
}

export const approvalsApi = {
  list: (query?: ApprovalsQuery) => {
    const params = new URLSearchParams()
    if (query?.agent) params.set("agent", query.agent)
    if (query?.risk) params.set("risk", query.risk)
    if (query?.status) params.set("status", query.status)
    if (query?.search) params.set("search", query.search)
    if (query?.sort) params.set("sort", query.sort)
    const qs = params.toString()
    return request<ApprovalAction[]>(`/api/approvals${qs ? `?${qs}` : ""}`)
  },

  get: (id: string) => request<ApprovalAction>(`/api/approvals/${id}`),

  approve: (id: string, notes?: string) =>
    request<ApprovalAction>(`/api/approvals/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ notes: notes || "" }),
    }),

  reject: (id: string, reason: string) =>
    request<ApprovalAction>(`/api/approvals/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),

  batch: (ids: string[], action: "approve" | "reject", reason?: string) =>
    request<{ message: string; affected_ids: string[] }>("/api/approvals/batch", {
      method: "POST",
      body: JSON.stringify({ ids, action, reason: reason || "" }),
    }),
}

// ── Agents ─────────────────────────────────────────────────

export interface AgentStatus {
  name: string
  display_name: string
  status: string
  accuracy: number
  confidence: number
  processed_today: number
  last_activity: string
  uptime: number
  error_rate: number
  avg_response_time: number
}

export const agentsApi = {
  status: () => request<AgentStatus[]>("/api/agents/status"),
}

// ── Analytics ──────────────────────────────────────────────

export interface AnalyticsData {
  summary: {
    total_decisions: number
    approval_rate: number
    actions_auto_approved: number
    total_financial_impact: number
    avg_confidence: number
    avg_decision_time_minutes: number
  }
  graduation: Array<{
    agent_id: string
    streak: number
    autonomy_level: string
    total_decisions: number
    avg_confidence: number
  }>
  risk_distribution: {
    critical: number
    high: number
    medium: number
    low: number
  }
  charts: {
    approval_rate_over_time: Array<Record<string, unknown>>
    volume_by_agent: Array<Record<string, unknown>>
    decision_time_dist: Record<string, unknown>
  }
}

export const analyticsApi = {
  get: () => request<AnalyticsData>("/api/analytics"),
}

// ── Audit ──────────────────────────────────────────────────

export interface AuditEntry {
  action_id: string
  timestamp: string
  agent: string
  action_type: string
  decision: string
  operator: string
  confidence: number
  financial_impact: number
  details: Record<string, unknown>
}

export interface AuditResponse {
  entries: AuditEntry[]
  total: number
  page: number
  limit: number
}

export const auditApi = {
  list: (params?: { page?: number; limit?: number; agent?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set("page", String(params.page))
    if (params?.limit) searchParams.set("limit", String(params.limit))
    if (params?.agent) searchParams.set("agent", params.agent)
    const qs = searchParams.toString()
    return request<AuditResponse>(`/api/audit${qs ? `?${qs}` : ""}`)
  },

  exportCsv: () =>
    request<string>("/api/audit/export?format=csv"),
}

// ── Settings ───────────────────────────────────────────────

export interface StoreSettings {
  id: number
  shadow_mode: boolean
  fraud_threshold: number
  po_limit: number
  pricing_limit: number
  reviews_rating_threshold: number
  slack_channel: string
  notify_on_failure: boolean
  notify_on_hitl: boolean
  notify_on_graduation: boolean
  created_at: string
  updated_at: string
}

export const settingsApi = {
  get: () => request<StoreSettings>("/api/settings"),
  update: (patch: Partial<StoreSettings>) =>
    request<StoreSettings>("/api/settings", {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),
}

// ── Pipeline ───────────────────────────────────────────────

export interface TaskStatus {
  id: string
  name: string
  status: string
  error: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export const pipelineApi = {
  run: () =>
    request<{ message: string; run_id: string }>("/api/run", {
      method: "POST",
    }),

  taskStatus: (taskId: string) =>
    request<TaskStatus>(`/api/tasks/${taskId}`),
}

// ── Auth ───────────────────────────────────────────────────

export const authApi = {
  login: (apiKey: string, operatorId?: string) =>
    request<{ status: string; operator: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ api_key: apiKey, operator_id: operatorId }),
    }),
}

// ── Export error class for callers ─────────────────────────

export { ApiError }
