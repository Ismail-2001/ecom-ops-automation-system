"use client"

import { useState } from "react"
import {
  Search,
  ChevronLeft,
  ChevronRight,
  Eye,
  MessageSquare,
  AlertTriangle,
  Star,
  TrendingUp,
  Clock,
  ThumbsUp,
} from "lucide-react"
import Shell from "@/components/layout/Shell"
import { cn } from "@/lib/utils"

const reviews = [
  {
    id: 1,
    product: "Wireless Pro Headphones",
    customer: "Emma Rodriguez",
    rating: 5,
    sentiment: "POSITIVE",
    sentimentClass: "badge-success",
    reviewText: '"Amazing sound quality and the noise cancellation is top-notch. Worth every penny!"',
    status: "RESPONDED",
    statusClass: "badge-success",
    action: "View",
    actionIcon: Eye,
  },
  {
    id: 2,
    product: "Organic Face Serum",
    customer: "Marcus Williams",
    rating: 1,
    sentiment: "NEGATIVE",
    sentimentClass: "badge-danger",
    reviewText: '"Caused skin irritation after two days of use. Very disappointed with this product."',
    status: "PENDING",
    statusClass: "badge-warning",
    action: "Respond",
    actionIcon: MessageSquare,
  },
  {
    id: 3,
    product: "Smart Fitness Tracker",
    customer: "Sarah Chen",
    rating: 4,
    sentiment: "POSITIVE",
    sentimentClass: "badge-success",
    reviewText: '"Good tracker but the app sync could be faster. Overall happy with the purchase."',
    status: "RESPONDED",
    statusClass: "badge-success",
    action: "View",
    actionIcon: Eye,
  },
  {
    id: 4,
    product: "Minimalist Desk Lamp",
    customer: "James O\'Connor",
    rating: 3,
    sentiment: "NEUTRAL",
    sentimentClass: "badge-info",
    reviewText: '"Decent lamp, takes a while to get used to the touch controls. Build quality is fine."',
    status: "PENDING",
    statusClass: "badge-warning",
    action: "Respond",
    actionIcon: MessageSquare,
  },
  {
    id: 5,
    product: "Premium Yoga Mat",
    customer: "Yuki Tanaka",
    rating: 5,
    sentiment: "POSITIVE",
    sentimentClass: "badge-success",
    reviewText: '"Perfect thickness and grip. No more knee pain during yoga sessions. Highly recommend!"',
    status: "RESPONDED",
    statusClass: "badge-success",
    action: "View",
    actionIcon: Eye,
  },
  {
    id: 6,
    product: "Bluetooth Speaker",
    customer: "Aisha Patel",
    rating: 2,
    sentiment: "NEGATIVE",
    sentimentClass: "badge-danger",
    reviewText: '"Speaker stopped working after a week. Terrible quality control. Want a refund."',
    status: "FLAGGED",
    statusClass: "badge-danger",
    action: "Escalate",
    actionIcon: AlertTriangle,
  },
]

const filters = ["All Reviews", "Pending", "Responded", "Flagged"]

const metricCards = [
  { label: "Total Reviews", value: "12,458", icon: Star, color: "bg-primary/15", iconColor: "text-primary" },
  { label: "Average Rating", value: "4.2", suffix: "/5", icon: Star, color: "bg-warning/15", iconColor: "text-warning" },
  { label: "Sentiment Score", value: "78%", suffix: " positive", icon: TrendingUp, color: "bg-success/15", iconColor: "text-success" },
  { label: "Pending Response", value: "23", icon: Clock, color: "bg-warning/15", iconColor: "text-warning" },
]

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((s) => (
        <Star
          key={s}
          className={cn(
            "w-3.5 h-3.5",
            s <= rating ? "text-warning fill-warning" : "text-surface-3"
          )}
        />
      ))}
    </div>
  )
}

export default function ReviewsPage() {
  const [activeFilter, setActiveFilter] = useState("All Reviews")
  const [searchQuery, setSearchQuery] = useState("")

  const filtered = reviews.filter((review) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      if (
        !review.product.toLowerCase().includes(q) &&
        !review.customer.toLowerCase().includes(q)
      )
        return false
    }
    if (activeFilter === "Pending") return review.status === "PENDING"
    if (activeFilter === "Responded") return review.status === "RESPONDED"
    if (activeFilter === "Flagged") return review.status === "FLAGGED"
    return true
  })

  return (
    <Shell
      title="Review Intelligence"
      subtitle="AI-powered review monitoring, sentiment analysis, and automated response orchestration."
    >
      <div className="space-y-6">
        <div className="grid grid-cols-4 gap-4">
          {metricCards.map((card) => {
            const Icon = card.icon
            return (
              <div key={card.label} className="card group hover:border-border-bright transition-all duration-150">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="label-caps mb-2">{card.label}</div>
                    <div className="font-display text-display-md text-text-primary">
                      {card.value}
                      {card.suffix && (
                        <span className="text-text-muted text-body-md font-normal">{card.suffix}</span>
                      )}
                    </div>
                  </div>
                  <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center", card.color)}>
                    <Icon className={cn("w-4 h-4", card.iconColor)} />
                  </div>
                </div>
              </div>
            )
          })}
        </div>

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
              placeholder="Search reviews..."
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
                  <th className="label-caps px-5 py-4 text-left">Product</th>
                  <th className="label-caps px-5 py-4 text-left">Customer</th>
                  <th className="label-caps px-5 py-4 text-center">Rating</th>
                  <th className="label-caps px-5 py-4 text-center">Sentiment</th>
                  <th className="label-caps px-5 py-4 text-left">Review Text</th>
                  <th className="label-caps px-5 py-4 text-center">Status</th>
                  <th className="label-caps px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((review) => {
                  const ActionIcon = review.actionIcon
                  return (
                    <tr key={review.id} className="group transition-colors">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-surface-2 flex items-center justify-center">
                            <Star className="w-4 h-4 text-text-muted" />
                          </div>
                          <span className="text-sm font-medium text-text-primary">{review.product}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-sm text-text-secondary">{review.customer}</span>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <StarRating rating={review.rating} />
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className={cn("badge", review.sentimentClass)}>{review.sentiment}</span>
                      </td>
                      <td className="px-5 py-4 max-w-[280px]">
                        <span className="text-sm text-text-secondary line-clamp-2">{review.reviewText}</span>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className={cn("badge", review.statusClass)}>{review.status}</span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <button
                          className={cn(
                            "btn-ghost text-xs gap-1.5",
                            review.action === "Escalate"
                              ? "text-danger hover:bg-danger/10 hover:text-danger"
                              : review.action === "Respond"
                                ? "text-primary hover:bg-primary/10 hover:text-primary"
                                : "text-text-secondary"
                          )}
                        >
                          <ActionIcon className="w-3.5 h-3.5" />
                          {review.action}
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
              <div className="dot-green" />
              <span className="text-sm text-text-secondary">
                Positive: <span className="font-mono text-data-sm text-success">78%</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="dot-amber" />
              <span className="text-sm text-text-secondary">
                Neutral: <span className="font-mono text-data-sm text-warning">15%</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="dot-red" />
              <span className="text-sm text-text-secondary">
                Negative: <span className="font-mono text-data-sm text-danger">7%</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-sm text-text-muted">
              Showing <span className="text-text-secondary font-medium">6</span> of <span className="text-text-secondary font-medium">12,458</span> reviews
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
                2077
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
