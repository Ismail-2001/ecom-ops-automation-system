"use client"

import { useState } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  KeyRound,
  Loader2,
  Send,
  ShieldCheck,
  Smartphone,
  XCircle,
} from "lucide-react"
import Shell from "@/components/layout/Shell"
import { Input } from "@/components/ui/input"
import FilterTabs from "@/components/shared/FilterTabs"
import { useCodHealth } from "@/lib/hooks"
import {
  ApiError,
  codApi,
  type OtpRequestResult,
  type OtpVerification,
  type PhoneValidation,
} from "@/lib/api"

const ACTION_DISPLAY: Record<
  PhoneValidation["action"],
  { label: string; className: string }
> = {
  allow: { label: "Allow", className: "badge-success" },
  needs_otp_verification: { label: "OTP Step-Up", className: "badge-warning" },
  review: { label: "Manual Review", className: "badge-danger" },
}

const OPERATOR_LABELS: Record<string, string> = {
  jazz: "Jazz",
  zong: "Zong",
  ufone: "Ufone",
  telenor: "Telenor",
  scom: "SCOM",
  onic: "Onic",
  unknown: "Unknown",
}

function permissionHint(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return "Your role does not hold the cod:execute permission required to send or verify codes."
  }
  if (error instanceof ApiError) return error.message
  return "Request failed — check that the backend is reachable."
}

export default function CodVerificationPage() {
  const { data: health, isLoading: healthLoading, isError: healthError } = useCodHealth()

  const [phone, setPhone] = useState("")
  const [validation, setValidation] = useState<PhoneValidation | null>(null)
  const [validating, setValidating] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const [otpPhone, setOtpPhone] = useState("")
  const [language, setLanguage] = useState("English")
  const [otpResult, setOtpResult] = useState<OtpRequestResult | null>(null)
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)

  const [code, setCode] = useState("")
  const [verifyResult, setVerifyResult] = useState<OtpVerification | null>(null)
  const [verifying, setVerifying] = useState(false)
  const [verifyError, setVerifyError] = useState<string | null>(null)

  async function handleValidate() {
    const value = phone.trim()
    if (!value) return
    setValidating(true)
    setValidationError(null)
    setValidation(null)
    try {
      setValidation(await codApi.validatePhone(value))
    } catch (err) {
      setValidationError(permissionHint(err))
    } finally {
      setValidating(false)
    }
  }

  async function handleRequestOtp() {
    const value = otpPhone.trim()
    if (!value) return
    setSending(true)
    setSendError(null)
    setOtpResult(null)
    setVerifyResult(null)
    try {
      setOtpResult(
        await codApi.requestOtp(value, language === "Roman Urdu" ? "ur" : "en"),
      )
    } catch (err) {
      setSendError(permissionHint(err))
    } finally {
      setSending(false)
    }
  }

  async function handleVerifyOtp() {
    const value = otpPhone.trim()
    if (!value || !code.trim()) return
    setVerifying(true)
    setVerifyError(null)
    setVerifyResult(null)
    try {
      setVerifyResult(await codApi.verifyOtp(value, code.trim()))
    } catch (err) {
      setVerifyError(permissionHint(err))
    } finally {
      setVerifying(false)
    }
  }

  const placeholder = healthLoading ? "…" : "—"
  const actionMeta = validation ? ACTION_DISPLAY[validation.action] : null

  const metrics = [
    {
      label: "Delivery Provider",
      value: health ? health.provider : placeholder,
      icon: ShieldCheck,
      tone: "text-success",
      iconTone: "bg-success-light text-success",
    },
    {
      label: "WhatsApp Live",
      value: health ? (health.whatsapp_configured ? "Yes" : "No") : placeholder,
      icon: Smartphone,
      tone: health?.whatsapp_configured ? "text-success" : "text-warning",
      iconTone: health?.whatsapp_configured
        ? "bg-success-light text-success"
        : "bg-warning-light text-warning",
    },
    {
      label: "Code Lifetime",
      value: health ? `${health.otp_ttl_seconds}s` : placeholder,
      icon: KeyRound,
      tone: "text-info",
      iconTone: "bg-info-light text-info",
    },
    {
      label: "Attempts / Hour",
      value: health
        ? `${health.otp_max_attempts} / ${health.otp_rate_limit_per_window}`
        : placeholder,
      icon: Send,
      tone: "text-text-primary",
      iconTone: "bg-surface-3 text-text-secondary",
    },
  ]

  return (
    <Shell
      title="COD Verification"
      subtitle="Pakistani phone sanitization, operator detection and OTP step-up for cash-on-delivery orders."
    >
      <div className="space-y-6">
        {healthError && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-danger-light border border-danger/20">
            <AlertTriangle className="w-4 h-4 text-danger shrink-0" />
            <span className="text-sm text-danger" data-testid="cod-health-error">
              COD health endpoint unreachable — no configuration to display.
            </span>
          </div>
        )}

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map((metric) => {
            const Icon = metric.icon
            return (
              <div key={metric.label} className="card" data-testid="cod-health-metric">
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className={`w-9 h-9 rounded-button ${metric.iconTone} flex items-center justify-center`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="label-caps">{metric.label}</span>
                </div>
                <div className={`font-display text-data-lg ${metric.tone}`}>
                  {metric.value}
                </div>
              </div>
            )
          })}
        </div>

        <div className="card">
          <h3 className="label-caps mb-1">Phone Sanitizer</h3>
          <p className="text-sm text-text-secondary mb-4">
            Normalize a checkout number, detect the Pakistani carrier and surface
            fake-number heuristics before the order is accepted.
          </p>

          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="03214567890 or +923214567890"
              aria-label="Phone number"
              data-testid="cod-validate-input"
              onKeyDown={(e) => {
                if (e.key === "Enter") void handleValidate()
              }}
            />
            <button
              onClick={() => void handleValidate()}
              disabled={validating || !phone.trim()}
              className="btn-primary shrink-0"
              data-testid="cod-validate-button"
            >
              {validating && <Loader2 className="w-4 h-4 animate-spin" />}
              Validate
            </button>
          </div>

          {validationError && (
            <div
              className="mt-4 flex items-center gap-2 text-sm text-danger"
              data-testid="cod-validation-error"
            >
              <XCircle className="w-4 h-4 shrink-0" />
              {validationError}
            </div>
          )}

          {validation && actionMeta && (
            <div
              className="mt-4 rounded-card border border-border bg-surface-2 p-4"
              data-testid="cod-validation-result"
            >
              <div className="flex flex-wrap items-center gap-3 mb-3">
                <span className={`badge ${actionMeta.className}`}>{actionMeta.label}</span>
                <span className="font-mono text-sm text-text-primary" data-testid="cod-e164">
                  {validation.e164 || "no E.164 form"}
                </span>
                <span className="badge badge-muted" data-testid="cod-operator">
                  {OPERATOR_LABELS[validation.operator] ?? validation.operator}
                </span>
                <span className="badge badge-muted">
                  risk: {validation.risk_level}
                </span>
              </div>

              <div className="text-sm text-text-secondary">
                {validation.is_valid ? (
                  <span data-testid="cod-validity">Structurally valid.</span>
                ) : (
                  <span data-testid="cod-validity">
                    Not deliverable as written — normalized to{" "}
                    <span className="font-mono">{validation.normalized || "—"}</span>.
                  </span>
                )}
              </div>

              <div className="mt-3">
                <span className="label-caps">Risk Signals</span>
                <div
                  className="mt-2 flex flex-wrap gap-2"
                  data-testid="cod-risk-signals"
                >
                  {validation.risk_signals.length === 0 ? (
                    <span className="text-sm text-text-muted">None</span>
                  ) : (
                    validation.risk_signals.map((signal) => (
                      <span key={signal} className="badge badge-warning">
                        {signal}
                      </span>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <div className="flex flex-wrap items-start justify-between gap-3 mb-1">
            <div>
              <h3 className="label-caps">OTP Step-Up Challenge</h3>
              <p className="text-sm text-text-secondary mt-1">
                Issue a one-time passcode to a flagged number. A failed or refused
                send never persists a code.
              </p>
            </div>
            <FilterTabs
              filters={["English", "Roman Urdu"]}
              active={language}
              onChange={setLanguage}
            />
          </div>

          <div className="flex flex-col sm:flex-row gap-3 mt-4">
            <Input
              value={otpPhone}
              onChange={(e) => setOtpPhone(e.target.value)}
              placeholder="03214567890"
              aria-label="OTP phone number"
              data-testid="cod-otp-phone"
            />
            <button
              onClick={() => void handleRequestOtp()}
              disabled={sending || !otpPhone.trim()}
              className="btn-outline shrink-0"
              data-testid="cod-otp-send"
            >
              {sending && <Loader2 className="w-4 h-4 animate-spin" />}
              Send Code
            </button>
          </div>

          {sendError && (
            <div
              className="mt-3 flex items-center gap-2 text-sm text-danger"
              data-testid="cod-send-error"
            >
              <XCircle className="w-4 h-4 shrink-0" />
              {sendError}
            </div>
          )}

          {otpResult && (
            <div
              className="mt-3 rounded-card border border-border bg-surface-2 p-4"
              data-testid="cod-otp-result"
            >
              <div className="flex flex-wrap items-center gap-3">
                <span
                  className={`badge ${otpResult.sent ? "badge-success" : "badge-warning"}`}
                >
                  {otpResult.sent ? "Sent" : "Not Sent"}
                </span>
                <span className="text-sm text-text-secondary">
                  reason: <span className="font-mono">{otpResult.reason}</span>
                </span>
                {otpResult.sent && (
                  <span className="text-sm text-text-secondary">
                    expires in {otpResult.expires_in}s via {otpResult.provider}
                  </span>
                )}
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3 mt-4">
            <Input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="123456"
              aria-label="Verification code"
              inputMode="numeric"
              maxLength={16}
              data-testid="cod-code-input"
            />
            <button
              onClick={() => void handleVerifyOtp()}
              disabled={verifying || !code.trim() || !otpPhone.trim()}
              className="btn-outline shrink-0"
              data-testid="cod-verify-button"
            >
              {verifying && <Loader2 className="w-4 h-4 animate-spin" />}
              Verify
            </button>
          </div>

          {verifyError && (
            <div
              className="mt-3 flex items-center gap-2 text-sm text-danger"
              data-testid="cod-verify-error"
            >
              <XCircle className="w-4 h-4 shrink-0" />
              {verifyError}
            </div>
          )}

          {verifyResult && (
            <div
              className="mt-3 rounded-card border border-border bg-surface-2 p-4 flex flex-wrap items-center gap-3"
              data-testid="cod-verify-result"
            >
              {verifyResult.verified ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-success" />
                  <span className="badge badge-success">Verified</span>
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4 text-danger" />
                  <span className="badge badge-danger">Rejected</span>
                  <span className="text-sm text-text-secondary">
                    reason: <span className="font-mono">{verifyResult.reason}</span>
                  </span>
                </>
              )}
              <span className="text-sm text-text-secondary">
                {verifyResult.attempts_remaining} attempts left
              </span>
            </div>
          )}
        </div>
      </div>
    </Shell>
  )
}
