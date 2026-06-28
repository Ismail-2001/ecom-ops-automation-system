"use client"

import { useState, useEffect } from "react"
import {
  Settings as SettingsIcon,
  Bell,
  Globe,
  Save,
  RefreshCw,
  CheckCircle,
  Loader2,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { useSettings, useUpdateSettings } from "@/lib/hooks"
import { cn } from "@/lib/utils"

export default function SettingsPage() {
  const settingsQuery = useSettings()
  const updateMutation = useUpdateSettings()
  const [saved, setSaved] = useState(false)
  const [local, setLocal] = useState({
    shadow_mode: true,
    fraud_threshold: 70,
    po_limit: 1000,
    pricing_limit: 20,
    reviews_rating_threshold: 3,
    notify_on_failure: true,
    notify_on_hitl: true,
    notify_on_graduation: false,
    slack_channel: "",
  })

  useEffect(() => {
    if (settingsQuery.data) {
      const s = settingsQuery.data
      setLocal({
        shadow_mode: s.shadow_mode,
        fraud_threshold: s.fraud_threshold,
        po_limit: s.po_limit,
        pricing_limit: s.pricing_limit,
        reviews_rating_threshold: s.reviews_rating_threshold,
        notify_on_failure: s.notify_on_failure,
        notify_on_hitl: s.notify_on_hitl,
        notify_on_graduation: s.notify_on_graduation,
        slack_channel: s.slack_channel,
      })
    }
  }, [settingsQuery.data])

  const handleSave = () => {
    updateMutation.mutate(local, {
      onSuccess: () => {
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
      },
    })
  }

  return (
    <Shell>
      <Topbar title="Settings" subtitle="System configuration and preferences" />

      <div className="p-6 space-y-6 max-w-4xl">
        {/* General */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 rounded-lg bg-indigo/10 flex items-center justify-center">
              <SettingsIcon className="w-4 h-4 text-indigo" />
            </div>
            <h2 className="font-display font-semibold text-text-1">General</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
              <div>
                <div className="text-sm font-medium text-text-1">Shadow Mode</div>
                <div className="text-xs text-text-3">Agents suggest but don't execute actions</div>
              </div>
              <button
                onClick={() => setLocal((p) => ({ ...p, shadow_mode: !p.shadow_mode }))}
                className={cn(
                  "w-10 h-6 rounded-full transition-colors relative",
                  local.shadow_mode ? "bg-indigo" : "bg-surface-3",
                )}
              >
                <div className={cn(
                  "w-4 h-4 rounded-full bg-white absolute top-1 transition-transform",
                  local.shadow_mode ? "left-5" : "left-1",
                )} />
              </button>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 rounded-lg bg-amber/10 flex items-center justify-center">
              <Bell className="w-4 h-4 text-amber" />
            </div>
            <h2 className="font-display font-semibold text-text-1">Notifications</h2>
          </div>
          <div className="space-y-4">
            {[
              { key: "notify_on_failure" as const, label: "Failure alerts", description: "Get notified when agents fail" },
              { key: "notify_on_hitl" as const, label: "Human-in-the-loop", description: "Alert when decisions need approval" },
              { key: "notify_on_graduation" as const, label: "Graduation alerts", description: "Notify when agents increase autonomy" },
            ].map((item) => (
              <div key={item.key} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
                <div>
                  <div className="text-sm font-medium text-text-1">{item.label}</div>
                  <div className="text-xs text-text-3">{item.description}</div>
                </div>
                <button
                  onClick={() => setLocal((p) => ({ ...p, [item.key]: !p[item.key] }))}
                  className={cn(
                    "w-10 h-6 rounded-full transition-colors relative",
                    local[item.key] ? "bg-indigo" : "bg-surface-3",
                  )}
                >
                  <div className={cn(
                    "w-4 h-4 rounded-full bg-white absolute top-1 transition-transform",
                    local[item.key] ? "left-5" : "left-1",
                  )} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* AI Agent Settings */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 rounded-lg bg-emerald/10 flex items-center justify-center">
              <Globe className="w-4 h-4 text-emerald" />
            </div>
            <h2 className="font-display font-semibold text-text-1">AI Agent Configuration</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-text-3 uppercase tracking-wider mb-2">
                Fraud Detection Threshold
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range" min="0" max="100"
                  value={local.fraud_threshold}
                  onChange={(e) => setLocal((p) => ({ ...p, fraud_threshold: Number(e.target.value) }))}
                  className="flex-1 accent-indigo"
                />
                <span className="font-mono text-data-sm text-indigo w-10 text-right">{(local.fraud_threshold / 100).toFixed(2)}</span>
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-3 uppercase tracking-wider mb-2">
                Purchase Order Limit ($)
              </label>
              <input
                type="number" min={0}
                value={local.po_limit}
                onChange={(e) => setLocal((p) => ({ ...p, po_limit: Number(e.target.value) }))}
                className="w-32 px-4 py-2.5 rounded-lg bg-surface-2 border border-border text-text-1 text-sm focus:border-border-bright focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-3 uppercase tracking-wider mb-2">
                Max Price Change (%)
              </label>
              <input
                type="number" min={0} max={100}
                value={local.pricing_limit}
                onChange={(e) => setLocal((p) => ({ ...p, pricing_limit: Number(e.target.value) }))}
                className="w-32 px-4 py-2.5 rounded-lg bg-surface-2 border border-border text-text-1 text-sm focus:border-border-bright focus:outline-none transition-colors"
              />
            </div>
          </div>
        </div>

        {/* Save */}
        <div className="flex items-center justify-end gap-3">
          <button
            onClick={() => settingsQuery.refetch()}
            className="btn-ghost"
            disabled={settingsQuery.isFetching}
          >
            <RefreshCw className={cn("w-4 h-4", settingsQuery.isFetching && "animate-spin")} />
            Refresh
          </button>
          <button onClick={handleSave} disabled={updateMutation.isPending} className={cn("btn-primary", saved && "bg-emerald")}>
            {updateMutation.isPending ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
            ) : saved ? (
              <><CheckCircle className="w-4 h-4" /> Saved!</>
            ) : (
              <><Save className="w-4 h-4" /> Save Changes</>
            )}
          </button>
        </div>
      </div>
    </Shell>
  )
}
