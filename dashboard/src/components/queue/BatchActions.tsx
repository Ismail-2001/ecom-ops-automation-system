import React, { useState } from 'react';
import { ShieldAlert, Check, X, Ban } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUIStore } from '../../store/uiStore';
import { useApprovalQueue } from '../../hooks/useApprovalQueue';
import { Button } from '../ui/Button';

interface BatchActionsProps {
  onToast: (title: string, message: string, type: 'info' | 'success' | 'warning' | 'error') => void;
}

export const BatchActions: React.FC<BatchActionsProps> = ({ onToast }) => {
  const { selectedActionIds, clearSelection } = useUIStore();
  const { batchActions, isBatchMutating } = useApprovalQueue();
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);

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
      <AnimatePresence>
        {selectedActionIds.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 50, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 50, x: '-50%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed bottom-6 left-1/2 z-40 bg-card/75 border border-white/10 rounded-xl px-6 py-4 flex items-center justify-between shadow-2xl backdrop-blur-xl max-w-xl w-[90%] md:w-full select-none"
          >
            {/* Ambient Background glow on banner */}
            <div className="absolute top-0 left-0 w-24 h-full bg-accent/5 rounded-l-xl blur-lg pointer-events-none" />

            <div className="flex items-center space-x-3 relative z-10">
              <div className="bg-accent/10 p-2 rounded-lg text-accent border border-accent/20">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-100">{selectedActionIds.length} decisions selected</h4>
                <p className="text-[10px] text-slate-400">Approve or reject bulk actions (low/medium risk only)</p>
              </div>
            </div>

            <div className="flex items-center space-x-2 relative z-10">
              {/* Cancel selection */}
              <Button
                variant="ghost"
                size="sm"
                onClick={clearSelection}
                disabled={isBatchMutating}
                className="text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </Button>

              {/* Bulk Reject */}
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setShowRejectModal(true)}
                disabled={isBatchMutating}
                className="text-xs flex items-center h-8"
              >
                <X className="w-3.5 h-3.5 mr-1" />
                Reject
              </Button>

              {/* Bulk Approve */}
              <Button
                variant="default"
                size="sm"
                onClick={handleBatchApprove}
                disabled={isBatchMutating}
                className="text-xs flex items-center bg-emerald-500 hover:bg-emerald-400 text-white border-emerald-500/20 shadow-lg shadow-emerald-500/10 h-8"
              >
                <Check className="w-3.5 h-3.5 mr-1" />
                Approve
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reject Reason Dialog */}
      <AnimatePresence>
        {showRejectModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ type: "spring", duration: 0.3 }}
              className="bg-card border border-white/10 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4 relative overflow-hidden"
            >
              {/* Glow decoration */}
              <div className="absolute -top-10 -right-10 w-32 h-32 bg-red-500/5 rounded-full blur-2xl pointer-events-none" />

              <div className="flex items-center space-x-3 text-red-400 relative z-10">
                <Ban className="w-6 h-6" />
                <h3 className="text-base font-bold text-slate-100">Reject {selectedActionIds.length} decisions?</h3>
              </div>
              
              <p className="text-xs text-slate-400 leading-relaxed relative z-10">
                Please provide a brief justification for audit logging. This reason will be recorded against all {selectedActionIds.length} actions in the immutable audit trail.
              </p>

              <textarea
                placeholder="Reason for rejection (e.g., Supplier pricing mismatch, false fraud flag)..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="w-full bg-black/45 border border-white/10 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 min-h-[90px] relative z-10 transition-all"
              />

              <div className="flex justify-end space-x-2 pt-2 relative z-10">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setShowRejectModal(false);
                    setRejectReason('');
                  }}
                  className="text-slate-400 hover:text-white"
                >
                  Go Back
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleBatchReject}
                  className="bg-red-600 hover:bg-red-500 text-white"
                >
                  Confirm Reject
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default BatchActions;
