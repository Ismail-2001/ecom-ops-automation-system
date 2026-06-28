"use client"

import {
  ShoppingCart,
  DollarSign,
  Bot,
  AlertTriangle,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { MetricCard } from "@/components/shared/MetricCard"
import { ActivityFeed } from "@/components/shared/ActivityFeed"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { ConfidencePill } from "@/components/shared/ConfidencePill"
import { MetricCardSkeleton, ActivityFeedSkeleton } from "@/components/shared/Skeleton"
import { useAgentStatus, useApprovals, useAnalytics, useHealth } from "@/lib/hooks"
import { formatCurrency } from "@/lib/utils"
import type { AgentStatus, ApprovalAction } from "@/lib/api"

// Fallback data when backend is unreachable
const fallbackAgents: AgentStatus[] = [
  { name: "fraud_detection", display_name: "Fraud Detection", status: "active", accuracy: 95.2, confidence: 0.92, processed_today: 120, last_activity: new Date().toISOString(), uptime: 99.9, error_rate: 0.1, avg_response_time: 1.2 },
  { name: "inventory_management", display_name: "Inventory", status: "active", accuracy: 88.5, confidence: 0.87, processed_today: 45, last_activity: new Date().toISOString(), uptime: 99.8, error_rate: 0.2, avg_response_time: 2.1 },
  { name: "price_optimization", display_name: "Pricing", status: "active", accuracy: 91.3, confidence: 0.89, processed_today: 89, last_activity: new Date().toISOString(), uptime: 99.7, error_rate: 0.1, avg_response_time: 0.5 },
  { name: "review_moderation", display_name: "Reviews", status: "active", accuracy: 90.1, confidence: 0.85, processed_today: 34, last_activity: new Date().toISOString(), uptime: 99.9, error_rate: 0.0, avg_response_time: 0.8 },
  { name: "marketing_automation", display_name: "Marketing", status: "active", accuracy: 87.2, confidence: 0.83, processed_today: 28, last_activity: new Date().toISOString(), uptime: 99.8, error_rate: 0.1, avg_response_time: 1.5 },
]

const fallbackDecisions: ApprovalAction[] = [
  { id: "ORD-8852", action_type: "fraud_review", agent: "fraud_detection", action: "flag", rationale: "Suspicious shipping address", risk_level: "high", confidence: 0.78, financial_impact: 150, status: "pending", shopify_entity_id: null, shopify_entity_type: null, suggested_response: null, draft_response: null, execution_result: null, error_message: null, executed_at: null, expires_at: null, metadata: null, created_at: new Date(Date.now() - 300000).toISOString(), updated_at: new Date().toISOString() },
  { id: "ORD-8853", action_type: "fraud_review", agent: "fraud_detection", action: "approve", rationale: "Low risk pattern", risk_level: "low", confidence: 0.95, financial_impact: 85, status: "pending", shopify_entity_id: null, shopify_entity_type: null, suggested_response: null, draft_response: null, execution_result: null, error_message: null, executed_at: null, expires_at: null, metadata: null, created_at: new Date(Date.now() - 600000).toISOString(), updated_at: new Date().toISOString() },
  { id: "ORD-8854", action_type: "price_change", agent: "price_optimization", action: "approve", rationale: "Competitor price drop detected", risk_level: "low", confidence: 0.91, financial_impact: 200, status: "pending", shopify_entity_id: null, shopify_entity_type: null, suggested_response: null, draft_response: null, execution_result: null, error_message: null, executed_at: null, expires_at: null, metadata: null, created_at: new Date(Date.now() - 900000).toISOString(), updated_at: new Date().toISOString() },
]

export default function DashboardPage() {
  const health = useHealth()
  const agents = useAgentStatus()
  const approvals = useApprovals({ status: "pending" })
  const analytics = useAnalytics()

  const agentData = agents.data?.length ? agents.data : fallbackAgents
  const pendingDecisions = approvals.data?.length ? approvals.data : fallbackDecisions
  const summary = analytics.data?.summary
  const isBackendUp = health.data?.status === "ok"

  const revenue = summary?.total_financial_impact || 125430
  const totalDecisions = summary?.total_decisions || 847
  const pendingCount = pendingDecisions.length
  const flaggedCount = pendingDecisions.filter((d) => d.risk_level === "high" || d.risk_level === "critical").length

  return (
    <Shell>
      <Topbar title="Command Center" subtitle="Real-time operations overview" />

      <div className="p-6 space-y-6">
        {/* Backend status banner */}
        {!isBackendUp && (
          <div className="flex items-center gap-3 p-3 rounded-lg bg-amber/10 border border-amber/20">
            <AlertTriangle className="w-4 h-4 text-amber" />
            <span className="text-sm text-amber">
              Backend offline — showing demo data. Start the API server for live data.
            </span>
          </div>
        )}

        {isBackendUp && flaggedCount > 0 && (
          <div className="flex items-center gap-3 p-3 rounded-lg bg-amber/10 border border-amber/20">
            <AlertTriangle className="w-4 h-4 text-amber" />
            <span className="text-sm text-amber">
              {pendingCount} orders pending review — {flaggedCount} flagged
            </span>
          </div>
        )}

        {/* Metrics row */}
        <div className="grid grid-cols-4 gap-4">
          {agents.isLoading ? (
            <>
              <MetricCardSkeleton />
              <MetricCardSkeleton />
              <MetricCardSkeleton />
              <MetricCardSkeleton />
            </>
          ) : (
            <>
              <MetricCard
                label="Revenue Today"
                value={formatCurrency(revenue)}
                icon={<DollarSign className="w-4 h-4 text-emerald" />}
                color="bg-emerald/10"
              />
              <MetricCard
                label="Total Decisions"
                value={totalDecisions}
                icon={<ShoppingCart className="w-4 h-4 text-indigo" />}
                color="bg-indigo/10"
              />
              <MetricCard
                label="Pending Decisions"
                value={pendingCount}
                icon={<Bot className="w-4 h-4 text-amber" />}
                color="bg-amber/10"
              />
              <MetricCard
                label="Flagged Orders"
                value={flaggedCount}
                icon={<AlertTriangle className="w-4 h-4 text-red" />}
                color="bg-red/10"
              />
            </>
          )}
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-3 gap-6">
          {/* Pending decisions */}
          <div className="col-span-2 card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-text-1">Pending Review</h2>
              <span className="text-xs text-text-3">
                {approvals.isLoading ? "Loading..." : `${pendingDecisions.length} items`}
              </span>
            </div>
            {approvals.isLoading ? (
              <ActivityFeedSkeleton />
            ) : (
              <div className="space-y-2">
                {pendingDecisions.map((d) => (
                  <div
                    key={d.id}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-data-sm text-indigo">{d.id}</span>
                      <StatusBadge status={d.status} />
                      <span className="text-xs text-text-3">{d.action_type}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <ConfidencePill value={d.confidence} />
                      <span className="text-xs text-text-3">{d.agent}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right panel */}
          <div className="space-y-6">
            {/* Agent status */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-display font-semibold text-text-1">Agents</h2>
              </div>
              <div className="space-y-3">
                {agentData.slice(0, 5).map((agent) => (
                  <div key={agent.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className={agent.status === "active" ? "dot-active" : "dot-paused"} />
                      <span className="text-sm text-text-2">{agent.display_name}</span>
                    </div>
                    <span className="font-mono text-data-xs text-text-3">
                      {agent.processed_today} today
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Health */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-display font-semibold text-text-1">System</h2>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-text-3">API</span>
                  <span className={`text-xs font-medium ${isBackendUp ? "text-emerald" : "text-red"}`}>
                    {isBackendUp ? "Healthy" : "Offline"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-text-3">Version</span>
                  <span className="font-mono text-data-xs text-text-2">{health.data?.version || "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-text-3">Uptime</span>
                  <span className="font-mono text-data-xs text-text-2">
                    {health.data?.uptime_seconds
                      ? `${Math.floor(health.data.uptime_seconds / 3600)}h`
                      : "—"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Agent performance row */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-semibold text-text-1">Agent Performance</h2>
          </div>
          <div className="grid grid-cols-5 gap-4">
            {agentData.map((agent) => (
              <div
                key={agent.name}
                className="p-3 rounded-lg bg-surface-2 hover:bg-surface-3 transition-colors"
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className={agent.status === "active" ? "dot-active" : "dot-paused"} />
                  <span className="text-sm font-medium text-text-1">{agent.display_name}</span>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-3">Accuracy</span>
                    <span className="font-mono text-data-xs text-emerald">{agent.accuracy}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-3">Processed</span>
                    <span className="font-mono text-data-xs text-text-2">{agent.processed_today}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-3">Avg Time</span>
                    <span className="font-mono text-data-xs text-text-2">{agent.avg_response_time}s</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Shell>
  )
}
