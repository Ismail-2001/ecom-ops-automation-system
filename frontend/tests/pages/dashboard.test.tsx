import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import './mocks'
import DashboardPage from '@/app/page'

vi.mock('@/components/layout/Shell', () => ({
  default: ({ children, title }: { children: React.ReactNode; title?: string }) => (
    <div data-testid="shell">
      {title && <h1>{title}</h1>}
      {children}
    </div>
  ),
}))

describe('DashboardPage', () => {
  it('renders page title', () => {
    render(<DashboardPage />)
    expect(screen.getByText('Command Center')).toBeDefined()
  })

  it('renders metric cards', () => {
    render(<DashboardPage />)
    expect(screen.getByText('Total Revenue')).toBeDefined()
    expect(screen.getByText('Decisions Made')).toBeDefined()
    expect(screen.getByText('Pending Reviews')).toBeDefined()
    expect(screen.getByText('Flagged Orders')).toBeDefined()
  })

  it('renders revenue value', () => {
    render(<DashboardPage />)
    expect(screen.getByText('$124,892.40')).toBeDefined()
  })

  it('renders pending approvals section', () => {
    render(<DashboardPage />)
    expect(screen.getByText('Pending Approvals')).toBeDefined()
  })

  it('renders agent fleet status', () => {
    render(<DashboardPage />)
    expect(screen.getByText('Agent Fleet Status')).toBeDefined()
  })

  it('renders system health card', () => {
    render(<DashboardPage />)
    expect(screen.getByText('System Health')).toBeDefined()
    expect(screen.getByText('WebSocket Status')).toBeDefined()
  })

  it('renders AI insight section', () => {
    render(<DashboardPage />)
    expect(screen.getByText('AI INSIGHT')).toBeDefined()
  })

  it('renders footer', () => {
    render(<DashboardPage />)
    expect(screen.getByText(/All Systems Operational/)).toBeDefined()
  })

  it('renders pagination controls', () => {
    render(<DashboardPage />)
    expect(screen.getByText(/Showing/)).toBeDefined()
  })
})
