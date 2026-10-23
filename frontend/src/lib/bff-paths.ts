/**
 * BFF path allowlist.
 *
 * The catch-all proxy at `/api/v1/[...path]` is **default-deny**: a frontend
 * path is only forwarded when its resource appears below. Anything else
 * returns 404 before a request ever leaves the Next server, so the proxy can
 * never be used to reach arbitrary internal backend paths.
 *
 * Kept out of the route handler so the rules can be unit-tested without
 * standing up Next.js.
 */

/** Core endpoints mounted under `/api/<resource>` (no `/v1`) on the backend. */
export const CORE_RESOURCES = new Set([
  "agents",
  "approvals",
  "analytics",
  "settings",
  "audit",
  "run",
  "tasks",
  "ws",
  "orders",
  "products",
  "reviews",
])

/** Endpoints exposed under `/api/v1/<resource>` on the backend. */
export const V1_RESOURCES = new Set([
  "shopify",
  "cart-recovery",
  "support",
  "observability",
  "memory",
  "security",
  "demo",
  "version",
  "cod",
])

/**
 * Translate a frontend path to the backend path, or `null` when the path is
 * not in the allowlist. Default-deny: unknown resources are never forwarded,
 * so the catch-all proxy cannot reach arbitrary internal backend paths.
 */
export function translatePath(pathname: string): string | null {
  // /health is mounted at the app root (not under /api)
  if (pathname === "/api/v1/health") {
    return "/health"
  }
  const m = pathname.match(/^\/api\/v1\/([^/]+)(.*)$/)
  if (!m) return null
  const resource = m[1]
  const rest = m[2] || ""
  if (CORE_RESOURCES.has(resource)) {
    return `/api/${resource}${rest}`
  }
  if (V1_RESOURCES.has(resource)) {
    return pathname
  }
  return null
}
