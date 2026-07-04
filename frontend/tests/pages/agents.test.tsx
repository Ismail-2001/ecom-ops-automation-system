import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import './mocks'
import AgentsPage from '@/app/agents/page'

vi.mock('@/components/layout/Shell', () => ({
  default: ({ children, title, actions }: { children: React.ReactNode; title?: string; actions?: React.ReactNode }) => (
    <div data-testid="shell">
      {title && <h1>{title}</h1>}
      {actions && <div data-testid="shell-actions">{actions}</div>}
      {children}
    </div>
  ),
}))

describe('AgentsPage', () => {
  it('renders page title', () => {
    render(<AgentsPage />)
    expect(screen.getByText('Autonomous Agents')).toBeDefined()
  })

  it('renders all 7 agent cards', () => {
    render(<AgentsPage />)
    expect(screen.getByText('Fraud Detection')).toBeDefined()
    expect(screen.getAllByText('Inventory').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Price Optimizer').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Review Moderator')).toBeDefined()
    expect(screen.getByText('Marketing')).toBeDefined()
    expect(screen.getByText('Cart Recovery')).toBeDefined()
    expect(screen.getByText('Customer Support')).toBeDefined()
  })

  it('renders filter tabs via actions', () => {
    render(<AgentsPage />)
    expect(screen.getByText('All Agents')).toBeDefined()
    expect(screen.getByText('Active')).toBeDefined()
    expect(screen.getByText('Maintenance')).toBeDefined()
  })

  it('filters agents when Active tab is clicked', () => {
    render(<AgentsPage />)
    fireEvent.click(screen.getByText('Active'))
    expect(screen.getByText('Fraud Detection')).toBeDefined()
    expect(screen.getAllByText('Inventory').length).toBeGreaterThanOrEqual(1)
    expect(screen.queryByText('Review Moderator')).toBeNull()
  })

  it('filters agents when Maintenance tab is clicked', () => {
    render(<AgentsPage />)
    fireEvent.click(screen.getByText('Maintenance'))
    expect(screen.getByText('Review Moderator')).toBeDefined()
    expect(screen.queryByText('Fraud Detection')).toBeNull()
  })

  it('renders deploy new agent button', () => {
    render(<AgentsPage />)
    expect(screen.getByText('Deploy New Agent')).toBeDefined()
  })

  it('renders inference logs table', () => {
    render(<AgentsPage />)
    expect(screen.getByText('Inference Logs')).toBeDefined()
    expect(screen.getByText('Blocked Tx #9012 (High Risk)')).toBeDefined()
  })

  it('renders system health status', () => {
    render(<AgentsPage />)
    expect(screen.getByText('System Healthy')).toBeDefined()
  })
})
