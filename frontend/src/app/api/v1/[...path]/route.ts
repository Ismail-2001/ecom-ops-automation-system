import { NextRequest, NextResponse } from "next/server"
import { getBackendUrl, readSessionFromRequest } from "@/lib/server-helpers"

export const runtime = "nodejs"

/**
 * BFF proxy.
 *
 * The browser calls same-origin `/api/...` routes. This handler:
 *  1. Reads the HttpOnly session cookie (raw API key never touches the browser).
 *  2. Injects `Authorization: Bearer <apiKey>` server-side.
 *  3. Forwards to the backend, translating frontend paths to backend paths.
 *
 * Known path translations (backend mounts some routers under /api/v1 and
 * core endpoints directly under /api):
 */
function translatePath(pathname: string): string {
  // /health is mounted at the app root (not under /api)
  if (pathname === "/api/v1/health") {
    return "/health"
  }
  // /api/v1/<resource>...
  const m = pathname.match(/^\/api\/v1\/([^/]+)(.*)$/)
  if (!m) return pathname
  const resource = m[1]
  const rest = m[2] || ""
  // Core app-level endpoints live under /api/<resource> (no /v1)
  const coreResources = new Set([
    "agents",
    "approvals",
    "analytics",
    "settings",
    "audit",
    "run",
    "tasks",
    "ws",
  ])
  if (coreResources.has(resource)) {
    return `/api/${resource}${rest}`
  }
  return pathname
}

async function proxy(request: NextRequest) {
  const session = await readSessionFromRequest(request)
  if (!session) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }

  const url = request.nextUrl
  const target = `${getBackendUrl()}${translatePath(url.pathname)}${url.search}`

  const headers = new Headers(request.headers)
  headers.set("Authorization", `Bearer ${session.apiKey}`)
  // Remove hop-by-hop / host headers
  headers.delete("host")
  headers.delete("connection")
  headers.delete("cookie")

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
    redirect: "manual",
  }

  const hasBody = !["GET", "HEAD"].includes(request.method)
  if (hasBody) {
    init.body = await request.arrayBuffer()
  }

  try {
    const backendRes = await fetch(target, init)
    const body = await backendRes.arrayBuffer()
    return new NextResponse(body, {
      status: backendRes.status,
      headers: {
        "content-type": backendRes.headers.get("content-type") || "application/json",
        "cache-control": "no-store",
      },
    })
  } catch {
    return NextResponse.json(
      { detail: "Backend is not reachable." },
      { status: 502 }
    )
  }
}

export async function GET(request: NextRequest) {
  return proxy(request)
}

export async function POST(request: NextRequest) {
  return proxy(request)
}

export async function PATCH(request: NextRequest) {
  return proxy(request)
}

export async function PUT(request: NextRequest) {
  return proxy(request)
}

export async function DELETE(request: NextRequest) {
  return proxy(request)
}