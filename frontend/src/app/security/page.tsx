"use client"

import { useState } from "react"
import {
  Shield,
  Lock,
  Key,
  Users,
  AlertTriangle,
  CheckCircle,
  Eye,
  EyeOff,
  Clock,
  Activity,
  RefreshCw,
  Plus,
  Trash2,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { cn, formatTimestamp } from "@/lib/utils"

const securityStats = {
  score: 87,
  activeUsers: 5,
  apiKeys: 3,
  failedLogins: 12,
  auditEvents: 1247,
}

const users = [
  { id: "u-1", name: "Ismail Sajid", email: "ismail@example.com", role: "super_admin", lastLogin: new Date(Date.now() - 300000).toISOString(), status: "active" },
  { id: "u-2", name: "Admin User", email: "admin@example.com", role: "admin", lastLogin: new Date(Date.now() - 3600000).toISOString(), status: "active" },
  { id: "u-3", name: "Operations Bot", email: "bot@example.com", role: "api_only", lastLogin: new Date(Date.now() - 120000).toISOString(), status: "active" },
  { id: "u-4", name: "Viewer Account", email: "viewer@example.com", role: "viewer", lastLogin: new Date(Date.now() - 86400000).toISOString(), status: "active" },
]

const apiKeys = [
  { id: "key-1", name: "Production API", prefix: "opsiq_prod_", lastUsed: new Date(Date.now() - 60000).toISOString(), status: "active" },
  { id: "key-2", name: "Staging API", prefix: "opsiq_stg_", lastUsed: new Date(Date.now() - 3600000).toISOString(), status: "active" },
  { id: "key-3", name: "Legacy Integration", prefix: "opsiq_leg_", lastUsed: new Date(Date.now() - 604800000).toISOString(), status: "paused" },
]

const auditLog = [
  { id: "a-1", action: "user.login", user: "Ismail Sajid", details: "Successful login from 192.168.1.1", timestamp: new Date(Date.now() - 300000).toISOString() },
  { id: "a-2", action: "api_key.created", user: "Admin User", details: "New API key created: Production API", timestamp: new Date(Date.now() - 600000).toISOString() },
  { id: "a-3", action: "agent.config.updated", user: "Ismail Sajid", details: "Fraud detection threshold changed to 0.7", timestamp: new Date(Date.now() - 1200000).toISOString() },
  { id: "a-4", action: "user.role.changed", user: "Admin User", details: "Viewer Account role changed to viewer", timestamp: new Date(Date.now() - 3600000).toISOString() },
  { id: "a-5", action: "system.backup", user: "System", details: "Daily backup completed successfully", timestamp: new Date(Date.now() - 7200000).toISOString() },
]

export default function SecurityPage() {
  const [showApiKey, setShowApiKey] = useState<string | null>(null)

  return (
    <Shell>
      <Topbar title="Security" subtitle="Access control, API keys, and audit logging" />
      
      <div className="p-6 space-y-6">
        {/* Security score */}
        <div className="grid grid-cols-5 gap-4">
          <div className="card">
            <div className="section-label mb-2">Security Score</div>
            <div className="metric-value text-display-md text-emerald">{securityStats.score}/100</div>
            <div className="progress-bar mt-2">
              <div className="progress-bar-fill" style={{ width: `${securityStats.score}%` }} />
            </div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Active Users</div>
            <div className="metric-value text-display-md text-text-1">{securityStats.activeUsers}</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">API Keys</div>
            <div className="metric-value text-display-md text-indigo">{securityStats.apiKeys}</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Failed Logins (24h)</div>
            <div className="metric-value text-display-md text-amber">{securityStats.failedLogins}</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Audit Events</div>
            <div className="metric-value text-display-md text-text-1">{securityStats.auditEvents.toLocaleString()}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Users */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-text-1">Users</h2>
              <button className="btn-primary text-xs py-1.5 px-3">
                <Plus className="w-3 h-3" />
                Add User
              </button>
            </div>
            <div className="space-y-3">
              {users.map((user) => (
                <div key={user.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-surface-3 flex items-center justify-center">
                      <span className="text-xs font-medium text-text-2">{user.name.split(" ").map(n => n[0]).join("")}</span>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-text-1">{user.name}</div>
                      <div className="text-xs text-text-3">{user.email}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="badge badge-active text-[10px]">{user.role.replace("_", " ")}</span>
                    <span className="text-xs text-text-3">{formatTimestamp(user.lastLogin)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* API Keys */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-text-1">API Keys</h2>
              <button className="btn-primary text-xs py-1.5 px-3">
                <Key className="w-3 h-3" />
                Generate Key
              </button>
            </div>
            <div className="space-y-3">
              {apiKeys.map((key) => (
                <div key={key.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo/10 flex items-center justify-center">
                      <Key className="w-4 h-4 text-indigo" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-text-1">{key.name}</div>
                      <div className="font-mono text-data-xs text-text-3">{key.prefix}{"•".repeat(24)}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={key.status} />
                    <span className="text-xs text-text-3">{formatTimestamp(key.lastUsed)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Audit log */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-semibold text-text-1">Audit Log</h2>
            <button className="btn-ghost text-xs py-1.5 px-3">
              <RefreshCw className="w-3 h-3" />
              Refresh
            </button>
          </div>
          <div className="space-y-2">
            {auditLog.map((event) => (
              <div key={event.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center",
                    event.action.includes("login") ? "bg-emerald/10" :
                    event.action.includes("created") ? "bg-indigo/10" :
                    event.action.includes("updated") ? "bg-amber/10" :
                    "bg-surface-3"
                  )}>
                    {event.action.includes("login") ? <CheckCircle className="w-4 h-4 text-emerald" /> :
                     event.action.includes("created") ? <Plus className="w-4 h-4 text-indigo" /> :
                     <Activity className="w-4 h-4 text-text-3" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-data-xs text-indigo">{event.action}</span>
                      <span className="text-xs text-text-3">by</span>
                      <span className="text-xs text-text-2">{event.user}</span>
                    </div>
                    <div className="text-xs text-text-3 mt-0.5">{event.details}</div>
                  </div>
                </div>
                <span className="text-xs text-text-3">{formatTimestamp(event.timestamp)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Shell>
  )
}
