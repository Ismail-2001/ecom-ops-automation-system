"use client"

import { useState } from "react"
import {
  Search,
  ChevronLeft,
  ChevronRight,
  Eye,
  ShoppingCart,
  AlertTriangle,
  TrendingUp,
  ArrowUpRight,
  Package,
  Zap,
  Percent,
} from "lucide-react"
import Shell from "@/components/layout/Shell"
import { cn } from "@/lib/utils"

const products = [
  {
    sku: "SKU-441",
    name: "Wireless Pro Headphones",
    stock: 24,
    status: "LOW STOCK",
    statusClass: "badge-warning",
    sales30d: "1,892",
    suggestion: "Increase +15% stock",
    suggestionIcon: TrendingUp,
    suggestionColor: "text-warning",
    action: "Restock",
    actionIcon: ShoppingCart,
  },
  {
    sku: "SKU-112",
    name: "Organic Face Serum",
    stock: 0,
    status: "OUT OF STOCK",
    statusClass: "badge-danger",
    sales30d: "2,341",
    suggestion: "Priority restock 500 units",
    suggestionIcon: AlertTriangle,
    suggestionColor: "text-danger",
    action: "Emergency",
    actionIcon: Zap,
  },
  {
    sku: "SKU-789",
    name: "Smart Fitness Tracker",
    stock: 542,
    status: "OPTIMAL",
    statusClass: "badge-success",
    sales30d: "456",
    suggestion: "Maintain current levels",
    suggestionIcon: Package,
    suggestionColor: "text-success",
    action: "View",
    actionIcon: Eye,
  },
  {
    sku: "SKU-203",
    name: "Minimalist Desk Lamp",
    stock: 18,
    status: "LOW STOCK",
    statusClass: "badge-warning",
    sales30d: "1,203",
    suggestion: "Increase +20% stock",
    suggestionIcon: TrendingUp,
    suggestionColor: "text-warning",
    action: "Restock",
    actionIcon: ShoppingCart,
  },
  {
    sku: "SKU-567",
    name: "Premium Yoga Mat",
    stock: 128,
    status: "OPTIMAL",
    statusClass: "badge-success",
    sales30d: "678",
    suggestion: "Consider 10% price increase",
    suggestionIcon: ArrowUpRight,
    suggestionColor: "text-success",
    action: "Adjust",
    actionIcon: TrendingUp,
  },
  {
    sku: "SKU-890",
    name: "Bluetooth Speaker",
    stock: 1240,
    status: "EXCESS",
    statusClass: "badge-info",
    sales30d: "234",
    suggestion: "Run promotion -15% discount",
    suggestionIcon: Percent,
    suggestionColor: "text-info",
    action: "Promote",
    actionIcon: Percent,
  },
]

const filters = ["All Products", "Low Stock", "Optimized", "New Arrivals"]

export default function ProductsPage() {
  const [activeFilter, setActiveFilter] = useState("All Products")
  const [searchQuery, setSearchQuery] = useState("")

  const filteredProducts = products.filter((product) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      if (!product.sku.toLowerCase().includes(q) && !product.name.toLowerCase().includes(q)) {
        return false
      }
    }
    if (activeFilter === "Low Stock") return product.status === "LOW STOCK"
    if (activeFilter === "Optimized") return product.status === "OPTIMAL"
    if (activeFilter === "New Arrivals") return false
    return true
  })

  return (
    <Shell
      title="Product Catalog"
      subtitle="AI-powered inventory management and catalog optimization."
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
              placeholder="Search products..."
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
                  <th className="label-caps px-5 py-4 text-left">SKU</th>
                  <th className="label-caps px-5 py-4 text-left">Product Name</th>
                  <th className="label-caps px-5 py-4 text-right">Stock</th>
                  <th className="label-caps px-5 py-4 text-center">Status</th>
                  <th className="label-caps px-5 py-4 text-right">Sales/30D</th>
                  <th className="label-caps px-5 py-4 text-left">AI Suggestion</th>
                  <th className="label-caps px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map((product) => {
                  const SuggestionIcon = product.suggestionIcon
                  const ActionIcon = product.actionIcon
                  return (
                    <tr key={product.sku} className="group transition-colors">
                      <td className="px-5 py-4">
                        <span className="font-mono text-data-sm text-primary">{product.sku}</span>
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-sm font-medium text-text-primary">{product.name}</span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <span
                          className={cn(
                            "font-mono text-data-sm",
                            product.stock === 0
                              ? "text-danger"
                              : product.stock <= 50
                                ? "text-warning"
                                : product.stock > 1000
                                  ? "text-info"
                                  : "text-text-primary"
                          )}
                        >
                          {product.stock.toLocaleString()}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className={cn("badge", product.statusClass)}>
                          {product.status}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <span className="font-mono text-data-sm text-text-secondary">{product.sales30d}</span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <SuggestionIcon className={cn("w-4 h-4 shrink-0", product.suggestionColor)} />
                          <span className="text-sm text-text-secondary">{product.suggestion}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <button
                          className={cn(
                            "btn-ghost text-xs gap-1.5",
                            product.action === "Emergency" &&
                              "text-danger hover:bg-danger/10 hover:text-danger border border-danger/20"
                          )}
                        >
                          <ActionIcon className="w-3.5 h-3.5" />
                          {product.action}
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
              <div className="dot-amber" />
              <span className="text-sm text-text-secondary">
                Low Stock Items: <span className="font-mono text-data-sm text-warning">12</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="dot-red" />
              <span className="text-sm text-text-secondary">
                Revenue at Risk: <span className="font-mono text-data-sm text-danger">$24,891</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-sm text-text-muted">
              Showing <span className="text-text-secondary font-medium">6</span> of <span className="text-text-secondary font-medium">1,847</span> products
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
                308
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
