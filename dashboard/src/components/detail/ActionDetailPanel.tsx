import React, { useState, useEffect } from 'react';
import { X, Send, Award, Database, AlertCircle, Ban, ShieldCheck } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { useApprovalQueue } from '../../hooks/useApprovalQueue';
import { getAgentColors, getRiskColors, getAgentLabel, getActionTypeLabel } from '../../utils/riskColors';
import { formatCurrency, formatDateTime } from '../../utils/formatters';

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
      <aside className="w-[480px] bg-slate-900 border-l border-slate-800 flex flex-col h-full shadow-2xl relative">
        <button 
          onClick={() => setSelectedActionId(null)}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
        >
          <X className="w-5 h-5" />
        </button>
        <div className="flex-1 flex items-center justify-center p-6 text-slate-400">
          <AlertCircle className="w-6 h-6 mr-2" />
          <span>Action not found.</span>
        </div>
      </aside>
    );
  }

  const agentColors = getAgentColors(action.agent);
  const riskColors = getRiskColors(action.risk_level);
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
    <aside className="w-[500px] bg-slate-900 border-l border-slate-800 flex flex-col h-full shadow-2xl relative z-30">
      {/* Slider Header */}
      <div className="p-6 border-b border-slate-850 flex items-center justify-between select-none">
        <div className="flex items-center space-x-3">
          <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${agentColors.bg} ${agentColors.text} ${agentColors.border}`}>
            {getAgentLabel(action.agent)}
          </span>
          <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${riskColors.bg} ${riskColors.text} ${riskColors.border}`}>
            {action.risk_level} risk
          </span>
        </div>
        <button
          onClick={() => setSelectedActionId(null)}
          className="text-slate-400 hover:text-slate-200 transition-colors"
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

        <hr className="border-slate-850" />

        {/* 1. Payload Details */}
        {renderAgentPayload()}

        {/* 2. Impact Estimator */}
        {action.impact && (
          <div className="bg-slate-900 border border-slate-850 rounded-xl p-4 space-y-3 select-none">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
              <ShieldCheck className="w-4 h-4 mr-2 text-slate-450" />
              Impact Estimation
            </h4>
            <hr className="border-slate-850" />
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Financial Impact</span>
                <span className={`font-semibold ${action.impact.financial_impact && action.impact.financial_impact >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {formatCurrency(action.impact.financial_impact)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Affected Scope</span>
                <span className="text-slate-300 font-medium">
                  {action.impact.affected_skus.length > 0 
                    ? `${action.impact.affected_skus.length} SKU(s)` 
                    : `${action.impact.affected_orders.length} Order(s)`}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Reversible?</span>
                <span className="text-slate-300 font-medium">
                  {action.impact.reversible 
                    ? `Yes, within ${action.impact.reversal_window_hours || 24} hours` 
                    : 'No (Immutable)'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* 3. Evidence Log Metrics */}
        {action.evidence && action.evidence.length > 0 && (
          <div className="space-y-3 select-none">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
              <Database className="w-4 h-4 mr-2 text-slate-500" />
              Decisive Evidence Logs
            </h4>
            <div className="grid grid-cols-1 gap-2">
              {action.evidence.map((ev, index) => (
                <div key={index} className="bg-slate-950 border border-slate-850 p-3 rounded-lg flex items-center justify-between text-xs">
                  <div>
                    <span className="text-slate-500 font-medium block text-[10px] uppercase tracking-wider">
                      {ev.label} ({ev.source})
                    </span>
                    <span className="text-slate-200 mt-1 font-semibold block">{ev.value}</span>
                  </div>
                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider border ${
                    ev.weight === 'primary' 
                      ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' 
                      : 'bg-slate-500/10 text-slate-400 border-slate-500/20'
                  }`}>
                    {ev.weight}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Decision Footer Panel */}
      <div className="p-6 border-t border-slate-850 bg-slate-900/80">
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
                  className="w-full bg-slate-950 border border-red-500/20 focus:border-red-500 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none min-h-[80px]"
                />
                <div className="flex space-x-2">
                  <button
                    onClick={() => {
                      setShowRejectInput(false);
                      setRejectionReason('');
                    }}
                    className="flex-1 py-2 text-xs font-semibold rounded-lg hover:bg-slate-800 text-slate-400 border border-transparent transition-colors"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleReject}
                    disabled={isRejecting}
                    className="flex-1 py-2 text-xs font-semibold rounded-lg bg-red-600 hover:bg-red-500 text-white transition-colors"
                  >
                    {isRejecting ? 'Rejecting...' : 'Confirm Reject'}
                  </button>
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
                    className="w-full bg-slate-950 border border-slate-850 focus:border-blue-500 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none transition-colors"
                  />
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={() => setShowRejectInput(true)}
                    className="flex-1 py-2.5 text-xs font-semibold rounded-lg bg-red-600/10 hover:bg-red-600/20 text-red-400 border border-red-500/25 transition-colors flex items-center justify-center"
                  >
                    <Ban className="w-3.5 h-3.5 mr-1.5" />
                    Reject Action
                  </button>
                  <button
                    onClick={handleApprove}
                    disabled={isApproving}
                    className="flex-1 py-2.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white border border-emerald-500/20 transition-all flex items-center justify-center shadow-lg shadow-emerald-600/10"
                  >
                    <Send className="w-3.5 h-3.5 mr-1.5" />
                    {isApproving ? 'Executing...' : 'Approve & Run'}
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Immutable Decision Logs Panel */
          <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-3 select-none">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
              <Award className="w-4 h-4 mr-2 text-blue-400" />
              Immutable Decision Log
            </h4>
            <hr className="border-slate-850" />
            <div className="space-y-2 text-xs leading-relaxed">
              <div className="flex justify-between">
                <span className="text-slate-500">Review Status</span>
                <span className="font-semibold text-slate-300 uppercase tracking-wider">
                  {action.status}
                </span>
              </div>
              {action.reviewed_by && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Operator ID</span>
                  <span className="text-slate-300 font-medium font-mono">{action.reviewed_by}</span>
                </div>
              )}
              {action.reviewed_at && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Decided At</span>
                  <span className="text-slate-300 font-medium">
                    {formatDateTime(action.reviewed_at)}
                  </span>
                </div>
              )}
              {action.rejection_reason && (
                <div>
                  <span className="text-slate-500 block mb-1">Rejection Reason</span>
                  <div className="bg-red-950/20 border border-red-500/10 p-2.5 rounded-lg text-red-400">
                    "{action.rejection_reason}"
                  </div>
                </div>
              )}
              {action.operator_notes && (
                <div>
                  <span className="text-slate-500 block mb-1">Operator Notes</span>
                  <div className="bg-slate-900 border border-slate-850 p-2.5 rounded-lg text-slate-400 italic">
                    "{action.operator_notes}"
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};

export default ActionDetailPanel;
