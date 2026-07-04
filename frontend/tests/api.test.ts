import { describe, it, expect, vi, beforeEach } from 'vitest'
import { authApi, ApiError } from '@/lib/api'

const mockFetch = vi.fn()
global.fetch = mockFetch

beforeEach(() => {
  mockFetch.mockReset()
})

describe('authApi.login', () => {
  it('returns success on valid login', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ status: 'ok', operator: 'test-operator' }),
    })

    const result = await authApi.login('test-key')
    expect(result.status).toBe('ok')
    expect(result.operator).toBe('test-operator')
  })

  it('throws ApiError on 401', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Invalid API key' }),
    })

    await expect(authApi.login('bad-key')).rejects.toThrow(ApiError)
  })

  it('sends correct request body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ status: 'ok' }),
    })

    await authApi.login('my-key')

    const [url, options] = mockFetch.mock.calls[0]
    expect(url).toContain('/api/v1/auth/login')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ api_key: 'my-key' })
  })
})

describe('ApiError', () => {
  it('stores status and message', () => {
    const err = new ApiError(404, 'Not Found')
    expect(err.status).toBe(404)
    expect(err.message).toBe('Not Found')
    expect(err.name).toBe('ApiError')
  })

  it('stores body', () => {
    const err = new ApiError(500, 'Error', { detail: 'something' })
    expect(err.body).toEqual({ detail: 'something' })
  })
})
