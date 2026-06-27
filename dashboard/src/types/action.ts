export type ActionType =
  | 'fraud_hold'
  | 'purchase_order'
  | 'price_change'
  | 'review_response'
  | 'marketing_campaign';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type ApprovalStatus =
  | 'pending'     // Awaiting human decision
  | 'approved'    // Human approved, queued for execution
  | 'rejected'    // Human rejected
  | 'executing'   // Currently being applied to Shopify
  | 'executed'    // Successfully applied
  | 'failed'      // Execution failed after approval
  | 'expired'     // Not acted on within TTL window
  | 'shadow';     // Shadow mode — logged but not queued

export interface Evidence {
  label: string;
  value: string;
  weight: 'primary' | 'supporting' | 'contextual';
  source: string;
}

export interface ImpactEstimate {
  financial_impact: number | null; // USD, positive = gain, negative = cost
  affected_skus: string[];
  affected_orders: string[];
  reversible: boolean;
  reversal_window_hours: number | null;
}

// Agent payloads
export interface FraudPayload {
  order_id: string;
  customer_name: string;
  customer_email: string;
  order_total: number;
  fraud_score: number;
  risk_signals: string[];
  recommended_action: 'hold' | 'cancel' | 'flag';
}

export interface InventoryPayload {
  sku: string;
  product_name: string;
  current_stock: number;
  daily_velocity: number;
  days_of_supply: number;
  reorder_quantity: number;
  supplier_name: string;
  unit_cost: number;
  total_po_value: number;
}

export interface PricingPayload {
  sku: string;
  product_name: string;
  current_price: number;
  proposed_price: number;
  change_percent: number;
  reasoning: string;
  competitor_prices: { competitor: string; price: number }[];
}

export interface ReviewPayload {
  review_id: string;
  product_name: string;
  rating: number;
  review_text: string;
  customer_name: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  draft_response: string;
  key_issues: string[];
}

export interface MarketingPayload {
  campaign_name: string;
  target_skus: string[];
  discount_percent: number;
  urgency_reason: string;
  estimated_reach: number;
  draft_message: string;
}

export interface ApprovalAction {
  id: string;
  agent: string;
  action_type: ActionType;
  status: ApprovalStatus;
  risk_level: RiskLevel;
  confidence_score: number;
  created_at: string;
  expires_at: string | null;
  requires_hitl: boolean;
  shadow_mode: boolean;
  payload: any; // FraudPayload | InventoryPayload | PricingPayload | ReviewPayload | MarketingPayload
  evidence: Evidence[];
  impact: ImpactEstimate | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  rejection_reason: string | null;
  operator_notes: string | null;
}
