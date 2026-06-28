"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { useAuthStore } from "@/lib/auth-store"

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login")
    }
  }, [isAuthenticated, router])

  if (!isAuthenticated) return null

  return <>{children}</>
}
