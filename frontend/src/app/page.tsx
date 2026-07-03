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
  TrendingDown,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Server,
  Database,
  MoreVertical,
  Clock,
  Zap,
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
  fraud_detection: "bg-danger-light text-danger",
  inventory_management: "bg-info-light text-info",
  price_optimization: "bg-warning-light text-warning",
  customer_support: "bg-primary-light text-primary",
  logistics: "bg-success-light text-success",
  review_moderation: "bg-info-light text-info",
  seo_optimization: "bg-primary-light text-primary",
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
        {/* Metric Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="metric-card">
            <div className="flex items-center justify-between mb-3">
              <span className="metric-label">Total Revenue</span>
              <div className="w-9 h-9 rounded-lg bg-success-light flex items-center justify-center">
                <DollarSign className="w-4 h-4 text-success" />
              </div>
            </div>
            <div className="metric-value">
              ${revenue.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="metric-change text-success flex items-center gap-1 mt-1">
              <TrendingUp className="w-3 h-3" />
              +12.4%
            </div>
          </div>

          <div className="metric-card">
            <div className="flex items-center justify-between mb-3">
              <span className="metric-label">Decisions Made</span>
              <div className="w-9 h-9 rounded-lg bg-primary-light flex items-center justify-center">
                <Bot className="w-4 h-4 text-primary" />
              </div>
            </div>
            <div className="metric-value">{totalDecisions.toLocaleString()}</div>
            <div className="metric-change text-success flex items-center gap-1 mt-1">
              <TrendingUp className="w-3 h-3" />
              +8.2%
            </div>
          </div>

          <div className="metric-card">
            <div className="flex items-center justify-between mb-3">
              <span className="metric-label">Pending Reviews</span>
              <div className="w-9 h-9 rounded-lg bg-warning-light flex items-center justify-center">
                <Clock className="w-4 h-4 text-warning" />
              </div>
            </div>
            <div className="metric-value">{pendingCount}</div>
            <div className="metric-change text-warning flex items-center gap-1 mt-1">
              <AlertTriangle className="w-3 h-3" />
              Critical
            </div>
          </div>

          <div className="metric-card">
            <div className="flex items-center justify-between mb-3">
              <span className="metric-label">Flagged Orders</span>
              <div className="w-9 h-9 rounded-lg bg-danger-light flex items-center justify-center">
                <ShoppingCart className="w-4 h-4 text-danger" />
              </div>
            </div>
            <div className="metric-value">{flaggedCount}</div>
            <div className="metric-change text-danger flex items-center gap-1 mt-1">
              <TrendingDown className="w-3 h-3" />
              -2.1%
            </div>
          </div>
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-12 gap-6 mb-6">
          {/* Left: Pending Approvals */}
          <div className="col-span-8 card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-primary-light flex items-center justify-center">
                  <Activity className="w-4 h-4 text-primary" />
                </div>
                <h2 className="font-display font-semibold text-text-primary">Pending Approvals</h2>
              </div>
              <button className="text-sm text-primary hover:text-primary-hover transition-colors font-medium">
                View All Records
              </button>
            </div>

            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>ORDER ID</th>
                    <th>RISK SCORE</th>
                    <th>AI CONFIDENCE</th>
                    <th className="text-right">ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleDecisions.map((d) => {
                    const riskScore = getRiskScore(d.risk_level)
                    return (
                      <tr key={d.id}>
                        <td className="font-mono text-sm text-primary font-medium">{d.id}</td>
                        <td>
                          <div className="flex items-center gap-3">
                            <div className="risk-bar flex-1 max-w-[120px]">
                              <div
                                className={getRiskBarClass(riskScore)}
                                style={{ width: `${riskScore}%` }}
                              />
                            </div>
                            <span className="font-mono text-sm text-text-primary font-medium">{riskScore}%</span>
                          </div>
                        </td>
                        <td>
                          <span className={getConfidenceClass(d.confidence)}>
                            {(d.confidence * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td>
                          <div className="flex items-center justify-end gap-2">
                            <button className="btn-success text-xs px-3 py-1">
                              Approve
                            </button>
                            <button className="btn-danger text-xs px-3 py-1">
                              Reject
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between pt-3 mt-3 border-t border-border">
              <span className="text-sm text-text-muted">Showing {visibleDecisions.length} of {pendingCount} pending orders</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="p-1.5 rounded-md hover:bg-surface-3 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-4 h-4 text-text-secondary" />
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="p-1.5 rounded-md hover:bg-surface-3 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-4 h-4 text-text-secondary" />
                </button>
              </div>
            </div>
          </div>

          {/* Right: Sidebar cards */}
          <div className="col-span-4 space-y-4">
            {/* System Health */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-success" />
                  <h3 className="text-sm font-semibold text-text-primary">System Health</h3>
                </div>
                <span className="label-caps">LIVE_01</span>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-surface-3">
                  <span className="text-sm text-text-secondary">WebSocket Status</span>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-success animate-pulse" : "bg-danger"}`} />
                    <span className={`text-xs font-medium ${isConnected ? "text-success" : "text-danger"}`}>
                      {isConnected ? "CONNECTED" : "DISCONNECTED"}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-surface-3">
                  <span className="text-sm text-text-secondary">API Latency</span>
                  <div className="flex items-center gap-1">
                    <span className="font-mono text-lg font-bold text-text-primary">12</span>
                    <span className="text-xs text-text-muted">ms</span>
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-surface-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-text-muted">Uptime</span>
                    <span className="font-mono text-xs font-medium text-success">99.8%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill bg-success" style={{ width: "99.8%" }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Active Clusters */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-text-primary">Active Clusters</h3>
                <button className="p-1 rounded hover:bg-surface-3 transition-colors">
                  <MoreVertical className="w-4 h-4 text-text-muted" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-3">
                  <div className="p-2 rounded-lg bg-primary-light">
                    <Server className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-text-primary">Inference Engine</span>
                      <span className="font-mono text-xs text-text-secondary">0.02ms</span>
                    </div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="text-xs text-text-muted">v2.4.1-stable</span>
                      <span className="badge-success">READY</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-3">
                  <div className="p-2 rounded-lg bg-info-light">
                    <Database className="w-4 h-4 text-info" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-text-primary">Vector DB</span>
                      <span className="font-mono text-xs text-text-secondary">4.2gb</span>
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
            <div className="rounded-card border border-primary/20 bg-gradient-to-br from-primary-light to-white p-4">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-semibold text-primary">AI INSIGHT</h3>
              </div>
              <p className="text-sm text-text-secondary leading-relaxed">
                &quot;Fraud patterns detected in Zone-7. Recommended: Temporary escalation of AI confidence threshold to 95%.&quot;
              </p>
            </div>
          </div>
        </div>

        {/* Agent Fleet Status */}
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary-light flex items-center justify-center">
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

          <div className="grid grid-cols-7 divide-x divide-border">
            {agentData.map((agent) => {
              const Icon = agentIcons[agent.name] || Zap
              return (
                <div key={agent.name} className="p-4 hover:bg-surface-2 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className={`p-2 rounded-lg ${agentColors[agent.name] || "bg-primary-light text-primary"}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="dot-green" />
                  </div>
                  <h3 className="text-sm font-medium text-text-primary mb-3">{agent.display_name}</h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-text-muted">Uptime</span>
                      <span className="font-mono text-xs text-text-secondary">{agentUptime[agent.name] || "—"}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-text-muted">Activity</span>
                      <span className="font-mono text-xs text-primary">{agentActivity[agent.name] || "—"}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-center gap-2 py-4 text-[11px] font-mono text-text-muted">
          <span>© 2024 OpsIQ v2.5.0</span>
          <span className="mx-1">|</span>
          <span className="flex items-center gap-1.5">
            <span className="dot-green" />
            All Systems Operational
          </span>
        </div>
      </div>
    </Shell>
  )
}
