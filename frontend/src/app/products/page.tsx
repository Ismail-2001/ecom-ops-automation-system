"use client"

import { useState } from "react"
import {
  Package,
  Search,
  Filter,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ExternalLink,
  DollarSign,
  ShoppingCart,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { ConfidencePill } from "@/components/shared/ConfidencePill"
import { cn, formatCurrency, formatNumber } from "@/lib/utils"

const mockProducts = [
  { id: "PROD-2847", name: "Wireless Noise-Canceling Headphones", sku: "WNC-001", price: 89.99, suggestedPrice: 79.99, stock: 342, sales30d: 187, status: "active", priceConfidence: 0.91, trend: "up" as const },
  { id: "PROD-1234", name: "Ergonomic Wireless Mouse", sku: "EWM-002", price: 49.99, suggestedPrice: 44.99, stock: 128, sales30d: 94, status: "active", priceConfidence: 0.89, trend: "up" as const },
  { id: "PROD-3456", name: "Ultra-Slim Laptop Stand", sku: "ULS-003", price: 34.99, suggestedPrice: 34.99, stock: 567, sales30d: 234, status: "active", priceConfidence: 0.85, trend: "up" as const },
  { id: "PROD-5678", name: "USB-C Hub 7-in-1", sku: "UCH-004", price: 29.99, suggestedPrice: 27.99, stock: 23, sales30d: 156, status: "low_stock", priceConfidence: 0.82, trend: "down" as const },
  { id: "PROD-7890", name: "Mechanical Keyboard RGB", sku: "MKR-005", price: 129.99, suggestedPrice: 119.99, stock: 89, sales30d: 67, status: "active", priceConfidence: 0.88, trend: "up" as const },
  { id: "PROD-9012", name: "Webcam 4K Pro", sku: "W4K-006", price: 79.99, suggestedPrice: 74.99, stock: 0, sales30d: 45, status: "out_of_stock", priceConfidence: 0.79, trend: "down" as const },
  { id: "PROD-3457", name: "Portable Charger 20000mAh", sku: "PC2-007", price: 39.99, suggestedPrice: 36.99, stock: 456, sales30d: 312, status: "active", priceConfidence: 0.93, trend: "up" as const },
  { id: "PROD-6789", name: "Smart LED Desk Lamp", sku: "SLD-008", price: 59.99, suggestedPrice: 54.99, stock: 15, sales30d: 28, status: "low_stock", priceConfidence: 0.76, trend: "down" as const },
]

export default function ProductsPage() {
  const [search, setSearch] = useState("")
  const [filter, setFilter] = useState("all")

  const filteredProducts = mockProducts.filter(p => {
    if (search && !p.name.toLowerCase().includes(search.toLowerCase()) && !p.sku.toLowerCase().includes(search.toLowerCase())) return false
    if (filter === "low_stock" && p.stock > 50) return false
    if (filter === "out_of_stock" && p.stock > 0) return false
    if (filter === "price_change" && p.price === p.suggestedPrice) return false
    return true
  })

  return (
    <Shell>
      <Topbar title="Products" subtitle="AI-optimized pricing and inventory management" />
      
      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          <div className="card">
            <div className="section-label mb-2">Total Products</div>
            <div className="metric-value text-display-md text-text-1">{mockProducts.length.toLocaleString()}</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Low Stock</div>
            <div className="metric-value text-display-md text-amber">{mockProducts.filter(p => p.stock <= 50 && p.stock > 0).length}</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Out of Stock</div>
            <div className="metric-value text-display-md text-red">{mockProducts.filter(p => p.stock === 0).length}</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Price Suggestions</div>
            <div className="metric-value text-display-md text-indigo">{mockProducts.filter(p => p.price !== p.suggestedPrice).length}</div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-3" />
            <input
              type="text"
              placeholder="Search products by name or SKU..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-surface border border-border text-text-1 text-sm focus:border-border-bright focus:outline-none transition-colors placeholder:text-text-3"
            />
          </div>
          <div className="flex items-center gap-2">
            {["all", "low_stock", "out_of_stock", "price_change"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "px-3 py-2 rounded-lg text-xs font-medium transition-colors",
                  filter === f ? "bg-indigo/10 text-indigo" : "bg-surface-2 text-text-2 hover:bg-surface-3"
                )}
              >
                {f === "all" ? "All" : f === "low_stock" ? "Low Stock" : f === "out_of_stock" ? "Out of Stock" : "Price Changes"}
              </button>
            ))}
          </div>
        </div>

        {/* Products table */}
        <div className="card overflow-hidden p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left text-xs font-semibold text-text-3 uppercase tracking-wider px-4 py-3">Product</th>
                <th className="text-left text-xs font-semibold text-text-3 uppercase tracking-wider px-4 py-3">SKU</th>
                <th className="text-right text-xs font-semibold text-text-3 uppercase tracking-wider px-4 py-3">Price</th>
                <th className="text-right text-xs font-semibold text-text-3 uppercase tracking-wider px-4 py-3">AI Suggested</th>
                <th className="text-right text-xs font-semibold text-text-3 uppercase tracking-wider px-4 py-3">Stock</th>
                <th className="text-right text-xs font-semibold text-text-3 uppercase tracking-wider px-4 py-3">Sales (30d)</th>
                <th className="text-center text-xs font-semibold text-text-3 uppercase tracking-wider px-4 py-3">Confidence</th>
                <th className="text-center text-xs font-semibold text-text-3 uppercase tracking-wider px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredProducts.map((product) => (
                <tr key={product.id} className="border-b border-border/50 hover:bg-surface-2 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-surface-3 flex items-center justify-center">
                        <Package className="w-4 h-4 text-text-3" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-text-1">{product.name}</div>
                        <div className="text-xs text-text-3">{product.id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-data-sm text-indigo">{product.sku}</td>
                  <td className="px-4 py-3 text-right font-mono text-data-sm text-text-1">{formatCurrency(product.price)}</td>
                  <td className="px-4 py-3 text-right">
                    {product.price !== product.suggestedPrice ? (
                      <div className="flex items-center justify-end gap-1.5">
                        <span className="font-mono text-data-sm text-emerald">{formatCurrency(product.suggestedPrice)}</span>
                        {product.suggestedPrice < product.price ? (
                          <TrendingDown className="w-3 h-3 text-emerald" />
                        ) : (
                          <TrendingUp className="w-3 h-3 text-amber" />
                        )}
                      </div>
                    ) : (
                      <span className="text-xs text-text-3">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={cn(
                      "font-mono text-data-sm",
                      product.stock === 0 ? "text-red" : product.stock <= 50 ? "text-amber" : "text-text-1"
                    )}>
                      {product.stock.toLocaleString()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-data-sm text-text-2">{product.sales30d}</td>
                  <td className="px-4 py-3 text-center"><ConfidencePill value={product.priceConfidence} /></td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={product.stock === 0 ? "flagged" : product.stock <= 50 ? "pending" : "approved"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Shell>
  )
}
