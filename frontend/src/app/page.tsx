"use client"

import { useQuery } from "@tanstack/react-query"
import {
  ShoppingCart,
  DollarSign,
  Bot,
  AlertTriangle,
  TrendingUp,
  Users,
  RefreshCw,
  HeadphonesIcon,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { MetricCard } from "@/components/shared/MetricCard"
import { ActivityFeed } from "@/components/shared/ActivityFeed"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { ConfidencePill } from "@/components/shared/ConfidencePill"
import { MetricCardSkeleton, ActivityFeedSkeleton } from "@/components/shared/Skeleton"
import { formatCurrency, formatTimestamp, getAgentColor } from "@/lib/utils"
import type { Activity, Agent } from "@/types/api"

// Mock data for demo
const mockMetrics = {
  revenue: { value: 125430, delta: 12.5 },
  orders: { value: 847, delta: 8.3 },
  pendingDecisions: { value: 23, delta: -15.2 },
  flaggedOrders: { value: 7, delta: 2.1 },
}

const mockAgents: Agent[] = [
  { id: "fraud", name: "fraud_detection", displayName: "Fraud Detection", description: "Analyzes orders for fraud patterns", status: "active", accuracy: 95.2, confidence: 0.92, processedToday: 120, lastActivity: new Date().toISOString(), uptime: 99.9, errorRate: 0.1, avgResponseTime: 1.2, color: "red" },
  { id: "inventory", name: "inventory_management", displayName: "Inventory", description: "Manages stock levels and reorders", status: "active", accuracy: 88.5, confidence: 0.87, processedToday: 45, lastActivity: new Date().toISOString(), uptime: 99.8, errorRate: 0.2, avgResponseTime: 2.1, color: "cyan" },
  { id: "pricing", name: "price_optimization", displayName: "Pricing", description: "Dynamic pricing optimization", status: "active", accuracy: 91.3, confidence: 0.89, processedToday: 89, lastActivity: new Date().toISOString(), uptime: 99.7, errorRate: 0.1, avgResponseTime: 0.5, color: "amber" },
  { id: "reviews", name: "review_moderation", displayName: "Reviews", description: "Sentiment analysis and moderation", status: "active", accuracy: 90.1, confidence: 0.85, processedToday: 34, lastActivity: new Date().toISOString(), uptime: 99.9, errorRate: 0.0, avgResponseTime: 0.8, color: "violet" },
  { id: "marketing", name: "marketing_automation", displayName: "Marketing", description: "Campaign automation and optimization", status: "active", accuracy: 87.2, confidence: 0.83, processedToday: 28, lastActivity: new Date().toISOString(), uptime: 99.8, errorRate: 0.1, avgResponseTime: 1.5, color: "indigo" },
  { id: "cart", name: "cart_recovery", displayName: "Cart Recovery", description: "Recovers abandoned carts", status: "active", accuracy: 85.6, confidence: 0.81, processedToday: 52, lastActivity: new Date().toISOString(), uptime: 99.9, errorRate: 0.0, avgResponseTime: 2.5, color: "emerald" },
  { id: "support", name: "customer_support", displayName: "Support", description: "Customer support automation", status: "active", accuracy: 89.4, confidence: 0.86, processedToday: 67, lastActivity: new Date().toISOString(), uptime: 99.8, errorRate: 0.1, avgResponseTime: 2.8, color: "cyan" },
]

const mockActivities: Activity[] = [
  { id: "1", type: "decision", agent: "fraud_detection", action: "approved", description: "Order #ORD-8847 — Risk score 0.12", confidence: 0.95, timestamp: new Date(Date.now() - 120000).toISOString() },
  { id: "2", type: "alert", agent: "fraud_detection", action: "flagged", description: "Order #ORD-8852 — Suspicious shipping address", confidence: 0.78, timestamp: new Date(Date.now() - 300000).toISOString() },
  { id: "3", type: "decision", agent: "cart_recovery", action: "sent email", description: "Recovery email sent to customer@example.com", confidence: 0.82, timestamp: new Date(Date.now() - 600000).toISOString() },
  { id: "4", type: "decision", agent: "price_optimization", action: "updated price", description: "PROD-2847: $49.99 → $44.99", confidence: 0.89, timestamp: new Date(Date.now() - 900000).toISOString() },
  { id: "5", type: "decision", agent: "customer_support", action: "resolved ticket", description: "Ticket #T-1234 — Auto-resolved billing inquiry", confidence: 0.88, timestamp: new Date(Date.now() - 1200000).toISOString() },
  { id: "6", type: "decision", agent: "review_moderation", action: "approved review", description: "5-star review auto-approved", confidence: 0.94, timestamp: new Date(Date.now() - 1500000).toISOString() },
  { id: "7", type: "decision", agent: "inventory_management", action: "reorder triggered", description: "PROD-1234 — 100 units reordered", confidence: 0.86, timestamp: new Date(Date.now() - 1800000).toISOString() },
  { id: "8", type: "decision", agent: "marketing_automation", action: "campaign sent", description: "Flash sale email to 2,400 customers", confidence: 0.84, timestamp: new Date(Date.now() - 2100000).toISOString() },
]

const mockPendingDecisions = [
  { id: "ORD-8852", agent: "fraud_detection", type: "Fraud Review", confidence: 0.78, status: "flagged", createdAt: new Date(Date.now() - 300000).toISOString() },
  { id: "ORD-8853", agent: "fraud_detection", type: "Fraud Review", confidence: 0.65, status: "pending", createdAt: new Date(Date.now() - 600000).toISOString() },
  { id: "ORD-8854", agent: "price_optimization", type: "Price Change", confidence: 0.91, status: "pending", createdAt: new Date(Date.now() - 900000).toISOString() },
]

export default function DashboardPage() {
  return (
    <Shell>
      <Topbar title="Command Center" subtitle="Real-time operations overview" />
      
      <div className="p-6 space-y-6">
        {/* Alerts strip */}
        <div className="flex items-center gap-3 p-3 rounded-lg bg-amber/10 border border-amber/20">
          <AlertTriangle className="w-4 h-4 text-amber" />
          <span className="text-sm text-amber">
            3 orders pending review — 2 flagged for fraud, 1 price change
          </span>
        </div>

        {/* Metrics row */}
        <div className="grid grid-cols-4 gap-4">
          <MetricCard
            label="Revenue Today"
            value={mockMetrics.revenue.value}
            delta={mockMetrics.revenue.delta}
            deltaLabel="vs yesterday"
            icon={<DollarSign className="w-4 h-4 text-emerald" />}
            color="bg-emerald/10"
            format="currency"
          />
          <MetricCard
            label="Orders Today"
            value={mockMetrics.orders.value}
            delta={mockMetrics.orders.delta}
            deltaLabel="vs yesterday"
            icon={<ShoppingCart className="w-4 h-4 text-indigo" />}
            color="bg-indigo/10"
          />
          <MetricCard
            label="Pending Decisions"
            value={mockMetrics.pendingDecisions.value}
            delta={mockMetrics.pendingDecisions.delta}
            deltaLabel="vs yesterday"
            icon={<Bot className="w-4 h-4 text-amber" />}
            color="bg-amber/10"
          />
          <MetricCard
            label="Flagged Orders"
            value={mockMetrics.flaggedOrders.value}
            delta={mockMetrics.flaggedOrders.delta}
            deltaLabel="vs yesterday"
            icon={<AlertTriangle className="w-4 h-4 text-red" />}
            color="bg-red/10"
          />
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-3 gap-6">
          {/* Activity feed - 2 columns */}
          <div className="col-span-2 card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-text-1">Recent Activity</h2>
              <span className="text-xs text-text-3">Live updates</span>
            </div>
            <ActivityFeed activities={mockActivities} />
          </div>

          {/* Right panel */}
          <div className="space-y-6">
            {/* Pending decisions */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-display font-semibold text-text-1">Pending Review</h2>
                <button className="text-xs text-indigo hover:text-indigo-400 transition-colors">
                  View all
                </button>
              </div>
              <div className="space-y-3">
                {mockPendingDecisions.map((decision) => (
                  <div
                    key={decision.id}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-surface-2 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-data-sm text-indigo">{decision.id}</span>
                      <StatusBadge status={decision.status} />
                    </div>
                    <ConfidencePill value={decision.confidence} />
                  </div>
                ))}
              </div>
            </div>

            {/* Agent status */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-display font-semibold text-text-1">Agent Status</h2>
                <button className="text-xs text-indigo hover:text-indigo-400 transition-colors">
                  View all
                </button>
              </div>
              <div className="space-y-3">
                {mockAgents.slice(0, 5).map((agent) => (
                  <div
                    key={agent.id}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className={agent.status === "active" ? "dot-active" : "dot-paused"} />
                      <span className="text-sm text-text-2">{agent.displayName}</span>
                    </div>
                    <span className="font-mono text-data-xs text-text-3">
                      {agent.processedToday} today
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom row - Agent performance */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-semibold text-text-1">Agent Performance</h2>
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-3">Last 24 hours</span>
            </div>
          </div>
          <div className="grid grid-cols-7 gap-4">
            {mockAgents.map((agent) => (
              <div
                key={agent.id}
                className="p-3 rounded-lg bg-surface-2 hover:bg-surface-3 transition-colors"
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className={agent.status === "active" ? "dot-active" : "dot-paused"} />
                  <span className="text-sm font-medium text-text-1">{agent.displayName}</span>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-3">Accuracy</span>
                    <span className="font-mono text-data-xs text-emerald">{agent.accuracy}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-3">Processed</span>
                    <span className="font-mono text-data-xs text-text-2">{agent.processedToday}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-3">Avg Time</span>
                    <span className="font-mono text-data-xs text-text-2">{agent.avgResponseTime}s</span>
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
