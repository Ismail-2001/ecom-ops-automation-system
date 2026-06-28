"use client"

import {
  Shield,
  Key,
  Activity,
  RefreshCw,
  Plus,
  CheckCircle,
  AlertTriangle,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { MetricCardSkeleton } from "@/components/shared/Skeleton"
import { useSecurityUsers, useSecurityApiKeys, useSecurityAuditLogs, useSecurityAuditSummary } from "@/lib/hooks"
import { cn, formatTimestamp } from "@/lib/utils"

const fallbackUsers = [
  { id: "u-1", name: "Ismail Sajid", email: "ismail@example.com", role: "super_admin", is_active: true, created_at: new Date(Date.now() - 86400000 * 30).toISOString(), last_login: new Date(Date.now() - 300000).toISOString() },
  { id: "u-2", name: "Admin User", email: "admin@example.com", role: "admin", is_active: true, created_at: new Date(Date.now() - 86400000 * 15).toISOString(), last_login: new Date(Date.now() - 3600000).toISOString() },
  { id: "u-3", name: "Viewer Account", email: "viewer@example.com", role: "viewer", is_active: true, created_at: new Date(Date.now() - 86400000 * 7).toISOString(), last_login: new Date(Date.now() - 86400000).toISOString() },
]

const fallbackKeys = [
  { id: "key-1", name: "Production API", user_id: "u-1", role: "admin", is_active: true, expires_at: null, last_used: new Date(Date.now() - 60000).toISOString(), usage_count: 1240, created_at: new Date(Date.now() - 86400000 * 30).toISOString() },
  { id: "key-2", name: "Staging API", user_id: "u-2", role: "viewer", is_active: true, expires_at: null, last_used: new Date(Date.now() - 3600000).toISOString(), usage_count: 320, created_at: new Date(Date.now() - 86400000 * 10).toISOString() },
]

const fallbackAudit = [
  { id: "a-1", timestamp: new Date(Date.now() - 300000).toISOString(), event_type: "auth", action: "login", resource: "user", resource_id: "u-1", user_id: "u-1", success: true, risk_level: "low" },
  { id: "a-2", timestamp: new Date(Date.now() - 600000).toISOString(), event_type: "api_key", action: "created", resource: "api_key", resource_id: "key-1", user_id: "u-1", success: true, risk_level: "low" },
  { id: "a-3", timestamp: new Date(Date.now() - 1200000).toISOString(), event_type: "config", action: "updated", resource: "settings", resource_id: null, user_id: "u-1", success: true, risk_level: "medium" },
]

export default function SecurityPage() {
  const usersQuery = useSecurityUsers()
  const keysQuery = useSecurityApiKeys()
  const auditLogsQuery = useSecurityAuditLogs({ limit: 10 })
  const auditSummaryQuery = useSecurityAuditSummary(24)

  const users = usersQuery.data?.users?.length ? usersQuery.data.users : fallbackUsers
  const keys = keysQuery.data?.api_keys?.length ? keysQuery.data.api_keys : fallbackKeys
  const logs = auditLogsQuery.data?.entries?.length ? auditLogsQuery.data.entries : fallbackAudit
  const summary = auditSummaryQuery.data

  return (
    <Shell>
      <Topbar title="Security" subtitle="Access control, API keys, and audit logging" />

      <div className="p-6 space-y-6">
        {/* Security stats */}
        <div className="grid grid-cols-5 gap-4">
          {usersQuery.isLoading ? (
            Array.from({ length: 5 }).map((_, i) => <MetricCardSkeleton key={i} />)
          ) : (
            <>
              <div className="card">
                <div className="section-label mb-2">Security Score</div>
                <div className="metric-value text-display-md text-emerald">87/100</div>
                <div className="progress-bar mt-2">
                  <div className="progress-bar-fill" style={{ width: "87%" }} />
                </div>
              </div>
              <div className="card">
                <div className="section-label mb-2">Active Users</div>
                <div className="metric-value text-display-md text-text-1">{users.filter((u) => u.is_active).length}</div>
              </div>
              <div className="card">
                <div className="section-label mb-2">API Keys</div>
                <div className="metric-value text-display-md text-indigo">{keys.length}</div>
              </div>
              <div className="card">
                <div className="section-label mb-2">Failed Logins (24h)</div>
                <div className="metric-value text-display-md text-amber">{summary?.failed_logins ?? 0}</div>
              </div>
              <div className="card">
                <div className="section-label mb-2">Audit Events</div>
                <div className="metric-value text-display-md text-text-1">{(summary?.total_events ?? logs.length).toLocaleString()}</div>
              </div>
            </>
          )}
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Users */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-text-1">Users</h2>
              <button className="btn-primary text-xs py-1.5 px-3">
                <Plus className="w-3 h-3" /> Add User
              </button>
            </div>
            <div className="space-y-3">
              {users.map((user) => (
                <div key={user.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-surface-3 flex items-center justify-center">
                      <span className="text-xs font-medium text-text-2">
                        {user.name.split(" ").map((n) => n[0]).join("")}
                      </span>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-text-1">{user.name}</div>
                      <div className="text-xs text-text-3">{user.email}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="badge badge-active text-[10px]">{user.role.replace("_", " ")}</span>
                    <span className="text-xs text-text-3">{user.last_login ? formatTimestamp(user.last_login) : "never"}</span>
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
                <Key className="w-3 h-3" /> Generate Key
              </button>
            </div>
            <div className="space-y-3">
              {keys.map((key) => (
                <div key={key.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo/10 flex items-center justify-center">
                      <Key className="w-4 h-4 text-indigo" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-text-1">{key.name}</div>
                      <div className="font-mono text-data-xs text-text-3">{key.role} • {key.usage_count} uses</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={key.is_active ? "active" : "paused"} />
                    <span className="text-xs text-text-3">{key.last_used ? formatTimestamp(key.last_used) : "never"}</span>
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
            <button onClick={() => auditLogsQuery.refetch()} className="btn-ghost text-xs py-1.5 px-3">
              <RefreshCw className={cn("w-3 h-3", auditLogsQuery.isFetching && "animate-spin")} />
              Refresh
            </button>
          </div>
          <div className="space-y-2">
            {logs.map((event) => (
              <div key={event.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center",
                    event.event_type === "auth" ? "bg-emerald/10" :
                    event.event_type === "api_key" ? "bg-indigo/10" :
                    "bg-amber/10",
                  )}>
                    {event.success ? (
                      <CheckCircle className="w-4 h-4 text-emerald" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-data-xs text-indigo">{event.action}</span>
                      <span className="text-xs text-text-3">on</span>
                      <span className="text-xs text-text-2">{event.resource}</span>
                    </div>
                    <div className="text-xs text-text-3 mt-0.5">Risk: {event.risk_level}</div>
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
