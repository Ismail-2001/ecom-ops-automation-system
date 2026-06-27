"use client"

import { useState } from "react"
import {
  Search,
  Filter,
  Download,
  Eye,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ExternalLink,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { ConfidencePill } from "@/components/shared/ConfidencePill"
import { RiskScore } from "@/components/shared/RiskScore"
import { cn, formatCurrency, formatTimestamp } from "@/lib/utils"
import type { Order, Decision } from "@/types/api"

const mockOrders: (Order & { decision?: Decision })[] = [
  {
    id: "ORD-8854",
    shopifyId: "482910374",
    customerEmail: "sarah.chen@example.com",
    customerName: "Sarah Chen",
    total: 284.97,
    currency: "USD",
    status: "pending",
    riskScore: 0.12,
    itemCount: 3,
    shippingAddress: { city: "New York", state: "NY", country: "US", zip: "10001" },
    createdAt: new Date(Date.now() - 300000).toISOString(),
    updatedAt: new Date(Date.now() - 300000).toISOString(),
    decision: {
      id: "DEC-1234",
      orderId: "ORD-8854",
      agent: "fraud_detection",
      type: "fraud_review",
      status: "approved",
      confidence: 0.95,
      riskScore: 0.12,
      reasoning: "Low risk indicators. Verified shipping address matches billing.",
      recommendedAction: "approve",
      data: {},
      createdAt: new Date(Date.now() - 300000).toISOString(),
      updatedAt: new Date(Date.now() - 300000).toISOString(),
    },
  },
  {
    id: "ORD-8853",
    shopifyId: "482910373",
    customerEmail: "mike.johnson@example.com",
    customerName: "Mike Johnson",
    total: 549.99,
    currency: "USD",
    status: "processing",
    riskScore: 0.68,
    itemCount: 1,
    shippingAddress: { city: "Los Angeles", state: "CA", country: "US", zip: "90001" },
    createdAt: new Date(Date.now() - 600000).toISOString(),
    updatedAt: new Date(Date.now() - 600000).toISOString(),
    decision: {
      id: "DEC-1233",
      orderId: "ORD-8853",
      agent: "fraud_detection",
      type: "fraud_review",
      status: "flagged",
      confidence: 0.78,
      riskScore: 0.68,
      reasoning: "Medium risk. New customer account with high-value order. Shipping address is a freight forwarder.",
      recommendedAction: "flag",
      data: {},
      createdAt: new Date(Date.now() - 600000).toISOString(),
      updatedAt: new Date(Date.now() - 600000).toISOString(),
    },
  },
  {
    id: "ORD-8852",
    shopifyId: "482910372",
    customerEmail: "attacker@malicious.com",
    customerName: "Suspicious User",
    total: 1249.95,
    currency: "USD",
    status: "cancelled",
    riskScore: 0.92,
    itemCount: 5,
    shippingAddress: { city: "Miami", state: "FL", country: "US", zip: "33101" },
    createdAt: new Date(Date.now() - 900000).toISOString(),
    updatedAt: new Date(Date.now() - 900000).toISOString(),
    decision: {
      id: "DEC-1232",
      orderId: "ORD-8852",
      agent: "fraud_detection",
      type: "fraud_review",
      status: "rejected",
      confidence: 0.94,
      riskScore: 0.92,
      reasoning: "High risk. Known fraud patterns detected. Multiple velocity checks failed.",
      recommendedAction: "reject",
      data: {},
      createdAt: new Date(Date.now() - 900000).toISOString(),
      updatedAt: new Date(Date.now() - 900000).toISOString(),
    },
  },
  {
    id: "ORD-8851",
    shopifyId: "482910371",
    customerEmail: "emma.wilson@example.com",
    customerName: "Emma Wilson",
    total: 89.99,
    currency: "USD",
    status: "delivered",
    riskScore: 0.08,
    itemCount: 1,
    shippingAddress: { city: "Chicago", state: "IL", country: "US", zip: "60601" },
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 86400000).toISOString(),
    decision: {
      id: "DEC-1231",
      orderId: "ORD-8851",
      agent: "fraud_detection",
      type: "fraud_review",
      status: "approved",
      confidence: 0.98,
      riskScore: 0.08,
      reasoning: "Very low risk. Repeat customer with verified address.",
      recommendedAction: "approve",
      data: {},
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      updatedAt: new Date(Date.now() - 86400000).toISOString(),
    },
  },
  {
    id: "ORD-8850",
    shopifyId: "482910370",
    customerEmail: "james.brown@example.com",
    customerName: "James Brown",
    total: 199.99,
    currency: "USD",
    status: "shipped",
    riskScore: 0.15,
    itemCount: 2,
    shippingAddress: { city: "Houston", state: "TX", country: "US", zip: "77001" },
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    updatedAt: new Date(Date.now() - 172800000).toISOString(),
  },
]

const statusFilters = ["All", "Pending", "Processing", "Shipped", "Delivered", "Cancelled"]

export default function OrdersPage() {
  const [activeFilter, setActiveFilter] = useState("All")
  const [searchQuery, setSearchQuery] = useState("")

  const filteredOrders = mockOrders.filter((order) => {
    if (activeFilter !== "All" && order.status !== activeFilter.toLowerCase()) return false
    if (searchQuery && !order.id.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !order.customerName.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  return (
    <Shell>
      <Topbar
        title="Orders"
        subtitle="Manage orders and fraud decisions"
        actions={
          <>
            <button className="btn-ghost">
              <Download className="w-3.5 h-3.5" />
              Export
            </button>
          </>
        }
      />

      <div className="p-6 space-y-4">
        {/* Filter bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {statusFilters.map((filter) => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                  activeFilter === filter
                    ? "bg-indigo/10 text-indigo"
                    : "text-text-3 hover:text-text-2 hover:bg-surface-2"
                )}
              >
                {filter}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-3" />
              <input
                type="text"
                placeholder="Search orders..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-2 rounded-lg bg-surface-2 border border-border text-sm text-text-1 placeholder:text-text-3 focus:outline-none focus:border-border-bright w-64"
              />
            </div>
            <button className="btn-ghost">
              <Filter className="w-3.5 h-3.5" />
              Filters
            </button>
          </div>
        </div>

        {/* Orders table */}
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left px-4 py-3 section-label text-[10px]">Order</th>
                <th className="text-left px-4 py-3 section-label text-[10px]">Customer</th>
                <th className="text-left px-4 py-3 section-label text-[10px]">Total</th>
                <th className="text-left px-4 py-3 section-label text-[10px]">Risk</th>
                <th className="text-left px-4 py-3 section-label text-[10px]">AI Decision</th>
                <th className="text-left px-4 py-3 section-label text-[10px]">Confidence</th>
                <th className="text-left px-4 py-3 section-label text-[10px]">Status</th>
                <th className="text-left px-4 py-3 section-label text-[10px]">Time</th>
                <th className="text-right px-4 py-3 section-label text-[10px]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order) => (
                <tr
                  key={order.id}
                  className="border-b border-white/3 hover:bg-indigo/4 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="font-mono text-data-sm text-indigo">{order.id}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <div className="text-sm text-text-1">{order.customerName}</div>
                      <div className="text-xs text-text-3">{order.customerEmail}</div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-data-sm text-text-1">{formatCurrency(order.total)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <RiskScore score={order.riskScore} />
                  </td>
                  <td className="px-4 py-3">
                    {order.decision ? (
                      <StatusBadge status={order.decision.status} />
                    ) : (
                      <span className="text-xs text-text-3">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {order.decision ? (
                      <ConfidencePill value={order.decision.confidence} />
                    ) : (
                      <span className="text-xs text-text-3">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={order.status} />
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-text-3">{formatTimestamp(order.createdAt)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button className="p-1.5 rounded hover:bg-surface-3 transition-colors">
                        <Eye className="w-3.5 h-3.5 text-text-3" />
                      </button>
                      {order.decision?.status === "flagged" && (
                        <>
                          <button className="p-1.5 rounded hover:bg-emerald/10 transition-colors">
                            <CheckCircle className="w-3.5 h-3.5 text-emerald" />
                          </button>
                          <button className="p-1.5 rounded hover:bg-red/10 transition-colors">
                            <XCircle className="w-3.5 h-3.5 text-red" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredOrders.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12">
              <CheckCircle className="w-12 h-12 text-emerald mb-3" />
              <p className="text-sm text-text-2">No orders match your filters</p>
              <p className="text-xs text-text-3 mt-1">All clear — no pending decisions</p>
            </div>
          )}
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-text-3">
            Showing {filteredOrders.length} of {mockOrders.length} orders
          </span>
          <div className="flex items-center gap-2">
            <button className="btn-ghost text-xs" disabled>Previous</button>
            <button className="btn-ghost text-xs" disabled>Next</button>
          </div>
        </div>
      </div>
    </Shell>
  )
}
