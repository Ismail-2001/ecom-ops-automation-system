export interface AgentMetrics {
  total_decisions: number;
  total_approvals: number;
  total_rejections: number;
  avg_confidence: number;
}

export interface AgentStatus {
  agent_id: string; // "FraudAgent", "InventoryAgent", etc.
  status: 'active' | 'paused';
  streak: number; // Consecutive approvals toward 50
  autonomy_level: 'shadow' | 'supervised' | 'autonomous';
  total_decisions: number;
  total_approvals: number;
  total_rejections: number;
  avg_confidence: number;
}
export interface StoreSettings {
  id: number;
  shadow_mode: boolean;
  fraud_threshold: number;
  po_limit: number;
  pricing_limit: number;
  reviews_rating_threshold: number;
}
