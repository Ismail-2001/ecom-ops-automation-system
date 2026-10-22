"use client"

import { useCallback, useEffect, useRef, useState } from "react"

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/queue"
const RECONNECT_BASE_MS = 1_000
const RECONNECT_MAX_MS = 30_000
const PING_INTERVAL_MS = 30_000
const TICKET_TTL_MARGIN_MS = 5_000
// If no frame (pong or event) arrives within ping interval + grace, the
// connection is presumed half-open/dead (sleep, captive portal, network
// switch) and is force-closed so the normal reconnect path takes over.
const PONG_TIMEOUT_MS = PING_INTERVAL_MS + 20_000
const WATCHDOG_INTERVAL_MS = 15_000

// WebSocket close codes matching backend
const CLOSE_AUTH_FAILED = 4001
const CLOSE_RATE_LIMITED = 4008
const CLOSE_TOO_MANY = 4013

export type WSEvent =
  | { type: "action_updated"; payload: Record<string, unknown> }
  | { type: "pipeline_started"; payload: Record<string, unknown> }
  | { type: "pipeline_completed"; payload: Record<string, unknown> }
  | { type: "pipeline_failed"; payload: Record<string, unknown> }
  | { type: "agent_status"; payload: Record<string, unknown> }
  | { type: "notification"; payload: Record<string, unknown> }
  | { type: "error"; payload: { code: string } }
  | { type: "pong" }
  | { type: string; payload?: Record<string, unknown> }

interface UseWebSocketOptions {
  onEvent?: (event: WSEvent) => void
  onConnect?: () => void
  onDisconnect?: () => void
  enabled?: boolean
}

interface WebSocketState {
  isConnected: boolean
  isConnecting: boolean
  reconnectAttempt: number
  lastEvent: WSEvent | null
  authFailed: boolean
}

/**
 * Fetch a short-lived, single-use WS ticket from the BFF. The ticket is issued
 * server-side from the HttpOnly session; the raw API key never touches JS.
 */
async function fetchTicket(): Promise<{ ticket: string; ttlMs: number }> {
  const res = await fetch("/api/auth/ws-ticket", { cache: "no-store" })
  if (!res.ok) {
    throw new Error(`ws-ticket failed: ${res.status}`)
  }
  const body = await res.json().catch(() => null)
  if (!body?.ticket) {
    throw new Error("ws-ticket returned no ticket")
  }
  const ttlSeconds = Number(body.ttl_seconds || 60)
  return { ticket: body.ticket as string, ttlMs: ttlSeconds * 1000 }
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { onEvent, onConnect, onDisconnect, enabled = true } = options
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const watchdogTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const attemptRef = useRef(0)
  const authFailedRef = useRef(false)
  const ticketExpiryRef = useRef(0)
  const lastMessageAtRef = useRef(0)
  const connectingRef = useRef(false)

  // Use refs for all callbacks to avoid stale closures and circular deps
  const onEventRef = useRef(onEvent)
  const onConnectRef = useRef(onConnect)
  const onDisconnectRef = useRef(onDisconnect)
  const enabledRef = useRef(enabled)
  const connectRef = useRef<() => Promise<void>>()

  onEventRef.current = onEvent
  onConnectRef.current = onConnect
  onDisconnectRef.current = onDisconnect
  enabledRef.current = enabled

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    reconnectAttempt: 0,
    lastEvent: null,
    authFailed: false,
  })

  const cleanup = useCallback(() => {
    if (pingTimer.current) {
      clearInterval(pingTimer.current)
      pingTimer.current = null
    }
    if (watchdogTimer.current) {
      clearInterval(watchdogTimer.current)
      watchdogTimer.current = null
    }
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
    }
  }, [])

  const scheduleReconnect = useCallback(() => {
    if (!enabledRef.current || authFailedRef.current) return
    const delay = Math.min(
      RECONNECT_BASE_MS * Math.pow(2, attemptRef.current),
      RECONNECT_MAX_MS,
    )
    attemptRef.current += 1
    setState((s) => ({ ...s, reconnectAttempt: attemptRef.current }))

    reconnectTimer.current = setTimeout(() => {
      connectRef.current?.()
    }, delay)
  }, [])

  const connect = useCallback(async () => {
    if (!enabledRef.current) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return
    if (connectingRef.current) return // ticket-mint window before the socket exists
    if (authFailedRef.current) return

    // A pending backoff is superseded by this attempt (it re-arms on failure).
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
    }
    connectingRef.current = true
    setState((s) => ({ ...s, isConnecting: true }))

    try {
      // Mint a fresh single-use ticket from the BFF per connection attempt.
      const { ticket, ttlMs } = await fetchTicket()
      ticketExpiryRef.current = Date.now() + ttlMs - TICKET_TTL_MARGIN_MS

      const base = WS_BASE_URL
      const finalUrl = `${base}${base.includes("?") ? "&" : "?"}ticket=${encodeURIComponent(ticket)}`
      const ws = new WebSocket(finalUrl)

      ws.onopen = () => {
        attemptRef.current = 0
        authFailedRef.current = false
        lastMessageAtRef.current = Date.now()
        setState((s) => ({
          ...s,
          isConnected: true,
          isConnecting: false,
          reconnectAttempt: 0,
          authFailed: false,
        }))
        onConnectRef.current?.()

        pingTimer.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }))
          }
        }, PING_INTERVAL_MS)

        // Force-close a half-open socket so onclose drives a clean reconnect.
        watchdogTimer.current = setInterval(() => {
          if (ws.readyState !== WebSocket.OPEN) return
          if (Date.now() - lastMessageAtRef.current > PONG_TIMEOUT_MS) {
            ws.close(4000, "pong timeout")
          }
        }, WATCHDOG_INTERVAL_MS)
      }

      ws.onmessage = (msg) => {
        lastMessageAtRef.current = Date.now()
        try {
          const event: WSEvent = JSON.parse(msg.data)
          if (event.type === "pong") return

          if (event.type === "error" && event.payload?.code === "rate_limited") {
            return
          }

          setState((s) => ({ ...s, lastEvent: event }))
          onEventRef.current?.(event)
        } catch {
          // Ignore malformed messages
        }
      }

      ws.onclose = (event) => {
        cleanup()

        // Auth failed — don't reconnect
        if (
          event.code === CLOSE_AUTH_FAILED ||
          event.code === CLOSE_TOO_MANY ||
          event.code === CLOSE_RATE_LIMITED
        ) {
          authFailedRef.current = true
          setState((s) => ({
            ...s,
            isConnected: false,
            isConnecting: false,
            authFailed: true,
          }))
          return
        }

        setState((s) => ({ ...s, isConnected: false, isConnecting: false }))
        onDisconnectRef.current?.()
        scheduleReconnect()
      }

      ws.onerror = () => {
        ws.close()
      }

      wsRef.current = ws
    } catch {
      setState((s) => ({ ...s, isConnecting: false }))
      scheduleReconnect()
    } finally {
      connectingRef.current = false
    }
  }, [cleanup, scheduleReconnect])

  // Update connectRef after connect is defined
  connectRef.current = connect

  const disconnect = useCallback(() => {
    cleanup()
    wsRef.current?.close()
    wsRef.current = null
    setState({
      isConnected: false,
      isConnecting: false,
      reconnectAttempt: 0,
      lastEvent: null,
      authFailed: false,
    })
    authFailedRef.current = false
    ticketExpiryRef.current = 0
  }, [cleanup])

  // Reset auth state after a new session is established (e.g., after login)
  const resetAuth = useCallback(() => {
    authFailedRef.current = false
    ticketExpiryRef.current = 0
    setState((s) => ({ ...s, authFailed: false }))
    attemptRef.current = 0
    connect()
  }, [connect])

  // The mount effect below only ever runs connect() once — with deps
  // [connect, cleanup] it would never re-fire when `enabled` flips
  // false→true after login, so the socket was never attempted for the
  // whole session. Watch `enabled` explicitly.
  useEffect(() => {
    if (enabled) {
      connectRef.current?.()
    } else {
      disconnect()
    }
  }, [enabled, disconnect])

  useEffect(() => {
    connect()

    // Network restored or tab visible again: recover immediately instead of
    // waiting out the current backoff (which can be up to 30s).
    const recover = () => {
      if (!enabledRef.current || authFailedRef.current) return
      if (wsRef.current?.readyState === WebSocket.OPEN) return
      if (wsRef.current?.readyState === WebSocket.CONNECTING) return
      if (connectingRef.current) return
      attemptRef.current = 0
      connectRef.current?.()
    }
    const onOnline = () => recover()
    const onVisibility = () => {
      if (document.visibilityState === "visible") recover()
    }
    window.addEventListener("online", onOnline)
    document.addEventListener("visibilitychange", onVisibility)

    return () => {
      window.removeEventListener("online", onOnline)
      document.removeEventListener("visibilitychange", onVisibility)
      cleanup()
      wsRef.current?.close()
    }
  }, [connect, cleanup])

  return {
    ...state,
    disconnect,
    reconnect: () => connect(),
    resetAuth,
  }
}