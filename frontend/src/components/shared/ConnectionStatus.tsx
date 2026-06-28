"use client"

import { useWs } from "@/app/providers"
import { Wifi, WifiOff, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export function ConnectionStatus() {
  const { isConnected, isConnecting } = useWs()

  return (
    <div
      className={cn(
        "flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-mono transition-colors",
        isConnected
          ? "bg-emerald/10 text-emerald"
          : isConnecting
            ? "bg-amber/10 text-amber"
            : "bg-red/10 text-red",
      )}
    >
      {isConnected ? (
        <Wifi className="w-3 h-3" />
      ) : isConnecting ? (
        <Loader2 className="w-3 h-3 animate-spin" />
      ) : (
        <WifiOff className="w-3 h-3" />
      )}
      {isConnected ? "Live" : isConnecting ? "Connecting..." : "Offline"}
    </div>
  )
}
