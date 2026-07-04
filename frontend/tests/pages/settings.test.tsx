import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import './mocks'
import SettingsPage from '@/app/settings/page'

vi.mock('@/components/layout/Shell', () => ({
  default: ({ children, title }: { children: React.ReactNode; title?: string }) => (
    <div data-testid="shell">
      {title && <h1>{title}</h1>}
      {children}
    </div>
  ),
}))

vi.mock('@/components/shared/Toggle', () => ({
  default: ({ enabled, onToggle, label }: { enabled: boolean; onToggle: () => void; label?: string }) => (
    <button
      role="switch"
      aria-checked={enabled}
      aria-label={label}
      onClick={onToggle}
      data-testid={`toggle-${label || 'unknown'}`}
    >
      {enabled ? 'On' : 'Off'}
    </button>
  ),
}))

describe('SettingsPage', () => {
  it('renders page title', () => {
    render(<SettingsPage />)
    expect(screen.getByText('System Settings')).toBeDefined()
  })

  it('renders API Configuration section', () => {
    render(<SettingsPage />)
    expect(screen.getByText('API Configuration')).toBeDefined()
    expect(screen.getByText('Manage LLM provider credentials')).toBeDefined()
  })

  it('renders Notification Settings section', () => {
    render(<SettingsPage />)
    expect(screen.getByText('Notification Settings')).toBeDefined()
    expect(screen.getByText('Configure alert delivery channels')).toBeDefined()
  })

  it('renders System Maintenance section', () => {
    render(<SettingsPage />)
    expect(screen.getByText('System Maintenance')).toBeDefined()
    expect(screen.getByText('Clear Cache')).toBeDefined()
    expect(screen.getByText('Restart Agents')).toBeDefined()
    expect(screen.getByText('Export Logs')).toBeDefined()
    expect(screen.getByText('Reset Defaults')).toBeDefined()
  })

  it('renders LLM provider select with default value', () => {
    render(<SettingsPage />)
    const select = screen.getByDisplayValue('Google Gemini')
    expect(select).toBeDefined()
  })

  it('renders Save Changes button', () => {
    render(<SettingsPage />)
    expect(screen.getByText('Save Changes')).toBeDefined()
  })

  it('renders notification toggles', () => {
    render(<SettingsPage />)
    expect(screen.getByText('Email Notifications')).toBeDefined()
    expect(screen.getByText('Slack Alerts')).toBeDefined()
    expect(screen.getByText('SMS Alerts')).toBeDefined()
    expect(screen.getByText('Browser Push')).toBeDefined()
  })

  it('toggles notification state on click', () => {
    render(<SettingsPage />)
    const toggles = screen.getAllByRole('switch')
    expect(toggles.length).toBeGreaterThanOrEqual(4)
    fireEvent.click(toggles[0])
    expect(toggles[0].getAttribute('aria-checked')).toBe('false')
  })
})
