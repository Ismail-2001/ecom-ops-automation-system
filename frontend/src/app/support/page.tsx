"use client"

import { useState } from "react"
import {
  HeadphonesIcon,
  MessageSquare,
  AlertTriangle,
  Clock,
  CheckCircle,
  Send,
  Bot,
  User,
  Smile,
  Frown,
  Meh,
  ArrowUpRight,
  Star,
  TrendingUp,
} from "lucide-react"
import { Shell } from "@/components/layout/Shell"
import { Topbar } from "@/components/layout/Topbar"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { MetricCard } from "@/components/shared/MetricCard"
import { cn, formatTimestamp } from "@/lib/utils"

interface Ticket {
  id: string
  customerEmail: string
  customerName: string
  subject: string
  message: string
  status: "open" | "in_progress" | "resolved" | "closed"
  priority: "low" | "medium" | "high" | "urgent"
  sentiment: "positive" | "neutral" | "negative"
  category: string
  aiResponse?: string
  createdAt: string
}

const mockTickets: Ticket[] = [
  {
    id: "T-1234",
    customerEmail: "angry.customer@example.com",
    customerName: "Angry Customer",
    subject: "Order never arrived!",
    message: "I placed an order 2 weeks ago and still haven't received it! This is unacceptable. I want a refund immediately.",
    status: "open",
    priority: "urgent",
    sentiment: "negative",
    category: "order_issue",
    aiResponse: "I understand your frustration, and I sincerely apologize for the delay. Let me look into your order immediately. I can see your order #ORD-8847 was shipped on Dec 15th via USPS. There appears to be a tracking issue. I've escalated this to our shipping team and will ensure you receive either the package or a full refund within 24 hours.",
    createdAt: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: "T-1233",
    customerEmail: "curious.shopper@example.com",
    customerName: "Curious Shopper",
    subject: "Product compatibility question",
    message: "Is the Smart Watch compatible with Android phones? I couldn't find this information on the product page.",
    status: "resolved",
    priority: "low",
    sentiment: "neutral",
    category: "product_question",
    aiResponse: "Great question! Yes, our Smart Watch is fully compatible with Android phones (Android 8.0+). You can download the companion app from the Google Play Store. It supports all features including notifications, health tracking, and custom watch faces.",
    createdAt: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: "T-1232",
    customerEmail: "happy.customer@example.com",
    customerName: "Happy Customer",
    subject: "Love the product!",
    message: "Just wanted to say the Wireless Headphones are amazing! Best purchase I've made this year. The noise cancellation is incredible.",
    status: "closed",
    priority: "low",
    sentiment: "positive",
    category: "feedback",
    createdAt: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: "T-1231",
    customerEmail: "billing.issue@example.com",
    customerName: "Billing Issue",
    subject: "Wrong amount charged",
    message: "I was charged $149.99 but my order total was $129.99. Please correct this.",
    status: "in_progress",
    priority: "high",
    sentiment: "negative",
    category: "billing",
    aiResponse: "I've verified your order #ORD-8851 and can confirm there was a billing discrepancy. The correct total is $129.99. I've initiated a refund of $20.00 to your original payment method. You should see the refund within 3-5 business days.",
    createdAt: new Date(Date.now() - 3600000).toISOString(),
  },
]

const sentimentIcons = {
  positive: { icon: Smile, color: "text-emerald" },
  neutral: { icon: Meh, color: "text-text-3" },
  negative: { icon: Frown, color: "text-red" },
}

const priorityColors = {
  low: "bg-surface-3",
  medium: "bg-amber/10 text-amber",
  high: "bg-red/10 text-red",
  urgent: "bg-red text-white",
}

export default function SupportPage() {
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(mockTickets[0])
  const [replyText, setReplyText] = useState("")

  return (
    <Shell>
      <Topbar
        title="Support"
        subtitle="AI-powered customer support"
        actions={
          <button className="btn-primary">
            <HeadphonesIcon className="w-3.5 h-3.5" />
            New Ticket
          </button>
        }
      />

      <div className="p-6 space-y-6">
        {/* Metrics */}
        <div className="grid grid-cols-4 gap-4">
          <MetricCard
            label="Open Tickets"
            value={12}
            delta={-15.2}
            deltaLabel="vs last week"
            icon={<MessageSquare className="w-4 h-4 text-indigo" />}
            color="bg-indigo/10"
          />
          <MetricCard
            label="Auto-Resolved"
            value="72%"
            delta={5.1}
            deltaLabel="vs last week"
            icon={<Bot className="w-4 h-4 text-emerald" />}
            color="bg-emerald/10"
          />
          <MetricCard
            label="Avg Response"
            value="2.8m"
            delta={-12.3}
            deltaLabel="vs last week"
            icon={<Clock className="w-4 h-4 text-cyan" />}
            color="bg-cyan/10"
          />
          <MetricCard
            label="Satisfaction"
            value="4.2"
            delta={0.3}
            deltaLabel="vs last week"
            icon={<Star className="w-4 h-4 text-amber" />}
            color="bg-amber/10"
          />
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Ticket list */}
          <div className="col-span-1 space-y-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="section-label">Tickets</h3>
              <span className="text-xs text-text-3">{mockTickets.length} total</span>
            </div>
            {mockTickets.map((ticket) => {
              const SentimentIcon = sentimentIcons[ticket.sentiment].icon
              const sentimentColor = sentimentIcons[ticket.sentiment].color
              return (
                <button
                  key={ticket.id}
                  onClick={() => setSelectedTicket(ticket)}
                  className={cn(
                    "card w-full text-left transition-all duration-150 p-3",
                    selectedTicket?.id === ticket.id && "border-indigo card-glow"
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-data-xs text-indigo">{ticket.id}</span>
                    <div className="flex items-center gap-2">
                      <SentimentIcon className={cn("w-3.5 h-3.5", sentimentColor)} />
                      <StatusBadge status={ticket.status} />
                    </div>
                  </div>
                  <div className="text-sm text-text-1 font-medium line-clamp-1 mb-1">
                    {ticket.subject}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-3">{ticket.customerName}</span>
                    <span className={cn("text-[10px] px-1.5 py-0.5 rounded", priorityColors[ticket.priority])}>
                      {ticket.priority}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Ticket detail */}
          <div className="col-span-2 space-y-4">
            {selectedTicket && (
              <>
                {/* Ticket header */}
                <div className="card">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-data-sm text-indigo">{selectedTicket.id}</span>
                      <StatusBadge status={selectedTicket.status} size="md" />
                      <span className={cn("text-[10px] px-2 py-0.5 rounded", priorityColors[selectedTicket.priority])}>
                        {selectedTicket.priority.toUpperCase()}
                      </span>
                    </div>
                    <span className="text-xs text-text-3">{formatTimestamp(selectedTicket.createdAt)}</span>
                  </div>
                  <h2 className="font-display font-semibold text-lg text-text-1 mb-2">
                    {selectedTicket.subject}
                  </h2>
                  <div className="flex items-center gap-4 text-sm text-text-2">
                    <span>{selectedTicket.customerName}</span>
                    <span className="text-text-3">•</span>
                    <span>{selectedTicket.customerEmail}</span>
                    <span className="text-text-3">•</span>
                    <span className="capitalize">{selectedTicket.category.replace(/_/g, " ")}</span>
                  </div>
                </div>

                {/* Conversation */}
                <div className="card space-y-4">
                  <h3 className="section-label">Conversation</h3>
                  
                  {/* Customer message */}
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-surface-3 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4 text-text-2" />
                    </div>
                    <div className="flex-1 p-3 rounded-lg bg-surface-2">
                      <p className="text-sm text-text-1">{selectedTicket.message}</p>
                    </div>
                  </div>

                  {/* AI response */}
                  {selectedTicket.aiResponse && (
                    <div className="flex gap-3">
                      <div className="w-8 h-8 rounded-full bg-indigo/20 flex items-center justify-center shrink-0">
                        <Bot className="w-4 h-4 text-indigo" />
                      </div>
                      <div className="flex-1 p-3 rounded-lg bg-indigo/5 border border-indigo/20">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-medium text-indigo">AI Suggested Response</span>
                          <span className="confidence-pill confidence-high">88%</span>
                        </div>
                        <p className="text-sm text-text-1">{selectedTicket.aiResponse}</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Reply box */}
                <div className="card">
                  <h3 className="section-label mb-3">Reply</h3>
                  <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Type your reply or use the AI suggestion above..."
                    className="w-full h-24 p-3 rounded-lg bg-surface-2 border border-border text-sm text-text-1 placeholder:text-text-3 focus:outline-none focus:border-border-bright resize-none"
                  />
                  <div className="flex items-center justify-between mt-3">
                    <div className="flex items-center gap-2">
                      <button className="btn-ghost text-xs">
                        <Bot className="w-3.5 h-3.5" />
                        Use AI Suggestion
                      </button>
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="btn-ghost text-xs">
                        <ArrowUpRight className="w-3.5 h-3.5" />
                        Escalate
                      </button>
                      <button className="btn-primary text-xs">
                        <Send className="w-3.5 h-3.5" />
                        Send Reply
                      </button>
                    </div>
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
