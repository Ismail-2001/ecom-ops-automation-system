"use client"

import { useState } from "react"
import { Search, ChevronLeft, ChevronRight, Eye, ShieldAlert, CheckCircle, Truck, Ban, Clock } from "lucide-react"
import Shell from "@/components/layout/Shell"
import { cn } from "@/lib/utils"

const orders = [
  {
    id: "ORD-7042",
    customer: "Sarah Chen",
    amount: "$2,847.00",
    status: "Processing",
    statusClass: "badge-primary",
    fraudScore: 87,
    riskClass: "risk-high",
    confidence: 98.2,
    confidenceClass: "confidence-high",
    action: "Review",
    actionIcon: Eye,
  },
  {
    id: "ORD-7041",
    customer: "Marcus Williams",
    amount: "$129.99",
    status: "Delivered",
    statusClass: "badge-success",
    fraudScore: 12,
    riskClass: "risk-low",
    confidence: 99.1,
    confidenceClass: "confidence-high",
    action: "View",
    actionIcon: Eye,
  },
  {
    id: "ORD-7040",
    customer: "Emma Rodriguez",
    amount: "$4,521.00",
    status: "Flagged",
    statusClass: "badge-danger",
    fraudScore: 94,
    riskClass: "risk-high",
    confidence: 82.4,
    confidenceClass: "confidence-low",
    action: "Block",
    actionIcon: Ban,
  },
  {
    id: "ORD-7039",
    customer: "James O'Connor",
    amount: "$89.99",
    status: "Processing",
    statusClass: "badge-primary",
    fraudScore: 23,
    riskClass: "risk-low",
    confidence: 95.7,
    confidenceClass: "confidence-high",
    action: "Review",
    actionIcon: Eye,
  },
  {
    id: "ORD-7038",
    customer: "Yuki Tanaka",
    amount: "$1,245.00",
    status: "Pending",
    statusClass: "badge-warning",
    fraudScore: 67,
    riskClass: "risk-medium",
    confidence: 88.9,
    confidenceClass: "confidence-medium",
    action: "Approve",
    actionIcon: CheckCircle,
  },
  {
    id: "ORD-7037",
    customer: "Aisha Patel",
    amount: "$342.00",
    status: "Shipped",
    statusClass: "badge-info",
    fraudScore: 8,
    riskClass: "risk-low",
    confidence: 97.3,
    confidenceClass: "confidence-high",
    action: "Track",
    actionIcon: Truck,
  },
]

const filters = ["All Orders", "Pending Review", "Flagged", "Completed"]

export default function OrdersPage() {
  const [activeFilter, setActiveFilter] = useState("All Orders")
  const [searchQuery, setSearchQuery] = useState("")

  const filteredOrders = orders.filter((order) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      if (!order.id.toLowerCase().includes(q) && !order.customer.toLowerCase().includes(q)) {
        return false
      }
    }
    if (activeFilter === "Pending Review") return order.status === "Pending"
    if (activeFilter === "Flagged") return order.status === "Flagged"
    if (activeFilter === "Completed") return order.status === "Delivered"
    return true
  })

  return (
    <Shell
      title="Order Intelligence"
      subtitle="AI-powered order tracking, fraud detection, and fulfillment optimization."
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-1 bg-surface-2 rounded-card p-1 border border-border">
            {filters.map((filter) => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={cn(
                  "px-4 py-2 rounded-button text-sm font-medium transition-all duration-200",
                  activeFilter === filter
                    ? "bg-primary text-white shadow-sm"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface-3"
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
              placeholder="Search orders..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2.5 rounded-button bg-white border border-border text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all w-72"
            />
          </div>
        </div>

        <div className="bg-white rounded-card shadow-card border border-border overflow-hidden">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr className="border-b border-border">
                  <th className="label-caps px-5 py-4 text-left">Order ID</th>
                  <th className="label-caps px-5 py-4 text-left">Customer</th>
                  <th className="label-caps px-5 py-4 text-right">Amount</th>
                  <th className="label-caps px-5 py-4 text-center">Status</th>
                  <th className="label-caps px-5 py-4 text-left">Fraud Score</th>
                  <th className="label-caps px-5 py-4 text-center">AI Confidence</th>
                  <th className="label-caps px-5 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map((order) => {
                  const ActionIcon = order.actionIcon
                  return (
                    <tr key={order.id} className="border-b border-border last:border-b-0 hover:bg-surface-2 transition-colors">
                      <td className="px-5 py-4">
                        <span className="font-mono text-data-sm text-primary">{order.id}</span>
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-sm font-medium text-text-primary">{order.customer}</span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <span className="font-mono text-data-sm text-text-primary">{order.amount}</span>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className={cn("badge", order.statusClass)}>{order.status}</span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3 min-w-[140px]">
                          <div className="risk-bar flex-1">
                            <div
                              className={cn("risk-bar-fill", order.riskClass)}
                              style={{ width: `${order.fraudScore}%` }}
                            />
                          </div>
                          <span className="font-mono text-data-sm text-text-secondary w-10 text-right">
                            {order.fraudScore}%
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className={cn("confidence-pill", order.confidenceClass)}>
                          {order.confidence}%
                        </span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <button
                          className={cn(
                            "btn-ghost text-xs gap-1.5",
                            order.action === "Block" && "text-danger hover:bg-danger/10 hover:text-danger"
                          )}
                        >
                          <ActionIcon className="w-3.5 h-3.5" />
                          {order.action}
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="dot-red" />
              <span className="text-sm text-text-secondary">Total Flagged Orders: <span className="font-mono text-data-sm text-danger">18</span></span>
            </div>
            <div className="flex items-center gap-2">
              <div className="dot-blue" />
              <span className="text-sm text-text-secondary">Avg Processing Time: <span className="font-mono text-data-sm text-primary">2.3s</span></span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-sm text-text-muted">
              Showing <span className="text-text-secondary font-medium">6</span> of <span className="text-text-secondary font-medium">2,847</span> orders
            </span>
            <div className="flex items-center gap-1">
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-3 hover:text-text-primary transition-colors border border-border">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center bg-primary text-white shadow-sm transition-colors">
                1
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-3 hover:text-text-primary transition-colors border border-border">
                2
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-3 hover:text-text-primary transition-colors border border-border">
                3
              </button>
              <span className="text-text-muted px-1">...</span>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-3 hover:text-text-primary transition-colors border border-border">
                475
              </button>
              <button className="w-8 h-8 rounded-button flex items-center justify-center text-text-muted hover:bg-surface-3 hover:text-text-primary transition-colors border border-border">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  )
}
