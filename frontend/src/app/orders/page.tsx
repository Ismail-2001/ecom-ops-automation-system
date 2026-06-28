"use client"

import { useState } from "react"
import {
  Search,
  Filter,
  Download,
  Eye,
  CheckCircle,
  XCircle,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { ConfidencePill } from "@/components/shared/ConfidencePill"
import { RiskScore } from "@/components/shared/RiskScore"
import { MetricCardSkeleton } from "@/components/shared/Skeleton"
import { useApprovals, useApproveAction, useRejectAction } from "@/lib/hooks"
import { cn, formatCurrency, formatTimestamp } from "@/lib/utils"
import type { ApprovalAction } from "@/lib/api"

const fallbackOrders: ApprovalAction[] = [
  { id: "ORD-8854", action_type: "fraud_review", agent: "fraud_detection", action: "approve", rationale: "Low risk indicators", risk_level: "low", confidence: 0.95, financial_impact: 284.97, status: "executed", shopify_entity_id: null, shopify_entity_type: null, suggested_response: null, draft_response: null, execution_result: null, error_message: null, executed_at: new Date().toISOString(), expires_at: null, metadata: null, created_at: new Date(Date.now() - 300000).toISOString(), updated_at: new Date().toISOString() },
  { id: "ORD-8853", action_type: "fraud_review", agent: "fraud_detection", action: "flag", rationale: "Medium risk — new customer", risk_level: "medium", confidence: 0.78, financial_impact: 549.99, status: "pending", shopify_entity_id: null, shopify_entity_type: null, suggested_response: null, draft_response: null, execution_result: null, error_message: null, executed_at: null, expires_at: null, metadata: null, created_at: new Date(Date.now() - 600000).toISOString(), updated_at: new Date().toISOString() },
  { id: "ORD-8852", action_type: "fraud_review", agent: "fraud_detection", action: "reject", rationale: "High risk — fraud patterns", risk_level: "high", confidence: 0.94, financial_impact: 1249.95, status: "pending", shopify_entity_id: null, shopify_entity_type: null, suggested_response: null, draft_response: null, execution_result: null, error_message: null, executed_at: null, expires_at: null, metadata: null, created_at: new Date(Date.now() - 900000).toISOString(), updated_at: new Date().toISOString() },
]

const statusFilters = ["All", "pending", "executed", "rejected", "flagged"]

export default function OrdersPage() {
  const [activeFilter, setActiveFilter] = useState("All")
  const [searchQuery, setSearchQuery] = useState("")
  const approvalsQuery = useApprovals({ status: activeFilter === "All" ? undefined : activeFilter })
  const approveMutation = useApproveAction()
  const rejectMutation = useRejectAction()

  const orders = approvalsQuery.data?.length ? approvalsQuery.data : fallbackOrders
  const filtered = orders.filter((o) => {
    if (searchQuery && !o.id.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  return (
    <Shell>
      <Topbar
        title="Orders"
        subtitle="Manage orders and fraud decisions"
        actions={
          <button className="btn-ghost">
            <Download className="w-3.5 h-3.5" />
            Export
          </button>
        }
      />

      <div className="p-6 space-y-4">
        {/* Filter bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {statusFilters.map((f) => (
              <button
                key={f}
                onClick={() => setActiveFilter(f)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                  activeFilter === f
                    ? "bg-indigo/10 text-indigo"
                    : "text-text-3 hover:text-text-2 hover:bg-surface-2",
                )}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-3" />
            <input
              type="text"
              placeholder="Search orders..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2 rounded-lg bg-surface-2 border border-border text-sm text-text-1 placeholder:text-text-3 focus:outline-none focus:border-border-bright w-64"
            />
          </div>
        </div>

        {/* Table */}
        <div className="card p-0 overflow-hidden">
          {approvalsQuery.isLoading ? (
            <div className="p-6 space-y-3">
              <MetricCardSkeleton /><MetricCardSkeleton /><MetricCardSkeleton />
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-3 section-label text-[10px]">Order</th>
                  <th className="text-left px-4 py-3 section-label text-[10px]">Agent</th>
                  <th className="text-left px-4 py-3 section-label text-[10px]">Type</th>
                  <th className="text-left px-4 py-3 section-label text-[10px]">Risk</th>
                  <th className="text-left px-4 py-3 section-label text-[10px]">Confidence</th>
                  <th className="text-left px-4 py-3 section-label text-[10px]">Impact</th>
                  <th className="text-left px-4 py-3 section-label text-[10px]">Status</th>
                  <th className="text-left px-4 py-3 section-label text-[10px]">Time</th>
                  <th className="text-right px-4 py-3 section-label text-[10px]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((order) => (
                  <tr key={order.id} className="border-b border-white/3 hover:bg-indigo/4 transition-colors">
                    <td className="px-4 py-3">
                      <span className="font-mono text-data-sm text-indigo">{order.id}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-text-2">{order.agent}</td>
                    <td className="px-4 py-3 text-sm text-text-3">{order.action_type}</td>
                    <td className="px-4 py-3"><RiskScore score={order.risk_level === "high" ? 0.8 : order.risk_level === "medium" ? 0.5 : 0.15} /></td>
                    <td className="px-4 py-3"><ConfidencePill value={order.confidence} /></td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-data-sm text-text-1">{formatCurrency(order.financial_impact)}</span>
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={order.status} /></td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-text-3">{formatTimestamp(order.created_at)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        {order.status === "pending" && (
                          <>
                            <button
                              onClick={() => approveMutation.mutate({ id: order.id })}
                              disabled={approveMutation.isPending}
                              className="p-1.5 rounded hover:bg-emerald/10 transition-colors"
                            >
                              <CheckCircle className="w-3.5 h-3.5 text-emerald" />
                            </button>
                            <button
                              onClick={() => rejectMutation.mutate({ id: order.id, reason: "Manual rejection" })}
                              disabled={rejectMutation.isPending}
                              className="p-1.5 rounded hover:bg-red/10 transition-colors"
                            >
                              <XCircle className="w-3.5 h-3.5 text-red" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {filtered.length === 0 && !approvalsQuery.isLoading && (
            <div className="flex flex-col items-center justify-center py-12">
              <CheckCircle className="w-12 h-12 text-emerald mb-3" />
              <p className="text-sm text-text-2">No orders match your filters</p>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs text-text-3">
            Showing {filtered.length} of {orders.length} orders
          </span>
        </div>
      </div>
    </Shell>
  )
}
