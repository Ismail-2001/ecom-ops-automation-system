const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || "v1"
const API_PREFIX = `/api/${API_VERSION}`

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

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'))
  return match ? decodeURIComponent(match[1]) : null
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`
  const token = getCookie("opsiq_api_key")

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  }

  const res = await fetch(url, { ...options, headers })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail || res.statusText, body)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

export const authApi = {
  login: (apiKey: string) =>
    request<{ status: string; operator?: string; permissions?: string[] }>(
      `${API_PREFIX}/auth/login`,
      {
        method: "POST",
        body: JSON.stringify({ api_key: apiKey }),
      }
    ),
}

export const healthApi = {
  check: () => request<{ status: string; version?: string; uptime?: number }>(`${API_PREFIX}/health`),
}

export const agentApi = {
  list: () => request<{ agents: AgentStatus[]; total: number }>(`${API_PREFIX}/agents`),
  status: () => request<AgentStatus[]>(`${API_PREFIX}/agents/status`),
  deploy: (agentType: string) =>
    request<{ status: string; agent_type: string }>(`${API_PREFIX}/agents/deploy`, {
      method: "POST",
      body: JSON.stringify({ agent_type: agentType }),
    }),
  logs: (params?: { agent?: string; limit?: number }) => {
    const qs = params ? `?${new URLSearchParams(params as Record<string, string>).toString()}` : ""
    return request<InferenceLog[]>(`${API_PREFIX}/agents/logs${qs}`)
  },
}

export const approvalApi = {
  list: (params?: { status?: string; agent?: string }) => {
    const qs = params ? `?${new URLSearchParams(params as Record<string, string>).toString()}` : ""
    return request<ApprovalAction[]>(`${API_PREFIX}/approvals${qs}`)
  },
  approve: (id: string) =>
    request<{ status: string }>(`${API_PREFIX}/approvals/${id}/approve`, { method: "POST" }),
  reject: (id: string) =>
    request<{ status: string }>(`${API_PREFIX}/approvals/${id}/reject`, { method: "POST" }),
  batch: (ids: string[], action: "approve" | "reject") =>
    request<{ processed: number }>(`${API_PREFIX}/approvals/batch`, {
      method: "POST",
      body: JSON.stringify({ action_ids: ids, action }),
    }),
}

export const analyticsApi = {
  summary: (days?: number) =>
    request<AnalyticsSummary>(`${API_PREFIX}/analytics/summary` + (days ? `?days=${days}` : "")),
}

export const orderApi = {
  list: (params?: { page?: number; limit?: number; status?: string }) => {
    const sp = new URLSearchParams()
    if (params?.page) sp.set("page", String(params.page))
    if (params?.limit) sp.set("limit", String(params.limit))
    if (params?.status) sp.set("status", params.status)
    const qs = sp.toString()
    return request<{ orders: Order[]; total: number; page: number; limit: number }>(`${API_PREFIX}/orders${qs ? `?${qs}` : ""}`)
  },
}

export const productApi = {
  list: (params?: { page?: number; limit?: number }) => {
    const sp = new URLSearchParams()
    if (params?.page) sp.set("page", String(params.page))
    if (params?.limit) sp.set("limit", String(params.limit))
    const qs = sp.toString()
    return request<{ products: Product[]; total: number }>(`${API_PREFIX}/products${qs ? `?${qs}` : ""}`)
  },
}

export const cartRecoveryApi = {
  list: (params?: { status?: string }) => {
    const qs = params?.status ? `?status=${params.status}` : ""
    return request<CartItem[]>(`${API_PREFIX}/cart-recovery${qs}`)
  },
  analytics: () => request<CartRecoveryAnalytics>(`${API_PREFIX}/cart-recovery/analytics`),
}

export const reviewApi = {
  list: (params?: { sentiment?: string }) => {
    const qs = params?.sentiment ? `?sentiment=${params.sentiment}` : ""
    return request<Review[]>(`${API_PREFIX}/reviews${qs}`)
  },
}

export const supportApi = {
  listTickets: (params?: { status?: string; priority?: string; page?: number; limit?: number }) => {
    const sp = new URLSearchParams()
    if (params?.status) sp.set("status", params.status)
    if (params?.priority) sp.set("priority", params.priority)
    if (params?.page) sp.set("page", String(params.page))
    if (params?.limit) sp.set("limit", String(params.limit))
    const qs = sp.toString()
    return request<{ tickets: SupportTicket[]; total: number; page: number; limit: number }>(`${API_PREFIX}/support/tickets${qs ? `?${qs}` : ""}`)
  },
  getTicket: (id: string) => request<SupportTicket>(`${API_PREFIX}/support/tickets/${id}`),
  getAnalytics: (days = 7) => request<SupportAnalytics>(`${API_PREFIX}/support/analytics?days=${days}`),
}

export const securityApi = {
  events: (params?: { severity?: string }) => {
    const qs = params?.severity ? `?severity=${params.severity}` : ""
    return request<SecurityEvent[]>(`${API_PREFIX}/security/events${qs}`)
  },
  health: () => request<Record<string, string>>(`${API_PREFIX}/security/health`),
}

export const settingsApi = {
  get: () => request<StoreSettings>(`${API_PREFIX}/settings`),
  update: (data: Partial<StoreSettings>) =>
    request<StoreSettings>(`${API_PREFIX}/settings`, { method: "PATCH", body: JSON.stringify(data) }),
}

export const shopifyApi = {
  status: () => request<ShopifyStatus>(`${API_PREFIX}/shopify/status`),
  sync: () => request<{ status: string }>(`${API_PREFIX}/shopify/sync`, { method: "POST" }),
}

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

export interface InferenceLog {
  id: string
  agent: string
  input: string
  output: string
  confidence: number
  latency_ms: number
  created_at: string
}

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
  metadata: unknown
  created_at: string
  updated_at: string
}

export interface AnalyticsSummary {
  summary: {
    total_decisions: number
    auto_approved: number
    escalated: number
    total_financial_impact: number
  }
  agent_breakdown: Record<string, { decisions: number; avg_confidence: number }>
}

export interface Order {
  id: string
  customer: string
  total: number
  status: string
  fraud_score: number
  created_at: string
}

export interface Product {
  id: string
  title: string
  price: number
  stock: number
  status: string
}

export interface CartItem {
  id: string
  customer_email: string
  items: Array<{ title: string; price: number; quantity: number }>
  total: number
  status: string
  created_at: string
}

export interface CartRecoveryAnalytics {
  total_carts: number
  recovered_carts: number
  recovery_rate: number
  total_revenue_lost: number
  revenue_recovered: number
}

export interface Review {
  id: string
  author: string
  rating: number
  content: string
  sentiment: string
  created_at: string
}

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

export interface SecurityEvent {
  id: string
  type: string
  severity: string
  description: string
  source_ip: string | null
  created_at: string
}

export interface StoreSettings {
  id: number
  shop_name: string
  shop_url: string
  auto_approve_threshold: number
  max_order_value: number
  fraud_check_enabled: boolean
  inventory_sync_enabled: boolean
  notification_email: string
}

export interface ShopifyStatus {
  connected: boolean
  shop_name: string
  last_sync: string | null
  products_count: number
  orders_count: number
}

export { ApiError }
