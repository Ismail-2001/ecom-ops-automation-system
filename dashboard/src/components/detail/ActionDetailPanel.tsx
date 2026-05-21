import React, { useState, useEffect } from 'react';
import { X, Send, Award, Database, AlertCircle, Ban, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';
import { useUIStore } from '../../store/uiStore';
import { useApprovalQueue } from '../../hooks/useApprovalQueue';
import { getAgentColors, getAgentLabel, getActionTypeLabel } from '../../utils/riskColors';
import { formatCurrency, formatDateTime } from '../../utils/formatters';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { cn } from '../../utils/cn';

import FraudDetail from './FraudDetail';
import InventoryDetail from './InventoryDetail';
import PricingDetail from './PricingDetail';
import ReviewDetail from './ReviewDetail';
import MarketingDetail from './MarketingDetail';

interface ActionDetailPanelProps {
  onToast: (title: string, message: string, type: 'info' | 'success' | 'warning' | 'error') => void;
}

export const ActionDetailPanel: React.FC<ActionDetailPanelProps> = ({ onToast }) => {
  const { selectedActionId, setSelectedActionId } = useUIStore();
  const { actions, approveAction, rejectAction, isApproving, isRejecting } = useApprovalQueue();
  
  const [operatorNotes, setOperatorNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [editedResponseText, setEditedResponseText] = useState<string | undefined>(undefined);

  // Find selected action
  const action = actions.find((a) => a.id === selectedActionId);

  // Reset inputs when selected action changes
  useEffect(() => {
    setOperatorNotes('');
    setRejectionReason('');
    setShowRejectInput(false);
    setEditedResponseText(undefined);
  }, [selectedActionId]);

  if (!selectedActionId) return null;
  if (!action) {
    return (
      <motion.aside 
        initial={{ x: 500, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 500, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="w-[480px] bg-card/90 border-l border-white/5 flex flex-col h-full shadow-2xl relative z-30 backdrop-blur-xl"
      >
        <button 
          onClick={() => setSelectedActionId(null)}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
        <div className="flex-1 flex items-center justify-center p-6 text-slate-400">
          <AlertCircle className="w-6 h-6 mr-2" />
          <span>Action not found.</span>
        </div>
      </motion.aside>
    );
  }

  const agentColors = getAgentColors(action.agent);
  const isPending = action.status === 'pending';

  const handleApprove = async () => {
    try {
      await approveAction({
        id: action.id,
        notes: operatorNotes || undefined,
        draft_response: editedResponseText,
      });
      onToast(
        'Action Approved', 
        `Successfully executing ${getActionTypeLabel(action.action_type)} command.`, 
        'success'
      );
      setSelectedActionId(null);
    } catch (e) {
      console.error(e);
      onToast('Error', 'Failed to approve this action. Check logs.', 'error');
    }
  };

  const handleReject = async () => {
    if (!rejectionReason.trim()) {
      onToast('Reason Required', 'Please specify a reason for rejecting this action.', 'warning');
      return;
    }

    try {
      await rejectAction({
        id: action.id,
        reason: rejectionReason,
        notes: operatorNotes || undefined,
      });
      onToast('Action Rejected', `Rejected ${getActionTypeLabel(action.action_type)} decision.`, 'info');
      setSelectedActionId(null);
    } catch (e) {
      console.error(e);
      onToast('Error', 'Failed to reject this action.', 'error');
    }
  };

  // Render correct subcomponent
  const renderAgentPayload = () => {
    switch (action.agent) {
      case 'FraudAgent':
        return <FraudDetail payload={action.payload} />;
      case 'InventoryAgent':
        return <InventoryDetail payload={action.payload} />;
      case 'PricingAgent':
        return <PricingDetail payload={action.payload} />;
      case 'ReviewsAgent':
        return (
          <ReviewDetail 
            payload={action.payload} 
            onChangeDraft={(text) => setEditedResponseText(text)} 
          />
        );
      case 'MarketingAgent':
        return <MarketingDetail payload={action.payload} />;
      default:
        return <pre className="text-xs font-mono">{JSON.stringify(action.payload, null, 2)}</pre>;
    }
  };

  return (
    <motion.aside 
      initial={{ x: 500, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 500, opacity: 0 }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="w-[500px] bg-card/90 border-l border-white/5 flex flex-col h-full shadow-2xl relative z-30 backdrop-blur-xl"
    >
      {/* Slider Header */}
      <div className="p-6 border-b border-white/5 flex items-center justify-between select-none">
        <div className="flex items-center space-x-3">
          <Badge variant="outline" className={cn("text-[10px] font-bold uppercase tracking-wider border px-2.5 py-0.5", agentColors.border, agentColors.text, "bg-white/5")}>
            {getAgentLabel(action.agent)}
          </Badge>
          <Badge 
            variant={action.risk_level === 'low' ? 'success' : action.risk_level === 'medium' ? 'warning' : 'destructive'}
            className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5"
          >
            {action.risk_level} risk
          </Badge>
        </div>
        <button
          onClick={() => setSelectedActionId(null)}
          className="text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Title */}
        <div>
          <h3 className="text-lg font-black text-slate-100">{getActionTypeLabel(action.action_type)}</h3>
          <p className="text-xs text-slate-500 mt-1">
            Registered: {formatDateTime(action.created_at)}
          </p>
        </div>

        <hr className="border-white/5" />

        {/* 1. Payload Details */}
        {renderAgentPayload()}

        {/* 2. Impact Estimator */}
        {action.impact && (
          <Card className="bg-black/20 border-white/5 p-4 space-y-3 select-none">
            <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider flex items-center">
              <ShieldCheck className="w-4 h-4 mr-2 text-accent" />
              Impact Estimation
            </h4>
            <hr className="border-white/5" />
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-550">Financial Impact</span>
                <span className={cn("font-bold text-sm", action.impact.financial_impact && action.impact.financial_impact >= 0 ? 'text-emerald-400' : 'text-red-400')}>
                  {formatCurrency(action.impact.financial_impact)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-550">Affected Scope</span>
                <span className="text-slate-300 font-semibold">
                  {action.impact.affected_skus.length > 0 
                    ? `${action.impact.affected_skus.length} SKU(s)` 
                    : `${action.impact.affected_orders.length} Order(s)`}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-550">Reversible?</span>
                <span className="text-slate-300 font-semibold">
                  {action.impact.reversible 
                    ? `Yes, within ${action.impact.reversal_window_hours || 24} hours` 
                    : 'No (Immutable)'}
                </span>
              </div>
            </div>
          </Card>
        )}

        {/* 3. Evidence Log Metrics */}
        {action.evidence && action.evidence.length > 0 && (
          <div className="space-y-3 select-none">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
              <Database className="w-4 h-4 mr-2 text-accent" />
              Decisive Evidence Logs
            </h4>
            <div className="grid grid-cols-1 gap-2">
              {action.evidence.map((ev, index) => (
                <div key={index} className="bg-black/30 border border-white/5 p-3 rounded-lg flex items-center justify-between text-xs">
                  <div>
                    <span className="text-slate-500 font-medium block text-[10px] uppercase tracking-wider">
                      {ev.label} ({ev.source})
                    </span>
                    <span className="text-slate-200 mt-1 font-bold block">{ev.value}</span>
                  </div>
                  <Badge variant={ev.weight === 'primary' ? 'default' : 'outline'} className="text-[9px] font-bold px-1.5 py-0.5">
                    {ev.weight}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Decision Footer Panel */}
      <div className="p-6 border-t border-white/5 bg-black/20">
        {isPending ? (
          <div className="space-y-4">
            {showRejectInput ? (
              <div className="space-y-3">
                <label className="text-[10px] text-red-400 font-bold uppercase tracking-wider block">
                  Rejection Justification (Required)
                </label>
                <textarea
                  placeholder="Specify why you are rejecting this decision (e.g. Price fluctuation updated, False fraud flag)..."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  className="w-full bg-black/45 border border-white/10 focus:border-red-500 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none min-h-[80px] transition-colors duration-250"
                />
                <div className="flex space-x-2">
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setShowRejectInput(false);
                      setRejectionReason('');
                    }}
                    className="flex-1 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                  >
                    Back
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleReject}
                    disabled={isRejecting}
                    className="flex-1 py-2 text-xs font-semibold"
                  >
                    {isRejecting ? 'Rejecting...' : 'Confirm Reject'}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">
                    Operator Audit Notes (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="Add operational notes for audit..."
                    value={operatorNotes}
                    onChange={(e) => setOperatorNotes(e.target.value)}
                    className="w-full bg-black/45 border border-white/10 focus:border-accent rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none transition-all duration-200"
                  />
                </div>

                <div className="flex space-x-3">
                  <Button
                    variant="destructive"
                    onClick={() => setShowRejectInput(true)}
                    className="flex-1 py-2.5 text-xs font-semibold flex items-center justify-center h-10"
                  >
                    <Ban className="w-3.5 h-3.5 mr-1.5" />
                    Reject Action
                  </Button>
                  <Button
                    variant="default"
                    onClick={handleApprove}
                    disabled={isApproving}
                    className="flex-1 py-2.5 text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-white border-emerald-500/20 shadow-lg shadow-emerald-500/10 flex items-center justify-center h-10"
                  >
                    <Send className="w-3.5 h-3.5 mr-1.5" />
                    {isApproving ? 'Executing...' : 'Approve & Run'}
                  </Button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Immutable Decision Logs Panel */
          <Card className="bg-black/35 border-white/5 p-4 rounded-xl space-y-3 select-none">
            <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider flex items-center">
              <Award className="w-4 h-4 mr-2 text-accent" />
              Immutable Decision Log
            </h4>
            <hr className="border-white/5" />
            <div className="space-y-2 text-xs leading-relaxed">
              <div className="flex justify-between">
                <span className="text-slate-500">Review Status</span>
                <Badge variant={action.status === 'executed' ? 'success' : action.status === 'rejected' ? 'destructive' : 'default'} className="font-bold text-[10px] uppercase px-2 py-0.5 border">
                  {action.status}
                </Badge>
              </div>
              {action.reviewed_by && (
                <div className="flex justify-between">
                  <span className="text-slate-550">Operator ID</span>
                  <span className="text-slate-300 font-semibold font-mono">{action.reviewed_by}</span>
                </div>
              )}
              {action.reviewed_at && (
                <div className="flex justify-between">
                  <span className="text-slate-550">Decided At</span>
                  <span className="text-slate-300 font-semibold">
                    {formatDateTime(action.reviewed_at)}
                  </span>
                </div>
              )}
              {action.rejection_reason && (
                <div className="mt-2">
                  <span className="text-slate-550 block mb-1">Rejection Reason</span>
                  <div className="bg-red-500/5 border border-red-500/25 p-2.5 rounded-lg text-red-400">
                    "{action.rejection_reason}"
                  </div>
                </div>
              )}
              {action.operator_notes && (
                <div className="mt-2">
                  <span className="text-slate-550 block mb-1">Operator Notes</span>
                  <div className="bg-black/30 border border-white/5 p-2.5 rounded-lg text-slate-400 italic">
                    "{action.operator_notes}"
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}
      </div>
    </motion.aside>
  );
};

export default ActionDetailPanel;
