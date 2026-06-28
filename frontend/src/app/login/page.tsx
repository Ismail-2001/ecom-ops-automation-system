"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/lib/auth-store"
import { KeyRound, AlertCircle, Loader2 } from "lucide-react"

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
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl bg-indigo/20 flex items-center justify-center">
              <KeyRound className="w-5 h-5 text-indigo" />
            </div>
          </div>
          <h1 className="font-display text-2xl font-bold text-text-1">OpsIQ</h1>
          <p className="text-sm text-text-3 mt-1">AI-Powered E-Commerce Operations</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div>
            <label className="section-label text-[11px] mb-1.5 block">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value)
                clearError()
              }}
              placeholder="opsiq-dev-key-2024"
              className="w-full px-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-sm text-text-1 placeholder:text-text-4 focus:outline-none focus:border-indigo transition-colors font-mono"
              autoFocus
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 p-2 rounded-lg bg-red/10 border border-red/20">
              <AlertCircle className="w-4 h-4 text-red shrink-0" />
              <span className="text-xs text-red">{error}</span>
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
              "Sign In"
            )}
          </button>
        </form>

        <p className="text-center text-[11px] text-text-4 mt-4">
          Contact your admin for API key access
        </p>
      </div>
    </div>
  )
}
