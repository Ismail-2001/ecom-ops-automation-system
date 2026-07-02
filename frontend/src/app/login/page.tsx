"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/lib/auth-store"
import { Zap, KeyRound, AlertCircle, Loader2, ExternalLink, Shield, Activity, Lock } from "lucide-react"

export default function LoginPage() {
  const [apiKey, setApiKey] = useState("")
  const { login, isLoading, error, clearError } = useAuthStore()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!apiKey.trim()) return
    const ok = await login(apiKey.trim())
    if (ok) router.push("/")
  }

  return (
    <div className="min-h-screen bg-void flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center">
              <Zap className="w-6 h-6 text-primary" />
            </div>
          </div>
          <h1 className="font-display text-3xl font-bold text-text-primary">OpsIQ</h1>
          <p className="text-sm text-text-muted mt-1 font-mono uppercase tracking-widest">AI Automation Interface</p>
        </div>

        {/* Form Card */}
        <form onSubmit={handleSubmit} className="rounded-xl bg-surface border border-border p-6 space-y-5">
          <h2 className="font-display text-display-sm text-text-primary text-center">
            Enter API Key to Access Command Center
          </h2>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="flex items-center gap-1.5 text-label font-semibold uppercase tracking-widest text-text-muted">
                <KeyRound className="w-3 h-3" />
                API Key
              </label>
              <span className="label-caps text-primary">ENCRYPTED</span>
            </div>
            <div className="relative">
              <input
                type="password"
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value)
                  clearError()
                }}
                placeholder="opsiq-dev-key-2024"
                className="w-full px-4 py-3 rounded-lg bg-surface-2 border border-border text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 transition-all font-mono"
                autoFocus
              />
              <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-danger/10 border border-danger/20">
              <AlertCircle className="w-4 h-4 text-danger shrink-0" />
              <span className="text-sm text-danger">{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={!apiKey.trim() || isLoading}
            className="w-full btn-primary justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Connecting...
              </>
            ) : (
              "Access Command Center"
            )}
          </button>
        </form>

        {/* Bottom Links */}
        <div className="flex items-center justify-center gap-6 mt-6">
          <a href="/docs" className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors">
            <ExternalLink className="w-3 h-3" />
            Documentation
          </a>
          <a href="/security" className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors">
            <Shield className="w-3 h-3" />
            Security Audit
          </a>
          <a href="/health" className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors">
            <Activity className="w-3 h-3" />
            Status
          </a>
        </div>

        {/* System Status */}
        <div className="flex items-center justify-center gap-2 mt-8 text-xs font-mono text-success">
          <span className="dot-green" />
          SYSTEMS OPERATIONAL
        </div>
      </div>
    </div>
  )
}
