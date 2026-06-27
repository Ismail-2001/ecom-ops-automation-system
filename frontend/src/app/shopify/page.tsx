"use client"

import {
  ShoppingBag,
  RefreshCw,
  Package,
  ShoppingCart,
  DollarSign,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Clock,
  ExternalLink,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { cn, formatCurrency, formatTimestamp } from "@/lib/utils"

const shopifyStats = {
  totalProducts: 1247,
  activeProducts: 1180,
  totalOrders: 8432,
  revenue: 284920,
  syncStatus: "connected" as const,
  lastSync: new Date(Date.now() - 120000).toISOString(),
}

const recentSyncs = [
  { id: "1", type: "orders", status: "completed", items: 24, timestamp: new Date(Date.now() - 120000).toISOString() },
  { id: "2", type: "products", status: "completed", items: 156, timestamp: new Date(Date.now() - 300000).toISOString() },
  { id: "3", type: "inventory", status: "in_progress", items: 89, timestamp: new Date(Date.now() - 60000).toISOString() },
  { id: "4", type: "customers", status: "completed", items: 43, timestamp: new Date(Date.now() - 600000).toISOString() },
  { id: "5", type: "orders", status: "failed", items: 0, timestamp: new Date(Date.now() - 900000).toISOString() },
]

const webhooks = [
  { id: "wh-1", event: "orders/create", status: "active", lastFired: new Date(Date.now() - 300000).toISOString() },
  { id: "wh-2", event: "orders/updated", status: "active", lastFired: new Date(Date.now() - 600000).toISOString() },
  { id: "wh-3", event: "products/update", status: "active", lastFired: new Date(Date.now() - 1200000).toISOString() },
  { id: "wh-4", event: "inventory/update", status: "paused", lastFired: new Date(Date.now() - 86400000).toISOString() },
]

export default function ShopifyPage() {
  return (
    <Shell>
      <Topbar title="Shopify Integration" subtitle="Connected store management and sync status" />
      
      <div className="p-6 space-y-6">
        {/* Connection status */}
        <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald/10 border border-emerald/20">
          <CheckCircle className="w-4 h-4 text-emerald" />
          <span className="text-sm text-emerald">
            Connected to Shopify — Last sync {formatTimestamp(shopifyStats.lastSync)}
          </span>
          <button className="ml-auto btn-ghost text-xs py-1.5 px-3">
            <RefreshCw className="w-3 h-3" />
            Sync Now
          </button>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-4 gap-4">
          <div className="card">
            <div className="section-label mb-2">Total Products</div>
            <div className="metric-value text-display-md text-text-1">{shopifyStats.totalProducts.toLocaleString()}</div>
            <div className="text-xs text-emerald mt-1">{shopifyStats.activeProducts} active</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Total Orders</div>
            <div className="metric-value text-display-md text-text-1">{shopifyStats.totalOrders.toLocaleString()}</div>
            <div className="text-xs text-emerald mt-1">+12.3% this month</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Revenue</div>
            <div className="metric-value text-display-md text-text-1">{formatCurrency(shopifyStats.revenue)}</div>
            <div className="text-xs text-emerald mt-1">+8.7% vs last month</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Sync Health</div>
            <div className="metric-value text-display-md text-emerald">99.8%</div>
            <div className="text-xs text-text-3 mt-1">Uptime</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Recent syncs */}
          <div className="col-span-2 card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-text-1">Recent Sync Activity</h2>
              <button className="text-xs text-indigo hover:text-indigo-400">View all</button>
            </div>
            <div className="space-y-2">
              {recentSyncs.map((sync) => (
                <div key={sync.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center",
                      sync.type === "orders" ? "bg-indigo/10" : sync.type === "products" ? "bg-emerald/10" : sync.type === "inventory" ? "bg-amber/10" : "bg-violet/10"
                    )}>
                      {sync.type === "orders" ? <ShoppingCart className="w-4 h-4 text-indigo" /> :
                       sync.type === "products" ? <Package className="w-4 h-4 text-emerald" /> :
                       sync.type === "inventory" ? <ShoppingBag className="w-4 h-4 text-amber" /> :
                       <TrendingUp className="w-4 h-4 text-violet" />}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-text-1 capitalize">{sync.type} sync</div>
                      <div className="text-xs text-text-3">{sync.items} items processed</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={sync.status === "completed" ? "approved" : sync.status === "in_progress" ? "processing" : "flagged"} />
                    <span className="text-xs text-text-3">{formatTimestamp(sync.timestamp)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Webhooks */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-semibold text-text-1">Webhooks</h2>
              <button className="text-xs text-indigo hover:text-indigo-400">Manage</button>
            </div>
            <div className="space-y-3">
              {webhooks.map((wh) => (
                <div key={wh.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-surface-2 transition-colors">
                  <div>
                    <div className="font-mono text-data-sm text-indigo">{wh.event}</div>
                    <div className="text-xs text-text-3 mt-0.5">Last: {formatTimestamp(wh.lastFired)}</div>
                  </div>
                  <StatusBadge status={wh.status === "active" ? "active" : "paused"} />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick actions */}
        <div className="card">
          <h2 className="font-display font-semibold text-text-1 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-4 gap-3">
            <button className="btn-primary justify-center">
              <RefreshCw className="w-4 h-4" />
              Full Sync
            </button>
            <button className="btn-ghost justify-center">
              <Package className="w-4 h-4" />
              Sync Products
            </button>
            <button className="btn-ghost justify-center">
              <ShoppingCart className="w-4 h-4" />
              Sync Orders
            </button>
            <a href="#" target="_blank" className="btn-ghost justify-center">
              <ExternalLink className="w-4 h-4" />
              Open Shopify Admin
            </a>
          </div>
        </div>
      </div>
    </Shell>
  )
}
