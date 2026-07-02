"use client"

import { useState } from "react"
import {
  Shield,
  ShieldAlert,
  UserX,
  Users,
  TrendingUp,
  TrendingDown,
  ChevronLeft,
  ChevronRight,
  Lock,
  Eye,
} from "lucide-react"
import Shell from "@/components/layout/Shell"
import { cn } from "@/lib/utils"

const filters = ["All Events", "Critical", "Warning", "Info"]

const metrics = [
  {
    label: "SECURITY SCORE",
    value: "A+",
    icon: Shield,
    iconBg: "bg-success/10",
    iconColor: "text-success",
  },
  {
    label: "THREATS BLOCKED",
    value: "1,247",
    change: "+23%",
    changeDir: "up" as const,
    icon: ShieldAlert,
    iconBg: "bg-primary/10",
    iconColor: "text-primary",
  },
  {
    label: "FAILED LOGINS",
    value: "12",
    change: "-45%",
    changeDir: "down" as const,
    icon: UserX,
    iconBg: "bg-danger/10",
    iconColor: "text-danger",
  },
  {
    label: "ACTIVE SESSIONS",
    value: "847",
    icon: Users,
    iconBg: "bg-info/10",
    iconColor: "text-info",
  },
]

const events = [
  {
    id: "SEC-001",
    time: "14:22:01",
    type: "Brute Force",
    typeClass: "badge-danger",
    severity: "CRITICAL",
    severityClass: "badge-danger",
    ip: "192.168.1.105",
    user: "unknown",
    action: "BLOCKED",
    actionClass: "badge-success",
  },
  {
    id: "SEC-002",
    time: "14:21:45",
    type: "SQL Injection",
    typeClass: "badge-danger",
    severity: "HIGH",
    severityClass: "badge-danger",
    ip: "10.0.0.52",
    user: "admin",
    action: "PREVENTED",
    actionClass: "badge-success",
  },
  {
    id: "SEC-003",
    time: "14:20:33",
    type: "Privilege Escalation",
    typeClass: "badge-danger",
    severity: "CRITICAL",
    severityClass: "badge-danger",
    ip: "172.16.0.88",
    user: "moderator",
    action: "BLOCKED",
    actionClass: "badge-success",
  },
  {
    id: "SEC-004",
    time: "14:19:12",
    type: "API Rate Limit",
    typeClass: "badge-warning",
    severity: "WARNING",
    severityClass: "badge-warning",
    ip: "192.168.1.201",
    user: "api-user",
    action: "THROTTLED",
    actionClass: "badge-warning",
  },
  {
    id: "SEC-005",
    time: "14:18:55",
    type: "Successful Login",
    typeClass: "badge-info",
    severity: "INFO",
    severityClass: "badge-info",
    ip: "10.0.0.15",
    user: "admin",
    action: "ALLOWED",
    actionClass: "badge-info",
  },
  {
    id: "SEC-006",
    time: "14:17:30",
    type: "File Upload",
    typeClass: "badge-warning",
    severity: "WARNING",
    severityClass: "badge-warning",
    ip: "172.16.0.44",
    user: "uploader",
    action: "SCANNING",
    actionClass: "badge-warning",
  },
]

export default function SecurityPage() {
  const [activeFilter, setActiveFilter] = useState("All Events")

  const filteredEvents = events.filter((event) => {
    if (activeFilter === "Critical") return event.severity === "CRITICAL"
    if (activeFilter === "Warning") return event.severity === "WARNING"
    if (activeFilter === "Info") return event.severity === "INFO"
    return true
  })

  return (
    <Shell
      title="Security Operations"
      subtitle="Real-time threat detection, access control monitoring, and compliance management."
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
                <div className={cn(
                  "font-display text-data-lg",
                  m.value === "A+" ? "text-success" : "text-text-primary"
                )}>
                  {m.value}
                </div>
                {m.change && (
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
                )}
              </div>
            )
          })}
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr className="border-b border-border">
                  <th className="label-caps px-5 py-4 text-left">EVENT ID</th>
                  <th className="label-caps px-5 py-4 text-left">TIMESTAMP</th>
                  <th className="label-caps px-5 py-4 text-left">EVENT TYPE</th>
                  <th className="label-caps px-5 py-4 text-center">SEVERITY</th>
                  <th className="label-caps px-5 py-4 text-left">SOURCE IP</th>
                  <th className="label-caps px-5 py-4 text-left">USER</th>
                  <th className="label-caps px-5 py-4 text-center">ACTION</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map((event) => (
                  <tr key={event.id} className="group transition-colors">
                    <td className="px-5 py-4">
                      <span className="font-mono text-data-sm text-primary">{event.id}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="font-mono text-data-sm text-text-secondary">{event.time}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={event.typeClass}>{event.type}</span>
                    </td>
                    <td className="px-5 py-4 text-center">
                      <span className={event.severityClass}>{event.severity}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="font-mono text-data-sm text-text-secondary">{event.ip}</span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        <div className={cn(
                          "w-6 h-6 rounded-full flex items-center justify-center shrink-0",
                          event.user === "unknown" ? "bg-danger/15" : "bg-surface-3"
                        )}>
                          {event.user === "unknown" ? (
                            <UserX className="w-3 h-3 text-danger" />
                          ) : (
                            <span className="text-[10px] font-medium text-text-secondary">
                              {event.user.slice(0, 2).toUpperCase()}
                            </span>
                          )}
                        </div>
                        <span className="text-sm text-text-primary">{event.user}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-center">
                      <span className={event.actionClass}>{event.action}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="dot-red" />
              <span className="text-sm text-text-secondary">
                Critical Threats Blocked: <span className="font-mono text-data-sm text-danger">3</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="dot-green" />
              <span className="text-sm text-text-secondary">
                Firewall Status: <span className="font-mono text-data-sm text-success">ACTIVE</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-sm text-text-muted">
              Showing <span className="text-text-secondary font-medium">6</span> of <span className="text-text-secondary font-medium">1,247</span> events
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
                208
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
