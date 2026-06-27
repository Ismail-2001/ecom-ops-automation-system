"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Bot,
  ShoppingCart,
  RefreshCw,
  HeadphonesIcon,
  Package,
  Star,
  BarChart3,
  ShoppingBag,
  Shield,
  Settings,
  ChevronLeft,
  Zap,
} from "lucide-react"
import { cn } from "@/lib/utils"

const navSections = [
  {
    label: "Overview",
    items: [
      { name: "Dashboard", href: "/", icon: LayoutDashboard },
    ],
  },
  {
    label: "Agents",
    items: [
      { name: "AI Agents", href: "/agents", icon: Bot },
    ],
  },
  {
    label: "Operations",
    items: [
      { name: "Orders", href: "/orders", icon: ShoppingCart },
      { name: "Cart Recovery", href: "/cart-recovery", icon: RefreshCw },
      { name: "Support", href: "/support", icon: HeadphonesIcon },
    ],
  },
  {
    label: "Commerce",
    items: [
      { name: "Products", href: "/products", icon: Package },
      { name: "Reviews", href: "/reviews", icon: Star },
    ],
  },
  {
    label: "Insights",
    items: [
      { name: "Analytics", href: "/analytics", icon: BarChart3 },
      { name: "Shopify", href: "/shopify", icon: ShoppingBag },
    ],
  },
  {
    label: "System",
    items: [
      { name: "Security", href: "/security", icon: Shield },
      { name: "Settings", href: "/settings", icon: Settings },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen bg-surface border-r border-border z-50 flex flex-col transition-all duration-200",
        collapsed ? "w-[68px]" : "w-[220px]"
      )}
    >
      {/* Logo */}
      <div className="h-14 flex items-center px-4 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <span className="font-display font-bold text-lg text-text-1 tracking-tight">
              OpsIQ
            </span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2">
        {navSections.map((section) => (
          <div key={section.label} className="mb-4">
            {!collapsed && (
              <div className="px-3 mb-2 section-label">
                {section.label}
              </div>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const isActive = pathname === item.href || 
                  (item.href !== "/" && pathname.startsWith(item.href))
                const Icon = item.icon

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150",
                      isActive
                        ? "bg-indigo/10 text-indigo"
                        : "text-text-2 hover:bg-surface-2 hover:text-text-1"
                    )}
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    {!collapsed && <span>{item.name}</span>}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div className="p-2 border-t border-border">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-text-3 hover:text-text-2 hover:bg-surface-2 transition-colors"
        >
          <ChevronLeft
            className={cn(
              "w-4 h-4 transition-transform duration-200",
              collapsed && "rotate-180"
            )}
          />
          {!collapsed && <span className="text-xs">Collapse</span>}
        </button>
      </div>

      {/* User chip */}
      {!collapsed && (
        <div className="p-3 border-t border-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-surface-3 flex items-center justify-center">
              <span className="text-xs font-medium text-text-2">IS</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-text-1 truncate">
                Ismail Sajid
              </div>
              <div className="text-xs text-text-3 truncate">
                Admin
              </div>
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}
