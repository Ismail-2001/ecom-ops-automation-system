import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  healthApi,
  approvalsApi,
  agentsApi,
  analyticsApi,
  auditApi,
  settingsApi,
  pipelineApi,
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
