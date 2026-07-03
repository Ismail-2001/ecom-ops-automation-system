"use client"

import { useState } from "react"
import {
  Key,
  Bell,
  Mail,
  MessageSquare,
  Smartphone,
  Globe,
  Trash2,
  RotateCcw,
  FileText,
  AlertTriangle,
  Save,
  CheckCircle,
  Loader2,
  Eye,
  EyeOff,
} from "lucide-react"
import Shell from "@/components/layout/Shell"
import Toggle from "@/components/shared/Toggle"

export default function SettingsPage() {
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)

  const [apiConfig, setApiConfig] = useState({
    provider: "Google Gemini",
    apiKey: "",
    model: "gemini-2.0-flash",
  })

  const [notifications, setNotifications] = useState({
    email: true,
    slack: true,
    sms: false,
    browserPush: true,
  })

  const handleSave = () => {
    setSaving(true)
    setTimeout(() => {
      setSaving(false)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    }, 1000)
  }

  return (
    <Shell
      title="System Settings"
      subtitle="Configure system parameters, API keys, and operational preferences."
    >
      <div className="space-y-6 max-w-6xl">
        <div className="grid grid-cols-2 gap-6">
          {/* API Configuration */}
          <div className="card border-l-4 border-l-primary">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-9 h-9 rounded-button bg-primary/10 flex items-center justify-center">
                <Key className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h3 className="font-display text-display-sm text-text-primary">
                  API Configuration
                </h3>
                <p className="text-body-sm text-text-muted mt-0.5">
                  Manage LLM provider credentials
                </p>
              </div>
            </div>

            <div className="space-y-5">
              <div>
                <label className="label-caps mb-2 block">LLM Provider</label>
                <select
                  value={apiConfig.provider}
                  onChange={(e) =>
                    setApiConfig((p) => ({ ...p, provider: e.target.value }))
                  }
                  className="w-full px-4 py-2.5 rounded-button bg-surface-2 border border-border text-text-primary text-body-md focus:border-border-bright focus:outline-none transition-colors appearance-none"
                >
                  <option>Google Gemini</option>
                  <option>OpenAI</option>
                  <option>Anthropic</option>
                  <option>Azure OpenAI</option>
                </select>
              </div>

              <div>
                <label className="label-caps mb-2 block">API Key</label>
                <div className="relative">
                  <input
                    type={showApiKey ? "text" : "password"}
                    value={apiConfig.apiKey}
                    onChange={(e) =>
                      setApiConfig((p) => ({ ...p, apiKey: e.target.value }))
                    }
                    className="w-full px-4 py-2.5 pr-10 rounded-button bg-surface-2 border border-border text-text-primary font-mono text-body-sm focus:border-border-bright focus:outline-none transition-colors"
                  />
                  <button
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                  >
                    {showApiKey ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              <div>
                <label className="label-caps mb-2 block">Model</label>
                <input
                  type="text"
                  value={apiConfig.model}
                  onChange={(e) =>
                    setApiConfig((p) => ({ ...p, model: e.target.value }))
                  }
                  className="w-full px-4 py-2.5 rounded-button bg-surface-2 border border-border text-text-primary text-body-md font-mono focus:border-border-bright focus:outline-none transition-colors"
                />
              </div>
            </div>

            <div className="mt-6 pt-5 border-t border-border">
              <button
                onClick={handleSave}
                disabled={saving}
                className="btn-primary w-full justify-center"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> Saving...
                  </>
                ) : saved ? (
                  <>
                    <CheckCircle className="w-4 h-4" /> Saved Successfully
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" /> Save Changes
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Notification Settings */}
          <div className="card border-l-4 border-l-primary">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-9 h-9 rounded-button bg-warning/10 flex items-center justify-center">
                <Bell className="w-4 h-4 text-warning" />
              </div>
              <div>
                <h3 className="font-display text-display-sm text-text-primary">
                  Notification Settings
                </h3>
                <p className="text-body-sm text-text-muted mt-0.5">
                  Configure alert delivery channels
                </p>
              </div>
            </div>

            <div className="space-y-1">
              {[
                {
                  key: "email" as const,
                  icon: Mail,
                  label: "Email Notifications",
                  description: "Receive alerts via email",
                  iconBg: "bg-info/10",
                  iconColor: "text-info",
                },
                {
                  key: "slack" as const,
                  icon: MessageSquare,
                  label: "Slack Alerts",
                  description: "Post alerts to Slack channel",
                  iconBg: "bg-primary/10",
                  iconColor: "text-primary",
                },
                {
                  key: "sms" as const,
                  icon: Smartphone,
                  label: "SMS Alerts",
                  description: "Critical alerts via text message",
                  iconBg: "bg-danger/10",
                  iconColor: "text-danger",
                },
                {
                  key: "browserPush" as const,
                  icon: Globe,
                  label: "Browser Push",
                  description: "Real-time browser notifications",
                  iconBg: "bg-success/10",
                  iconColor: "text-success",
                },
              ].map((item) => {
                const Icon = item.icon
                return (
                  <div
                    key={item.key}
                    className="flex items-center justify-between p-3 rounded-button hover:bg-surface-2 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-8 h-8 rounded-button ${item.iconBg} flex items-center justify-center`}
                      >
                        <Icon className={`w-4 h-4 ${item.iconColor}`} />
                      </div>
                      <div>
                        <div className="text-body-md text-text-primary font-medium">
                          {item.label}
                        </div>
                        <div className="text-body-sm text-text-muted">
                          {item.description}
                        </div>
                      </div>
                    </div>
                    <Toggle
                      enabled={notifications[item.key]}
                      onToggle={() =>
                        setNotifications((p) => ({
                          ...p,
                          [item.key]: !p[item.key],
                        }))
                      }
                    />
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* System Maintenance */}
        <div className="card border-l-4 border-l-primary">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-button bg-danger/10 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-danger" />
            </div>
            <div>
              <h3 className="font-display text-display-sm text-text-primary">
                System Maintenance
              </h3>
              <p className="text-body-sm text-text-muted mt-0.5">
                Administrative actions and system management
              </p>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4">
            {[
              {
                icon: Trash2,
                label: "Clear Cache",
                description: "Purge all cached data",
                iconBg: "bg-warning/10",
                iconColor: "text-warning",
                hoverBorder: "hover:border-warning/30",
              },
              {
                icon: RotateCcw,
                label: "Restart Agents",
                description: "Restart all AI agents",
                iconBg: "bg-info/10",
                iconColor: "text-info",
                hoverBorder: "hover:border-info/30",
              },
              {
                icon: FileText,
                label: "Export Logs",
                description: "Download system logs",
                iconBg: "bg-primary/10",
                iconColor: "text-primary",
                hoverBorder: "hover:border-primary/30",
              },
              {
                icon: AlertTriangle,
                label: "Reset Defaults",
                description: "Restore factory settings",
                iconBg: "bg-danger/10",
                iconColor: "text-danger",
                hoverBorder: "hover:border-danger/30",
              },
            ].map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.label}
                  className={`flex flex-col items-center gap-3 p-5 rounded-card bg-surface-2 border border-border ${item.hoverBorder} transition-all duration-200 hover:bg-surface-3 text-center group`}
                >
                  <div
                    className={`w-11 h-11 rounded-button ${item.iconBg} flex items-center justify-center transition-transform group-hover:scale-110`}
                  >
                    <Icon className={`w-5 h-5 ${item.iconColor}`} />
                  </div>
                  <div>
                    <div className="text-body-md text-text-primary font-medium">
                      {item.label}
                    </div>
                    <div className="text-body-sm text-text-muted mt-0.5">
                      {item.description}
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </Shell>
  )
}
