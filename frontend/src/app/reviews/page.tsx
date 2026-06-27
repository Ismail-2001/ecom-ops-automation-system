"use client"

import { useState } from "react"
import {
  Star,
  Search,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  CheckCircle,
  MessageSquare,
  TrendingUp,
  Filter,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { ConfidencePill } from "@/components/shared/ConfidencePill"
import { cn, formatTimestamp } from "@/lib/utils"

const reviewStats = {
  totalReviews: 2847,
  averageRating: 4.6,
  pendingModeration: 12,
  autoApproved: 2654,
  flagged: 23,
}

const mockReviews = [
  { id: "R-1001", customer: "Sarah C.", product: "Wireless Headphones", rating: 5, text: "Absolutely love these headphones! The noise cancellation is incredible and the battery lasts all day.", sentiment: "positive", confidence: 0.96, status: "approved", timestamp: new Date(Date.now() - 300000).toISOString() },
  { id: "R-1002", customer: "Mike R.", product: "Ergonomic Mouse", rating: 4, text: "Great mouse, very comfortable for long work sessions. Only downside is the scroll wheel could be smoother.", sentiment: "positive", confidence: 0.89, status: "approved", timestamp: new Date(Date.now() - 600000).toISOString() },
  { id: "R-1003", customer: "Emily W.", product: "USB-C Hub", rating: 1, text: "STOP BUYING THIS GARBAGE!!! THIS IS A SCAM!!! Click here for amazing deals: bit.ly/scam-link", sentiment: "spam", confidence: 0.94, status: "flagged", timestamp: new Date(Date.now() - 900000).toISOString() },
  { id: "R-1004", customer: "David L.", product: "Laptop Stand", rating: 5, text: "Perfect for my home office setup. Solid build quality and the angle is just right.", sentiment: "positive", confidence: 0.93, status: "approved", timestamp: new Date(Date.now() - 1200000).toISOString() },
  { id: "R-1005", customer: "Anna K.", product: "Mechanical Keyboard", rating: 3, text: "Decent keyboard for the price. Keys feel a bit mushy compared to Cherry MX switches. RGB is nice though.", sentiment: "neutral", confidence: 0.81, status: "approved", timestamp: new Date(Date.now() - 1500000).toISOString() },
  { id: "R-1006", customer: "James T.", product: "Webcam 4K", rating: 2, text: "The webcam works fine but the software is terrible. Crashes constantly on Windows 11.", sentiment: "negative", confidence: 0.87, status: "pending", timestamp: new Date(Date.now() - 1800000).toISOString() },
  { id: "R-1007", customer: "Lisa M.", product: "Portable Charger", rating: 5, text: "Best portable charger I've ever owned. Charges my phone 4 times and still has juice left!", sentiment: "positive", confidence: 0.97, status: "approved", timestamp: new Date(Date.now() - 2100000).toISOString() },
  { id: "R-1008", customer: "Bob H.", product: "Smart Desk Lamp", rating: 4, text: "Love the smart features and app control. Wish it was a bit brighter at max setting.", sentiment: "positive", confidence: 0.88, status: "pending", timestamp: new Date(Date.now() - 2400000).toISOString() },
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

  const filteredReviews = mockReviews.filter(r => {
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
            <div className="metric-value text-display-md text-text-1">{reviewStats.totalReviews.toLocaleString()}</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Avg Rating</div>
            <div className="metric-value text-display-md text-amber flex items-center gap-2">
              {reviewStats.averageRating}
              <Star className="w-5 h-5 text-amber fill-amber" />
            </div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Auto-Approved</div>
            <div className="metric-value text-display-md text-emerald">{reviewStats.autoApproved.toLocaleString()}</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Pending</div>
            <div className="metric-value text-display-md text-amber">{reviewStats.pendingModeration}</div>
          </div>
          <div className="card">
            <div className="section-label mb-2">Flagged</div>
            <div className="metric-value text-display-md text-red">{reviewStats.flagged}</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Reviews list */}
          <div className="col-span-2 space-y-4">
            {/* Filters */}
            <div className="flex items-center gap-2">
              {["all", "pending", "flagged", "negative"].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={cn(
                    "px-3 py-2 rounded-lg text-xs font-medium transition-colors",
                    filter === f ? "bg-indigo/10 text-indigo" : "bg-surface-2 text-text-2 hover:bg-surface-3"
                  )}
                >
                  {f === "all" ? "All Reviews" : f === "pending" ? "Pending" : f === "flagged" ? "Flagged" : "Negative"}
                </button>
              ))}
            </div>

            {/* Reviews */}
            <div className="space-y-3">
              {filteredReviews.map((review) => (
                <div key={review.id} className="card">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-surface-3 flex items-center justify-center">
                        <span className="text-xs font-medium text-text-2">{review.customer.split(" ").map(n => n[0]).join("")}</span>
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
                        review.sentiment === "positive" ? "bg-emerald" : review.sentiment === "negative" ? "bg-red" : review.sentiment === "spam" ? "bg-red" : "bg-amber"
                      )} />
                      <span className="text-xs text-text-3 capitalize">{review.sentiment}</span>
                    </div>
                    {review.status === "pending" && (
                      <div className="flex items-center gap-2 ml-auto">
                        <button className="flex items-center gap-1 px-2 py-1 rounded bg-emerald/10 text-emerald text-xs hover:bg-emerald/20 transition-colors">
                          <ThumbsUp className="w-3 h-3" />
                          Approve
                        </button>
                        <button className="flex items-center gap-1 px-2 py-1 rounded bg-red/10 text-red text-xs hover:bg-red/20 transition-colors">
                          <ThumbsDown className="w-3 h-3" />
                          Reject
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
            {/* Rating distribution */}
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

            {/* Sentiment breakdown */}
            <div className="card">
              <h3 className="font-display font-semibold text-text-1 mb-4">Sentiment Analysis</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-emerald" />
                    <span className="text-sm text-text-2">Positive</span>
                  </div>
                  <span className="text-sm font-medium text-emerald">78%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-amber" />
                    <span className="text-sm text-text-2">Neutral</span>
                  </div>
                  <span className="text-sm font-medium text-amber">15%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red" />
                    <span className="text-sm text-text-2">Negative</span>
                  </div>
                  <span className="text-sm font-medium text-red">5%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-violet" />
                    <span className="text-sm text-text-2">Spam</span>
                  </div>
                  <span className="text-sm font-medium text-violet">2%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  )
}
