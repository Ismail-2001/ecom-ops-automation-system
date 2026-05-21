import React from 'react';
import { Clock, DollarSign, Check, X, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import type { ApprovalAction } from '../../types/action';
import { getAgentColors, getAgentLabel, getActionTypeLabel } from '../../utils/riskColors';
import { formatCurrency, getCountdown } from '../../utils/formatters';
import { useUIStore } from '../../store/uiStore';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';

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
    <motion.div
      layoutId={`card-${action.id}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ y: -2, transition: { duration: 0.15 } }}
      onClick={handleCardClick}
      className="cursor-pointer mb-4 focus-visible:outline-none"
    >
      <Card
        className={cn(
          "p-5 transition-all duration-300 relative overflow-hidden group select-none",
          isSelected 
            ? "border-accent bg-card/65 shadow-2xl shadow-accent/10 ring-2 ring-accent/30" 
            : "border-white/5 hover:border-white/15 bg-card/40 hover:bg-card/60 shadow-lg",
          isBatchSelected && "bg-accent/5 border-accent/20"
        )}
      >
        {/* Subtle decorative glow when selected */}
        {isSelected && (
          <div className="absolute top-0 right-0 w-48 h-48 bg-accent/5 rounded-full blur-3xl pointer-events-none -mr-16 -mt-16 transition-opacity duration-500" />
        )}

        {/* Top row: Badges and Selection */}
        <div className="flex items-center justify-between mb-3 relative z-10">
          <div className="flex items-center space-x-2">
            {/* Checkbox (Batch Selection) */}
            {canBatchSelect && (
              <input
                type="checkbox"
                checked={isBatchSelected}
                onChange={() => toggleSelectedActionId(action.id)}
                className="mr-1.5 rounded border-white/10 bg-black/40 text-accent focus:ring-accent/20 h-4 w-4 transition-all duration-150 cursor-pointer"
              />
            )}

            {/* Agent Badge */}
            <Badge variant="outline" className={cn("text-[10px] font-semibold tracking-wide uppercase px-2 py-0.5 border", agentColors.border, agentColors.text, "bg-white/5")}>
              {getAgentLabel(action.agent)}
            </Badge>

            {/* Risk Badge */}
            <Badge 
              variant={action.risk_level === 'low' ? 'success' : action.risk_level === 'medium' ? 'warning' : 'destructive'} 
              className="text-[10px] font-semibold tracking-wide uppercase px-2 py-0.5"
            >
              {action.risk_level} risk
            </Badge>
          </div>

          {/* Expiry or Status badge */}
          <div className="flex items-center text-xs">
            {isPending ? (
              timeRemaining && (
                <span className={cn(
                  "inline-flex items-center font-medium tracking-wide text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/5",
                  timeRemaining === 'Expired' ? 'text-red-400 border-red-500/20' : 'text-slate-400'
                )}>
                  <Clock className="w-3.5 h-3.5 mr-1" />
                  {timeRemaining === 'Expired' ? 'EXPIRED' : `TTL: ${timeRemaining}`}
                </span>
              )
            ) : (
              <Badge 
                variant={action.status === 'executed' ? 'success' : action.status === 'rejected' ? 'destructive' : 'default'}
                className="text-[10px] uppercase font-bold px-2 py-0.5 border"
              >
                {action.status}
              </Badge>
            )}
          </div>
        </div>

        {/* Main Details */}
        <div className="mb-4 relative z-10">
          <h3 className="text-sm font-bold text-slate-100 mb-1.5 flex items-center justify-between">
            <span className="group-hover:text-accent transition-colors duration-200">{actionTitle}</span>
            <span className="text-xs text-slate-400 font-normal">{actionSubtitle}</span>
          </h3>
          <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
            {action.payload?.reasoning || action.operator_notes || 'Analyzing e-commerce inventory details to suggest operations metrics.'}
          </p>
        </div>

        {/* Bottom Row: Metrics & Quick Actions */}
        <div className="flex items-center justify-between border-t border-white/5 pt-4 relative z-10">
          {/* Impact Metric & Confidence */}
          <div className="flex items-center space-x-6 text-xs text-slate-400">
            {action.impact?.financial_impact !== undefined && action.impact.financial_impact !== null && (
              <div className="flex items-center">
                <DollarSign className="w-4 h-4 text-emerald-400 mr-0.5" />
                <span className="text-slate-200 font-semibold text-sm">
                  {formatCurrency(Math.abs(action.impact.financial_impact))}
                  <span className="text-[10px] text-slate-500 font-normal ml-1">
                    {action.impact.financial_impact >= 0 ? 'impact' : 'cost'}
                  </span>
                </span>
              </div>
            )}

            <div>
              <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider block mb-0.5">Confidence</span>
              <span className="text-xs font-bold text-slate-200">
                {Math.round(action.confidence_score * 100)}%
              </span>
            </div>
          </div>

          {/* Quick Decision Actions (Pending Only) */}
          <div className="flex items-center space-x-2">
            {isPending ? (
              <>
                <Button
                  variant="destructive"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onReject(action.id);
                  }}
                  className="h-8 w-8 rounded-lg p-0"
                  title="Reject Decision"
                >
                  <X className="w-4 h-4" />
                </Button>
                <Button
                  variant="default"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onApprove(action.id);
                  }}
                  className="h-8 w-8 rounded-lg p-0 bg-emerald-500/10 hover:bg-emerald-500 text-emerald-400 hover:text-white border border-emerald-500/20"
                  title="Approve & Execute"
                >
                  <Check className="w-4 h-4" />
                </Button>
              </>
            ) : (
              <button 
                onClick={() => setSelectedActionId(action.id)}
                className="flex items-center text-xs text-accent font-semibold hover:text-blue-400 transition-colors"
              >
                Logs
                <ChevronRight className="w-4 h-4 ml-0.5 group-hover:translate-x-0.5 transition-transform" />
              </button>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export default ApprovalCard;
