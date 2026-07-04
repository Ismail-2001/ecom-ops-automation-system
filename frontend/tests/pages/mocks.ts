import { vi } from 'vitest'

vi.mock('@/lib/hooks', () => ({
  useHealth: vi.fn(() => ({ data: { status: 'ok', version: 'v2.5.0' }, isLoading: false })),
  useAgentStatus: vi.fn(() => ({ data: [], isLoading: false })),
  useApprovals: vi.fn(() => ({ data: [], isLoading: false })),
  useAnalytics: vi.fn(() => ({ data: { summary: { total_financial_impact: 124892.40, total_decisions: 14208 } }, isLoading: false })),
  useSettings: vi.fn(() => ({ data: {}, isLoading: false })),
  useUpdateSettings: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useSupportTickets: vi.fn(() => ({ data: [], isLoading: false })),
  useCartRecoveryStats: vi.fn(() => ({ data: {}, isLoading: false })),
  useShopifyStatus: vi.fn(() => ({ data: {}, isLoading: false })),
  useOrders: vi.fn(() => ({ data: [], isLoading: false })),
  useProducts: vi.fn(() => ({ data: [], isLoading: false })),
  useReviews: vi.fn(() => ({ data: [], isLoading: false })),
}))

vi.mock('@/app/providers', () => ({
  useWs: vi.fn(() => ({ isConnected: true })),
}))

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
  usePathname: vi.fn(() => '/'),
}))

vi.mock('@/lib/auth-store', () => ({
  useAuthStore: vi.fn(() => ({
    login: vi.fn().mockResolvedValue(true),
    logout: vi.fn(),
    isLoading: false,
    error: null,
    clearError: vi.fn(),
    apiKey: null,
  })),
}))
