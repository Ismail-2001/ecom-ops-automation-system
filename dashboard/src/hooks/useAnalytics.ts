import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';

export interface AnalyticsData {
  summary: {
    total_decisions: number;
    approval_rate: number;
    actions_auto_approved: number;
    total_financial_impact: number;
    avg_confidence: number;
    avg_decision_time_minutes: number;
  };
  graduation: {
    agent_id: string;
    streak: number;
    autonomy_level: 'shadow' | 'supervised' | 'autonomous';
    total_decisions: number;
    avg_confidence: number;
  }[];
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  charts: {
    approval_rate_over_time: {
      date: string;
      FraudAgent: number;
      InventoryAgent: number;
      PricingAgent: number;
      ReviewsAgent: number;
      MarketingAgent: number;
    }[];
    volume_by_agent: {
      day: string;
      Fraud: number;
      Inventory: number;
      Pricing: number;
      Reviews: number;
      Marketing: number;
    }[];
    decision_time_dist: {
      under_1m: number;
      '1m_5m': number;
      '5m_30m': number;
      over_30m: number;
    };
  };
}

export const useAnalytics = () => {
  const query = useQuery<AnalyticsData>({
    queryKey: ['analytics'],
    queryFn: async () => {
      const response = await apiClient.get('/api/analytics');
      return response.data;
    },
    refetchInterval: 60000, // Refresh analytics once a minute
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
};
