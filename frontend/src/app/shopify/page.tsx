"use client"

import {
  CheckCircle,
  ExternalLink,
  Package,
  ShoppingCart,
  Users,
  RefreshCw,
  Clock,
  AlertCircle,
  ArrowRight,
} from "lucide-react"
import Shell from "@/components/layout/Shell"
import { useShopifyStatus, useShopifySync } from "@/lib/hooks"

const fallbackSyncStats = [
  {
    label: "Products Synced",
    value: "1,847",
    icon: Package,
    iconBg: "bg-success/10",
    iconColor: "text-success",
    accentColor: "text-success",
  },
  {
    label: "Orders Synced",
    value: "2,847",
    icon: ShoppingCart,
    iconBg: "bg-info/10",
    iconColor: "text-info",
    accentColor: "text-info",
  },
  {
    label: "Customers Synced",
    value: "12,458",
    icon: Users,
    iconBg: "bg-warning/10",
    iconColor: "text-warning",
    accentColor: "text-warning",
  },
]

const recentActivity = [
  {
    timestamp: "14:22:01",
    type: "Order",
    status: "success" as const,
    details: "ORD-7042 synced",
  },
  {
    timestamp: "14:21:45",
    type: "Product",
    status: "success" as const,
    details: "SKU-441 inventory updated",
  },
  {
    timestamp: "14:20:33",
    type: "Customer",
    status: "pending" as const,
    details: "New customer import",
  },
  {
    timestamp: "14:18:55",
    type: "Order",
    status: "error" as const,
    details: "ORD-7039 retry required",
  },
]

function StatusDot({ status }: { status: "success" | "pending" | "error" }) {
  return (
    <span className="relative flex h-2.5 w-2.5">
      {status === "success" && (
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-40" />
      )}
      <span
        className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
          status === "success"
            ? "bg-success"
            : status === "pending"
              ? "bg-warning"
              : "bg-danger"
        }`}
      />
    </span>
  )
}

function StatusBadge({ status }: { status: "success" | "pending" | "error" }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-badge text-body-sm font-medium ${
        status === "success"
          ? "badge-success"
          : status === "pending"
            ? "badge-warning"
            : "badge-danger"
      }`}
    >
      <StatusDot status={status} />
      {status === "success" ? "Success" : status === "pending" ? "Pending" : "Error"}
    </span>
  )
}

export default function ShopifyPage() {
  const { data: shopifyStatus, isLoading } = useShopifyStatus()
   const { mutate: syncNow, isPending: isSyncing } = useShopifySync()

  const status = (shopifyStatus ?? { connected: true, store_url: "mystore.myshopify.com", last_sync: "2 minutes ago", products_count: 1847, orders_today: 142 }) as Record<string, unknown>
  const isConnected = status.connected !== false
  const storeUrl = (status.store_url as string) || "mystore.myshopify.com"
  const lastSync = (status.last_sync as string) || "2 minutes ago"
  const productsCount = (status.products_count as number) || 1847
  const ordersToday = (status.orders_today as number) || 142

  const syncStats = [
    {
      label: "Products Synced",
      value: productsCount.toLocaleString(),
      icon: Package,
      iconBg: "bg-success/10",
      iconColor: "text-success",
      accentColor: "text-success",
    },
    {
      label: "Orders Synced",
      value: "2,847",
      icon: ShoppingCart,
      iconBg: "bg-info/10",
      iconColor: "text-info",
      accentColor: "text-info",
    },
    {
      label: "Customers Synced",
      value: "12,458",
      icon: Users,
      iconBg: "bg-warning/10",
      iconColor: "text-warning",
      accentColor: "text-warning",
    },
  ]

  return (
    <Shell
      title="Shopify Integration"
      subtitle="Monitor and manage your connected Shopify store."
    >
      <div className="space-y-6 max-w-6xl">
        {/* Connection Status */}
        <div className="card border-l-4 border-l-success">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-14 h-14 rounded-card bg-success/10 flex items-center justify-center">
                  <CheckCircle className="w-7 h-7 text-success" />
                </div>
                <span className="absolute -top-1 -right-1 flex h-4 w-4">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-40" />
                  <span className="relative inline-flex rounded-full h-4 w-4 bg-success" />
                </span>
              </div>
              <div>
                <h3 className="font-display text-display-md text-text-primary">
                  Connected to Shopify
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-body-md text-text-secondary font-mono">
                    {storeUrl}
                  </span>
                  <a
                    href={`https://${storeUrl}/admin`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary hover:text-primary-hover transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            </div>
            <button 
              className="btn-primary" 
               onClick={() => syncNow(undefined)}
              disabled={isSyncing}
            >
              <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} /> {isSyncing ? 'Syncing...' : 'Sync Now'}
            </button>
          </div>

          <div className="grid grid-cols-3 gap-6 mt-6 pt-6 border-t border-border">
            <div>
              <div className="label-caps mb-1.5">Last Sync</div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-text-muted" />
                <span className="text-data-md text-text-primary">{lastSync}</span>
              </div>
            </div>
            <div>
              <div className="label-caps mb-1.5">Products Synced</div>
              <div className="flex items-center gap-2">
                <Package className="w-4 h-4 text-success" />
                <span className="font-display text-data-lg text-success">{productsCount.toLocaleString()}</span>
              </div>
            </div>
            <div>
              <div className="label-caps mb-1.5">Orders Today</div>
              <div className="flex items-center gap-2">
                <ShoppingCart className="w-4 h-4 text-info" />
                <span className="font-display text-data-lg text-info">{ordersToday.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sync Overview */}
        <div>
          <h3 className="label-caps mb-4">Sync Overview</h3>
          <div className="grid grid-cols-3 gap-4">
            {syncStats.map((stat) => {
              const Icon = stat.icon
              return (
                <div key={stat.label} className="card">
                  <div className="flex items-center gap-3 mb-3">
                    <div
                      className={`w-9 h-9 rounded-button ${stat.iconBg} flex items-center justify-center`}
                    >
                      <Icon className={`w-4 h-4 ${stat.iconColor}`} />
                    </div>
                    <span className="label-caps">{stat.label}</span>
                  </div>
                  <div
                    className={`font-display text-data-lg ${stat.accentColor}`}
                  >
                    {stat.value}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Recent Sync Activity */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="label-caps">Recent Sync Activity</h3>
            <button className="btn-ghost text-body-sm">
              View All <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>TIMESTAMP</th>
                  <th>TYPE</th>
                  <th>STATUS</th>
                  <th>DETAILS</th>
                </tr>
              </thead>
              <tbody>
                {recentActivity.map((row, i) => (
                  <tr key={i}>
                    <td className="font-mono text-data-sm text-text-secondary">
                      {row.timestamp}
                    </td>
                    <td>
                      <span className="inline-flex items-center gap-1.5 text-body-md text-text-primary">
                        {row.type === "Order" && (
                          <ShoppingCart className="w-3.5 h-3.5 text-info" />
                        )}
                        {row.type === "Product" && (
                          <Package className="w-3.5 h-3.5 text-success" />
                        )}
                        {row.type === "Customer" && (
                          <Users className="w-3.5 h-3.5 text-warning" />
                        )}
                        {row.type}
                      </span>
                    </td>
                    <td>
                      <StatusBadge status={row.status} />
                    </td>
                    <td className="text-body-md text-text-secondary">
                      {row.details}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Shell>
  )
}
