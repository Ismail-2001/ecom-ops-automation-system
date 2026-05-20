import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { ApprovalAction, ApprovalStatus } from '../types/action';
import { useUIStore } from '../store/uiStore';

export const useApprovalQueue = () => {
  const queryClient = useQueryClient();
  const { filters, sort, searchQuery } = useUIStore();

  // Query: Get approval actions
  const approvalsQuery = useQuery<ApprovalAction[]>({
    queryKey: ['approvals', filters, sort, searchQuery],
    queryFn: async () => {
      const response = await apiClient.get('/api/approvals', {
        params: {
          agent: filters.agent,
          risk: filters.risk,
          status: filters.status,
          sort: sort,
          search: searchQuery || undefined,
        },
      });
      return response.data;
    },
    refetchInterval: 15000, // 15s polling fallback if WebSockets are down
  });

  // Mutation: Approve Action (Optimistic UI)
  const approveMutation = useMutation<
    ApprovalAction,
    Error,
    { id: string; notes?: string; draft_response?: string },
    { previousApprovals: ApprovalAction[] | undefined }
  >({
    mutationFn: async ({ id, notes, draft_response }) => {
      const response = await apiClient.post(`/api/approvals/${id}/approve`, {
        notes,
        draft_response,
      });
      return response.data;
    },
    onMutate: async ({ id }) => {
      // Cancel outgoing refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({ queryKey: ['approvals', filters, sort, searchQuery] });

      // Snapshot the previous state
      const previousApprovals = queryClient.getQueryData<ApprovalAction[]>([
        'approvals',
        filters,
        sort,
        searchQuery,
      ]);

      // Optimistically update the status to "executing"
      if (previousApprovals) {
        queryClient.setQueryData<ApprovalAction[]>(
          ['approvals', filters, sort, searchQuery],
          previousApprovals.map((action) =>
            action.id === id ? { ...action, status: 'executing' as ApprovalStatus } : action
          )
        );
      }

      return { previousApprovals };
    },
    onError: (_err, _variables, context) => {
      // Rollback to previous state on error
      if (context?.previousApprovals) {
        queryClient.setQueryData(
          ['approvals', filters, sort, searchQuery],
          context.previousApprovals
        );
      }
    },
    onSuccess: (data) => {
      // Update cache with the actual result from the server
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['approval', data.id] });
      queryClient.invalidateQueries({ queryKey: ['audit'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });

  // Mutation: Reject Action (Optimistic UI)
  const rejectMutation = useMutation<
    ApprovalAction,
    Error,
    { id: string; reason: string; notes?: string },
    { previousApprovals: ApprovalAction[] | undefined }
  >({
    mutationFn: async ({ id, reason, notes }) => {
      const response = await apiClient.post(`/api/approvals/${id}/reject`, {
        reason,
        notes,
      });
      return response.data;
    },
    onMutate: async ({ id }) => {
      await queryClient.cancelQueries({ queryKey: ['approvals', filters, sort, searchQuery] });

      const previousApprovals = queryClient.getQueryData<ApprovalAction[]>([
        'approvals',
        filters,
        sort,
        searchQuery,
      ]);

      // Optimistically remove from list (if status is pending and we only view pending)
      if (previousApprovals) {
        if (filters.status === 'pending') {
          queryClient.setQueryData<ApprovalAction[]>(
            ['approvals', filters, sort, searchQuery],
            previousApprovals.filter((action) => action.id !== id)
          );
        } else {
          queryClient.setQueryData<ApprovalAction[]>(
            ['approvals', filters, sort, searchQuery],
            previousApprovals.map((action) =>
              action.id === id ? { ...action, status: 'rejected' as ApprovalStatus } : action
            )
          );
        }
      }

      return { previousApprovals };
    },
    onError: (_err, _variables, context) => {
      if (context?.previousApprovals) {
        queryClient.setQueryData(
          ['approvals', filters, sort, searchQuery],
          context.previousApprovals
        );
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['audit'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });

  // Mutation: Batch Actions (Optimistic UI)
  const batchMutation = useMutation<
    any,
    Error,
    { ids: string[]; action: 'approve' | 'reject'; reason?: string; notes?: string },
    { previousApprovals: ApprovalAction[] | undefined }
  >({
    mutationFn: async (variables) => {
      const response = await apiClient.post('/api/approvals/batch', variables);
      return response.data;
    },
    onMutate: async ({ ids, action }) => {
      await queryClient.cancelQueries({ queryKey: ['approvals', filters, sort, searchQuery] });

      const previousApprovals = queryClient.getQueryData<ApprovalAction[]>([
        'approvals',
        filters,
        sort,
        searchQuery,
      ]);

      if (previousApprovals) {
        if (filters.status === 'pending') {
          // Remove them optimistically from pending list
          queryClient.setQueryData<ApprovalAction[]>(
            ['approvals', filters, sort, searchQuery],
            previousApprovals.filter((a) => !ids.includes(a.id))
          );
        } else {
          const targetStatus: ApprovalStatus = action === 'approve' ? 'executed' : 'rejected';
          queryClient.setQueryData<ApprovalAction[]>(
            ['approvals', filters, sort, searchQuery],
            previousApprovals.map((a) =>
              ids.includes(a.id) ? { ...a, status: targetStatus } : a
            )
          );
        }
      }

      return { previousApprovals };
    },
    onError: (_err, _variables, context) => {
      if (context?.previousApprovals) {
        queryClient.setQueryData(
          ['approvals', filters, sort, searchQuery],
          context.previousApprovals
        );
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['audit'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });

  // Mutation: Run Pipeline
  const runPipelineMutation = useMutation<any, Error, void>({
    mutationFn: async () => {
      const response = await apiClient.post('/api/run');
      return response.data;
    },
  });

  return {
    actions: approvalsQuery.data || [],
    isLoading: approvalsQuery.isLoading,
    isError: approvalsQuery.isError,
    error: approvalsQuery.error,
    refetch: approvalsQuery.refetch,
    
    // Mutations
    approveAction: approveMutation.mutateAsync,
    isApproving: approveMutation.isPending,
    
    rejectAction: rejectMutation.mutateAsync,
    isRejecting: rejectMutation.isPending,
    
    batchActions: batchMutation.mutateAsync,
    isBatchMutating: batchMutation.isPending,
    
    runPipeline: runPipelineMutation.mutateAsync,
    isPipelineTriggering: runPipelineMutation.isPending,
  };
};
