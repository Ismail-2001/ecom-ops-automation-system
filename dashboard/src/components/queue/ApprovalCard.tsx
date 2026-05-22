import React from 'react';
import { Clock, DollarSign, Check, X, ChevronRight, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import type { ApprovalAction } from '../../types/action';
import { getAgentLabel, getActionTypeLabel } from '../../utils/riskColors';
import { formatCurrency, getCountdown } from '../../utils/formatters';
import { useUIStore } from '../../store/uiStore';

interface ApprovalCardProps {
  action: ApprovalAction;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

const riskStyle = (level: string) => {
  switch (level) {
    case 'critical': return { bg: 'rgba(244,63,94,0.12)', color: '#fb7185', border: 'rgba(244,63,94,0.25)', glow: 'rgba(244,63,94,0.15)' };
    case 'high':     return { bg: 'rgba(245,158,11,0.12)', color: '#fbbf24', border: 'rgba(245,158,11,0.25)', glow: 'rgba(245,158,11,0.15)' };
    case 'medium':   return { bg: 'rgba(139,92,246,0.12)', color: '#a78bfa', border: 'rgba(139,92,246,0.25)', glow: 'rgba(139,92,246,0.1)' };
    default:         return { bg: 'rgba(16,185,129,0.12)', color: '#34d399', border: 'rgba(16,185,129,0.25)', glow: 'rgba(16,185,129,0.1)' };
  }
};

export const ApprovalCard: React.FC<ApprovalCardProps> = ({ action, onApprove, onReject }) => {
  const { selectedActionId, setSelectedActionId, selectedActionIds, toggleSelectedActionId } = useUIStore();

  const isSelected = selectedActionId === action.id;
  const isBatchSelected = selectedActionIds.includes(action.id);
  const isPending = action.status === 'pending';
  const isHighRisk = action.risk_level === 'high' || action.risk_level === 'critical';
  const canBatchSelect = isPending && !isHighRisk;
  const timeRemaining = getCountdown(action.expires_at);
  const risk = riskStyle(action.risk_level);


  let actionTitle = getActionTypeLabel(action.action_type);
  let actionSubtitle = '';
  if (action.action_type === 'fraud_hold') actionSubtitle = `Order ${action.payload?.order_id || 'Unknown'}`;
  else if (action.action_type === 'purchase_order') actionSubtitle = `${action.payload?.reorder_quantity || 0}× ${action.payload?.sku || 'Item'}`;
  else if (action.action_type === 'price_change') actionSubtitle = `${action.payload?.sku || 'Item'} → ${formatCurrency(action.payload?.proposed_price)}`;
  else if (action.action_type === 'review_response') actionSubtitle = `${action.payload?.rating || 0}★ · ${action.payload?.product_name || 'Product'}`;
  else if (action.action_type === 'marketing_campaign') actionSubtitle = `${action.payload?.discount_percent || 0}% · ${action.payload?.campaign_name || 'Campaign'}`;

  const cardBg = isSelected
    ? 'rgba(37,99,235,0.08)'
    : isBatchSelected
    ? 'rgba(37,99,235,0.05)'
    : 'rgba(13,17,23,0.7)';

  const cardBorder = isSelected
    ? 'rgba(59,130,246,0.35)'
    : isBatchSelected
    ? 'rgba(59,130,246,0.2)'
    : 'rgba(255,255,255,0.06)';

  const cardShadow = isSelected
    ? '0 0 0 1px rgba(59,130,246,0.2), 0 8px 32px rgba(37,99,235,0.15)'
    : '0 2px 12px rgba(0,0,0,0.4)';

  return (
    <motion.div
      layoutId={`card-${action.id}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.18 }}
      onClick={() => setSelectedActionId(action.id)}
      style={{ cursor: 'pointer', marginBottom: '10px' }}
    >
      <div
        style={{
          background: cardBg,
          backdropFilter: 'blur(20px) saturate(160%)',
          border: `1px solid ${cardBorder}`,
          borderRadius: '14px',
          boxShadow: cardShadow,
          padding: '16px 18px',
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.2s ease',
        }}
      >
        {/* Glow accent for selected */}
        {isSelected && (
          <div style={{
            position: 'absolute', top: '-40px', right: '-40px',
            width: '160px', height: '160px',
            background: 'radial-gradient(circle, rgba(37,99,235,0.15) 0%, transparent 70%)',
            pointerEvents: 'none',
          }} />
        )}

        {/* Risk left border accent */}
        {(action.risk_level === 'critical' || action.risk_level === 'high') && (
          <div style={{
            position: 'absolute', left: 0, top: '16px', bottom: '16px',
            width: '3px', borderRadius: '0 2px 2px 0',
            background: risk.color,
            boxShadow: `0 0 8px ${risk.glow}`,
          }} />
        )}

        {/* Row 1: Badges + expiry */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {canBatchSelect && (
              <input
                type="checkbox"
                checked={isBatchSelected}
                onChange={() => toggleSelectedActionId(action.id)}
                onClick={(e) => e.stopPropagation()}
                style={{ width: '14px', height: '14px', accentColor: '#2563eb', cursor: 'pointer' }}
              />
            )}

            {/* Agent badge */}
            <span style={{
              fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em',
              padding: '2px 8px', borderRadius: '5px',
              background: 'rgba(59,130,246,0.1)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.2)',
            }}>
              {getAgentLabel(action.agent)}
            </span>

            {/* Risk badge */}
            <span style={{
              fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em',
              padding: '2px 8px', borderRadius: '5px',
              background: risk.bg, color: risk.color, border: `1px solid ${risk.border}`,
              boxShadow: `0 0 8px ${risk.glow}`,
            }}>
              {action.risk_level === 'critical' && <AlertTriangle size={9} style={{ display: 'inline', marginRight: '3px', verticalAlign: 'middle' }} />}
              {action.risk_level}
            </span>
          </div>

          {/* Expiry / Status */}
          <div>
            {isPending ? (
              timeRemaining && (
                <span style={{
                  fontSize: '10px', fontWeight: 600,
                  padding: '2px 8px', borderRadius: '999px',
                  background: timeRemaining === 'Expired' ? 'rgba(244,63,94,0.1)' : 'rgba(255,255,255,0.05)',
                  color: timeRemaining === 'Expired' ? '#fb7185' : '#64748b',
                  border: `1px solid ${timeRemaining === 'Expired' ? 'rgba(244,63,94,0.2)' : 'rgba(255,255,255,0.08)'}`,
                  display: 'flex', alignItems: 'center', gap: '4px',
                }}>
                  <Clock size={9} />
                  {timeRemaining === 'Expired' ? 'EXPIRED' : timeRemaining}
                </span>
              )
            ) : (
              <span style={{
                fontSize: '10px', fontWeight: 700, textTransform: 'uppercase',
                padding: '2px 8px', borderRadius: '5px',
                background: action.status === 'executed' ? 'rgba(16,185,129,0.1)' : action.status === 'rejected' ? 'rgba(244,63,94,0.1)' : 'rgba(255,255,255,0.05)',
                color: action.status === 'executed' ? '#34d399' : action.status === 'rejected' ? '#fb7185' : '#94a3b8',
                border: `1px solid ${action.status === 'executed' ? 'rgba(16,185,129,0.2)' : action.status === 'rejected' ? 'rgba(244,63,94,0.2)' : 'rgba(255,255,255,0.08)'}`,
              }}>
                {action.status}
              </span>
            )}
          </div>
        </div>

        {/* Row 2: Title + subtitle */}
        <div style={{ marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '5px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>{actionTitle}</h3>
            <span style={{ fontSize: '11px', color: '#475569', fontFamily: 'JetBrains Mono, monospace' }}>{actionSubtitle}</span>
          </div>
          <p style={{ fontSize: '12px', color: '#64748b', lineHeight: '1.55', margin: 0, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {action.payload?.reasoning || action.operator_notes || 'AI agent analyzed store data and proposed this operational change.'}
          </p>
        </div>

        {/* Confidence bar */}
        <div style={{ marginBottom: '14px' }}>
          <div style={{ height: '2px', borderRadius: '1px', background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.round(action.confidence_score * 100)}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              style={{
                height: '100%', borderRadius: '1px',
                background: action.confidence_score > 0.8
                  ? 'linear-gradient(90deg, #10b981, #34d399)'
                  : action.confidence_score > 0.6
                  ? 'linear-gradient(90deg, #2563eb, #7c3aed)'
                  : 'linear-gradient(90deg, #f59e0b, #fb7185)',
                boxShadow: '0 0 6px rgba(37,99,235,0.4)',
              }}
            />
          </div>
        </div>

        {/* Row 3: Metrics + actions */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {action.impact?.financial_impact != null && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                <DollarSign size={14} color="#34d399" />
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>
                  {formatCurrency(Math.abs(action.impact.financial_impact))}
                </span>
                <span style={{ fontSize: '10px', color: '#475569', marginLeft: '2px' }}>
                  {action.impact.financial_impact >= 0 ? 'impact' : 'cost'}
                </span>
              </div>
            )}
            <div>
              <div style={{ fontSize: '9px', color: '#475569', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1px' }}>Confidence</div>
              <div style={{ fontSize: '13px', fontWeight: 700, color: action.confidence_score > 0.8 ? '#34d399' : action.confidence_score > 0.6 ? '#60a5fa' : '#fbbf24' }}>
                {Math.round(action.confidence_score * 100)}%
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {isPending ? (
              <>
                <button
                  onClick={(e) => { e.stopPropagation(); onReject(action.id); }}
                  title="Reject"
                  style={{
                    width: '32px', height: '32px', borderRadius: '8px',
                    background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.25)',
                    color: '#fb7185', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'rgba(244,63,94,0.25)'; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'rgba(244,63,94,0.1)'; }}
                >
                  <X size={14} />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); onApprove(action.id); }}
                  title="Approve & Execute"
                  style={{
                    width: '32px', height: '32px', borderRadius: '8px',
                    background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)',
                    color: '#34d399', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = '#10b981'; (e.currentTarget as HTMLElement).style.color = '#fff'; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'rgba(16,185,129,0.1)'; (e.currentTarget as HTMLElement).style.color = '#34d399'; }}
                >
                  <Check size={14} />
                </button>
              </>
            ) : (
              <button
                onClick={() => setSelectedActionId(action.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '3px',
                  fontSize: '12px', fontWeight: 600, color: '#60a5fa',
                  background: 'none', border: 'none', cursor: 'pointer', padding: '4px 6px',
                }}
              >
                Logs <ChevronRight size={13} />
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default ApprovalCard;
