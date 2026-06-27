"use client"

import { useState } from "react"
import {
  RefreshCw,
  Mail,
  MessageSquare,
  DollarSign,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  Eye,
  Send,
  Percent,
  Truck,
  Zap,
  Users,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { ConfidencePill } from "@/components/shared/ConfidencePill"
import { MetricCard } from "@/components/shared/MetricCard"
import { cn, formatCurrency, formatTimestamp } from "@/lib/utils"

interface AbandonedCart {
  id: string
  customerEmail: string
  customerName: string
  items: { name: string; price: number; quantity: number }[]
  total: number
  abandonedAt: string
  strategy: string
  status: "pending" | "sent" | "recovered" | "expired"
  discountCode?: string
  confidence: number
}

const mockCarts: AbandonedCart[] = [
  {
    id: "CART-4821",
    customerEmail: "sarah.chen@example.com",
    customerName: "Sarah Chen",
    items: [
      { name: "Wireless Headphones", price: 79.99, quantity: 1 },
      { name: "Phone Case", price: 29.99, quantity: 2 },
    ],
    total: 139.97,
    abandonedAt: new Date(Date.now() - 3600000).toISOString(),
    strategy: "discount_10",
    status: "sent",
    discountCode: "SAVE10-SARAH",
    confidence: 0.82,
  },
  {
    id: "CART-4820",
    customerEmail: "mike.johnson@example.com",
    customerName: "Mike Johnson",
    items: [
      { name: "Smart Watch", price: 199.99, quantity: 1 },
    ],
    total: 199.99,
    abandonedAt: new Date(Date.now() - 7200000).toISOString(),
    strategy: "free_shipping",
    status: "recovered",
    confidence: 0.78,
  },
  {
    id: "CART-4819",
    customerEmail: "emma.wilson@example.com",
    customerName: "Emma Wilson",
    items: [
      { name: "Running Shoes", price: 129.99, quantity: 1 },
      { name: "Sports Bag", price: 49.99, quantity: 1 },
    ],
    total: 179.98,
    abandonedAt: new Date(Date.now() - 14400000).toISOString(),
    strategy: "urgency",
    status: "pending",
    confidence: 0.85,
  },
  {
    id: "CART-4818",
    customerEmail: "james.brown@example.com",
    customerName: "James Brown",
    items: [
      { name: "Laptop Stand", price: 49.99, quantity: 1 },
      { name: "USB-C Hub", price: 39.99, quantity: 1 },
    ],
    total: 89.98,
    abandonedAt: new Date(Date.now() - 28800000).toISOString(),
    strategy: "discount_15",
    status: "expired",
    confidence: 0.71,
  },
]

const strategyLabels: Record<string, string> = {
  discount_10: "10% Discount",
  discount_15: "15% Discount",
  free_shipping: "Free Shipping",
  urgency: "Urgency Message",
  social_proof: "Social Proof",
}

const strategyIcons: Record<string, any> = {
  discount_10: Percent,
  discount_15: Percent,
  free_shipping: Truck,
  urgency: Zap,
  social_proof: Users,
}

export default function CartRecoveryPage() {
  const [selectedCart, setSelectedCart] = useState<AbandonedCart | null>(mockCarts[0])

  return (
    <Shell>
      <Topbar
        title="Cart Recovery"
        subtitle="AI-powered abandoned cart recovery"
        actions={
          <button className="btn-primary">
            <Send className="w-3.5 h-3.5" />
            Send All Pending
          </button>
        }
      />

      <div className="p-6 space-y-6">
        {/* Metrics */}
        <div className="grid grid-cols-4 gap-4">
          <MetricCard
            label="Carts Abandoned"
            value={45}
            delta={-8.2}
            deltaLabel="vs last week"
            icon={<RefreshCw className="w-4 h-4 text-amber" />}
            color="bg-amber/10"
          />
          <MetricCard
            label="Recovery Rate"
            value="18.5%"
            delta={2.3}
            deltaLabel="vs last week"
            icon={<TrendingUp className="w-4 h-4 text-emerald" />}
            color="bg-emerald/10"
          />
          <MetricCard
            label="Revenue Recovered"
            value={12500}
            delta={15.2}
            deltaLabel="vs last week"
            icon={<DollarSign className="w-4 h-4 text-indigo" />}
            color="bg-indigo/10"
            format="currency"
          />
          <MetricCard
            label="Pending Emails"
            value={8}
            icon={<Mail className="w-4 h-4 text-cyan" />}
            color="bg-cyan/10"
          />
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Cart list */}
          <div className="col-span-2 space-y-3">
            {mockCarts.map((cart) => {
              const StrategyIcon = strategyIcons[cart.strategy] || RefreshCw
              return (
                <button
                  key={cart.id}
                  onClick={() => setSelectedCart(cart)}
                  className={cn(
                    "card w-full text-left transition-all duration-150",
                    selectedCart?.id === cart.id && "border-indigo card-glow"
                  )}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-data-sm text-indigo">{cart.id}</span>
                      <StatusBadge status={cart.status} />
                    </div>
                    <ConfidencePill value={cart.confidence} />
                  </div>

                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <div className="text-sm text-text-1">{cart.customerName}</div>
                      <div className="text-xs text-text-3">{cart.customerEmail}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-data-sm text-text-1">{formatCurrency(cart.total)}</div>
                      <div className="text-xs text-text-3">{cart.items.length} items</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <StrategyIcon className="w-3.5 h-3.5 text-violet" />
                      <span className="text-xs text-text-2">{strategyLabels[cart.strategy]}</span>
                    </div>
                    <span className="text-xs text-text-3">{formatTimestamp(cart.abandonedAt)}</span>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Cart detail */}
          <div className="space-y-4">
            {selectedCart && (
              <>
                <div className="card">
                  <h3 className="section-label mb-4">Cart Details</h3>
                  <div className="space-y-3">
                    {selectedCart.items.map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-surface-2">
                        <div>
                          <div className="text-sm text-text-1">{item.name}</div>
                          <div className="text-xs text-text-3">Qty: {item.quantity}</div>
                        </div>
                        <span className="font-mono text-data-sm text-text-2">{formatCurrency(item.price * item.quantity)}</span>
                      </div>
                    ))}
                    <div className="flex items-center justify-between pt-2 border-t border-border">
                      <span className="text-sm font-medium text-text-1">Total</span>
                      <span className="font-mono text-data-sm text-indigo">{formatCurrency(selectedCart.total)}</span>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3 className="section-label mb-4">Recovery Strategy</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-2">Strategy</span>
                      <span className="text-sm text-text-1">{strategyLabels[selectedCart.strategy]}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-2">AI Confidence</span>
                      <ConfidencePill value={selectedCart.confidence} />
                    </div>
                    {selectedCart.discountCode && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-text-2">Discount Code</span>
                        <span className="font-mono text-data-sm text-violet">{selectedCart.discountCode}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="card">
                  <h3 className="section-label mb-4">Actions</h3>
                  <div className="space-y-2">
                    {selectedCart.status === "pending" && (
                      <button className="w-full btn-primary justify-center">
                        <Send className="w-4 h-4" />
                        Send Recovery Email
                      </button>
                    )}
                    <button className="w-full btn-ghost justify-center">
                      <Mail className="w-4 h-4" />
                      Send Manual Email
                    </button>
                    <button className="w-full btn-ghost justify-center">
                      <Eye className="w-4 h-4" />
                      View Customer Profile
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </Shell>
  )
}
