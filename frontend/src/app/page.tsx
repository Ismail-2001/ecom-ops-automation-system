"use client"

import { useState } from "react"
import {
  DollarSign,
  ShoppingCart,
  Bot,
  AlertTriangle,
  Bell,
  Wifi,
  Activity,
  Shield,
  Box,
  Tag,
  Headphones,
  Truck,
  Star,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Server,
  Database,
  MoreVertical,
  Clock,
  Zap,
  MessageSquare,
  Search,
} from "lucide-react"
import Shell from "@/components/layout/Shell"
import { useAgentStatus, useApprovals, useAnalytics, useHealth } from "@/lib/hooks"
import { useWs } from "@/app/providers"
import type { AgentStatus, ApprovalAction } from "@/lib/api"

const fallbackAgents: AgentStatus[] = [
  { name: "fraud_detection", display_name: "Fraud", status: "active", accuracy: 95.2, confidence: 0.92, processed_today: 120, last_activity: new Date().toISOString(), uptime: 99.9, error_rate: 0.1, avg_response_time: 1.2 },
  { name: "inventory_management", display_name: "Inventory", status: "active", accuracy: 88.5, confidence: 0.87, processed_today: 45, last_activity: new Date().toISOString(), uptime: 99.8, error_rate: 0.2, avg_response_time: 2.1 },
  { name: "price_optimization", display_name: "Price", status: "active", accuracy: 91.3, confidence: 0.89, processed_today: 89, last_activity: new Date().toISOString(), uptime: 99.7, error_rate: 0.1, avg_response_time: 0.5 },
  { name: "customer_support", display_name: "Support", status: "active", accuracy: 92.1, confidence: 0.91, processed_today: 67, last_activity: new Date().toISOString(), uptime: 99.8, error_rate: 0.1, avg_response_time: 1.8 },
  { name: "logistics", display_name: "Logistics", status: "active", accuracy: 89.4, confidence: 0.86, processed_today: 52, last_activity: new Date().toISOString(), uptime: 99.9, error_rate: 0.0, avg_response_time: 1.0 },
  { name: "review_moderation", display_name: "Review", status: "active", accuracy: 90.1, confidence: 0.85, processed_today: 34, last_activity: new Date().toISOString(), uptime: 99.9, error_rate: 0.0, avg_response_time: 0.8 },
  { name: "seo_optimization", display_name: "SEO", status: "active", accuracy: 87.2, confidence: 0.83, processed_today: 28, last_activity: new Date().toISOString(), uptime: 99.8, error_rate: 0.1, avg_response_time: 1.5 },
]

const fallbackDecisions: ApprovalAction[] = [
  { id: "ORD-90210", action_type: "fraud_review", agent: "fraud_detection", action: "flag", rationale: "Suspicious shipping address", risk_level: "high", confidence: 0.942, financial_impact: 150, status: "pending", shopify_entity_id: null, shopify_entity_type: null, suggested_response: null, draft_response: null, execution_result: null, error_message: null, executed_at: null, expires_at: null, metadata: null, created_at: new Date(Date.now() - 300000).toISOString(), updated_at: new Date().toISOString() },
  { id: "ORD-90211", action_type: "fraud_review", agent: "fraud_detection", action: "approve", rationale: "Low risk pattern", risk_level: "medium", confidence: 0.887, financial_impact: 85, status: "pending", shopify_entity_id: null, shopify_entity_type: null, suggested_response: null, draft_response: null, execution_result: null, error_message: null, executed_at: null, expires_at: null, metadata: null, created_at: new Date(Date.now() - 600000).toISOString(), updated_at: new Date().toISOString() },
  { id: "ORD-90212", action_type: "price_change", agent: "price_optimization", action: "approve", rationale: "Competitor price drop detected", risk_level: "low", confidence: 0.991, financial_impact: 200, status: "pending", shopify_entity_id: null, shopify_entity_type: null, suggested_response: null, draft_response: null, execution_result: null, error_message: null, executed_at: null, expires_at: null, metadata: null, created_at: new Date(Date.now() - 900000).toISOString(), updated_at: new Date().toISOString() },
  { id: "ORD-90213", action_type: "fraud_review", agent: "fraud_detection", action: "flag", rationale: "Velocity anomaly detected", risk_level: "high", confidence: 0.915, financial_impact: 320, status: "pending", shopify_entity_id: null, shopify_entity_type: null, suggested_response: null, draft_response: null, execution_result: null, error_message: null, executed_at: null, expires_at: null, metadata: null, created_at: new Date(Date.now() - 1200000).toISOString(), updated_at: new Date().toISOString() },
]

function getRiskColor(score: number): string {
  if (score >= 75) return "bg-danger"
  if (score >= 50) return "bg-warning"
  if (score >= 25) return "bg-info"
  return "bg-success"
}

function getRiskBarClass(score: number): string {
  if (score >= 75) return "risk-high"
  if (score >= 50) return "risk-medium"
  return "risk-low"
}

function getRiskScore(risk: string): number {
  switch (risk) {
    case "critical": return 92
    case "high": return 82
    case "medium": return 67
    case "low": return 32
    default: return 50
  }
}

function getConfidenceClass(confidence: number): string {
  if (confidence >= 0.8) return "confidence-high"
  if (confidence >= 0.5) return "confidence-medium"
  return "confidence-low"
}

const agentIcons: Record<string, typeof Shield> = {
  fraud_detection: Shield,
  inventory_management: Box,
  price_optimization: Tag,
  customer_support: Headphones,
  logistics: Truck,
  review_moderation: Star,
  seo_optimization: TrendingUp,
}

const agentUptime: Record<string, string> = {
  fraud_detection: "14d 2h",
  inventory_management: "31d 5h",
  price_optimization: "4h 12m",
  customer_support: "45d 8h",
  logistics: "2d 1h",
  review_moderation: "112d 1h",
  seo_optimization: "9d 18h",
}

const agentActivity: Record<string, string> = {
  fraud_detection: "Scanning...",
  inventory_management: "Synced",
  price_optimization: "Adj. +2%",
  customer_support: "Keywords",
  logistics: "Route Opt.",
  review_moderation: "4 Active",
  seo_optimization: "Indexing",
}

const agentColors: Record<string, string> = {
  fraud_detection: "bg-danger/10 text-danger",
  inventory_management: "bg-info/10 text-info",
  price_optimization: "bg-warning/10 text-warning",
  customer_support: "bg-primary/10 text-primary",
  logistics: "bg-success/10 text-success",
  review_moderation: "bg-info/10 text-info",
  seo_optimization: "bg-primary/10 text-primary",
}

export default function DashboardPage() {
  const health = useHealth()
  const agents = useAgentStatus()
  const approvals = useApprovals({ status: "pending" })
  const analytics = useAnalytics()
  const { isConnected } = useWs()
  const [page, setPage] = useState(0)

  const agentData = agents.data?.length ? agents.data : fallbackAgents
  const pendingDecisions = approvals.data?.length ? approvals.data : fallbackDecisions
  const isBackendUp = health.data?.status === "ok"

  const revenue = analytics.data?.summary?.total_financial_impact || 124892.40
  const totalDecisions = analytics.data?.summary?.total_decisions || 14208
  const pendingCount = pendingDecisions.length || 42
  const flaggedCount = pendingDecisions.filter((d) => d.risk_level === "high" || d.risk_level === "critical").length || 18

  const pageSize = 4
  const totalPages = Math.ceil(pendingDecisions.length / pageSize)
  const visibleDecisions = pendingDecisions.slice(page * pageSize, (page + 1) * pageSize)

  return (
    <Shell title="Command Center" subtitle="Real-time operations overview">
      <div className="flex flex-col h-full">
        {/* Topbar */}
        <div className="sticky top-0 z-40 flex items-center justify-between px-6 py-3 bg-void/80 backdrop-blur-xl border-b border-border">
          <div className="flex items-center gap-4 flex-1">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                type="text"
                placeholder="Search operations, orders, or agents..."
                className="w-full pl-10 pr-4 py-2.5 bg-surface border border-border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary/50 transition-colors font-body"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="relative p-2 rounded-lg hover:bg-surface transition-colors">
              <Bell className="w-5 h-5 text-text-secondary" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-danger rounded-full" />
            </button>
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${isConnected ? "bg-success/10 border border-success/20" : "bg-warning/10 border border-warning/20"}`}>
              <Wifi className={`w-3.5 h-3.5 ${isConnected ? "text-success" : "text-warning"}`} />
              <span className={`text-xs font-medium ${isConnected ? "text-success" : "text-warning"}`}>{isConnected ? "Live" : "Reconnecting"}</span>
            </div>
            <div className="flex items-center gap-3 pl-4 border-l border-border">
              <div className="text-right">
                <p className="text-sm font-medium text-text-primary">Admin User</p>
                <p className="text-[10px] font-mono text-text-muted uppercase">superuser_root</p>
              </div>
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-white font-semibold text-sm">
                AU
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Main Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-4 gap-4">
              {/* Total Revenue */}
              <div className="p-5 rounded-xl bg-surface border border-border">
                <p className="label-caps mb-2">Total Revenue</p>
                <div className="flex items-end gap-3">
                  <span className="text-2xl font-display font-bold text-text-primary">
                    ${revenue.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                  <span className="flex items-center gap-1 text-xs font-medium text-success mb-1">
                    <TrendingUp className="w-3 h-3" />
                    +12.4%
                  </span>
                </div>
                <div className="mt-3 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                  <div className="h-full w-[72%] bg-gradient-to-r from-primary to-primary/60 rounded-full" />
                </div>
              </div>

              {/* Decisions Made */}
              <div className="p-5 rounded-xl bg-surface border border-border">
                <p className="label-caps mb-2">Decisions Made</p>
                <div className="flex items-end gap-3">
                  <span className="text-2xl font-display font-bold text-text-primary">{totalDecisions.toLocaleString()}</span>
                  <span className="flex items-center gap-1 text-xs font-medium text-success mb-1">
                    <TrendingUp className="w-3 h-3" />
                    +8.2%
                  </span>
                </div>
                <div className="mt-3 flex gap-1">
                  {[40, 55, 35, 70, 60, 45, 80, 65, 50, 75, 55, 40].map((h, i) => (
                    <div key={i} className="flex-1 bg-surface-3 rounded-sm" style={{ height: `${h * 0.4}px` }} />
                  ))}
                </div>
              </div>

              {/* Pending Reviews */}
              <div className="p-5 rounded-xl bg-surface border border-border">
                <p className="label-caps mb-2">Pending Reviews</p>
                <div className="flex items-end gap-3">
                  <span className="text-2xl font-display font-bold text-text-primary">{pendingCount}</span>
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-warning/15 text-xs font-medium text-warning mb-1">
                    <Clock className="w-3 h-3" />
                    Critical
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-2 text-xs text-text-muted">
                  <AlertTriangle className="w-3.5 h-3.5 text-warning" />
                  Awaiting human verification
                </div>
              </div>

              {/* Flagged Orders */}
              <div className="p-5 rounded-xl bg-surface border border-border">
                <p className="label-caps mb-2">Flagged Orders</p>
                <div className="flex items-end gap-3">
                  <span className="text-2xl font-display font-bold text-text-primary">{flaggedCount}</span>
                  <span className="flex items-center gap-1 text-xs font-medium text-danger mb-1">
                    <AlertTriangle className="w-3 h-3" />
                    -2.1%
                  </span>
                </div>
                <div className="mt-3 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                  <div className="h-full w-[35%] bg-gradient-to-r from-danger to-danger/60 rounded-full" />
                </div>
              </div>
            </div>

            {/* Pending Approvals Table */}
            <div className="rounded-xl bg-surface border border-border overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="p-1.5 rounded-md bg-primary/10">
                    <Activity className="w-4 h-4 text-primary" />
                  </div>
                  <h2 className="font-display font-semibold text-text-primary">Pending Approvals</h2>
                </div>
                <button className="text-sm text-primary hover:text-primary-hover transition-colors">
                  View All Records
                </button>
              </div>

              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-5 py-3 text-left text-label text-text-muted font-medium">ORDER ID</th>
                    <th className="px-5 py-3 text-left text-label text-text-muted font-medium">RISK SCORE</th>
                    <th className="px-5 py-3 text-left text-label text-text-muted font-medium">AI CONFIDENCE</th>
                    <th className="px-5 py-3 text-right text-label text-text-muted font-medium">ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleDecisions.map((d) => {
                    const riskScore = getRiskScore(d.risk_level)
                    return (
                      <tr key={d.id} className="border-b border-border/50 hover:bg-surface-2/50 transition-colors">
                        <td className="px-5 py-4 font-mono text-sm text-primary font-medium">{d.id}</td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="flex-1 h-2 bg-surface-3 rounded-full overflow-hidden max-w-[120px]">
                              <div
                                className={`h-full ${getRiskColor(riskScore)} rounded-full transition-all`}
                                style={{ width: `${riskScore}%` }}
                              />
                            </div>
                            <span className="font-mono text-sm text-text-primary font-medium">{riskScore}%</span>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <span className={getConfidenceClass(d.confidence)}>
                            {(d.confidence * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <div className="flex items-center justify-end gap-2">
                            <button className="px-4 py-1.5 rounded-lg bg-success/10 border border-success/20 text-sm font-medium text-success hover:bg-success/20 transition-colors">
                              Approve
                            </button>
                            <button className="px-4 py-1.5 rounded-lg bg-danger/10 border border-danger/20 text-sm font-medium text-danger hover:bg-danger/20 transition-colors">
                              Reject
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

              <div className="flex items-center justify-between px-5 py-3 border-t border-border">
                <span className="text-sm text-text-muted">Showing {visibleDecisions.length} of {pendingCount} pending orders</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(Math.max(0, page - 1))}
                    disabled={page === 0}
                    className="p-1.5 rounded-md hover:bg-surface-2 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4 text-text-secondary" />
                  </button>
                  <button
                    onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                    disabled={page >= totalPages - 1}
                    className="p-1.5 rounded-md hover:bg-surface-2 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight className="w-4 h-4 text-text-secondary" />
                  </button>
                </div>
              </div>
            </div>

            {/* Agent Fleet Status */}
            <div className="rounded-xl bg-surface border border-border overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="p-1.5 rounded-md bg-primary/10">
                    <Bot className="w-4 h-4 text-primary" />
                  </div>
                  <h2 className="font-display font-semibold text-text-primary">Agent Fleet Status</h2>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <div className="dot-green" />
                    <span className="text-sm text-text-secondary">{agentData.length} Online</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="dot-gray" />
                    <span className="text-sm text-text-secondary">0 Offline</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-7 divide-x divide-border/50">
                {agentData.map((agent) => {
                  const Icon = agentIcons[agent.name] || Zap
                  return (
                    <div key={agent.name} className="p-4 hover:bg-surface-2/30 transition-colors">
                      <div className="flex items-center justify-between mb-3">
                        <div className={`p-2 rounded-lg ${agentColors[agent.name] || "bg-primary/10 text-primary"}`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div className="dot-green" />
                      </div>
                      <h3 className="text-sm font-medium text-text-primary mb-3">{agent.display_name}</h3>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-text-muted">Uptime</span>
                          <span className="font-mono text-data-sm text-text-secondary">{agentUptime[agent.name] || "—"}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-text-muted">Activity</span>
                          <span className="font-mono text-data-sm text-primary">{agentActivity[agent.name] || "—"}</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-center gap-2 py-4 text-[11px] font-mono text-text-muted">
              <span>© 2024 OPS-IQ SYSTEM v2.5.0-ALPHA</span>
              <span className="mx-1">|</span>
              <span className="hover:text-text-secondary cursor-pointer transition-colors">PROTOCOL</span>
              <span className="mx-1">|</span>
              <span className="hover:text-text-secondary cursor-pointer transition-colors">SECURITY</span>
              <span className="mx-1">|</span>
              <span className="hover:text-text-secondary cursor-pointer transition-colors">LOGS</span>
              <span className="mx-2">|</span>
              <span className="flex items-center gap-1.5">
                <span className="dot-green" />
                ALL SYSTEMS OPERATIONAL
              </span>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="w-[320px] border-l border-border bg-surface/50 overflow-y-auto p-4 space-y-4">
            {/* System Health */}
            <div className="rounded-xl bg-surface-2 border border-border p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-success" />
                  <h3 className="text-sm font-semibold text-text-primary">System Health</h3>
                </div>
                <span className="label-caps">LIVE_01</span>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-surface-3/50">
                  <span className="text-sm text-text-secondary">WebSocket Status</span>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-success animate-pulse-agent" : "bg-danger"}`} />
                    <span className={`text-xs font-medium ${isConnected ? "text-success" : "text-danger"}`}>
                      {isConnected ? "CONNECTED" : "DISCONNECTED"}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-surface-3/50">
                  <span className="text-sm text-text-secondary">API Latency</span>
                  <div className="flex items-center gap-1">
                    <span className="font-mono text-lg font-bold text-text-primary">12</span>
                    <span className="text-xs text-text-muted">ms</span>
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-surface-3/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-text-muted">Uptime</span>
                    <span className="font-mono text-data-sm text-success">99.8%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill bg-success" style={{ width: "99.8%" }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Active Clusters */}
            <div className="rounded-xl bg-surface-2 border border-border p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-text-primary">Active Clusters</h3>
                <button className="p-1 rounded hover:bg-surface-3 transition-colors">
                  <MoreVertical className="w-4 h-4 text-text-muted" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-3/50">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Server className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-text-primary">Inference Engine</span>
                      <span className="font-mono text-data-sm text-text-secondary">0.02ms</span>
                    </div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="text-xs text-text-muted">v2.4.1-stable</span>
                      <span className="badge-success">READY</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-3/50">
                  <div className="p-2 rounded-lg bg-info/10">
                    <Database className="w-4 h-4 text-info" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-text-primary">Vector DB</span>
                      <span className="font-mono text-data-sm text-text-secondary">4.2gb</span>
                    </div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="text-xs text-text-muted">shard_us_east_1</span>
                      <span className="badge-success">READY</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Insight */}
            <div className="rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20 p-4">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-semibold text-primary">AI INSIGHT</h3>
              </div>
              <p className="text-sm text-text-secondary leading-relaxed italic">
                &quot;Fraud patterns detected in Zone-7. Recommended: Temporary escalation of AI confidence threshold to 95%.&quot;
              </p>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  )
}
