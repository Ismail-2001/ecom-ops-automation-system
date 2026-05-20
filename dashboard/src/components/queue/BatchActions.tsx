import React, { useState } from 'react';
import { ShieldAlert, Check, X, Ban } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { useApprovalQueue } from '../../hooks/useApprovalQueue';

interface BatchActionsProps {
  onToast: (title: string, message: string, type: 'info' | 'success' | 'warning' | 'error') => void;
}

export const BatchActions: React.FC<BatchActionsProps> = ({ onToast }) => {
  const { selectedActionIds, clearSelection } = useUIStore();
  const { batchActions, isBatchMutating } = useApprovalQueue();
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);

  if (selectedActionIds.length === 0) return null;

  const handleBatchApprove = async () => {
    try {
      await batchActions({
        ids: selectedActionIds,
        action: 'approve',
      });
      onToast(
        'Batch Approved',
        `Successfully approved and executing ${selectedActionIds.length} decisions.`,
        'success'
      );
      clearSelection();
    } catch (e) {
      console.error(e);
      onToast('Batch Error', 'Failed to approve batch decisions. High risk items might be present.', 'error');
    }
  };

  const handleBatchReject = async () => {
    if (!rejectReason.trim()) {
      onToast('Reason Required', 'Please specify a reason for rejecting these actions.', 'warning');
      return;
    }

    try {
      await batchActions({
        ids: selectedActionIds,
        action: 'reject',
        reason: rejectReason,
      });
      onToast(
        'Batch Rejected',
        `Successfully rejected ${selectedActionIds.length} decisions.`,
        'info'
      );
      clearSelection();
      setRejectReason('');
      setShowRejectModal(false);
    } catch (e) {
      console.error(e);
      onToast('Batch Error', 'Failed to reject batch decisions.', 'error');
    }
  };

  return (
    <>
      {/* Floating Action Banner */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40 bg-slate-900 border border-slate-700/60 rounded-xl px-6 py-4 flex items-center justify-between shadow-2xl shadow-slate-950 max-w-xl w-full select-none animate-bounce-short">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-500/10 p-2 rounded-lg text-blue-400 border border-blue-500/20">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-100">{selectedActionIds.length} decisions selected</h4>
            <p className="text-[10px] text-slate-400">Approve or reject bulk actions (low/medium risk only)</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Cancel selection */}
          <button
            onClick={clearSelection}
            disabled={isBatchMutating}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-slate-800 text-slate-400 transition-colors"
          >
            Cancel
          </button>

          {/* Bulk Reject */}
          <button
            onClick={() => setShowRejectModal(true)}
            disabled={isBatchMutating}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-600/10 hover:bg-red-600/20 text-red-400 border border-red-500/25 transition-colors flex items-center"
          >
            <X className="w-3.5 h-3.5 mr-1" />
            Reject
          </button>

          {/* Bulk Approve */}
          <button
            onClick={handleBatchApprove}
            disabled={isBatchMutating}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white border border-emerald-500/20 transition-colors flex items-center shadow-lg shadow-emerald-600/15"
          >
            <Check className="w-3.5 h-3.5 mr-1" />
            Approve
          </button>
        </div>
      </div>

      {/* Reject Reason Dialog */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center space-x-3 text-red-400">
              <Ban className="w-6 h-6" />
              <h3 className="text-base font-bold text-slate-100">Reject {selectedActionIds.length} decisions?</h3>
            </div>
            
            <p className="text-xs text-slate-400 leading-relaxed">
              Please provide a brief justification for audit logging. This reason will be recorded against all {selectedActionIds.length} actions in the immutable audit trail.
            </p>

            <textarea
              placeholder="Reason for rejection (e.g., Supplier pricing mismatch, false fraud flag)..."
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="w-full bg-slate-950 border border-slate-850 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 min-h-[90px]"
            />

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectReason('');
                }}
                className="px-4 py-2 rounded-lg text-xs font-semibold hover:bg-slate-800 text-slate-400 transition-colors"
              >
                Go Back
              </button>
              <button
                onClick={handleBatchReject}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-red-600 hover:bg-red-500 text-white transition-colors"
              >
                Confirm Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default BatchActions;
