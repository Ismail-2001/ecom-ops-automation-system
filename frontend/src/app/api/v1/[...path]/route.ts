import { NextRequest, NextResponse } from "next/server"
import { getBackendUrl, readSessionFromRequest } from "@/lib/server-helpers"
import { applyTraceContext } from "@/lib/trace-context"
import { translatePath } from "@/lib/bff-paths"

export const runtime = "nodejs"

/**
 * BFF proxy.
 *
 * The browser calls same-origin `/api/...` routes. This handler:
 *  1. Reads the HttpOnly session cookie (raw API key never touches the browser).
 *  2. Injects `Authorization: Bearer <apiKey>` server-side.
 *  3. Forwards to the backend, translating frontend paths to backend paths.
 *
 * Path translation and the default-deny allowlist live in `@/lib/bff-paths`
 * so the rules are unit-testable without booting Next.js.
 */

async function proxy(request: NextRequest) {
  const session = await readSessionFromRequest(request)
  if (!session) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }

  const url = request.nextUrl
  const translated = translatePath(url.pathname)
  if (translated === null) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 })
  }
  const target = `${getBackendUrl()}${translated}${url.search}`

  const headers = new Headers(request.headers)
  headers.set("Authorization", `Bearer ${session.apiKey}`)
  // Remove hop-by-hop / host headers
  headers.delete("host")
  headers.delete("connection")
  headers.delete("cookie")
  // Ensure standard W3C trace context reaches the backend (browsers don't send it)
  applyTraceContext(headers)

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