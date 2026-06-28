"use client"

import { useState } from "react"
import {
  Star,
  ThumbsUp,
  ThumbsDown,
  Bot,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { ConfidencePill } from "@/components/shared/ConfidencePill"
import { cn, formatTimestamp } from "@/lib/utils"

const reviews = [
  { id: "R-1001", customer: "Sarah C.", product: "Wireless Headphones", rating: 5, text: "Absolutely love these headphones! The noise cancellation is incredible.", sentiment: "positive", confidence: 0.96, status: "approved", agent: "review_moderation", timestamp: new Date(Date.now() - 300000).toISOString() },
  { id: "R-1002", customer: "Mike R.", product: "Ergonomic Mouse", rating: 4, text: "Great mouse, very comfortable for long work sessions.", sentiment: "positive", confidence: 0.89, status: "approved", agent: "review_moderation", timestamp: new Date(Date.now() - 600000).toISOString() },
  { id: "R-1003", customer: "Spam Bot", product: "USB-C Hub", rating: 1, text: "STOP BUYING THIS GARBAGE!!! Click here for amazing deals: bit.ly/scam", sentiment: "spam", confidence: 0.94, status: "flagged", agent: "review_moderation", timestamp: new Date(Date.now() - 900000).toISOString() },
  { id: "R-1004", customer: "David L.", product: "Laptop Stand", rating: 5, text: "Perfect for my home office setup. Solid build quality.", sentiment: "positive", confidence: 0.93, status: "approved", agent: "review_moderation", timestamp: new Date(Date.now() - 1200000).toISOString() },
  { id: "R-1005", customer: "Anna K.", product: "Mechanical Keyboard", rating: 3, text: "Decent keyboard for the price. Keys feel a bit mushy.", sentiment: "neutral", confidence: 0.81, status: "approved", agent: "review_moderation", timestamp: new Date(Date.now() - 1500000).toISOString() },
  { id: "R-1006", customer: "James T.", product: "Webcam 4K", rating: 2, text: "The webcam works fine but the software crashes on Windows 11.", sentiment: "negative", confidence: 0.87, status: "pending", agent: "review_moderation", timestamp: new Date(Date.now() - 1800000).toISOString() },
]

const ratingDistribution = [
  { stars: 5, count: 1823, percentage: 64 },
  { stars: 4, count: 570, percentage: 20 },
  { stars: 3, count: 256, percentage: 9 },
  { stars: 2, count: 114, percentage: 4 },
  { stars: 1, count: 84, percentage: 3 },
]

export default function ReviewsPage() {
  const [filter, setFilter] = useState("all")

  const filtered = reviews.filter((r) => {
    if (filter === "pending") return r.status === "pending"
    if (filter === "flagged") return r.status === "flagged"
    if (filter === "negative") return r.sentiment === "negative" || r.sentiment === "spam"
    return true
  })

  return (
    <Shell>
      <Topbar title="Reviews" subtitle="AI-powered sentiment analysis and moderation" />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-5 gap-4">
          <div className="card">
            <div className="section-label mb-2">Total Reviews</div>
            <div className="metric-value text-display-md text-text-1">2,847</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Avg Rating</div>
            <div className="metric-value text-display-md text-amber flex items-center gap-2">
              4.6 <Star className="w-5 h-5 text-amber fill-amber" />
            </div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Auto-Approved</div>
            <div className="metric-value text-display-md text-emerald">2,654</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Pending</div>
            <div className="metric-value text-display-md text-amber">12</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Flagged</div>
            <div className="metric-value text-display-md text-red">23</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Reviews list */}
          <div className="col-span-2 space-y-4">
            <div className="flex items-center gap-2">
              {["all", "pending", "flagged", "negative"].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={cn(
                    "px-3 py-2 rounded-lg text-xs font-medium transition-colors",
                    filter === f ? "bg-indigo/10 text-indigo" : "bg-surface-2 text-text-2 hover:bg-surface-3",
                  )}
                >
                  {f === "all" ? "All Reviews" : f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>

            <div className="space-y-3">
              {filtered.map((review) => (
                <div key={review.id} className="card">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-surface-3 flex items-center justify-center">
                        <span className="text-xs font-medium text-text-2">{review.customer.split(" ").map((n) => n[0]).join("")}</span>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-text-1">{review.customer}</span>
                          <span className="text-xs text-text-3">on</span>
                          <span className="text-xs text-indigo">{review.product}</span>
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          {[1, 2, 3, 4, 5].map((s) => (
                            <Star key={s} className={cn("w-3 h-3", s <= review.rating ? "text-amber fill-amber" : "text-surface-3")} />
                          ))}
                          <span className="text-xs text-text-3">{formatTimestamp(review.timestamp)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <ConfidencePill value={review.confidence} />
                      <StatusBadge status={review.status} />
                    </div>
                  </div>
                  <p className="text-sm text-text-2 leading-relaxed">{review.text}</p>
                  <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border/50">
                    <div className="flex items-center gap-1.5">
                      <div className={cn(
                        "w-2 h-2 rounded-full",
                        review.sentiment === "positive" ? "bg-emerald" : review.sentiment === "negative" || review.sentiment === "spam" ? "bg-red" : "bg-amber",
                      )} />
                      <span className="text-xs text-text-3 capitalize">{review.sentiment}</span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-text-4">
                      <Bot className="w-3 h-3" /> review_moderation
                    </div>
                    {review.status === "pending" && (
                      <div className="flex items-center gap-2 ml-auto">
                        <button className="flex items-center gap-1 px-2 py-1 rounded bg-emerald/10 text-emerald text-xs hover:bg-emerald/20 transition-colors">
                          <ThumbsUp className="w-3 h-3" /> Approve
                        </button>
                        <button className="flex items-center gap-1 px-2 py-1 rounded bg-red/10 text-red text-xs hover:bg-red/20 transition-colors">
                          <ThumbsDown className="w-3 h-3" /> Reject
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <div className="card">
              <h3 className="font-display font-semibold text-text-1 mb-4">Rating Distribution</h3>
              <div className="space-y-2">
                {ratingDistribution.map((r) => (
                  <div key={r.stars} className="flex items-center gap-3">
                    <div className="flex items-center gap-1 w-12">
                      <span className="text-xs text-text-2">{r.stars}</span>
                      <Star className="w-3 h-3 text-amber fill-amber" />
                    </div>
                    <div className="flex-1 h-2 bg-surface-3 rounded-full overflow-hidden">
                      <div className="h-full bg-amber rounded-full" style={{ width: `${r.percentage}%` }} />
                    </div>
                    <span className="text-xs text-text-3 w-8 text-right">{r.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h3 className="font-display font-semibold text-text-1 mb-4">Sentiment Analysis</h3>
              <div className="space-y-3">
                {[
                  { label: "Positive", pct: 78, color: "emerald" },
                  { label: "Neutral", pct: 15, color: "amber" },
                  { label: "Negative", pct: 5, color: "red" },
                  { label: "Spam", pct: 2, color: "violet" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full bg-${item.color}`} />
                      <span className="text-sm text-text-2">{item.label}</span>
                    </div>
                    <span className={`text-sm font-medium text-${item.color}`}>{item.pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  )
}
