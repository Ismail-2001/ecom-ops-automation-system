import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import './mocks'
import CodVerificationPage from '@/app/cod-verification/page'

vi.mock('@/components/layout/Shell', () => ({
  default: ({ children, title }: { children: React.ReactNode; title?: string }) => (
    <div data-testid="shell">
      {title && <h1>{title}</h1>}
      {children}
    </div>
  ),
}))

interface MockResponse {
  status?: number
  body?: unknown
}

function stubFetch({ status = 200, body = {} }: MockResponse = {}) {
  const fn = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: status >= 200 && status < 300 ? 'OK' : 'Error',
    json: async () => body,
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

const VALID_CLEAN = {
  raw: '03214567890',
  normalized: '03214567890',
  e164: '+923214567890',
  operator: 'jazz',
  is_valid: true,
  risk_signals: [],
  risk_level: 'low',
  action: 'allow',
}

const VALID_SUSPICIOUS = {
  raw: '03000000000',
  normalized: '03000000000',
  e164: '+923000000000',
  operator: 'jazz',
  is_valid: true,
  risk_signals: ['all_same_digit', 'low_entropy'],
  risk_level: 'high',
  action: 'needs_otp_verification',
}

const INVALID_NUMBER = {
  raw: '12345',
  normalized: '',
  e164: '',
  operator: 'unknown',
  is_valid: false,
  risk_signals: ['incomplete'],
  risk_level: 'high',
  action: 'review',
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('CodVerificationPage', () => {
  it('renders page title', () => {
    render(<CodVerificationPage />)
    expect(screen.getByText('COD Verification')).toBeDefined()
  })

  it('renders health metrics from the cod health endpoint', () => {
    render(<CodVerificationPage />)
    const metrics = screen.getAllByTestId('cod-health-metric')
    expect(metrics).toHaveLength(4)
    expect(screen.getByText('Delivery Provider')).toBeDefined()
    expect(screen.getByText('log')).toBeDefined()
    expect(screen.getByText('300s')).toBeDefined()
    expect(screen.getByText('5 / 3')).toBeDefined()
    expect(screen.getByText('No')).toBeDefined()
  })

  it('renders the phone sanitizer and step-up sections', () => {
    render(<CodVerificationPage />)
    expect(screen.getByText('Phone Sanitizer')).toBeDefined()
    expect(screen.getByText('OTP Step-Up Challenge')).toBeDefined()
    expect(screen.getByTestId('cod-validate-input')).toBeDefined()
    expect(screen.getByTestId('cod-otp-phone')).toBeDefined()
    expect(screen.getByTestId('cod-code-input')).toBeDefined()
  })

  it('keeps the validate button disabled until a number is entered', () => {
    render(<CodVerificationPage />)
    const button = screen.getByTestId('cod-validate-button')
    expect(button).toHaveProperty('disabled', true)

    fireEvent.change(screen.getByTestId('cod-validate-input'), {
      target: { value: '03214567890' },
    })
    expect(screen.getByTestId('cod-validate-button')).toHaveProperty('disabled', false)
  })

  it('shows normalized E.164, operator and Allow badge for a clean number', async () => {
    stubFetch({ body: VALID_CLEAN })
    render(<CodVerificationPage />)

    fireEvent.change(screen.getByTestId('cod-validate-input'), {
      target: { value: '03214567890' },
    })
    fireEvent.click(screen.getByTestId('cod-validate-button'))

    await waitFor(() => expect(screen.getByTestId('cod-validation-result')).toBeTruthy())

    expect(screen.getByTestId('cod-e164').textContent).toBe('+923214567890')
    expect(screen.getByTestId('cod-operator').textContent).toBe('Jazz')
    expect(screen.getByText('Allow')).toBeDefined()
    expect(screen.getByTestId('cod-risk-signals').textContent).toBe('None')
    expect(screen.getByTestId('cod-validity').textContent).toContain('Structurally valid')
  })

  it('surfaces heuristics and the OTP Step-Up action for a suspicious number', async () => {
    stubFetch({ body: VALID_SUSPICIOUS })
    render(<CodVerificationPage />)

    fireEvent.change(screen.getByTestId('cod-validate-input'), {
      target: { value: '03000000000' },
    })
    fireEvent.click(screen.getByTestId('cod-validate-button'))

    await waitFor(() => expect(screen.getByTestId('cod-validation-result')).toBeTruthy())

    expect(screen.getByText('OTP Step-Up')).toBeDefined()
    const signals = screen.getByTestId('cod-risk-signals')
    expect(signals.textContent).toContain('all_same_digit')
    expect(signals.textContent).toContain('low_entropy')
  })

  it('marks an undeliverable number for manual review', async () => {
    stubFetch({ body: INVALID_NUMBER })
    render(<CodVerificationPage />)

    fireEvent.change(screen.getByTestId('cod-validate-input'), {
      target: { value: '12345' },
    })
    fireEvent.click(screen.getByTestId('cod-validate-button'))

    await waitFor(() => expect(screen.getByTestId('cod-validation-result')).toBeTruthy())

    expect(screen.getByText('Manual Review')).toBeDefined()
    expect(screen.getByTestId('cod-validity').textContent).toContain('Not deliverable')
  })

  it('reports the API error message when validation is refused', async () => {
    stubFetch({ status: 400, body: { detail: 'phone number rejected' } })
    render(<CodVerificationPage />)

    fireEvent.change(screen.getByTestId('cod-validate-input'), {
      target: { value: '12345' },
    })
    fireEvent.click(screen.getByTestId('cod-validate-button'))

    await waitFor(() => expect(screen.getByTestId('cod-validation-error')).toBeTruthy())
    expect(screen.getByTestId('cod-validation-error').textContent).toContain(
      'phone number rejected',
    )
    expect(screen.queryByTestId('cod-validation-result')).toBeNull()
  })

  it('explains a missing cod:execute permission on OTP send', async () => {
    stubFetch({ status: 403, body: { detail: 'Permission denied: cod:execute' } })
    render(<CodVerificationPage />)

    fireEvent.change(screen.getByTestId('cod-otp-phone'), {
      target: { value: '03214567890' },
    })
    fireEvent.click(screen.getByTestId('cod-otp-send'))

    await waitFor(() => expect(screen.getByTestId('cod-send-error')).toBeTruthy())
    expect(screen.getByTestId('cod-send-error').textContent).toContain('cod:execute')
    expect(screen.queryByTestId('cod-otp-result')).toBeNull()
  })

  it('shows the issued-code metadata without ever echoing a code', async () => {
    stubFetch({
      body: {
        sent: true,
        phone: '03214567890',
        channel: 'whatsapp',
        provider: 'log',
        purpose: 'cod_verification',
        expires_in: 300,
        resend_after: 60,
        attempts_allowed: 5,
        reason: 'ok',
        request_id: 'abc123',
      },
    })
    render(<CodVerificationPage />)

    fireEvent.change(screen.getByTestId('cod-otp-phone'), {
      target: { value: '03214567890' },
    })
    fireEvent.click(screen.getByTestId('cod-otp-send'))

    await waitFor(() => expect(screen.getByTestId('cod-otp-result')).toBeTruthy())

    const result = screen.getByTestId('cod-otp-result')
    expect(result.textContent).toContain('Sent')
    expect(result.textContent).toContain('reason: ok')
    expect(result.textContent).toContain('expires in 300s')
    // The passcode itself must never reach the UI.
    expect(result.textContent).not.toMatch(/\b\d{6}\b/)
  })

  it('shows a refused send with its reason', async () => {
    stubFetch({
      body: {
        sent: false,
        phone: '03214567890',
        channel: 'whatsapp',
        provider: 'none',
        purpose: 'cod_verification',
        expires_in: 0,
        resend_after: 42,
        attempts_allowed: 5,
        reason: 'cooldown_active',
        request_id: 'abc123',
      },
    })
    render(<CodVerificationPage />)

    fireEvent.change(screen.getByTestId('cod-otp-phone'), {
      target: { value: '03214567890' },
    })
    fireEvent.click(screen.getByTestId('cod-otp-send'))

    await waitFor(() => expect(screen.getByTestId('cod-otp-result')).toBeTruthy())

    const result = screen.getByTestId('cod-otp-result')
    expect(result.textContent).toContain('Not Sent')
    expect(result.textContent).toContain('cooldown_active')
  })

  it('confirms a successful verification', async () => {
    stubFetch({
      body: {
        verified: true,
        phone: '03214567890',
        purpose: 'cod_verification',
        attempts_remaining: 0,
        reason: 'ok',
      },
    })
    render(<CodVerificationPage />)

    fireEvent.change(screen.getByTestId('cod-otp-phone'), {
      target: { value: '03214567890' },
    })
    fireEvent.change(screen.getByTestId('cod-code-input'), {
      target: { value: '123456' },
    })
    fireEvent.click(screen.getByTestId('cod-verify-button'))

    await waitFor(() => expect(screen.getByTestId('cod-verify-result')).toBeTruthy())

    const result = screen.getByTestId('cod-verify-result')
    expect(result.textContent).toContain('Verified')
    expect(result.textContent).toContain('0 attempts left')
  })

  it('shows a rejected verification with the remaining attempt budget', async () => {
    stubFetch({
      body: {
        verified: false,
        phone: '03214567890',
        purpose: 'cod_verification',
        attempts_remaining: 4,
        reason: 'invalid_code',
      },
    })
    render(<CodVerificationPage />)

    fireEvent.change(screen.getByTestId('cod-otp-phone'), {
      target: { value: '03214567890' },
    })
    fireEvent.change(screen.getByTestId('cod-code-input'), {
      target: { value: '000000' },
    })
    fireEvent.click(screen.getByTestId('cod-verify-button'))

    await waitFor(() => expect(screen.getByTestId('cod-verify-result')).toBeTruthy())

    const result = screen.getByTestId('cod-verify-result')
    expect(result.textContent).toContain('Rejected')
    expect(result.textContent).toContain('invalid_code')
    expect(result.textContent).toContain('4 attempts left')
  })

  it('sends the Roman Urdu template when that language is selected', async () => {
    const fetchMock = stubFetch({
      body: {
        sent: true,
        phone: '03214567890',
        channel: 'whatsapp',
        provider: 'log',
        purpose: 'cod_verification',
        expires_in: 300,
        resend_after: 60,
        attempts_allowed: 5,
        reason: 'ok',
        request_id: 'abc123',
      },
    })
    render(<CodVerificationPage />)

    fireEvent.click(screen.getByText('Roman Urdu'))
    fireEvent.change(screen.getByTestId('cod-otp-phone'), {
      target: { value: '03214567890' },
    })
    fireEvent.click(screen.getByTestId('cod-otp-send'))

    await waitFor(() => expect(fetchMock).toHaveBeenCalled())

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toContain('/api/v1/cod/otp/request')
    expect(JSON.parse(init.body as string).language).toBe('ur')
  })
})
