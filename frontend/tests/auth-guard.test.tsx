import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { AuthGuard } from '@/components/auth/AuthGuard'
import { useAuthStore } from '@/lib/auth-store'

const h = vi.hoisted(() => ({
  replace: vi.fn(),
  pathname: '/cod-verification',
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: h.replace }),
  usePathname: () => h.pathname,
}))

vi.mock('@/lib/auth-store', () => ({
  useAuthStore: vi.fn(),
}))

/**
 * Simulates the real store: `checkSession` resolves and *then* flips
 * `isAuthenticated`, which the guard re-reads on its next render.
 */
function setSession(check: () => Promise<boolean>, authenticated = false) {
  const state = { isAuthenticated: authenticated }
  vi.mocked(useAuthStore).mockReturnValue({
    get isAuthenticated() {
      return state.isAuthenticated
    },
    checkSession: async () => {
      const valid = await check()
      if (valid) state.isAuthenticated = true
      else state.isAuthenticated = false
      return valid
    },
  } as unknown as ReturnType<typeof useAuthStore>)
}

beforeEach(() => {
  h.replace.mockClear()
  h.pathname = '/cod-verification'
  vi.mocked(useAuthStore).mockReset()
})

describe('AuthGuard', () => {
  it('keeps protected content hidden until the session check settles', async () => {
    let resolve!: (v: boolean) => void
    setSession(() => new Promise<boolean>((r) => (resolve = r)))

    const { container } = render(
      <AuthGuard>
        <p>protected</p>
      </AuthGuard>,
    )

    // Pending: no children, no redirect.
    expect(container.textContent).toBe('')
    expect(h.replace).not.toHaveBeenCalled()

    await act(async () => resolve(true))

    expect(screen.getByText('protected')).toBeTruthy()
    expect(h.replace).not.toHaveBeenCalled()
  })

  it('redirects to /login only after the session check fails', async () => {
    setSession(async () => false)

    const { container } = render(
      <AuthGuard>
        <p>protected</p>
      </AuthGuard>,
    )

    await waitFor(() => expect(h.replace).toHaveBeenCalledWith('/login'))
    expect(container.textContent).toBe('')
    expect(screen.queryByText('protected')).toBeNull()
  })

  it('never renders protected children when the session is invalid', async () => {
    setSession(async () => false)

    render(
      <AuthGuard>
        <p>protected</p>
      </AuthGuard>,
    )

    await waitFor(() => expect(h.replace).toHaveBeenCalledWith('/login'))
    // Give React a chance to flush any late render of the children.
    await act(async () => {})
    expect(screen.queryByText('protected')).toBeNull()
  })

  it('renders the login page without waiting or redirecting', async () => {
    h.pathname = '/login'
    let resolve!: (v: boolean) => void
    setSession(() => new Promise<boolean>((r) => (resolve = r)))

    render(
      <AuthGuard>
        <p>login form</p>
      </AuthGuard>,
    )

    expect(screen.getByText('login form')).toBeTruthy()
    expect(h.replace).not.toHaveBeenCalled()

    await act(async () => resolve(false))
    expect(h.replace).not.toHaveBeenCalled()
  })

  it('redirects when the store reports no session', async () => {
    // checkSession resolves false (already authenticated=false).
    setSession(async () => false)

    render(
      <AuthGuard>
        <p>protected</p>
      </AuthGuard>,
    )

    await waitFor(() => expect(h.replace).toHaveBeenCalledTimes(1))
    expect(h.replace).toHaveBeenCalledWith('/login')
  })
})
