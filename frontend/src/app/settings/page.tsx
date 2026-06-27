"use client"

import { useState } from "react"
import {
  Settings as SettingsIcon,
  Bell,
  Palette,
  Database,
  Globe,
  Mail,
  Save,
  RefreshCw,
  CheckCircle,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { cn } from "@/lib/utils"

export default function SettingsPage() {
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
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
            <div>
              <label className="block text-xs font-semibold text-text-3 uppercase tracking-wider mb-2">Store Name</label>
              <input type="text" defaultValue="OpsIQ Demo Store" className="w-full px-4 py-2.5 rounded-lg bg-surface-2 border border-border text-text-1 text-sm focus:border-border-bright focus:outline-none transition-colors" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-3 uppercase tracking-wider mb-2">Shopify Store URL</label>
              <input type="text" defaultValue="https://opsiq-demo.myshopify.com" className="w-full px-4 py-2.5 rounded-lg bg-surface-2 border border-border text-text-1 text-sm focus:border-border-bright focus:outline-none transition-colors" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-3 uppercase tracking-wider mb-2">Timezone</label>
              <select className="w-full px-4 py-2.5 rounded-lg bg-surface-2 border border-border text-text-1 text-sm focus:border-border-bright focus:outline-none transition-colors">
                <option>UTC</option>
                <option>America/New_York</option>
                <option>America/Los_Angeles</option>
                <option>Europe/London</option>
                <option selected>Asia/Karachi</option>
              </select>
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
              { label: "Fraud alerts", description: "Get notified when high-risk orders are detected", enabled: true },
              { label: "Stock warnings", description: "Alerts when products fall below minimum stock level", enabled: true },
              { label: "Price changes", description: "Notifications when AI suggests price adjustments", enabled: false },
              { label: "Daily digest", description: "Summary of all agent activity and decisions", enabled: true },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
                <div>
                  <div className="text-sm font-medium text-text-1">{item.label}</div>
                  <div className="text-xs text-text-3">{item.description}</div>
                </div>
                <button className={cn(
                  "w-10 h-6 rounded-full transition-colors relative",
                  item.enabled ? "bg-indigo" : "bg-surface-3"
                )}>
                  <div className={cn(
                    "w-4 h-4 rounded-full bg-white absolute top-1 transition-transform",
                    item.enabled ? "left-5" : "left-1"
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
              <label className="block text-xs font-semibold text-text-3 uppercase tracking-wider mb-2">Fraud Detection Threshold</label>
              <div className="flex items-center gap-4">
                <input type="range" min="0" max="100" defaultValue="70" className="flex-1 accent-indigo" />
                <span className="font-mono text-data-sm text-indigo w-10 text-right">0.70</span>
              </div>
              <p className="text-xs text-text-3 mt-1">Orders above this risk score will be flagged for review</p>
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-3 uppercase tracking-wider mb-2">Auto-Approve Confidence Threshold</label>
              <div className="flex items-center gap-4">
                <input type="range" min="0" max="100" defaultValue="85" className="flex-1 accent-indigo" />
                <span className="font-mono text-data-sm text-indigo w-10 text-right">0.85</span>
              </div>
              <p className="text-xs text-text-3 mt-1">Decisions above this confidence are auto-approved without human review</p>
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-3 uppercase tracking-wider mb-2">Max Discount Code Value (%)</label>
              <input type="number" defaultValue={25} min={0} max={50} className="w-32 px-4 py-2.5 rounded-lg bg-surface-2 border border-border text-text-1 text-sm focus:border-border-bright focus:outline-none transition-colors" />
              <p className="text-xs text-text-3 mt-1">Maximum discount percentage AI agents can generate for cart recovery</p>
            </div>
          </div>
        </div>

        {/* Save */}
        <div className="flex items-center justify-end gap-3">
          <button className="btn-ghost">
            <RefreshCw className="w-4 h-4" />
            Reset Defaults
          </button>
          <button onClick={handleSave} className={cn("btn-primary", saved && "bg-emerald")}>
            {saved ? (
              <>
                <CheckCircle className="w-4 h-4" />
                Saved!
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>
    </Shell>
  )
}
