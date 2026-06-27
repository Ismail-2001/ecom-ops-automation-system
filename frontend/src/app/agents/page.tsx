"use client"

import { useState } from "react"
import {
  Bot,
  Shield,
  Package,
  DollarSign,
  Star,
  Megaphone,
  RefreshCw,
  HeadphonesIcon,
  Activity,
  Zap,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Settings,
  Play,
  Pause,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { ConfidencePill } from "@/components/shared/ConfidencePill"
import { cn, formatNumber, formatPercent, getAgentColor, getAgentDotColor } from "@/lib/utils"
import type { Agent } from "@/types/api"

const agents: Agent[] = [
  {
    id: "fraud",
    name: "fraud_detection",
    displayName: "Fraud Detection",
    description: "Analyzes orders for fraud patterns using ML and rule-based scoring. Detects suspicious shipping addresses, unusual purchase patterns, and high-risk transactions.",
    status: "active",
    accuracy: 95.2,
    confidence: 0.92,
    processedToday: 120,
    lastActivity: new Date().toISOString(),
    uptime: 99.9,
    errorRate: 0.1,
    avgResponseTime: 1.2,
    color: "red",
  },
  {
    id: "inventory",
    name: "inventory_management",
    displayName: "Inventory Management",
    description: "Monitors stock levels, forecasts demand, and triggers automatic reorders. Prevents stockouts and optimizes inventory turnover.",
    status: "active",
    accuracy: 88.5,
    confidence: 0.87,
    processedToday: 45,
    lastActivity: new Date().toISOString(),
    uptime: 99.8,
    errorRate: 0.2,
    avgResponseTime: 2.1,
    color: "cyan",
  },
  {
    id: "pricing",
    name: "price_optimization",
    displayName: "Price Optimization",
    description: "Dynamic pricing engine that analyzes competitor prices, demand elasticity, and margin targets to optimize product pricing in real-time.",
    status: "active",
    accuracy: 91.3,
    confidence: 0.89,
    processedToday: 89,
    lastActivity: new Date().toISOString(),
    uptime: 99.7,
    errorRate: 0.1,
    avgResponseTime: 0.5,
    color: "amber",
  },
  {
    id: "reviews",
    name: "review_moderation",
    displayName: "Review Moderation",
    description: "Automated sentiment analysis and review moderation. Detects spam, flags negative reviews, and generates empathetic responses.",
    status: "active",
    accuracy: 90.1,
    confidence: 0.85,
    processedToday: 34,
    lastActivity: new Date().toISOString(),
    uptime: 99.9,
    errorRate: 0.0,
    avgResponseTime: 0.8,
    color: "violet",
  },
  {
    id: "marketing",
    name: "marketing_automation",
    displayName: "Marketing Automation",
    description: "AI-driven campaign creation and optimization. Segments audiences, personalizes content, and A/B tests for maximum ROI.",
    status: "active",
    accuracy: 87.2,
    confidence: 0.83,
    processedToday: 28,
    lastActivity: new Date().toISOString(),
    uptime: 99.8,
    errorRate: 0.1,
    avgResponseTime: 1.5,
    color: "indigo",
  },
  {
    id: "cart",
    name: "cart_recovery",
    displayName: "Cart Recovery",
    description: "Intelligent abandoned cart recovery with AI-selected strategies. Personalizes discount offers, timing, and messaging for maximum recovery rate.",
    status: "active",
    accuracy: 85.6,
    confidence: 0.81,
    processedToday: 52,
    lastActivity: new Date().toISOString(),
    uptime: 99.9,
    errorRate: 0.0,
    avgResponseTime: 2.5,
    color: "emerald",
  },
  {
    id: "support",
    name: "customer_support",
    displayName: "Customer Support",
    description: "AI-powered ticket handling with sentiment analysis, priority routing, and automated response generation. Escalates complex issues to human agents.",
    status: "active",
    accuracy: 89.4,
    confidence: 0.86,
    processedToday: 67,
    lastActivity: new Date().toISOString(),
    uptime: 99.8,
    errorRate: 0.1,
    avgResponseTime: 2.8,
    color: "cyan",
  },
]

const agentIcons: Record<string, any> = {
  fraud: Shield,
  inventory: Package,
  pricing: DollarSign,
  reviews: Star,
  marketing: Megaphone,
  cart: RefreshCw,
  support: HeadphonesIcon,
}

export default function AgentsPage() {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(agents[0])

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
          {/* Agent cards - 2 columns */}
          <div className="col-span-2">
            <div className="grid grid-cols-2 gap-4">
              {agents.map((agent) => {
                const Icon = agentIcons[agent.id] || Bot
                const isSelected = selectedAgent?.id === agent.id

                return (
                  <button
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent)}
                    className={cn(
                      "card text-left transition-all duration-150",
                      isSelected && "border-indigo card-glow"
                    )}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "w-10 h-10 rounded-lg flex items-center justify-center",
                          `bg-${agent.color}/10`
                        )}>
                          <Icon className={cn("w-5 h-5", `text-${agent.color}`)} />
                        </div>
                        <div>
                          <h3 className="font-display font-semibold text-text-1">{agent.displayName}</h3>
                          <div className="flex items-center gap-2 mt-1">
                            <div className={agent.status === "active" ? "dot-active" : "dot-paused"} />
                            <StatusBadge status={agent.status} />
                          </div>
                        </div>
                      </div>
                      <ConfidencePill value={agent.confidence} />
                    </div>

                    <p className="text-sm text-text-3 line-clamp-2 mb-4">{agent.description}</p>

                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <div className="section-label text-[9px] mb-1">Accuracy</div>
                        <div className="font-mono text-data-sm text-emerald">{agent.accuracy}%</div>
                      </div>
                      <div>
                        <div className="section-label text-[9px] mb-1">Processed</div>
                        <div className="font-mono text-data-sm text-text-2">{agent.processedToday}</div>
                      </div>
                      <div>
                        <div className="section-label text-[9px] mb-1">Avg Time</div>
                        <div className="font-mono text-data-sm text-text-2">{agent.avgResponseTime}s</div>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Agent detail panel */}
          <div className="space-y-4">
            {selectedAgent && (
              <>
                {/* Header */}
                <div className="card">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={cn(
                      "w-12 h-12 rounded-lg flex items-center justify-center",
                      `bg-${selectedAgent.color}/10`
                    )}>
                      {(() => {
                        const Icon = agentIcons[selectedAgent.id] || Bot
                        return <Icon className={cn("w-6 h-6", `text-${selectedAgent.color}`)} />
                      })()}
                    </div>
                    <div>
                      <h2 className="font-display font-bold text-lg text-text-1">{selectedAgent.displayName}</h2>
                      <div className="flex items-center gap-2 mt-1">
                        <div className={selectedAgent.status === "active" ? "dot-active" : "dot-paused"} />
                        <StatusBadge status={selectedAgent.status} size="md" />
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-text-2">{selectedAgent.description}</p>
                </div>

                {/* Performance metrics */}
                <div className="card">
                  <h3 className="section-label mb-4">Performance</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald" />
                        <span className="text-sm text-text-2">Accuracy</span>
                      </div>
                      <span className="font-mono text-data-sm text-emerald">{selectedAgent.accuracy}%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-amber" />
                        <span className="text-sm text-text-2">Confidence</span>
                      </div>
                      <ConfidencePill value={selectedAgent.confidence} />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-indigo" />
                        <span className="text-sm text-text-2">Processed Today</span>
                      </div>
                      <span className="font-mono text-data-sm text-text-2">{selectedAgent.processedToday}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-cyan" />
                        <span className="text-sm text-text-2">Avg Response</span>
                      </div>
                      <span className="font-mono text-data-sm text-text-2">{selectedAgent.avgResponseTime}s</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-red" />
                        <span className="text-sm text-text-2">Error Rate</span>
                      </div>
                      <span className="font-mono text-data-sm text-text-2">{selectedAgent.errorRate}%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-violet" />
                        <span className="text-sm text-text-2">Uptime</span>
                      </div>
                      <span className="font-mono text-data-sm text-emerald">{selectedAgent.uptime}%</span>
                    </div>
                  </div>
                </div>

                {/* Recent decisions */}
                <div className="card">
                  <h3 className="section-label mb-4">Recent Decisions</h3>
                  <div className="space-y-3">
                    {[
                      { id: "ORD-8847", action: "Approved", confidence: 0.95, time: "2m ago" },
                      { id: "ORD-8852", action: "Flagged", confidence: 0.78, time: "5m ago" },
                      { id: "ORD-8853", action: "Approved", confidence: 0.92, time: "8m ago" },
                    ].map((decision) => (
                      <div key={decision.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-surface-2 transition-colors">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-data-sm text-indigo">{decision.id}</span>
                          <span className={cn(
                            "text-xs",
                            decision.action === "Approved" ? "text-emerald" : "text-amber"
                          )}>
                            {decision.action}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <ConfidencePill value={decision.confidence} />
                          <span className="text-[11px] text-text-3">{decision.time}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="card">
                  <h3 className="section-label mb-4">Actions</h3>
                  <div className="space-y-2">
                    <button className="w-full btn-ghost justify-start">
                      <Play className="w-4 h-4" />
                      Run Now
                    </button>
                    <button className="w-full btn-ghost justify-start">
                      <Pause className="w-4 h-4" />
                      Pause Agent
                    </button>
                    <button className="w-full btn-ghost justify-start">
                      <Settings className="w-4 h-4" />
                      Configure Rules
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </Shell>
  )
}
