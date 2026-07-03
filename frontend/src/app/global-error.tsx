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
    <html lang="en">
      <body className="min-h-screen bg-white flex items-center justify-center p-6 font-sans antialiased">
        <div className="card max-w-lg w-full text-center">
          <div className="w-14 h-14 rounded-2xl bg-primary-light flex items-center justify-center mx-auto mb-5">
            <Zap className="w-7 h-7 text-primary" />
          </div>
          <h1 className="font-display text-xl font-bold text-text-primary mb-2">
            OpsIQ encountered an error
          </h1>
          <p className="text-sm text-text-secondary mb-2">
            The application hit an unexpected error and needs to reload.
          </p>
          {error.digest && (
            <p className="text-xs text-text-muted font-mono mb-1">
              Error ID: {error.digest}
            </p>
          )}
          <p className="text-xs text-danger font-mono mb-6 max-w-sm mx-auto break-all">
            {error.message}
          </p>
          <div className="flex gap-3 justify-center">
            <button onClick={reset} className="btn-primary">
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
            <a href="/" className="btn-outline">
              <AlertTriangle className="w-4 h-4" />
              Go to Dashboard
            </a>
          </div>
        </div>
      </body>
    </html>
  )
}
