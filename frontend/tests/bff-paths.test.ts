import { describe, it, expect } from 'vitest'
import { translatePath, CORE_RESOURCES, V1_RESOURCES } from '@/lib/bff-paths'

describe('BFF path allowlist (translatePath)', () => {
  it('translates the root health endpoint', () => {
    expect(translatePath('/api/v1/health')).toBe('/health')
  })

  it('remaps core resources from /api/v1/<res> to /api/<res>', () => {
    expect(translatePath('/api/v1/agents')).toBe('/api/agents')
    expect(translatePath('/api/v1/approvals/42/approve')).toBe(
      '/api/approvals/42/approve',
    )
    expect(translatePath('/api/v1/analytics/summary')).toBe('/api/analytics/summary')
  })

  it('passes v1 resources through unchanged, including cod', () => {
    expect(translatePath('/api/v1/cod/health')).toBe('/api/v1/cod/health')
    expect(translatePath('/api/v1/cod/phone/validate')).toBe(
      '/api/v1/cod/phone/validate',
    )
    expect(translatePath('/api/v1/cod/otp/request')).toBe('/api/v1/cod/otp/request')
    expect(translatePath('/api/v1/cod/otp/verify')).toBe('/api/v1/cod/otp/verify')
    expect(translatePath('/api/v1/cart-recovery/campaigns')).toBe(
      '/api/v1/cart-recovery/campaigns',
    )
    expect(translatePath('/api/v1/version')).toBe('/api/v1/version')
  })

  it('is default-deny for unknown resources', () => {
    expect(translatePath('/api/v1/internal/secrets')).toBeNull()
    expect(translatePath('/api/v1/../../etc/passwd')).toBeNull()
    expect(translatePath('/api/v1/')).toBeNull()
    expect(translatePath('/api/v1')).toBeNull()
    expect(translatePath('/api/v1/cod-extra')).toBeNull()
  })

  it('refuses paths outside the /api/v1 namespace', () => {
    expect(translatePath('/api/v2/cod/health')).toBeNull()
    expect(translatePath('/cod/health')).toBeNull()
    expect(translatePath('/admin')).toBeNull()
  })

  it('never exposes an allowlisted resource under a nested prefix', () => {
    for (const resource of [...CORE_RESOURCES, ...V1_RESOURCES]) {
      expect(translatePath(`/api/v1/${resource}`)).not.toBeNull()
      expect(translatePath(`/api/v1/deep/${resource}`)).toBeNull()
    }
  })

  it('keeps query-irrelevant trailing segments attached to the translation', () => {
    expect(translatePath('/api/v1/cod/health')).toBe('/api/v1/cod/health')
    expect(translatePath('/api/v1/demo/demo/orders')).toBe('/api/v1/demo/demo/orders')
  })
})
