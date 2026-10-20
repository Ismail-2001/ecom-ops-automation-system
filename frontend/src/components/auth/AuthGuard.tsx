"use client"

import { usePathname, useRouter } from "next/navigation"
import { useEffect, useRef, useState } from "react"
import { useAuthStore } from "@/lib/auth-store"

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, checkSession } = useAuthStore()
  const router = useRouter()
  const pathname = usePathname()
  const checkedRef = useRef(false)
  // Session verification is async. Until it settles we must neither render
  // protected content nor redirect: `isAuthenticated` starts false on a hard
  // load (Zustand only persists the operator, never the auth flag), so
  // redirecting on that value alone bounced every deep link / refresh to
  // /login even with a perfectly valid HttpOnly session cookie.
  const [checking, setChecking] = useState(true)

  // On first mount (e.g., a hard refresh), verify the HttpOnly session against
  // the BFF so a stale Zustand persist value can't grant access. The redirect
  // itself is owned by the effect below so it fires exactly once, when the
  // check settles — never against the initial `isAuthenticated === false`.
  useEffect(() => {
    if (checkedRef.current) return
    checkedRef.current = true
    checkSession().finally(() => setChecking(false))
  }, [checkSession])

  useEffect(() => {
    if (checking || isAuthenticated || pathname === "/login") return
    router.replace("/login")
  }, [checking, isAuthenticated, pathname, router])

  const onLoginPage = pathname === "/login"

  // Gate: render children only when the session has been verified as
  // authenticated, or when the login page itself needs to render. Protected
  // content stays hidden for the whole verification window.
  if (checking && !onLoginPage) return null
  if (!isAuthenticated && !onLoginPage) return null

  return <>{children}</>
}
