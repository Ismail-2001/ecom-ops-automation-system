"use client"
import { useState, useRef, useEffect } from "react"
import { Search, Bell, Wifi, WifiOff, User, Menu, LogOut, Settings, ChevronDown, Check, Clock, AlertTriangle, X } from "lucide-react"
import { useWs } from "@/app/providers"
import { useAuthStore } from "@/lib/auth-store"
import { useRouter } from "next/navigation"

const mockNotifications = [
  { id: 1, icon: AlertTriangle, iconBg: "bg-danger/10", iconColor: "text-danger", title: "Fraud Alert", message: "High-risk order #ORD-90210 flagged for review", time: "2 min ago", read: false },
  { id: 2, icon: Check, iconBg: "bg-success/10", iconColor: "text-success", title: "Agent Deployed", message: "Price Optimization agent restarted successfully", time: "15 min ago", read: false },
  { id: 3, icon: Clock, iconBg: "bg-warning/10", iconColor: "text-warning", title: "Cart Abandoned", message: "3 new carts abandoned in the last hour", time: "1 hr ago", read: true },
  { id: 4, icon: Check, iconBg: "bg-info/10", iconColor: "text-info", title: "Sync Complete", message: "Shopify products synced — 1,247 items updated", time: "2 hrs ago", read: true },
]

export default function Topbar({ title, subtitle, actions, onMenuToggle }: {
  title?: string
  subtitle?: string
  actions?: React.ReactNode
  onMenuToggle?: () => void
}) {
  const { isConnected } = useWs()
  const { logout } = useAuthStore()
  const router = useRouter()
  const [notifOpen, setNotifOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const notifRef = useRef<HTMLDivElement>(null)
  const profileRef = useRef<HTMLDivElement>(null)

  const unreadCount = mockNotifications.filter(n => !n.read).length

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setNotifOpen(false)
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setProfileOpen(false)
    }
    document.addEventListener("mousedown", handleClick)
    return () => document.removeEventListener("mousedown", handleClick)
  }, [])

  function handleLogout() {
    logout()
    router.push("/login")
  }

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

        {/* Bell / Notifications */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => { setNotifOpen(!notifOpen); setProfileOpen(false) }}
            className="w-9 h-9 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-3 hover:text-text-primary transition-colors relative"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-danger ring-2 ring-void" aria-hidden="true" />
            )}
          </button>

          {notifOpen && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-surface border border-border rounded-card shadow-2xl shadow-black/30 overflow-hidden z-50">
              <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <span className="font-display font-semibold text-sm text-text-primary">Notifications</span>
                <span className="badge-primary text-[10px]">{unreadCount} NEW</span>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {mockNotifications.map(n => {
                  const Icon = n.icon
                  return (
                    <div key={n.id} className={`flex items-start gap-3 px-4 py-3 border-b border-border/50 hover:bg-surface-2 transition-colors cursor-pointer ${!n.read ? 'bg-primary/5' : ''}`}>
                      <div className={`w-8 h-8 rounded-lg ${n.iconBg} flex items-center justify-center shrink-0 mt-0.5`}>
                        <Icon className={`w-4 h-4 ${n.iconColor}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-text-primary">{n.title}</span>
                          {!n.read && <div className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />}
                        </div>
                        <p className="text-xs text-text-muted mt-0.5 truncate">{n.message}</p>
                        <span className="text-[10px] font-mono text-text-muted mt-1 block">{n.time}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="px-4 py-2.5 border-t border-border text-center">
                <button className="text-xs font-medium text-primary hover:text-primary-hover transition-colors">View All Notifications</button>
              </div>
            </div>
          )}
        </div>

        {/* Admin User Profile */}
        <div className="relative" ref={profileRef}>
          <button
            onClick={() => { setProfileOpen(!profileOpen); setNotifOpen(false) }}
            className="hidden sm:flex items-center gap-2.5 pl-2 ml-1 border-l border-border hover:bg-surface-2 rounded-button px-2 py-1 transition-colors cursor-pointer"
          >
            <div className="text-right hidden md:block">
              <div className="text-sm font-medium text-text-primary">Admin User</div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-text-muted">SUPERUSER_ROOT</div>
            </div>
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center ring-2 ring-primary/20">
              <User className="w-4 h-4 text-primary" />
            </div>
            <ChevronDown className="w-3 h-3 text-text-muted hidden md:block" />
          </button>

          {profileOpen && (
            <div className="absolute right-0 top-full mt-2 w-56 bg-surface border border-border rounded-card shadow-2xl shadow-black/30 overflow-hidden z-50">
              <div className="px-4 py-3 border-b border-border">
                <div className="text-sm font-medium text-text-primary">Admin User</div>
                <div className="text-xs font-mono text-text-muted mt-0.5">admin@opsiq.dev</div>
                <div className="flex items-center gap-1.5 mt-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-success" />
                  <span className="text-[10px] font-mono text-success uppercase">Active</span>
                </div>
              </div>
              <div className="py-1">
                <button
                  onClick={() => { router.push("/settings"); setProfileOpen(false) }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-text-secondary hover:bg-surface-2 hover:text-text-primary transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-danger hover:bg-danger/10 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>

        {actions}
      </div>
    </header>
  )
}
