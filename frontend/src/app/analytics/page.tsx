"use client"

import { useState } from "react"
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  ShoppingCart,
  Bot,
  Users,
  RefreshCw,
  HeadphonesIcon,
  Shield,
  Package,
  Star,
  Megaphone,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { MetricCard } from "@/components/shared/MetricCard"
import { cn, formatCurrency, formatNumber } from "@/lib/utils"

const roiData = [
  { agent: "Fraud Detection", savings: 5000, roi: 300, icon: Shield, color: "red" },
  { agent: "Inventory Management", savings: 8000, roi: 400, icon: Package, color: "cyan" },
  { agent: "Price Optimization", savings: 12000, roi: 600, icon: DollarSign, color: "amber" },
  { agent: "Review Moderation", savings: 3000, roi: 250, icon: Star, color: "violet" },
  { agent: "Marketing Automation", savings: 10000, roi: 500, icon: Megaphone, color: "indigo" },
  { agent: "Cart Recovery", savings: 8000, roi: 450, icon: RefreshCw, color: "emerald" },
  { agent: "Customer Support", savings: 10000, roi: 350, icon: HeadphonesIcon, color: "cyan" },
]

const performanceData = [
  { metric: "Total Orders", value: "24,500", change: "+12.5%", period: "Last 30 days" },
  { metric: "Revenue", value: "$1.25M", change: "+8.3%", period: "Last 30 days" },
  { metric: "Fraud Prevented", value: "$45,000", change: "+15.2%", period: "Last 30 days" },
  { metric: "Carts Recovered", value: "812", change: "+22.1%", period: "Last 30 days" },
  { metric: "Tickets Resolved", value: "1,847", change: "+18.7%", period: "Last 30 days" },
  { metric: "Avg Response Time", value: "2.8s", change: "-12.3%", period: "Last 30 days" },
]

const chartData = [
  { name: "Jan", revenue: 85000, orders: 650 },
  { name: "Feb", revenue: 92000, orders: 710 },
  { name: "Mar", revenue: 98000, orders: 750 },
  { name: "Apr", revenue: 105000, orders: 820 },
  { name: "May", revenue: 112000, orders: 870 },
  { name: "Jun", revenue: 118000, orders: 910 },
  { name: "Jul", revenue: 125000, orders: 960 },
  { name: "Aug", revenue: 132000, orders: 1020 },
  { name: "Sep", revenue: 128000, orders: 990 },
  { name: "Oct", revenue: 135000, orders: 1050 },
  { name: "Nov", revenue: 142000, orders: 1100 },
  { name: "Dec", revenue: 150000, orders: 1180 },
]

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("30d")
  const maxRevenue = Math.max(...chartData.map(d => d.revenue))

  return (
    <Shell>
      <Topbar
        title="Analytics"
        subtitle="ROI and performance metrics"
        actions={
          <div className="flex items-center gap-2">
            {["7d", "30d", "90d", "1y"].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                  timeRange === range
                    ? "bg-indigo/10 text-indigo"
                    : "text-text-3 hover:text-text-2 hover:bg-surface-2"
                )}
              >
                {range}
              </button>
            ))}
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Top metrics */}
        <div className="grid grid-cols-4 gap-4">
          <MetricCard
            label="Total Savings"
            value={56000}
            delta={18.5}
            deltaLabel="vs last month"
            icon={<DollarSign className="w-4 h-4 text-emerald" />}
            color="bg-emerald/10"
            format="currency"
          />
          <MetricCard
            label="ROI"
            value="420%"
            delta={25.3}
            deltaLabel="vs last month"
            icon={<TrendingUp className="w-4 h-4 text-indigo" />}
            color="bg-indigo/10"
          />
          <MetricCard
            label="Agents Active"
            value={7}
            icon={<Bot className="w-4 h-4 text-violet" />}
            color="bg-violet/10"
          />
          <MetricCard
            label="Uptime"
            value="99.97%"
            delta={0.02}
            deltaLabel="vs last month"
            icon={<BarChart3 className="w-4 h-4 text-cyan" />}
            color="bg-cyan/10"
          />
        </div>

        {/* Revenue chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="section-label">Revenue Trend</h3>
            <span className="text-xs text-text-3">Last 12 months</span>
          </div>
          <div className="flex items-end gap-2 h-48">
            {chartData.map((d, i) => (
              <div key={d.name} className="flex-1 flex flex-col items-center gap-2">
                <div
                  className="w-full bg-indigo/20 rounded-t transition-all duration-500 hover:bg-indigo/30"
                  style={{ height: `${(d.revenue / maxRevenue) * 100}%` }}
                />
                <span className="text-[10px] text-text-3">{d.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Agent ROI */}
          <div className="card">
            <h3 className="section-label mb-4">Agent ROI</h3>
            <div className="space-y-4">
              {roiData.map((agent) => {
                const Icon = agent.icon
                return (
                  <div key={agent.agent} className="flex items-center gap-3">
                    <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", `bg-${agent.color}/10`)}>
                      <Icon className={cn("w-4 h-4", `text-${agent.color}`)} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-text-1">{agent.agent}</span>
                        <span className="font-mono text-data-sm text-emerald">{formatCurrency(agent.savings)}/mo</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-indigo rounded-full"
                            style={{ width: `${Math.min(agent.roi / 6, 100)}%` }}
                          />
                        </div>
                        <span className="font-mono text-data-xs text-text-3">{agent.roi}%</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Performance metrics */}
          <div className="card">
            <h3 className="section-label mb-4">Performance Metrics</h3>
            <div className="space-y-4">
              {performanceData.map((item) => (
                <div key={item.metric} className="flex items-center justify-between p-2 rounded-lg hover:bg-surface-2 transition-colors">
                  <div>
                    <div className="text-sm text-text-1">{item.metric}</div>
                    <div className="text-xs text-text-3">{item.period}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-data-sm text-text-1">{item.value}</div>
                    <div className={cn(
                      "text-xs font-medium",
                      item.change.startsWith("+") ? "text-emerald" : "text-amber"
                    )}>
                      {item.change}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Cost breakdown */}
        <div className="card">
          <h3 className="section-label mb-4">Cost Breakdown</h3>
          <div className="grid grid-cols-4 gap-6">
            <div className="text-center p-4 rounded-lg bg-surface-2">
              <div className="text-xs text-text-3 mb-1">Infrastructure</div>
              <div className="font-mono text-data-lg text-text-1">$265</div>
              <div className="text-xs text-text-3">/month</div>
            </div>
            <div className="text-center p-4 rounded-lg bg-surface-2">
              <div className="text-xs text-text-3 mb-1">LLM API</div>
              <div className="font-mono text-data-lg text-text-1">$180</div>
              <div className="text-xs text-text-3">/month</div>
            </div>
            <div className="text-center p-4 rounded-lg bg-surface-2">
              <div className="text-xs text-text-3 mb-1">Total Cost</div>
              <div className="font-mono text-data-lg text-indigo">$445</div>
              <div className="text-xs text-text-3">/month</div>
            </div>
            <div className="text-center p-4 rounded-lg bg-emerald/10 border border-emerald/20">
              <div className="text-xs text-emerald mb-1">Net Savings</div>
              <div className="font-mono text-data-lg text-emerald">$55,555</div>
              <div className="text-xs text-emerald">/month</div>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  )
}
