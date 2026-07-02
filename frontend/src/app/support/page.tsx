"use client"

import { useState } from "react"
import {
  MessageSquare,
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  ChevronLeft,
  ChevronRight,
  Star,
  Bot,
  Eye,
  UserPlus,
  MoreHorizontal,
} from "lucide-react"
import Shell from "@/components/layout/Shell"
import { cn } from "@/lib/utils"

const filters = ["All Tickets", "Escalated", "AI Resolved", "Pending"]

const metrics = [
  {
    label: "TOTAL TICKETS",
    value: "5,412",
    change: "+12%",
    changeDir: "up" as const,
    icon: MessageSquare,
    iconBg: "bg-primary/10",
    iconColor: "text-primary",
  },
  {
    label: "RESOLUTION RATE",
    value: "84.2%",
    change: "+3%",
    changeDir: "up" as const,
    icon: CheckCircle2,
    iconBg: "bg-success/10",
    iconColor: "text-success",
  },
  {
    label: "AVG RESPONSE TIME",
    value: "1.2s",
    change: "improving",
    changeDir: "down" as const,
    icon: Clock,
    iconBg: "bg-info/10",
    iconColor: "text-info",
  },
  {
    label: "ESCALATION RATE",
    value: "8.3%",
    change: "decreasing",
    changeDir: "down" as const,
    icon: AlertTriangle,
    iconBg: "bg-warning/10",
    iconColor: "text-warning",
  },
]

const tickets = [
  {
    id: "TK-8901",
    customer: "Emily Watson",
    issue: "Refund Request",
    issueClass: "badge-primary",
    priority: "HIGH",
    priorityClass: "badge-danger",
    confidence: 94,
    confidenceClass: "confidence-high",
    status: "RESOLVED",
    statusClass: "badge-success",
    action: "View",
  },
  {
    id: "TK-8902",
    customer: "Carlos Mendez",
    issue: "Shipping Delay",
    issueClass: "badge-warning",
    priority: "MEDIUM",
    priorityClass: "badge-warning",
    confidence: 87,
    confidenceClass: "confidence-high",
    status: "ESCALATED",
    statusClass: "badge-danger",
    action: "Review",
  },
  {
    id: "TK-8903",
    customer: "Lisa Park",
    issue: "Product Defect",
    issueClass: "badge-danger",
    priority: "CRITICAL",
    priorityClass: "badge-danger",
    confidence: 92,
    confidenceClass: "confidence-high",
    status: "AI WORKING",
    statusClass: "badge-info",
    action: "View",
  },
  {
    id: "TK-8904",
    customer: "Robert Singh",
    issue: "Account Issue",
    issueClass: "badge-muted",
    priority: "LOW",
    priorityClass: "badge-muted",
    confidence: 96,
    confidenceClass: "confidence-high",
    status: "RESOLVED",
    statusClass: "badge-success",
    action: "View",
  },
  {
    id: "TK-8905",
    customer: "Maria Garcia",
    issue: "Billing Error",
    issueClass: "badge-primary",
    priority: "HIGH",
    priorityClass: "badge-danger",
    confidence: 89,
    confidenceClass: "confidence-medium",
    status: "PENDING",
    statusClass: "badge-warning",
    action: "Assign",
  },
  {
    id: "TK-8906",
    customer: "Tom Anderson",
    issue: "Technical Issue",
    issueClass: "badge-info",
    priority: "MEDIUM",
    priorityClass: "badge-warning",
    confidence: 81,
    confidenceClass: "confidence-medium",
    status: "AI WORKING",
    statusClass: "badge-info",
    action: "View",
  },
]

const actionIcons: Record<string, typeof Eye> = {
  View: Eye,
  Review: Eye,
  Assign: UserPlus,
}

export default function SupportPage() {
  const [activeFilter, setActiveFilter] = useState("All Tickets")

  const filteredTickets = tickets.filter((ticket) => {
    if (activeFilter === "Escalated") return ticket.status === "ESCALATED"
    if (activeFilter === "AI Resolved") return ticket.status === "RESOLVED"
    if (activeFilter === "Pending") return ticket.status === "PENDING"
    return true
  })

  return (
    <Shell
      title="Customer Support"
      subtitle="AI-powered ticket orchestration and automated customer resolution workflows."
    >
      <div className="space-y-6">
        <div className="flex items-center gap-1 bg-surface rounded-card p-1 border border-border w-fit">
          {filters.map((filter) => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              className={cn(
                "px-4 py-2 rounded-button text-sm font-medium transition-all duration-200",
                activeFilter === filter
                  ? "bg-primary text-white shadow-lg shadow-primary/20"
                  : "text-text-secondary hover:text-text-primary hover:bg-surface-2"
              )}
            >
              {filter}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-4 gap-4">
          {metrics.map((m) => {
            const Icon = m.icon
            return (
              <div key={m.label} className="card">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-9 h-9 rounded-button ${m.iconBg} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${m.iconColor}`} />
                  </div>
                  <span className="label-caps">{m.label}</span>
                </div>
                <div className="font-display text-data-lg text-text-primary">{m.value}</div>
                <div className="mt-1">
                  {m.changeDir === "up" && (
                    <span className="inline-flex items-center gap-1 text-body-sm text-success font-medium">
                      <TrendingUp className="w-3 h-3" />{m.change}
                    </span>
                  )}
                  {m.changeDir === "down" && (
                    <span className="inline-flex items-center gap-1 text-body-sm text-success font-medium">
                      <TrendingDown className="w-3 h-3" />{m.change}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr className="border-b border-border">
                  <th className="label-caps px-5 py-4 text-left">TICKET ID</th>
                  <th className="label-caps px-5 py-4 text-left">CUSTOMER</th>
                  <th className="label-caps px-5 py-4 text-left">ISSUE TYPE</th>
                  <th className="label-caps px-5 py-4 text-center">PRIORITY</th>
                  <th className="label-caps px-5 py-4 text-center">AI CONFIDENCE</th>
                  <th className="label-caps px-5 py-4 text-center">STATUS</th>
                  <th className="label-caps px-5 py-4 text-right">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {filteredTickets.map((ticket) => {
                  const ActionIcon = actionIcons[ticket.action] || Eye
                  return (
                    <tr key={ticket.id} className="group transition-colors">
                      <td className="px-5 py-4">
                        <span className="font-mono text-data-sm text-primary">{ticket.id}</span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-surface-3 flex items-center justify-center shrink-0">
                            <span className="text-xs font-medium text-text-secondary">
                              {ticket.customer.split(" ").map((n) => n[0]).join("")}
                            </span>
                          </div>
                          <span className="text-sm font-medium text-text-primary">{ticket.customer}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className={ticket.issueClass}>{ticket.issue}</span>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className={ticket.priorityClass}>{ticket.priority}</span>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className={ticket.confidenceClass}>
                          {ticket.confidence}%
                        </span>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className={ticket.statusClass}>{ticket.status}</span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <button className="btn-ghost text-xs gap-1.5">
                          <ActionIcon className="w-3.5 h-3.5" />
                          {ticket.action}
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="dot-green" />
              <span className="text-sm text-text-secondary">
                AI Auto-Resolved Today: <span className="font-mono text-data-sm text-success">847</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="dot-blue" />
              <span className="text-sm text-text-secondary">
                Customer Satisfaction: <span className="font-mono text-data-sm text-primary">4.6/5</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-sm text-text-muted">
              Showing <span className="text-text-secondary font-medium">6</span> of <span className="text-text-secondary font-medium">5,412</span> tickets
            </span>
            <div className="flex items-center gap-1">
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors border border-border">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center bg-primary text-white shadow-lg shadow-primary/20 transition-colors">
                1
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors border border-border">
                2
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors border border-border">
                3
              </button>
              <span className="text-text-muted px-1">...</span>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors border border-border">
                902
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors border border-border">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  )
}
