"use client"

import { useState } from "react"
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Bot,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { MetricCard } from "@/components/shared/MetricCard"
import { MetricCardSkeleton } from "@/components/shared/Skeleton"
import { useAnalytics } from "@/lib/hooks"
import { cn, formatCurrency } from "@/lib/utils"

const fallbackAnalytics = {
  summary: {
    total_decisions: 24500,
    approval_rate: 87.3,
    actions_auto_approved: 21400,
    total_financial_impact: 56000,
    avg_confidence: 0.89,
    avg_decision_time_minutes: 1.2,
  },
  graduation: [],
  risk_distribution: { critical: 3, high: 12, medium: 34, low: 51 },
  charts: {
    approval_rate_over_time: [],
    volume_by_agent: [
      { agent: "fraud_detection", count: 8200 },
      { agent: "inventory_management", count: 3100 },
      { agent: "price_optimization", count: 5800 },
      { agent: "review_moderation", count: 2400 },
      { agent: "marketing_automation", count: 1900 },
      { agent: "cart_recovery", count: 3200 },
      { agent: "customer_support", count: 4400 },
    ],
    decision_time_dist: {},
  },
}

const chartData = [
  { name: "Jan", revenue: 85000 }, { name: "Feb", revenue: 92000 },
  { name: "Mar", revenue: 98000 }, { name: "Apr", revenue: 105000 },
  { name: "May", revenue: 112000 }, { name: "Jun", revenue: 118000 },
  { name: "Jul", revenue: 125000 }, { name: "Aug", revenue: 132000 },
  { name: "Sep", revenue: 128000 }, { name: "Oct", revenue: 135000 },
  { name: "Nov", revenue: 142000 }, { name: "Dec", revenue: 150000 },
]

const agentRoi = [
  { agent: "Fraud Detection", savings: 5000, roi: 300, color: "red" },
  { agent: "Inventory Management", savings: 8000, roi: 400, color: "cyan" },
  { agent: "Price Optimization", savings: 12000, roi: 600, color: "amber" },
  { agent: "Review Moderation", savings: 3000, roi: 250, color: "violet" },
  { agent: "Marketing Automation", savings: 10000, roi: 500, color: "indigo" },
  { agent: "Cart Recovery", savings: 8000, roi: 450, color: "emerald" },
  { agent: "Customer Support", savings: 10000, roi: 350, color: "cyan" },
]

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("30d")
  const analytics = useAnalytics()
  const data = analytics.data || fallbackAnalytics
  const maxRevenue = Math.max(...chartData.map((d) => d.revenue))

  return (
    <Shell>
      <Topbar
        title="Analytics"
        subtitle="ROI and performance metrics"
        actions={
          <div className="flex items-center gap-2">
            {["7d", "30d", "90d", "1y"].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                  timeRange === range ? "bg-indigo/10 text-indigo" : "text-text-3 hover:text-text-2 hover:bg-surface-2",
                )}
              >
                {range}
              </button>
            ))}
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Top metrics */}
        {analytics.isLoading ? (
          <div className="grid grid-cols-4 gap-4">
            <MetricCardSkeleton /><MetricCardSkeleton /><MetricCardSkeleton /><MetricCardSkeleton />
          </div>
        ) : (
          <div className="grid grid-cols-4 gap-4">
            <MetricCard
              label="Total Savings"
              value={formatCurrency(data.summary.total_financial_impact)}
              icon={<DollarSign className="w-4 h-4 text-emerald" />}
              color="bg-emerald/10"
            />
            <MetricCard
              label="Approval Rate"
              value={`${data.summary.approval_rate}%`}
              icon={<TrendingUp className="w-4 h-4 text-indigo" />}
              color="bg-indigo/10"
            />
            <MetricCard
              label="Total Decisions"
              value={data.summary.total_decisions.toLocaleString()}
              icon={<Bot className="w-4 h-4 text-violet" />}
              color="bg-violet/10"
            />
            <MetricCard
              label="Avg Confidence"
              value={`${(data.summary.avg_confidence * 100).toFixed(0)}%`}
              icon={<BarChart3 className="w-4 h-4 text-cyan" />}
              color="bg-cyan/10"
            />
          </div>
        )}

        {/* Revenue chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="section-label">Revenue Trend</h3>
            <span className="text-xs text-text-3">Last 12 months</span>
          </div>
          <div className="flex items-end gap-2 h-48">
            {chartData.map((d) => (
              <div key={d.name} className="flex-1 flex flex-col items-center gap-2">
                <div
                  className="w-full bg-indigo/20 rounded-t transition-all duration-500 hover:bg-indigo/30"
                  style={{ height: `${(d.revenue / maxRevenue) * 100}%` }}
                />
                <span className="text-[10px] text-text-3">{d.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Agent ROI */}
          <div className="card">
            <h3 className="section-label mb-4">Agent ROI</h3>
            <div className="space-y-4">
              {agentRoi.map((agent) => (
                <div key={agent.agent} className="flex items-center gap-3">
                  <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", `bg-${agent.color}/10`)}>
                    <DollarSign className={cn("w-4 h-4", `text-${agent.color}`)} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-text-1">{agent.agent}</span>
                      <span className="font-mono text-data-sm text-emerald">{formatCurrency(agent.savings)}/mo</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                        <div className="h-full bg-indigo rounded-full" style={{ width: `${Math.min(agent.roi / 6, 100)}%` }} />
                      </div>
                      <span className="font-mono text-data-xs text-text-3">{agent.roi}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Risk distribution */}
          <div className="card">
            <h3 className="section-label mb-4">Risk Distribution</h3>
            <div className="space-y-4">
              {Object.entries(data.risk_distribution).map(([level, count]) => {
                const total = Object.values(data.risk_distribution).reduce((a, b) => a + b, 0)
                const pct = total > 0 ? ((count as number) / total) * 100 : 0
                const color = level === "critical" || level === "high" ? "red" : level === "medium" ? "amber" : "emerald"
                return (
                  <div key={level} className="flex items-center gap-3">
                    <span className="text-sm text-text-2 w-20 capitalize">{level}</span>
                    <div className="flex-1 h-2 bg-surface-3 rounded-full overflow-hidden">
                      <div className={`h-full bg-${color} rounded-full`} style={{ width: `${pct}%` }} />
                    </div>
                    <span className="font-mono text-data-xs text-text-3 w-12 text-right">{count as number}</span>
                  </div>
                )
              })}
            </div>

            <div className="mt-6 pt-4 border-t border-border">
              <h4 className="section-label mb-3">Agent Volume</h4>
              <div className="space-y-2">
                {data.charts.volume_by_agent.map((item: any) => (
                  <div key={item.agent} className="flex items-center justify-between text-sm">
                    <span className="text-text-2 capitalize">{item.agent.replace(/_/g, " ")}</span>
                    <span className="font-mono text-data-xs text-text-3">{item.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  )
}
