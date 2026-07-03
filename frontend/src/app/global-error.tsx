"use client"

import { useEffect } from "react"
import { AlertTriangle, RefreshCw, Zap } from "lucide-react"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error("[OpsIQ GlobalError]", error)
  }, [error])

  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0B1120] flex items-center justify-center p-6 font-sans antialiased">
        <div className="card max-w-lg w-full text-center">
          <div className="w-14 h-14 rounded-2xl bg-[#6366F1]/15 flex items-center justify-center mx-auto mb-5">
            <Zap className="w-7 h-7 text-[#6366F1]" />
          </div>
          <h1 className="font-display text-xl font-bold text-[#F1F5F9] mb-2">
            OpsIQ encountered an error
          </h1>
          <p className="text-sm text-[#94A3B8] mb-2">
            The application hit an unexpected error and needs to reload.
          </p>
          {error.digest && (
            <p className="text-xs text-[#64748B] font-mono mb-1">
              Error ID: {error.digest}
            </p>
          )}
          <p className="text-xs text-[#EF4444] font-mono mb-6 max-w-sm mx-auto break-all">
            {error.message}
          </p>
          <div className="flex gap-3 justify-center">
            <button onClick={reset} className="bg-[#6366F1] text-white px-5 py-2.5 rounded-lg font-medium text-sm hover:bg-[#818CF8] transition-colors inline-flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
            <a
              href="/"
              className="border border-[rgba(99,102,241,0.10)] text-[#94A3B8] px-5 py-2.5 rounded-lg font-medium text-sm hover:bg-[#1A2035] transition-colors inline-flex items-center gap-2"
            >
              <AlertTriangle className="w-4 h-4" />
              Go to Dashboard
            </a>
          </div>
        </div>
      </body>
    </html>
  )
}
