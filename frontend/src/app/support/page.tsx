"use client"

import { useState } from "react"
import {
  HeadphonesIcon,
  MessageSquare,
  Clock,
  Bot,
  User,
  Smile,
  Frown,
  Meh,
  Send,
  Star,
  Loader2,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { MetricCard } from "@/components/shared/MetricCard"
import { MetricCardSkeleton } from "@/components/shared/Skeleton"
import { useSupportTickets, useSupportAnalytics } from "@/lib/hooks"
import { cn, formatTimestamp } from "@/lib/utils"
import type { SupportTicket } from "@/lib/api"

const fallbackTickets: SupportTicket[] = [
  { id: "T-1234", customer_email: "angry.customer@example.com", customer_name: "Angry Customer", subject: "Order never arrived!", body: "I placed an order 2 weeks ago and still haven't received it!", status: "open", priority: "urgent", category: "order_issue", channel: "email", order_id: null, created_at: new Date(Date.now() - 1800000).toISOString(), messages: [{ id: "m1", sender_type: "customer", content: "I placed an order 2 weeks ago and still haven't received it!", created_at: new Date(Date.now() - 1800000).toISOString() }, { id: "m2", sender_type: "agent", content: "I understand your frustration. Let me look into your order immediately.", created_at: new Date(Date.now() - 1700000).toISOString() }] },
  { id: "T-1233", customer_email: "curious.shopper@example.com", customer_name: "Curious Shopper", subject: "Product compatibility question", body: "Is the Smart Watch compatible with Android phones?", status: "resolved", priority: "low", category: "product_question", channel: "email", order_id: null, created_at: new Date(Date.now() - 7200000).toISOString(), messages: [] },
  { id: "T-1232", customer_email: "happy.customer@example.com", customer_name: "Happy Customer", subject: "Love the product!", body: "Just wanted to say the Wireless Headphones are amazing!", status: "closed", priority: "low", category: "feedback", channel: "email", order_id: null, created_at: new Date(Date.now() - 86400000).toISOString(), messages: [] },
  { id: "T-1231", customer_email: "billing.issue@example.com", customer_name: "Billing Issue", subject: "Wrong amount charged", body: "I was charged $149.99 but my order total was $129.99.", status: "in_progress", priority: "high", category: "billing", channel: "email", order_id: null, created_at: new Date(Date.now() - 3600000).toISOString(), messages: [] },
]

const sentimentIcons: Record<string, { icon: any; color: string }> = {
  positive: { icon: Smile, color: "text-emerald" },
  neutral: { icon: Meh, color: "text-text-3" },
  negative: { icon: Frown, color: "text-red" },
}

const priorityColors: Record<string, string> = {
  low: "bg-surface-3",
  medium: "bg-amber/10 text-amber",
  high: "bg-red/10 text-red",
  urgent: "bg-red text-white",
}

export default function SupportPage() {
  const [selectedId, setSelectedId] = useState<string | null>("T-1234")
  const ticketsQuery = useSupportTickets({ limit: 20 })
  const analyticsQuery = useSupportAnalytics(7)
  const analytics = analyticsQuery.data

  const tickets = ticketsQuery.data?.tickets?.length ? ticketsQuery.data.tickets : fallbackTickets
  const selected = tickets.find((t) => t.id === selectedId) || tickets[0]

  return (
    <Shell>
      <Topbar title="Support" subtitle="AI-powered customer support" />

      <div className="p-6 space-y-6">
        {/* Metrics */}
        {analyticsQuery.isLoading ? (
          <div className="grid grid-cols-4 gap-4">
            <MetricCardSkeleton /><MetricCardSkeleton /><MetricCardSkeleton /><MetricCardSkeleton />
          </div>
        ) : (
          <div className="grid grid-cols-4 gap-4">
            <MetricCard
              label="Open Tickets"
              value={analytics?.open_tickets ?? 12}
              icon={<MessageSquare className="w-4 h-4 text-indigo" />}
              color="bg-indigo/10"
            />
            <MetricCard
              label="Satisfaction"
              value={analytics?.satisfaction_score?.toFixed(1) ?? "4.2"}
              icon={<Star className="w-4 h-4 text-amber" />}
              color="bg-amber/10"
            />
            <MetricCard
              label="Avg Response"
              value={`${(analytics?.avg_response_time_hours?.toFixed(1) ?? "2.8")}h`}
              icon={<Clock className="w-4 h-4 text-cyan" />}
              color="bg-cyan/10"
            />
            <MetricCard
              label="Resolution Rate"
              value={`${((analytics?.first_contact_resolution_rate ?? 0.72) * 100).toFixed(0)}%`}
              icon={<Bot className="w-4 h-4 text-emerald" />}
              color="bg-emerald/10"
            />
          </div>
        )}

        <div className="grid grid-cols-3 gap-6">
          {/* Ticket list */}
          <div className="col-span-1 space-y-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="section-label">Tickets</h3>
              <span className="text-xs text-text-3">{tickets.length} total</span>
            </div>
            {tickets.map((ticket) => (
              <button
                key={ticket.id}
                onClick={() => setSelectedId(ticket.id)}
                className={cn(
                  "card w-full text-left transition-all duration-150 p-3",
                  selected?.id === ticket.id && "border-indigo card-glow",
                )}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-data-xs text-indigo">{ticket.id}</span>
                  <StatusBadge status={ticket.status} />
                </div>
                <div className="text-sm text-text-1 font-medium line-clamp-1 mb-1">{ticket.subject}</div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-text-3">{ticket.customer_name}</span>
                  <span className={cn("text-[10px] px-1.5 py-0.5 rounded", priorityColors[ticket.priority] || "bg-surface-3")}>
                    {ticket.priority}
                  </span>
                </div>
              </button>
            ))}
          </div>

          {/* Ticket detail */}
          <div className="col-span-2 space-y-4">
            {selected && (
              <>
                <div className="card">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="font-mono text-data-sm text-indigo">{selected.id}</span>
                    <StatusBadge status={selected.status} size="md" />
                    <span className={cn("text-[10px] px-2 py-0.5 rounded", priorityColors[selected.priority] || "bg-surface-3")}>
                      {selected.priority.toUpperCase()}
                    </span>
                  </div>
                  <h2 className="font-display font-semibold text-lg text-text-1 mb-2">{selected.subject}</h2>
                  <div className="flex items-center gap-4 text-sm text-text-2">
                    <span>{selected.customer_name}</span>
                    <span className="text-text-3">•</span>
                    <span>{selected.customer_email}</span>
                    <span className="text-text-3">•</span>
                    <span className="capitalize">{selected.category.replace(/_/g, " ")}</span>
                  </div>
                </div>

                <div className="card space-y-4">
                  <h3 className="section-label">Conversation</h3>
                  {selected.messages.length > 0 ? selected.messages.map((msg) => (
                    <div key={msg.id} className="flex gap-3">
                      <div className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                        msg.sender_type === "customer" ? "bg-surface-3" : "bg-indigo/20",
                      )}>
                        {msg.sender_type === "customer" ? (
                          <User className="w-4 h-4 text-text-2" />
                        ) : (
                          <Bot className="w-4 h-4 text-indigo" />
                        )}
                      </div>
                      <div className={cn(
                        "flex-1 p-3 rounded-lg",
                        msg.sender_type === "customer" ? "bg-surface-2" : "bg-indigo/5 border border-indigo/20",
                      )}>
                        <p className="text-sm text-text-1">{msg.content}</p>
                      </div>
                    </div>
                  )) : (
                    <div className="flex gap-3">
                      <div className="w-8 h-8 rounded-full bg-surface-3 flex items-center justify-center shrink-0">
                        <User className="w-4 h-4 text-text-2" />
                      </div>
                      <div className="flex-1 p-3 rounded-lg bg-surface-2">
                        <p className="text-sm text-text-1">{selected.body}</p>
                      </div>
                    </div>
                  )}
                </div>

                <div className="card">
                  <h3 className="section-label mb-3">Reply</h3>
                  <textarea
                    placeholder="Type your reply..."
                    className="w-full h-24 p-3 rounded-lg bg-surface-2 border border-border text-sm text-text-1 placeholder:text-text-3 focus:outline-none focus:border-border-bright resize-none"
                  />
                  <div className="flex items-center justify-end gap-2 mt-3">
                    <button className="btn-ghost text-xs">
                      <Bot className="w-3.5 h-3.5" /> AI Suggest
                    </button>
                    <button className="btn-primary text-xs">
                      <Send className="w-3.5 h-3.5" /> Send
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
