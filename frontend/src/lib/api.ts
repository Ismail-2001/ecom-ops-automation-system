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

// ── Security ────────────────────────────────────────────────

export interface SecurityUser {
  id: string
  email: string
  name: string
  role: string
  is_active: boolean
  created_at: string
  last_login: string | null
}

export interface ApiKey {
  id: string
  name: string
  user_id: string
  role: string
  is_active: boolean
  expires_at: string | null
  last_used: string | null
  usage_count: number
  created_at: string
}

export interface SecurityAuditEntry {
  id: string
  timestamp: string
  event_type: string
  action: string
  resource: string
  resource_id: string | null
  user_id: string | null
  success: boolean
  risk_level: string
}

export interface SecuritySummary {
  total_events: number
  failed_logins: number
  successful_logins: number
  api_key_events: number
  role_changes: number
  risk_events: number
  period_hours: number
}

export const securityApi = {
  listUsers: (params?: { role?: string; is_active?: boolean }) => {
    const searchParams = new URLSearchParams()
    if (params?.role) searchParams.set("role", params.role)
    if (params?.is_active !== undefined) searchParams.set("is_active", String(params.is_active))
    const qs = searchParams.toString()
    return request<{ users: SecurityUser[]; total: number }>(`/security/users${qs ? `?${qs}` : ""}`)
  },

  listApiKeys: () =>
    request<{ api_keys: ApiKey[]; total: number }>("/security/api-keys"),

  getAuditSummary: (hours = 24) =>
    request<SecuritySummary>(`/security/audit/summary?hours=${hours}`),

  getAuditLogs: (params?: { event_type?: string; limit?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.event_type) searchParams.set("event_type", params.event_type)
    if (params?.limit) searchParams.set("limit", String(params.limit))
    const qs = searchParams.toString()
    return request<{ entries: SecurityAuditEntry[]; total: number }>(`/security/audit/logs${qs ? `?${qs}` : ""}`)
  },

  health: () => request<Record<string, string>>("/security/health"),
}

// ── Support ─────────────────────────────────────────────────

export interface SupportTicket {
  id: string
  customer_email: string
  customer_name: string
  subject: string
  body: string
  category: string
  priority: string
  status: string
  channel: string
  order_id: string | null
  created_at: string
  messages: Array<{ id: string; sender_type: string; content: string; created_at: string }>
}

export interface SupportAnalytics {
  total_tickets: number
  open_tickets: number
  avg_response_time_hours: number
  avg_resolution_time_hours: number
  satisfaction_score: number
  first_contact_resolution_rate: number
  escalation_rate: number
  category_breakdown: Record<string, number>
  priority_breakdown: Record<string, number>
  sentiment_distribution: Record<string, number>
}

export const supportApi = {
  listTickets: (params?: { status?: string; priority?: string; page?: number; limit?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set("status", params.status)
    if (params?.priority) searchParams.set("priority", params.priority)
    if (params?.page) searchParams.set("page", String(params.page))
    if (params?.limit) searchParams.set("limit", String(params.limit))
    const qs = searchParams.toString()
    return request<{ tickets: SupportTicket[]; total: number; page: number; limit: number }>(`/support/tickets${qs ? `?${qs}` : ""}`)
  },

  getTicket: (id: string) => request<SupportTicket>(`/support/tickets/${id}`),

  getAnalytics: (days = 7) =>
    request<SupportAnalytics>(`/support/analytics?days=${days}`),

  health: () => request<Record<string, string>>("/support/health"),
}

// ── Cart Recovery ───────────────────────────────────────────

export interface CartRecoveryAnalytics {
  total_abandoned: number
  total_recovered: number
  recovery_rate: number
  total_revenue_lost: number
  total_revenue_recovered: number
  average_cart_value: number
  average_recovery_time_hours: number
  top_recovery_strategy: string
  strategy_breakdown: Record<string, number>
  risk_distribution: Record<string, number>
}

export interface CartAnalysisResult {
  cart_id: string
  recommendation: {
    strategy: string
    risk_level: string
    discount_value: number
    discount_code: string | null
    recovery_probability: number
    estimated_revenue: number
    reasoning: string
  }
  email_context: Record<string, unknown>
}

export const cartRecoveryApi = {
  getAnalytics: (days = 7) =>
    request<CartRecoveryAnalytics>(`/cart-recovery/analytics?days=${days}`),

  analyze: (cartId: string, items: Array<{ name: string; price: number; quantity: number }>, totalValue: number) =>
    request<CartAnalysisResult>("/cart-recovery/analyze", {
      method: "POST",
      body: JSON.stringify({ cart_id: cartId, items, total_value: totalValue }),
    }),

  recover: (cartId: string, strategy: string) =>
    request<{ status: string; cart_id: string; strategy: string; discount_code: string }>("/cart-recovery/recover", {
      method: "POST",
      body: JSON.stringify({ cart_id: cartId, strategy }),
    }),

  health: () => request<Record<string, string>>("/cart-recovery/health"),
}

// ── Shopify ─────────────────────────────────────────────────

export interface ShopifyStatus {
  configured: boolean
  shop_domain: string | null
  api_version: string
  webhook_topics: string[]
}

export interface SyncResult {
  status: string
  products_synced: number
  orders_synced: number
  customers_synced: number
  duration_seconds: number
  errors: string[]
}

export const shopifyApi = {
  status: () => request<ShopifyStatus>("/shopify/status"),

  sync: (full = false) =>
    request<SyncResult>(`/shopify/sync?full=${full}`, { method: "POST" }),

  products: (limit = 50) =>
    request<unknown>(`/shopify/products?limit=${limit}`),

  orders: (status = "any", limit = 50) =>
    request<unknown>(`/shopify/orders?status=${status}&limit=${limit}`),
}

// ── Export error class for callers ─────────────────────────

export { ApiError }
