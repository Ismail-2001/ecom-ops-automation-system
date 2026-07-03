"use client"

import { useState } from "react"
import {
  Search,
  ChevronLeft,
  ChevronRight,
  Send,
  Eye,
  Mail,
  MessageSquare,
  Bell,
  TrendingUp,
  DollarSign,
  Megaphone,
  ShoppingCart,
} from "lucide-react"
import Shell from "@/components/layout/Shell"
import { cn } from "@/lib/utils"
import { useCartRecoveryAnalytics } from "@/lib/hooks"

const fallbackCarts = [
  {
    id: 1,
    customer: "Michael C.",
    cartValue: "$342.00",
    items: 3,
    abandoned: "2h ago",
    outlook: "HIGH POTENTIAL",
    outlookClass: "badge-success",
    lastTouchpoint: "Email Sent 14:30",
    action: "Remind",
  },
  {
    id: 2,
    customer: "Jessica L.",
    cartValue: "$128.00",
    items: 1,
    abandoned: "5h ago",
    outlook: "MEDIUM",
    outlookClass: "badge-warning",
    lastTouchpoint: "SMS Queued",
    action: "Remind",
  },
  {
    id: 3,
    customer: "David R.",
    cartValue: "$1,247.00",
    items: 7,
    abandoned: "1d ago",
    outlook: "LOW",
    outlookClass: "badge-danger",
    lastTouchpoint: "Email Sent Yesterday",
    action: "View",
  },
  {
    id: 4,
    customer: "Sarah M.",
    cartValue: "$89.00",
    items: 2,
    abandoned: "3h ago",
    outlook: "HIGH POTENTIAL",
    outlookClass: "badge-success",
    lastTouchpoint: "Push Sent 14:32",
    action: "Remind",
  },
  {
    id: 5,
    customer: "Chris W.",
    cartValue: "$567.00",
    items: 4,
    abandoned: "8h ago",
    outlook: "MEDIUM",
    outlookClass: "badge-warning",
    lastTouchpoint: "Email Sent 09:15",
    action: "Remind",
  },
  {
    id: 6,
    customer: "Anna K.",
    cartValue: "$234.00",
    items: 2,
    abandoned: "30m ago",
    outlook: "NEW",
    outlookClass: "badge-info",
    lastTouchpoint: "Just Abandoned",
    action: "Remind",
  },
]

const filters = ["All Carts", "Recoverable", "Recovered", "Lost"]

export default function CartRecoveryPage() {
  const [activeFilter, setActiveFilter] = useState("All Carts")
  const [searchQuery, setSearchQuery] = useState("")
  const { data: analyticsData, isLoading } = useCartRecoveryAnalytics()

  const analytics = (analyticsData ?? { recovery_rate: 22.4, total_revenue_lost: 48291, total_abandoned: 142 }) as Record<string, unknown>
  const recoveryRate = (analytics.recovery_rate as number) || 22.4
  const revenueAtRisk = (analytics.total_revenue_lost as number) || 48291
  const activeCampaigns = (analytics.active_campaigns as number) || 38
  const totalAbandoned = (analytics.total_abandoned as number) || 142
  const carts = fallbackCarts

  const filtered = carts.filter((cart) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      if (!cart.customer.toLowerCase().includes(q)) return false
    }
    if (activeFilter === "Recoverable") return cart.outlook === "HIGH POTENTIAL" || cart.outlook === "MEDIUM"
    if (activeFilter === "Recovered") return false
    if (activeFilter === "Lost") return cart.outlook === "LOW"
    return true
  })

  return (
    <Shell
      title="Cart Recovery"
      subtitle="AI-powered abandoned cart detection and automated drip campaign orchestration."
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-1 bg-surface rounded-card p-1 border border-border">
            {filters.map((filter) => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={cn(
                  "px-4 py-2 rounded-button text-sm font-medium transition-all duration-200",
                  activeFilter === filter
                    ? "bg-primary text-white shadow-lg shadow-primary/20"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface-2"
                )}
              >
                {filter}
              </button>
            ))}
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search abandoned carts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2.5 rounded-button bg-surface border border-border text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary/30 transition-colors w-72"
            />
          </div>
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr className="border-b border-border">
                  <th className="label-caps px-5 py-4 text-left">Customer</th>
                  <th className="label-caps px-5 py-4 text-right">Cart Value</th>
                  <th className="label-caps px-5 py-4 text-center">Items</th>
                  <th className="label-caps px-5 py-4 text-left">Abandoned</th>
                  <th className="label-caps px-5 py-4 text-center">AI Outlook</th>
                  <th className="label-caps px-5 py-4 text-left">Last Touchpoint</th>
                  <th className="label-caps px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((cart) => (
                  <tr key={cart.id} className="group transition-colors">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/15 flex items-center justify-center">
                          <span className="text-xs font-medium text-primary">
                            {cart.customer.split(" ").map((n) => n[0]).join("")}
                          </span>
                        </div>
                        <span className="text-sm font-medium text-text-primary">{cart.customer}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <span className="font-mono text-data-sm text-text-primary">{cart.cartValue}</span>
                    </td>
                    <td className="px-5 py-4 text-center">
                      <span className="font-mono text-data-sm text-text-secondary">{cart.items}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-sm text-text-secondary">{cart.abandoned}</span>
                    </td>
                    <td className="px-5 py-4 text-center">
                      <span className={cn("badge", cart.outlookClass)}>{cart.outlook}</span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        {cart.lastTouchpoint.includes("Email") && (
                          <Mail className="w-3.5 h-3.5 text-primary" />
                        )}
                        {cart.lastTouchpoint.includes("SMS") && (
                          <MessageSquare className="w-3.5 h-3.5 text-info" />
                        )}
                        {cart.lastTouchpoint.includes("Push") && (
                          <Bell className="w-3.5 h-3.5 text-success" />
                        )}
                        {cart.lastTouchpoint === "Just Abandoned" && (
                          <ShoppingCart className="w-3.5 h-3.5 text-text-muted" />
                        )}
                        <span className="text-sm text-text-secondary">{cart.lastTouchpoint}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <button
                        className={cn(
                          "btn-ghost text-xs gap-1.5",
                          cart.action === "View" ? "text-text-secondary" : "text-primary hover:bg-primary/10 hover:text-primary"
                        )}
                      >
                        {cart.action === "Remind" ? (
                          <>
                            <Send className="w-3.5 h-3.5" />
                            {cart.action}
                          </>
                        ) : (
                          <>
                            <Eye className="w-3.5 h-3.5" />
                            {cart.action}
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="dot-green" />
              <span className="text-sm text-text-secondary">
                Recovery Rate: <span className="font-mono text-data-sm text-success">{recoveryRate}%</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="dot-red" />
              <span className="text-sm text-text-secondary">
                Revenue at Risk: <span className="font-mono text-data-sm text-danger">${revenueAtRisk.toLocaleString()}</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="dot-blue" />
              <span className="text-sm text-text-secondary">
                Active Campaigns: <span className="font-mono text-data-sm text-primary">{activeCampaigns}</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-sm text-text-muted">
              Showing <span className="text-text-secondary font-medium">{carts.length}</span> of <span className="text-text-secondary font-medium">{totalAbandoned}</span> abandoned carts
            </span>
            <div className="flex items-center gap-1">
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors border border-border">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center bg-primary text-white shadow-lg shadow-primary/20 transition-colors">
                1
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors border border-border">
                2
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors border border-border">
                3
              </button>
              <span className="text-text-muted px-1">...</span>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors border border-border">
                24
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-2 hover:text-text-primary transition-colors border border-border">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  )
}
