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
  ExternalLink,
  Loader2,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { MetricCardSkeleton } from "@/components/shared/Skeleton"
import { useShopifyStatus, useShopifySync } from "@/lib/hooks"
import { cn, formatTimestamp } from "@/lib/utils"

export default function ShopifyPage() {
  const statusQuery = useShopifyStatus()
  const syncMutation = useShopifySync()
  const status = statusQuery.data

  return (
    <Shell>
      <Topbar title="Shopify Integration" subtitle="Connected store management and sync status" />

      <div className="p-6 space-y-6">
        {/* Connection status */}
        <div className={cn(
          "flex items-center gap-3 p-3 rounded-lg border",
          status?.configured ? "bg-emerald/10 border-emerald/20" : "bg-amber/10 border-amber/20",
        )}>
          {status?.configured ? (
            <CheckCircle className="w-4 h-4 text-emerald" />
          ) : (
            <AlertCircle className="w-4 h-4 text-amber" />
          )}
          <span className={cn("text-sm", status?.configured ? "text-emerald" : "text-amber")}>
            {status?.configured
              ? `Connected to ${status.shop_domain} — API ${status.api_version}`
              : "Shopify not configured — add credentials to .env"}
          </span>
          {status?.configured && (
            <button
              onClick={() => syncMutation.mutate(false)}
              disabled={syncMutation.isPending}
              className="ml-auto btn-ghost text-xs py-1.5 px-3"
            >
              {syncMutation.isPending ? (
                <><Loader2 className="w-3 h-3 animate-spin" /> Syncing...</>
              ) : (
                <><RefreshCw className="w-3 h-3" /> Sync Now</>
              )}
            </button>
          )}
        </div>

        {/* Sync result */}
        {syncMutation.data && (
          <div className="flex items-center gap-3 p-3 rounded-lg bg-indigo/10 border border-indigo/20">
            <CheckCircle className="w-4 h-4 text-indigo" />
            <span className="text-sm text-indigo">
              Sync complete — {syncMutation.data.products_synced} products, {syncMutation.data.orders_synced} orders, {syncMutation.data.customers_synced} customers ({syncMutation.data.duration_seconds.toFixed(1)}s)
            </span>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          {statusQuery.isLoading ? (
            Array.from({ length: 4 }).map((_, i) => <MetricCardSkeleton key={i} />)
          ) : (
            <>
              <div className="card">
                <div className="section-label mb-2">Status</div>
                <div className={cn("metric-value text-display-md", status?.configured ? "text-emerald" : "text-amber")}>
                  {status?.configured ? "Connected" : "Not Configured"}
                </div>
              </div>
              <div className="card">
                <div className="section-label mb-2">API Version</div>
                <div className="metric-value text-display-md text-text-1">{status?.api_version ?? "—"}</div>
              </div>
              <div className="card">
                <div className="section-label mb-2">Store Domain</div>
                <div className="metric-value text-display-md text-indigo truncate">{status?.shop_domain ?? "—"}</div>
              </div>
              <div className="card">
                <div className="section-label mb-2">Webhooks</div>
                <div className="metric-value text-display-md text-text-1">{status?.webhook_topics?.length ?? 0}</div>
              </div>
            </>
          )}
        </div>

        {/* Webhooks */}
        {status?.webhook_topics && status.webhook_topics.length > 0 && (
          <div className="card">
            <h2 className="font-display font-semibold text-text-1 mb-4">Webhook Topics</h2>
            <div className="space-y-2">
              {status.webhook_topics.map((topic) => (
                <div key={topic} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-2 transition-colors">
                  <span className="font-mono text-data-sm text-indigo">{topic}</span>
                  <StatusBadge status="active" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick actions */}
        <div className="card">
          <h2 className="font-display font-semibold text-text-1 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => syncMutation.mutate(true)}
              disabled={syncMutation.isPending}
              className="btn-primary justify-center"
            >
              {syncMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Full Sync
            </button>
            <button
              onClick={() => syncMutation.mutate(false)}
              disabled={syncMutation.isPending}
              className="btn-ghost justify-center"
            >
              <Package className="w-4 h-4" /> Incremental Sync
            </button>
            <a href={`https://${status?.shop_domain || "your-store"}.myshopify.com/admin`} target="_blank" rel="noreferrer" className="btn-ghost justify-center">
              <ExternalLink className="w-4 h-4" /> Shopify Admin
            </a>
          </div>
        </div>
      </div>
    </Shell>
  )
}
