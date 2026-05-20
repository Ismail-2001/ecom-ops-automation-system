import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { AuditEntry } from '../types/audit';

interface AuditFilters {
  agent: string;
  decision: string;
  operator: string;
  action_type: string;
}

export const useAuditLog = (filters: AuditFilters, page = 1, limit = 20) => {
  const query = useQuery<{ entries: AuditEntry[]; total: number }>({
    queryKey: ['audit', filters, page, limit],
    queryFn: async () => {
      const response = await apiClient.get('/api/audit', {
        params: {
          agent: filters.agent === 'all' ? undefined : filters.agent,
          decision: filters.decision === 'all' ? undefined : filters.decision,
          operator: filters.operator === 'all' ? undefined : filters.operator,
          action_type: filters.action_type === 'all' ? undefined : filters.action_type,
          page,
          limit,
        },
      });
      return response.data;
    },
    refetchInterval: 30000, // 30s cache refresh fallback
  });

  return {
    entries: query.data?.entries || [],
    total: query.data?.total || 0,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
};
