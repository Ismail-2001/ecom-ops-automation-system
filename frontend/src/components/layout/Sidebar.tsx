"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard, Bot, ShoppingCart, Headphones, Package,
  Star, BarChart3, Store, Shield, Settings, Zap, Plus
} from "lucide-react"

const navSections = [
  {
    label: null,
    items: [
      { href: "/", label: "Dashboard", icon: LayoutDashboard },
      { href: "/agents", label: "Agents", icon: Bot },
    ],
  },
  {
    label: null,
    items: [
      { href: "/orders", label: "Orders", icon: ShoppingCart },
      { href: "/cart-recovery", label: "Cart Recovery", icon: Package },
      { href: "/support", label: "Support", icon: Headphones },
    ],
  },
  {
    label: null,
    items: [
      { href: "/products", label: "Products", icon: Package },
      { href: "/reviews", label: "Reviews", icon: Star },
    ],
  },
  {
    label: null,
    items: [
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/shopify", label: "Shopify", icon: Store },
    ],
  },
  {
    label: "SYSTEM",
    items: [
      { href: "/security", label: "Security", icon: Shield },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
]

export default function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="fixed left-0 top-0 bottom-0 w-[240px] bg-void border-r border-border flex flex-col z-50">
      <div className="p-5 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center">
          <Zap className="w-4 h-4 text-primary" />
        </div>
        <div>
          <div className="font-display font-bold text-sm text-text-primary leading-tight">OpsIQ</div>
          <div className="text-[10px] font-mono uppercase tracking-widest text-text-muted">AI Automation</div>
        </div>
      </div>

      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto">
        {navSections.map((section, si) => (
          <div key={si}>
            {section.label && (
              <div className="label-caps px-3 pt-5 pb-2">{section.label}</div>
            )}
            {section.items.map((item) => {
              const active = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={active ? "sidebar-link-active" : "sidebar-link"}
                >
                  <item.icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
        ))}
      </nav>

      <div className="p-3 border-t border-border">
        <Link href="/agents" className="btn-primary w-full text-sm">
          <Plus className="w-4 h-4" />
          Deploy Agent
        </Link>
      </div>

      <div className="px-5 py-3 border-t border-border">
        <div className="flex items-center gap-2 text-xs">
          <div className="dot-green" />
          <span className="text-text-secondary">System Healthy</span>
          <span className="ml-auto font-mono text-success">94%</span>
        </div>
        <div className="progress-bar mt-2">
          <div className="progress-fill bg-success" style={{ width: "94%" }} />
        </div>
      </div>
    </aside>
  )
}
