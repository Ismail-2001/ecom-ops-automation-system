"use client"

import { useState } from "react"
import {
  Shield,
  ClipboardList,
  DollarSign,
  MessageSquare,
  Megaphone,
  ShoppingCart,
  Headphones,
  Plus,
  Activity,
} from "lucide-react"
import Shell from "@/components/layout/Shell"

type AgentStatus = "ACTIVE" | "BUSY" | "IDLE"

interface Agent {
  id: string
  name: string
  description: string
  icon: any
  status: AgentStatus
  metrics: { label: string; value: string }[]
  sparkColor: string
}

const agents: Agent[] = [
  {
    id: "fraud",
    name: "Fraud Detection",
    description: "Real-time transaction auditing.",
    icon: Shield,
    status: "ACTIVE",
    metrics: [
      { label: "ACCURACY", value: "98.2%" },
      { label: "DECISIONS", value: "1,242" },
    ],
    sparkColor: "#10B981",
  },
  {
    id: "inventory",
    name: "Inventory",
    description: "Stock optimization & replenishment.",
    icon: ClipboardList,
    status: "ACTIVE",
    metrics: [
      { label: "PRECISION", value: "99.1%" },
      { label: "DECISIONS", value: "456" },
    ],
    sparkColor: "#06B6D4",
  },
  {
    id: "price",
    name: "Price Optimizer",
    description: "Dynamic market re-pricing.",
    icon: DollarSign,
    status: "BUSY",
    metrics: [
      { label: "PROFIT Δ", value: "+14.2%" },
      { label: "DECISIONS", value: "8,902" },
    ],
    sparkColor: "#F59E0B",
  },
  {
    id: "review",
    name: "Review Moderator",
    description: "Sentiment & spam filtering.",
    icon: MessageSquare,
    status: "IDLE",
    metrics: [
      { label: "SENTIMENT", value: "Neutral" },
      { label: "DECISIONS", value: "129" },
    ],
    sparkColor: "#64748B",
  },
  {
    id: "marketing",
    name: "Marketing",
    description: "Ad spend and copy generation.",
    icon: Megaphone,
    status: "ACTIVE",
    metrics: [
      { label: "ROAS", value: "4.2x" },
      { label: "DECISIONS", value: "231" },
    ],
    sparkColor: "#6366F1",
  },
  {
    id: "cart",
    name: "Cart Recovery",
    description: "Drip campaigns & offer intent.",
    icon: ShoppingCart,
    status: "ACTIVE",
    metrics: [
      { label: "RECOVERY", value: "22.4%" },
      { label: "DECISIONS", value: "3,110" },
    ],
    sparkColor: "#10B981",
  },
  {
    id: "support",
    name: "Customer Support",
    description: "Tier-1 automated ticket resolution.",
    icon: Headphones,
    status: "BUSY",
    metrics: [
      { label: "RESOLUTION", value: "84%" },
      { label: "AVG RESPONSE", value: "1.2s" },
      { label: "TICKETS", value: "5,412" },
    ],
    sparkColor: "#EF4444",
  },
]

const inferenceLogs = [
  {
    timestamp: "14:22:01.04",
    agent: "Fraud Detector",
    action: "Blocked Tx #9012 (High Risk)",
    result: "PREVENTED",
    resultClass: "badge-success",
    latency: "82ms",
  },
  {
    timestamp: "14:21:58.21",
    agent: "Inventory",
    action: "Restock triggered: SKU-441",
    result: "ORDERED",
    resultClass: "badge-info",
    latency: "114ms",
  },
  {
    timestamp: "14:21:44.92",
    agent: "Price Optimizer",
    action: "Adjusted MSRP +2.1% (Competitor Out)",
    result: "APPLIED",
    resultClass: "badge-success",
    latency: "45ms",
  },
]

function Sparkline({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 120 32" className="w-full h-8 mt-3 opacity-60">
      <path
        d="M0,24 C10,22 15,18 25,20 C35,22 40,14 50,16 C60,18 65,10 75,12 C85,14 90,8 100,10 C110,12 115,6 120,8"
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M0,24 C10,22 15,18 25,20 C35,22 40,14 50,16 C60,18 65,10 75,12 C85,14 90,8 100,10 C110,12 115,6 120,8 L120,32 L0,32 Z"
        fill={color}
        opacity="0.1"
      />
    </svg>
  )
}

const statusConfig: Record<AgentStatus, { dot: string; badge: string; label: string }> = {
  ACTIVE: { dot: "dot-green", badge: "badge-success", label: "ACTIVE" },
  BUSY: { dot: "dot-amber", badge: "badge-warning", label: "BUSY" },
  IDLE: { dot: "dot-gray", badge: "badge-muted", label: "IDLE" },
}

const filterTabs = ["All Agents", "Active", "Maintenance"] as const

export default function AgentsPage() {
  const [activeFilter, setActiveFilter] = useState<string>("All Agents")

  const filteredAgents = agents.filter((agent) => {
    if (activeFilter === "All Agents") return true
    if (activeFilter === "Active") return agent.status === "ACTIVE" || agent.status === "BUSY"
    if (activeFilter === "Maintenance") return agent.status === "IDLE"
    return true
  })

  return (
    <Shell
      title="Autonomous Agents"
      subtitle="Manage and monitor your AI-driven operational workforce."
      actions={
        <div className="flex items-center gap-1 bg-surface rounded-card p-1 border border-border">
          {filterTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveFilter(tab)}
              className={
                activeFilter === tab
                  ? "px-3 py-1.5 rounded-button text-xs font-medium bg-primary/15 text-primary transition-colors"
                  : "px-3 py-1.5 rounded-button text-xs font-medium text-text-muted hover:text-text-secondary transition-colors"
              }
            >
              {tab}
            </button>
          ))}
        </div>
      }
    >
      <div className="grid grid-cols-4 gap-4">
        {filteredAgents.map((agent) => {
          const Icon = agent.icon
          const sc = statusConfig[agent.status]
          return (
            <div key={agent.id} className="card-hover group">
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 rounded-button bg-primary/10 flex items-center justify-center">
                  <Icon className="w-5 h-5 text-primary" />
                </div>
                <span className={sc.badge}>{sc.label}</span>
              </div>
              <h3 className="font-display font-semibold text-text-primary mb-1">{agent.name}</h3>
              <p className="text-body-sm text-text-muted mb-3">{agent.description}</p>
              <div className="flex gap-4">
                {agent.metrics.map((m) => (
                  <div key={m.label}>
                    <div className="label-caps text-[10px] mb-0.5">{m.label}</div>
                    <div className="font-mono text-data-sm text-text-primary">{m.value}</div>
                  </div>
                ))}
              </div>
              <Sparkline color={agent.sparkColor} />
            </div>
          )
        })}

        <button className="card border-2 border-dashed border-border hover:border-primary/40 flex flex-col items-center justify-center gap-3 min-h-[200px] transition-all duration-200 group">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
            <Plus className="w-6 h-6 text-primary" />
          </div>
          <span className="label-caps text-text-muted group-hover:text-primary transition-colors">Deploy New Agent</span>
        </button>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="col-span-2 card">
          <h3 className="label-caps mb-4">Inference Logs</h3>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>TIMESTAMP</th>
                  <th>AGENT</th>
                  <th>ACTION TAKEN</th>
                  <th>RESULT</th>
                  <th>LATENCY</th>
                </tr>
              </thead>
              <tbody>
                {inferenceLogs.map((log, i) => (
                  <tr key={i}>
                    <td className="font-mono text-data-sm text-text-secondary">{log.timestamp}</td>
                    <td className="text-body-md text-text-primary">{log.agent}</td>
                    <td className="text-body-md text-text-secondary">{log.action}</td>
                    <td><span className={log.resultClass}>{log.result}</span></td>
                    <td className="font-mono text-data-sm text-text-muted">{log.latency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card flex flex-col justify-center">
          <div className="flex items-center gap-3 mb-3">
            <Activity className="w-5 h-5 text-success" />
            <span className="font-display font-semibold text-text-primary">System Healthy</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill bg-success" style={{ width: "94%" }} />
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-body-sm text-text-muted">Uptime</span>
            <span className="font-mono text-data-sm text-success">94%</span>
          </div>
        </div>
      </div>
    </Shell>
  )
}
