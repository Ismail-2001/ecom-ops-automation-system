import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import './mocks'
import AnalyticsPage from '@/app/analytics/page'

vi.mock('@/components/layout/Shell', () => ({
  default: ({ children, title, actions }: { children: React.ReactNode; title?: string; actions?: React.ReactNode }) => (
    <div data-testid="shell">
      {title && <h1>{title}</h1>}
      {actions && <div data-testid="shell-actions">{actions}</div>}
      {children}
    </div>
  ),
}))

describe('AnalyticsPage', () => {
  it('renders page title', () => {
    render(<AnalyticsPage />)
    expect(screen.getByText('Performance Intelligence')).toBeDefined()
  })

  it('renders metric cards', () => {
    render(<AnalyticsPage />)
    expect(screen.getByText('ROI FROM AI AGENTS')).toBeDefined()
    expect(screen.getByText('428.4%')).toBeDefined()
    expect(screen.getByText('TOTAL REVENUE SAVED')).toBeDefined()
    expect(screen.getByText('$1.24M')).toBeDefined()
    expect(screen.getByText('AVG. RESOLUTION TIME')).toBeDefined()
    expect(screen.getByText('1.4m')).toBeDefined()
    expect(screen.getByText('AGENT ACCURACY')).toBeDefined()
    expect(screen.getByText('99.1%')).toBeDefined()
  })

  it('renders time range filter buttons', () => {
    render(<AnalyticsPage />)
    expect(screen.getByText('30D')).toBeDefined()
    expect(screen.getByText('7D')).toBeDefined()
    expect(screen.getByText('24H')).toBeDefined()
  })

  it('switches time range on click', () => {
    render(<AnalyticsPage />)
    const btn7d = screen.getByText('7D')
    fireEvent.click(btn7d)
    expect(btn7d.className).toContain('bg-primary/15')
  })

  it('renders revenue trends section', () => {
    render(<AnalyticsPage />)
    expect(screen.getByText('Revenue Trends')).toBeDefined()
  })

  it('renders decision distribution chart', () => {
    render(<AnalyticsPage />)
    expect(screen.getByText('Decision Distribution')).toBeDefined()
    expect(screen.getByText('Auto-Approved')).toBeDefined()
    expect(screen.getByText('Human Intervention')).toBeDefined()
    expect(screen.getByText('Auto-Rejected')).toBeDefined()
  })

  it('renders risk distribution table', () => {
    render(<AnalyticsPage />)
    expect(screen.getByText('Risk Distribution')).toBeDefined()
    expect(screen.getByText('North America - East')).toBeDefined()
    expect(screen.getByText('APAC - Singapore')).toBeDefined()
    expect(screen.getByText('EMEA - Frankfurt')).toBeDefined()
  })

  it('renders export button', () => {
    render(<AnalyticsPage />)
    expect(screen.getByText('Export')).toBeDefined()
  })
})
