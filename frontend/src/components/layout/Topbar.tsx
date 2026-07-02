"use client"
import { Search, Bell, Wifi, WifiOff, User } from "lucide-react"
import { useWs } from "@/app/providers"

export default function Topbar({ title, subtitle, actions }: {
  title?: string
  subtitle?: string
  actions?: React.ReactNode
}) {
  const { isConnected } = useWs()
  return (
    <header className="sticky top-0 z-40 h-16 bg-void/80 backdrop-blur-xl border-b border-border flex items-center px-6 gap-4">
      <div className="flex-1 flex items-center gap-4">
        {title && (
          <div className="hidden lg:block">
            <h1 className="font-display font-semibold text-base text-text-primary">{title}</h1>
            {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <div className="relative hidden md:flex items-center">
          <Search className="absolute left-3 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search operations, orders, or agents..."
            className="w-72 h-9 pl-9 pr-4 rounded-button bg-surface border border-border text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary/30 transition-colors"
          />
          <kbd className="absolute right-3 px-1.5 py-0.5 rounded bg-surface-3 text-[10px] font-mono text-text-muted">⌘K</kbd>
        </div>

        <button className="w-9 h-9 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-danger" />
        </button>

        <div className="w-9 h-9 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors">
          {isConnected ? <Wifi className="w-4 h-4 text-success" /> : <WifiOff className="w-4 h-4 text-danger" />}
        </div>

        <div className="flex items-center gap-2.5 pl-2 ml-1 border-l border-border">
          <div className="text-right hidden sm:block">
            <div className="text-sm font-medium text-text-primary">Admin User</div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-text-muted">SUPERUSER_ROOT</div>
          </div>
          <div className="w-8 h-8 rounded-full bg-primary/15 flex items-center justify-center">
            <User className="w-4 h-4 text-primary" />
          </div>
        </div>

        {actions}
      </div>
    </header>
  )
}
