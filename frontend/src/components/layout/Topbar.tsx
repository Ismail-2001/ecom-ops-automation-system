"use client"
import { Search, Bell, Wifi, WifiOff, User, Menu } from "lucide-react"
import { useWs } from "@/app/providers"

export default function Topbar({ title, subtitle, actions, onMenuToggle }: {
  title?: string
  subtitle?: string
  actions?: React.ReactNode
  onMenuToggle?: () => void
}) {
  const { isConnected } = useWs()
  return (
    <header className="sticky top-0 z-40 h-14 sm:h-16 bg-void/80 backdrop-blur-xl border-b border-border flex items-center px-4 sm:px-6 gap-3" role="banner">
      <button
        onClick={onMenuToggle}
        className="lg:hidden w-9 h-9 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-3 hover:text-text-primary transition-colors"
        aria-label="Toggle menu"
      >
        <Menu className="w-5 h-5" />
      </button>

      <div className="flex-1 flex items-center gap-4 min-w-0">
        {title && (
          <div className="hidden sm:block truncate">
            <h1 className="font-display font-semibold text-base text-text-primary truncate">{title}</h1>
            {subtitle && <p className="text-xs text-text-muted mt-0.5 truncate">{subtitle}</p>}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
        <div className="relative hidden md:flex items-center">
          <Search className="absolute left-3 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search..."
            aria-label="Search operations"
            className="w-56 lg:w-72 h-9 pl-9 pr-4 rounded-button bg-surface-2 border border-border text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/40 transition-all"
          />
          <kbd className="absolute right-3 px-1.5 py-0.5 rounded bg-surface-3 text-[10px] font-mono text-text-muted border border-border">⌘K</kbd>
        </div>

        <button className="w-9 h-9 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-3 hover:text-text-primary transition-colors relative" aria-label="Notifications">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-danger ring-2 ring-void" aria-hidden="true" />
        </button>

        <div className="hidden sm:flex items-center gap-2.5 pl-2 ml-1 border-l border-border">
          <div className="text-right hidden md:block">
            <div className="text-sm font-medium text-text-primary">Admin User</div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-text-muted">SUPERUSER_ROOT</div>
          </div>
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center ring-2 ring-primary/20">
            <User className="w-4 h-4 text-primary" />
          </div>
        </div>

        {actions}
      </div>
    </header>
  )
}
