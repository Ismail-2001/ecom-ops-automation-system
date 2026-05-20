import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { AgentStatus } from '../types/agent';

export const useAgentStatus = () => {
  const query = useQuery<AgentStatus[]>({
    queryKey: ['agents-status'],
    queryFn: async () => {
      const response = await apiClient.get('/api/agents/status');
      return response.data;
    },
    refetchInterval: 15000,
  });

  return {
    agents: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
};
