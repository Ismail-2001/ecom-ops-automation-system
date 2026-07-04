import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import './mocks'
import LoginPage from '@/app/login/page'

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
  usePathname: vi.fn(() => '/'),
}))

describe('LoginPage', () => {
  it('renders login form with API key input', () => {
    render(<LoginPage />)
    expect(screen.getByPlaceholderText('opsiq-dev-key-2024')).toBeDefined()
    expect(screen.getByText('Access Command Center')).toBeDefined()
  })

  it('renders OpsIQ branding', () => {
    render(<LoginPage />)
    expect(screen.getByText('OpsIQ')).toBeDefined()
    expect(screen.getByText('AI Automation Interface')).toBeDefined()
  })

  it('renders documentation and security links', () => {
    render(<LoginPage />)
    expect(screen.getByText('Documentation')).toBeDefined()
    expect(screen.getByText('Security Audit')).toBeDefined()
    expect(screen.getByText('Status')).toBeDefined()
  })

  it('disables submit when API key is empty', () => {
    render(<LoginPage />)
    const button = screen.getByRole('button', { name: /Access Command Center/i })
    expect(button.hasAttribute('disabled')).toBe(true)
  })

  it('enables submit when API key is entered', () => {
    render(<LoginPage />)
    const input = screen.getByPlaceholderText('opsiq-dev-key-2024')
    fireEvent.change(input, { target: { value: 'test-key' } })
    const button = screen.getByRole('button', { name: /Access Command Center/i })
    expect(button.hasAttribute('disabled')).toBe(false)
  })

  it('shows system operational status', () => {
    render(<LoginPage />)
    expect(screen.getByText('System Operational')).toBeDefined()
  })
})
