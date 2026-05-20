import React from 'react';
import { Clock, DollarSign, Check, X, ChevronRight } from 'lucide-react';
import type { ApprovalAction } from '../../types/action';
import { getAgentColors, getRiskColors, getAgentLabel, getActionTypeLabel, getStatusColors } from '../../utils/riskColors';
import { formatCurrency, getCountdown } from '../../utils/formatters';
import { useUIStore } from '../../store/uiStore';

interface ApprovalCardProps {
  action: ApprovalAction;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({ action, onApprove, onReject }) => {
  const { 
    selectedActionId, 
    setSelectedActionId, 
    selectedActionIds, 
    toggleSelectedActionId 
  } = useUIStore();

  const isSelected = selectedActionId === action.id;
  const isBatchSelected = selectedActionIds.includes(action.id);
  
  const agentColors = getAgentColors(action.agent);
  const riskColors = getRiskColors(action.risk_level);
  const statusColors = getStatusColors(action.status);
  
  const isPending = action.status === 'pending';
  const isHighRisk = action.risk_level === 'high' || action.risk_level === 'critical';
  const canBatchSelect = isPending && !isHighRisk; // Only allow low/medium risk for batch selection

  // Expiry countdown
  const timeRemaining = getCountdown(action.expires_at);

  // Construct description title
  let actionTitle = getActionTypeLabel(action.action_type);
  let actionSubtitle = '';
  
  if (action.action_type === 'fraud_hold') {
    actionSubtitle = `Order ${action.payload?.order_id || 'Unknown'}`;
  } else if (action.action_type === 'purchase_order') {
    actionSubtitle = `Order ${action.payload?.reorder_quantity || 0}x of ${action.payload?.sku || 'Item'}`;
  } else if (action.action_type === 'price_change') {
    actionSubtitle = `Update ${action.payload?.sku || 'Item'} to ${formatCurrency(action.payload?.proposed_price)}`;
  } else if (action.action_type === 'review_response') {
    actionSubtitle = `Respond to rating ${action.payload?.rating || 0}★ for ${action.payload?.product_name || 'Product'}`;
  } else if (action.action_type === 'marketing_campaign') {
    actionSubtitle = `Discount ${action.payload?.discount_percent || 0}% for ${action.payload?.campaign_name || 'Campaign'}`;
  }

  const handleCardClick = (e: React.MouseEvent) => {
    // Avoid selecting if clicking checkbox or action buttons
    const target = e.target as HTMLElement;
    if (target.closest('input[type="checkbox"]') || target.closest('button')) {
      return;
    }
    setSelectedActionId(action.id);
  };

  return (
    <div
      onClick={handleCardClick}
      className={`bg-slate-900 border rounded-xl p-5 mb-4 hover:border-slate-700 transition-all duration-200 cursor-pointer ${
        isSelected 
          ? 'border-blue-500 shadow-lg shadow-blue-500/5 ring-1 ring-blue-500/20' 
          : 'border-slate-800'
      } ${isBatchSelected ? 'bg-blue-600/5' : ''}`}
    >
      {/* Top row: Badges and Selection */}
      <div className="flex items-center justify-between mb-3 select-none">
        <div className="flex items-center space-x-2">
          {/* Checkbox (Batch Selection) */}
          {canBatchSelect && (
            <input
              type="checkbox"
              checked={isBatchSelected}
              onChange={() => toggleSelectedActionId(action.id)}
              className="mr-2 rounded border-slate-800 bg-slate-950 text-blue-600 focus:ring-blue-500/20 h-4 w-4"
            />
          )}

          {/* Agent Badge */}
          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${agentColors.bg} ${agentColors.text} ${agentColors.border}`}>
            {getAgentLabel(action.agent)}
          </span>

          {/* Risk Badge */}
          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${riskColors.bg} ${riskColors.text} ${riskColors.border}`}>
            {action.risk_level} risk
          </span>
        </div>

        {/* Expiry or Status badge */}
        <div className="flex items-center text-xs">
          {isPending ? (
            timeRemaining && (
              <span className={`inline-flex items-center font-medium ${timeRemaining === 'Expired' ? 'text-red-400' : 'text-slate-400'}`}>
                <Clock className="w-3.5 h-3.5 mr-1" />
                {timeRemaining === 'Expired' ? 'EXPIRED' : `TTL: ${timeRemaining}`}
              </span>
            )
          ) : (
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold border ${statusColors.bg} ${statusColors.text} ${statusColors.border}`}>
              {action.status}
            </span>
          )}
        </div>
      </div>

      {/* Main Details */}
      <div className="mb-4">
        <h3 className="text-sm font-bold text-slate-100 mb-1 flex items-center justify-between">
          <span>{actionTitle}</span>
          <span className="text-xs text-slate-400 font-normal">{actionSubtitle}</span>
        </h3>
        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
          {action.payload?.reasoning || action.operator_notes || 'Analyzing e-commerce inventory details to suggest operations metrics.'}
        </p>
      </div>

      {/* Bottom Row: Metrics & Quick Actions */}
      <div className="flex items-center justify-between border-t border-slate-800/80 pt-4">
        {/* Impact Metric & Confidence */}
        <div className="flex items-center space-x-6 text-xs text-slate-400">
          {action.impact?.financial_impact !== undefined && action.impact.financial_impact !== null && (
            <div className="flex items-center">
              <DollarSign className="w-4 h-4 text-slate-400 mr-1" />
              <span className="text-slate-300 font-medium">
                {formatCurrency(Math.abs(action.impact.financial_impact))}
                <span className="text-[10px] text-slate-500 font-normal ml-1">
                  {action.impact.financial_impact >= 0 ? 'impact' : 'cost'}
                </span>
              </span>
            </div>
          )}

          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Confidence</span>
            <span className="text-xs font-semibold text-slate-300">
              {Math.round(action.confidence_score * 100)}%
            </span>
          </div>
        </div>

        {/* Quick Decision Actions (Pending Only) */}
        <div className="flex items-center space-x-2">
          {isPending ? (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onReject(action.id);
                }}
                className="p-1.5 rounded-lg border border-red-500/20 bg-red-500/5 hover:bg-red-500/10 text-red-400 transition-colors"
                title="Reject Decision"
              >
                <X className="w-4 h-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onApprove(action.id);
                }}
                className="p-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/5 hover:bg-emerald-500/10 text-emerald-400 transition-colors"
                title="Approve & Execute"
              >
                <Check className="w-4 h-4" />
              </button>
            </>
          ) : (
            <button 
              onClick={() => setSelectedActionId(action.id)}
              className="flex items-center text-xs text-blue-400 font-medium hover:text-blue-300 transition-colors"
            >
              Logs
              <ChevronRight className="w-4 h-4 ml-0.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApprovalCard;
