import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const publicRoutes = ['/login', '/api/auth/login']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (publicRoutes.some((r) => pathname.startsWith(r))) {
    return NextResponse.next()
  }

  const apiKey = request.cookies.get('opsiq_api_key')?.value
  const isAuthenticated = request.cookies.get('opsiq_auth')?.value

  if (!apiKey && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  const response = NextResponse.next()
  response.headers.set('x-pathname', pathname)
  return response
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
}
