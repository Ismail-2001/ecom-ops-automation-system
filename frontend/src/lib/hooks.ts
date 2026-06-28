import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  healthApi,
  approvalsApi,
  agentsApi,
  analyticsApi,
  auditApi,
  settingsApi,
  pipelineApi,
  securityApi,
  supportApi,
  cartRecoveryApi,
  shopifyApi,
  type ApprovalsQuery,
} from "./api"

// ── Health ─────────────────────────────────────────────────

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: healthApi.check,
    refetchInterval: 15_000,
    staleTime: 5_000,
    retry: 2,
  })
}

// ── Approvals ──────────────────────────────────────────────

export function useApprovals(query?: ApprovalsQuery) {
  return useQuery({
    queryKey: ["approvals", query],
    queryFn: () => approvalsApi.list(query),
    refetchInterval: 30_000,
    staleTime: 10_000,
  })
}

export function useApproveAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      approvalsApi.approve(id, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] })
      qc.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}

export function useRejectAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      approvalsApi.reject(id, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] })
      qc.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}

export function useBatchApprove() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      ids,
      action,
      reason,
    }: {
      ids: string[]
      action: "approve" | "reject"
      reason?: string
    }) => approvalsApi.batch(ids, action, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] })
      qc.invalidateQueries({ queryKey: ["analytics"] })
    },
  })
}

// ── Agents ─────────────────────────────────────────────────

export function useAgentStatus() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: agentsApi.status,
    refetchInterval: 30_000,
    staleTime: 10_000,
  })
}

// ── Analytics ──────────────────────────────────────────────

export function useAnalytics() {
  return useQuery({
    queryKey: ["analytics"],
    queryFn: analyticsApi.get,
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

// ── Audit ──────────────────────────────────────────────────

export function useAuditLog(params?: { page?: number; limit?: number; agent?: string }) {
  return useQuery({
    queryKey: ["audit", params],
    queryFn: () => auditApi.list(params),
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

// ── Settings ───────────────────────────────────────────────

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: settingsApi.get,
    staleTime: 60_000,
  })
}

export function useUpdateSettings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (patch: Parameters<typeof settingsApi.update>[0]) =>
      settingsApi.update(patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings"] })
    },
  })
}

// ── Pipeline ───────────────────────────────────────────────

export function useRunPipeline() {
  return useMutation({
    mutationFn: pipelineApi.run,
  })
}

export function useTaskStatus(taskId: string | null) {
  return useQuery({
    queryKey: ["task", taskId],
    queryFn: () => pipelineApi.taskStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === "completed" || status === "failed") return false
      return 2_000
    },
  })
}

// ── Security ────────────────────────────────────────────────

export function useSecurityUsers(params?: { role?: string; is_active?: boolean }) {
  return useQuery({
    queryKey: ["security", "users", params],
    queryFn: () => securityApi.listUsers(params),
    staleTime: 30_000,
  })
}

export function useSecurityApiKeys() {
  return useQuery({
    queryKey: ["security", "api-keys"],
    queryFn: securityApi.listApiKeys,
    staleTime: 30_000,
  })
}

export function useSecurityAuditSummary(hours = 24) {
  return useQuery({
    queryKey: ["security", "audit-summary", hours],
    queryFn: () => securityApi.getAuditSummary(hours),
    staleTime: 30_000,
  })
}

export function useSecurityAuditLogs(params?: { event_type?: string; limit?: number }) {
  return useQuery({
    queryKey: ["security", "audit-logs", params],
    queryFn: () => securityApi.getAuditLogs(params),
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

// ── Support ─────────────────────────────────────────────────

export function useSupportTickets(params?: { status?: string; priority?: string; page?: number; limit?: number }) {
  return useQuery({
    queryKey: ["support", "tickets", params],
    queryFn: () => supportApi.listTickets(params),
    refetchInterval: 30_000,
    staleTime: 10_000,
  })
}

export function useSupportTicket(id: string | null) {
  return useQuery({
    queryKey: ["support", "ticket", id],
    queryFn: () => supportApi.getTicket(id!),
    enabled: !!id,
    staleTime: 10_000,
  })
}

export function useSupportAnalytics(days = 7) {
  return useQuery({
    queryKey: ["support", "analytics", days],
    queryFn: () => supportApi.getAnalytics(days),
    staleTime: 60_000,
  })
}

// ── Cart Recovery ───────────────────────────────────────────

export function useCartRecoveryAnalytics(days = 7) {
  return useQuery({
    queryKey: ["cart-recovery", "analytics", days],
    queryFn: () => cartRecoveryApi.getAnalytics(days),
    staleTime: 60_000,
  })
}

export function useCartRecover() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ cartId, strategy }: { cartId: string; strategy: string }) =>
      cartRecoveryApi.recover(cartId, strategy),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cart-recovery"] })
    },
  })
}

// ── Shopify ─────────────────────────────────────────────────

export function useShopifyStatus() {
  return useQuery({
    queryKey: ["shopify", "status"],
    queryFn: shopifyApi.status,
    staleTime: 30_000,
  })
}

export function useShopifySync() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (full?: boolean) => shopifyApi.sync(full),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["shopify"] })
    },
  })
}
