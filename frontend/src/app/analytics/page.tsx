"use client"

import { useState } from "react"
import {
  TrendingUp,
  DollarSign,
  Clock,
  Target,
  Download,
} from "lucide-react"
import Shell from "@/components/layout/Shell"

const timeRanges = ["30D", "7D", "24H"] as const

const metricCards = [
  {
    label: "ROI FROM AI AGENTS",
    value: "428.4%",
    change: "+12.4%",
    changeDir: "up" as const,
    icon: TrendingUp,
    iconBg: "bg-primary/10",
    iconColor: "text-primary",
  },
  {
    label: "TOTAL REVENUE SAVED",
    value: "$1.24M",
    change: "+8.2%",
    changeDir: "up" as const,
    icon: DollarSign,
    iconBg: "bg-success/10",
    iconColor: "text-success",
  },
  {
    label: "AVG. RESOLUTION TIME",
    value: "1.4m",
    change: "-0.3m",
    changeDir: "down" as const,
    icon: Clock,
    iconBg: "bg-info/10",
    iconColor: "text-info",
  },
  {
    label: "AGENT ACCURACY",
    value: "99.1%",
    change: "Stable",
    changeDir: "stable" as const,
    icon: Target,
    iconBg: "bg-success/10",
    iconColor: "text-success",
  },
]

const revenueBars = [
  { label: "OCT 01", saved: 72, cost: 48 },
  { label: "", saved: 65, cost: 42 },
  { label: "", saved: 80, cost: 52 },
  { label: "", saved: 58, cost: 38 },
  { label: "OCT 15", saved: 88, cost: 55 },
  { label: "", saved: 75, cost: 45 },
  { label: "", saved: 92, cost: 58 },
  { label: "", saved: 68, cost: 40 },
  { label: "OCT 30", saved: 95, cost: 60 },
  { label: "", saved: 82, cost: 50 },
  { label: "", saved: 90, cost: 56 },
  { label: "", saved: 98, cost: 62 },
]

const riskDistribution = [
  {
    region: "North America - East",
    volume: "452,801",
    threat: "OPTIMAL",
    threatClass: "badge-success",
    flagRatio: 12,
    flagColor: "bg-success",
    action: "View Logs",
  },
  {
    region: "APAC - Singapore",
    volume: "212,890",
    threat: "CRITICAL",
    threatClass: "badge-danger",
    flagRatio: 78,
    flagColor: "bg-danger",
    action: "Audit Now",
  },
  {
    region: "EMEA - Frankfurt",
    volume: "98,401",
    threat: "WARNING",
    threatClass: "badge-warning",
    flagRatio: 45,
    flagColor: "bg-warning",
    action: "View Logs",
  },
]

const donutLegend = [
  { label: "Auto-Approved", value: "12,450", color: "#6366F1" },
  { label: "Human Intervention", value: "2,140", color: "#F59E0B" },
  { label: "Auto-Rejected", value: "452", color: "#EF4444" },
]

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<string>("30D")

  return (
    <Shell
      title="Performance Intelligence"
      subtitle="Real-time monitoring of AI operational efficiency and financial impact."
      actions={
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-surface rounded-card p-1 border border-border">
            {timeRanges.map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={
                  timeRange === range
                    ? "px-3 py-1.5 rounded-button text-xs font-medium bg-primary/15 text-primary transition-colors"
                    : "px-3 py-1.5 rounded-button text-xs font-medium text-text-muted hover:text-text-secondary transition-colors"
                }
              >
                {range}
              </button>
            ))}
          </div>
          <button className="btn-ghost">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      }
    >
      <div className="grid grid-cols-4 gap-4 mb-6">
        {metricCards.map((m) => {
          const Icon = m.icon
          return (
            <div key={m.label} className="card">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-9 h-9 rounded-button ${m.iconBg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${m.iconColor}`} />
                </div>
                <span className="label-caps">{m.label}</span>
              </div>
              <div className="font-display text-data-lg text-text-primary">{m.value}</div>
              <div className="mt-1">
                {m.changeDir === "up" && (
                  <span className="inline-flex items-center gap-1 text-body-sm text-success font-medium">
                    <TrendingUp className="w-3 h-3" />{m.change}
                  </span>
                )}
                {m.changeDir === "down" && (
                  <span className="inline-flex items-center gap-1 text-body-sm text-success font-medium">
                    <TrendingUp className="w-3 h-3 rotate-180" />{m.change}
                  </span>
                )}
                {m.changeDir === "stable" && (
                  <span className="badge-muted">{m.change}</span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="label-caps">Revenue Trends</h3>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm bg-primary/60" />
              <span className="text-body-sm text-text-muted">Revenue Saved</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm bg-primary/20" />
              <span className="text-body-sm text-text-muted">Operational Cost</span>
            </div>
          </div>
        </div>
        <div className="flex items-end gap-2 h-48">
          {revenueBars.map((bar, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-1">
              <div className="w-full flex gap-0.5 items-end" style={{ height: "160px" }}>
                <div
                  className="flex-1 rounded-t bg-primary/50 transition-all duration-500 hover:bg-primary/60"
                  style={{ height: `${bar.saved}%` }}
                />
                <div
                  className="flex-1 rounded-t bg-primary/15 transition-all duration-500 hover:bg-primary/25"
                  style={{ height: `${bar.cost}%` }}
                />
              </div>
              {bar.label && (
                <span className="text-[10px] text-text-muted mt-1 font-mono">{bar.label}</span>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="card">
          <h3 className="label-caps mb-6">Decision Distribution</h3>
          <div className="flex items-center gap-8">
            <div className="relative w-40 h-40 shrink-0">
              <div
                className="w-full h-full rounded-full"
                style={{
                  background: `conic-gradient(
                    #6366F1 0deg 297.6deg,
                    #F59E0B 297.6deg 350.4deg,
                    #EF4444 350.4deg 360deg
                  )`,
                }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-24 h-24 rounded-full bg-surface flex items-center justify-center">
                  <span className="font-display text-data-md text-text-primary">82%<br /><span className="text-[10px] text-text-muted font-body">AUTONOMOUS</span></span>
                </div>
              </div>
            </div>
            <div className="space-y-3">
              {donutLegend.map((item) => (
                <div key={item.label} className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: item.color }} />
                  <span className="text-body-sm text-text-secondary">{item.label}</span>
                  <span className="font-mono text-data-sm text-text-primary ml-auto">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="label-caps mb-6">Agent Efficiency Spectrum</h3>
          <div className="flex items-center gap-8">
            <svg viewBox="0 0 200 200" className="w-40 h-40 shrink-0">
              <polygon
                points="100,10 190,75 155,170 45,170 10,75"
                fill="none"
                stroke="rgba(99,102,241,0.2)"
                strokeWidth="1"
              />
              <polygon
                points="100,30 170,80 148,158 52,158 30,80"
                fill="none"
                stroke="rgba(99,102,241,0.15)"
                strokeWidth="1"
              />
              <polygon
                points="100,50 150,85 140,145 60,145 50,85"
                fill="none"
                stroke="rgba(99,102,241,0.1)"
                strokeWidth="1"
              />
              <polygon
                points="100,18 182,78 152,167 48,167 18,78"
                fill="rgba(99,102,241,0.15)"
                stroke="#6366F1"
                strokeWidth="1.5"
              />
              <circle cx="100" cy="18" r="3" fill="#6366F1" />
              <circle cx="182" cy="78" r="3" fill="#6366F1" />
              <circle cx="152" cy="167" r="3" fill="#6366F1" />
              <circle cx="48" cy="167" r="3" fill="#6366F1" />
              <circle cx="18" cy="78" r="3" fill="#6366F1" />
              <text x="100" y="6" textAnchor="middle" className="fill-text-muted text-[9px] font-body">SPEED</text>
              <text x="196" y="78" textAnchor="start" className="fill-text-muted text-[9px] font-body">ACCURACY</text>
              <text x="162" y="180" textAnchor="middle" className="fill-text-muted text-[9px] font-body">LATENCY</text>
              <text x="38" y="180" textAnchor="middle" className="fill-text-muted text-[9px] font-body">REASONING</text>
              <text x="4" y="78" textAnchor="end" className="fill-text-muted text-[9px] font-body">CONTEXT</text>
            </svg>
            <div className="space-y-3">
              <div>
                <div className="label-caps text-[10px] mb-1">LATENCY</div>
                <div className="font-mono text-data-sm text-text-primary">124ms</div>
              </div>
              <div>
                <div className="label-caps text-[10px] mb-1">CONTEXT</div>
                <div className="font-mono text-data-sm text-text-primary">128k Token</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="label-caps mb-4">Risk Distribution</h3>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>REGION / MARKET</th>
                <th>VOLUME</th>
                <th>THREAT LEVEL</th>
                <th>FLAG RATIO</th>
                <th>ACTION TAKEN</th>
              </tr>
            </thead>
            <tbody>
              {riskDistribution.map((row, i) => (
                <tr key={i}>
                  <td className="text-body-md text-text-primary font-medium">{row.region}</td>
                  <td className="font-mono text-data-sm text-text-secondary">{row.volume}</td>
                  <td><span className={row.threatClass}>{row.threat}</span></td>
                  <td>
                    <div className="w-24 h-1.5 rounded-full bg-surface-3 overflow-hidden">
                      <div className={`h-full rounded-full ${row.flagColor}`} style={{ width: `${row.flagRatio}%` }} />
                    </div>
                  </td>
                  <td>
                    <button className="text-body-sm text-primary hover:text-primary-hover transition-colors">
                      {row.action}
                    </button>
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
