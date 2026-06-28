"use client"

import { useState } from "react"
import { Search, Bell, ChevronDown, Command } from "lucide-react"
import { cn } from "@/lib/utils"
import { ConnectionStatus } from "@/components/shared/ConnectionStatus"

interface TopbarProps {
  title: string
  subtitle?: string
  actions?: React.ReactNode
}

export function Topbar({ title, subtitle, actions }: TopbarProps) {
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <header className="h-14 border-b border-border bg-surface flex items-center justify-between px-6 sticky top-0 z-40">
      {/* Left: Title */}
      <div className="flex items-center gap-3">
        <div>
          <h1 className="font-display font-bold text-lg text-text-1 tracking-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-text-3">{subtitle}</p>
          )}
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Command search */}
        <button
          onClick={() => setSearchOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-2 border border-border text-text-3 text-sm hover:border-border-bright transition-colors"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Search...</span>
          <div className="flex items-center gap-0.5 ml-4">
            <kbd className="px-1.5 py-0.5 rounded bg-surface-3 text-[10px] font-mono text-text-3">
              <Command className="w-2.5 h-2.5 inline" />
            </kbd>
            <kbd className="px-1.5 py-0.5 rounded bg-surface-3 text-[10px] font-mono text-text-3">
              K
            </kbd>
          </div>
        </button>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg hover:bg-surface-2 transition-colors">
          <Bell className="w-4 h-4 text-text-2" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red rounded-full" />
        </button>

        {/* Live indicator */}
        <ConnectionStatus />

        {/* Custom actions */}
        {actions && (
          <div className="flex items-center gap-2">
            {actions}
          </div>
        )}
      </div>
    </header>
  )
}
