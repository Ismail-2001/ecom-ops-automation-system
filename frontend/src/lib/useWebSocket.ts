"use client"

import { useCallback, useEffect, useRef, useState } from "react"

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/queue"
const RECONNECT_BASE_MS = 1_000
const RECONNECT_MAX_MS = 30_000
const PING_INTERVAL_MS = 30_000

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

function getAuthToken(): string | null {
  if (typeof document === "undefined") return null
  const match = document.cookie.match(/(?:^|; )opsiq_api_key=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : null
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { onEvent, onConnect, onDisconnect, enabled = true } = options
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const attemptRef = useRef(0)
  const authFailedRef = useRef(false)

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    reconnectAttempt: 0,
    lastEvent: null,
    authFailed: false,
  })

  const buildWsUrl = useCallback(() => {
    const token = getAuthToken()
    if (token) {
      return `${WS_BASE_URL}?token=${encodeURIComponent(token)}`
    }
    return WS_BASE_URL
  }, [])

  const connect = useCallback(() => {
    if (!enabled) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    if (authFailedRef.current) return

    // Re-check auth token — if no token and in production, don't attempt
    const token = getAuthToken()
    if (!token && process.env.NODE_ENV === "production") {
      authFailedRef.current = true
      setState((s) => ({ ...s, authFailed: true }))
      return
    }

    setState((s) => ({ ...s, isConnecting: true }))

    try {
      const wsUrl = buildWsUrl()
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        attemptRef.current = 0
        authFailedRef.current = false
        setState((s) => ({
          ...s,
          isConnected: true,
          isConnecting: false,
          reconnectAttempt: 0,
          authFailed: false,
        }))
        onConnect?.()

        pingTimer.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }))
          }
        }, PING_INTERVAL_MS)
      }

      ws.onmessage = (msg) => {
        try {
          const event: WSEvent = JSON.parse(msg.data)
          if (event.type === "pong") return

          // Handle auth error from server
          if (event.type === "error" && event.payload?.code === "rate_limited") {
            return
          }

          setState((s) => ({ ...s, lastEvent: event }))
          onEvent?.(event)
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
        onDisconnect?.()
        scheduleReconnect()
      }

      ws.onerror = () => {
        ws.close()
      }

      wsRef.current = ws
    } catch {
      setState((s) => ({ ...s, isConnecting: false }))
      scheduleReconnect()
    }
  }, [enabled, onEvent, onConnect, onDisconnect, buildWsUrl])

  const cleanup = useCallback(() => {
    if (pingTimer.current) {
      clearInterval(pingTimer.current)
      pingTimer.current = null
    }
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
    }
  }, [])

  const scheduleReconnect = useCallback(() => {
    if (!enabled || authFailedRef.current) return
    const delay = Math.min(
      RECONNECT_BASE_MS * Math.pow(2, attemptRef.current),
      RECONNECT_MAX_MS,
    )
    attemptRef.current += 1
    setState((s) => ({ ...s, reconnectAttempt: attemptRef.current }))

    reconnectTimer.current = setTimeout(() => {
      connect()
    }, delay)
  }, [enabled, connect])

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
  }, [cleanup])

  // Reset auth state when token changes (e.g., after login)
  const resetAuth = useCallback(() => {
    authFailedRef.current = false
    setState((s) => ({ ...s, authFailed: false }))
    attemptRef.current = 0
    connect()
  }, [connect])

  useEffect(() => {
    connect()
    return () => {
      cleanup()
      wsRef.current?.close()
    }
  }, [connect, cleanup])

  return {
    ...state,
    disconnect,
    reconnect: connect,
    resetAuth,
  }
}
