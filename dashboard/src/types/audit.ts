export interface AuditEntry {
  id: number;
  action_id: string | null;
  timestamp: string;
  agent: string;
  action_type: string;
  decision: 'approved' | 'rejected' | 'auto-approved' | 'shadow';
  operator: string | null;
  confidence_score: number;
  financial_impact: number | null;
  details: any;
}
