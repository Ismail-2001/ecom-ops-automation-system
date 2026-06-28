"use client"

import { useCallback, useEffect, useRef, useState } from "react"

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/queue"
const RECONNECT_BASE_MS = 1_000
const RECONNECT_MAX_MS = 30_000
const PING_INTERVAL_MS = 30_000

export type WSEvent =
  | { type: "action_updated"; payload: Record<string, unknown> }
  | { type: "pipeline_started"; payload: Record<string, unknown> }
  | { type: "pipeline_completed"; payload: Record<string, unknown> }
  | { type: "agent_status"; payload: Record<string, unknown> }
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
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { onEvent, onConnect, onDisconnect, enabled = true } = options
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const attemptRef = useRef(0)

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    reconnectAttempt: 0,
    lastEvent: null,
  })

  const connect = useCallback(() => {
    if (!enabled) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    setState((s) => ({ ...s, isConnecting: true }))

    try {
      const ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        attemptRef.current = 0
        setState((s) => ({
          ...s,
          isConnected: true,
          isConnecting: false,
          reconnectAttempt: 0,
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
          setState((s) => ({ ...s, lastEvent: event }))
          onEvent?.(event)
        } catch {
          // Ignore malformed messages
        }
      }

      ws.onclose = () => {
        cleanup()
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
  }, [enabled, onEvent, onConnect, onDisconnect])

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
    if (!enabled) return
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
    })
  }, [cleanup])

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
  }
}
