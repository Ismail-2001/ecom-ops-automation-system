import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { StoreSettings } from '../types/agent';

export const useSettings = () => {
  const queryClient = useQueryClient();

  // Query: Get store settings
  const settingsQuery = useQuery<StoreSettings>({
    queryKey: ['settings'],
    queryFn: async () => {
      const response = await apiClient.get('/api/settings');
      return response.data;
    },
  });

  // Mutation: Patch store settings
  const updateSettingsMutation = useMutation<StoreSettings, Error, Partial<StoreSettings>>({
    mutationFn: async (settings) => {
      const response = await apiClient.patch('/api/settings', settings);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate settings query and agent status query (since shadow mode syncs autonomy level)
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      queryClient.invalidateQueries({ queryKey: ['agents-status'] });
    },
  });

  return {
    settings: settingsQuery.data,
    isLoading: settingsQuery.isLoading,
    isError: settingsQuery.isError,
    error: settingsQuery.error,
    
    // Mutations
    updateSettings: updateSettingsMutation.mutateAsync,
    isUpdating: updateSettingsMutation.isPending,
  };
};
