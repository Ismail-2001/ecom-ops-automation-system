"use client"

import { useState } from "react"
import {
  Bot,
  Shield,
  Package,
  DollarSign,
  Star,
  Megaphone,
  HeadphonesIcon,
  RefreshCw,
  Activity,
  Zap,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Settings,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { ConfidencePill } from "@/components/shared/ConfidencePill"
import { MetricCardSkeleton } from "@/components/shared/Skeleton"
import { useAgentStatus } from "@/lib/hooks"
import { cn } from "@/lib/utils"
import type { AgentStatus } from "@/lib/api"

const fallbackAgents: AgentStatus[] = [
  { name: "fraud_detection", display_name: "Fraud Detection", status: "active", accuracy: 95.2, confidence: 0.92, processed_today: 120, last_activity: new Date().toISOString(), uptime: 99.9, error_rate: 0.1, avg_response_time: 1.2 },
  { name: "inventory_management", display_name: "Inventory Management", status: "active", accuracy: 88.5, confidence: 0.87, processed_today: 45, last_activity: new Date().toISOString(), uptime: 99.8, error_rate: 0.2, avg_response_time: 2.1 },
  { name: "price_optimization", display_name: "Price Optimization", status: "active", accuracy: 91.3, confidence: 0.89, processed_today: 89, last_activity: new Date().toISOString(), uptime: 99.7, error_rate: 0.1, avg_response_time: 0.5 },
  { name: "review_moderation", display_name: "Review Moderation", status: "active", accuracy: 90.1, confidence: 0.85, processed_today: 34, last_activity: new Date().toISOString(), uptime: 99.9, error_rate: 0.0, avg_response_time: 0.8 },
  { name: "marketing_automation", display_name: "Marketing Automation", status: "active", accuracy: 87.2, confidence: 0.83, processed_today: 28, last_activity: new Date().toISOString(), uptime: 99.8, error_rate: 0.1, avg_response_time: 1.5 },
  { name: "cart_recovery", display_name: "Cart Recovery", status: "active", accuracy: 85.6, confidence: 0.81, processed_today: 52, last_activity: new Date().toISOString(), uptime: 99.9, error_rate: 0.0, avg_response_time: 2.5 },
  { name: "customer_support", display_name: "Customer Support", status: "active", accuracy: 89.4, confidence: 0.86, processed_today: 67, last_activity: new Date().toISOString(), uptime: 99.8, error_rate: 0.1, avg_response_time: 2.8 },
]

const agentIcons: Record<string, any> = {
  fraud_detection: Shield,
  inventory_management: Package,
  price_optimization: DollarSign,
  review_moderation: Star,
  marketing_automation: Megaphone,
  cart_recovery: RefreshCw,
  customer_support: HeadphonesIcon,
}

const agentColors: Record<string, string> = {
  fraud_detection: "red",
  inventory_management: "cyan",
  price_optimization: "amber",
  review_moderation: "violet",
  marketing_automation: "indigo",
  cart_recovery: "emerald",
  customer_support: "cyan",
}

export default function AgentsPage() {
  const agentsQuery = useAgentStatus()
  const agents = agentsQuery.data?.length ? agentsQuery.data : fallbackAgents
  const [selected, setSelected] = useState<AgentStatus>(agents[0])

  return (
    <Shell>
      <Topbar
        title="AI Agents"
        subtitle="Manage and monitor intelligent automation"
        actions={
          <button className="btn-primary">
            <Settings className="w-3.5 h-3.5" />
            Configure
          </button>
        }
      />

      <div className="p-6">
        <div className="grid grid-cols-3 gap-6">
          {/* Agent cards */}
          <div className="col-span-2">
            {agentsQuery.isLoading ? (
              <div className="grid grid-cols-2 gap-4">
                <MetricCardSkeleton /><MetricCardSkeleton />
                <MetricCardSkeleton /><MetricCardSkeleton />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {agents.map((agent) => {
                  const Icon = agentIcons[agent.name] || Bot
                  const color = agentColors[agent.name] || "indigo"
                  const isSelected = selected.name === agent.name

                  return (
                    <button
                      key={agent.name}
                      onClick={() => setSelected(agent)}
                      className={cn(
                        "card text-left transition-all duration-150",
                        isSelected && "border-indigo card-glow",
                      )}
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", `bg-${color}/10`)}>
                            <Icon className={cn("w-5 h-5", `text-${color}`)} />
                          </div>
                          <div>
                            <h3 className="font-display font-semibold text-text-1">{agent.display_name}</h3>
                            <div className="flex items-center gap-2 mt-1">
                              <div className={agent.status === "active" ? "dot-active" : "dot-paused"} />
                              <StatusBadge status={agent.status} />
                            </div>
                          </div>
                        </div>
                        <ConfidencePill value={agent.confidence} />
                      </div>

                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <div className="section-label text-[9px] mb-1">Accuracy</div>
                          <div className="font-mono text-data-sm text-emerald">{agent.accuracy}%</div>
                        </div>
                        <div>
                          <div className="section-label text-[9px] mb-1">Processed</div>
                          <div className="font-mono text-data-sm text-text-2">{agent.processed_today}</div>
                        </div>
                        <div>
                          <div className="section-label text-[9px] mb-1">Avg Time</div>
                          <div className="font-mono text-data-sm text-text-2">{agent.avg_response_time}s</div>
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Detail panel */}
          <div className="space-y-4">
            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <div className={cn("w-12 h-12 rounded-lg flex items-center justify-center", `bg-${agentColors[selected.name] || "indigo"}/10`)}>
                  {(() => {
                    const Icon = agentIcons[selected.name] || Bot
                    return <Icon className={cn("w-6 h-6", `text-${agentColors[selected.name] || "indigo"}`)} />
                  })()}
                </div>
                <div>
                  <h2 className="font-display font-bold text-lg text-text-1">{selected.display_name}</h2>
                  <div className="flex items-center gap-2 mt-1">
                    <div className={selected.status === "active" ? "dot-active" : "dot-paused"} />
                    <StatusBadge status={selected.status} size="md" />
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="section-label mb-4">Performance</h3>
              <div className="space-y-4">
                {[
                  { icon: CheckCircle, label: "Accuracy", value: `${selected.accuracy}%`, color: "emerald" },
                  { icon: Zap, label: "Confidence", pill: <ConfidencePill value={selected.confidence} /> },
                  { icon: Activity, label: "Processed Today", value: String(selected.processed_today), color: "text-text-2" },
                  { icon: Clock, label: "Avg Response", value: `${selected.avg_response_time}s`, color: "text-text-2" },
                  { icon: AlertCircle, label: "Error Rate", value: `${selected.error_rate}%`, color: "text-text-2" },
                  { icon: TrendingUp, label: "Uptime", value: `${selected.uptime}%`, color: "emerald" },
                ].map(({ icon: Icon, label, value, pill, color }) => (
                  <div key={label} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Icon className={`w-4 h-4 text-${color || "indigo"}`} />
                      <span className="text-sm text-text-2">{label}</span>
                    </div>
                    {pill || <span className={`font-mono text-data-sm text-${color}`}>{value}</span>}
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
