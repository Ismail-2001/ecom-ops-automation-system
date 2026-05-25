import React, { useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { 
  Inbox, 
  Keyboard, 
  X,
  FileCheck
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUIStore } from '../store/uiStore';
import { useApprovalQueue } from '../hooks/useApprovalQueue';

import QueueFilters from '../components/queue/QueueFilters';
import ApprovalCard from '../components/queue/ApprovalCard';
import ActionDetailPanel from '../components/detail/ActionDetailPanel';
import BatchActions from '../components/queue/BatchActions';
import { CardSkeleton } from '../components/common/SkeletonLoader';
import { Button } from '../components/ui/Button';

export const Dashboard: React.FC = () => {
  const { triggerToast } = useOutletContext<{ triggerToast: any }>();
  const { actions, isLoading, approveAction } = useApprovalQueue();
  
  const { 
    selectedActionId, 
    setSelectedActionId, 
    toggleSelectedActionId,
    keyboardHelpOpen,
    setKeyboardHelpOpen,
  } = useUIStore();

  const pendingActions = actions.filter((a) => a.status === 'pending');

  // Keyboard Shortcuts Handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // If user is writing in any inputs, textareas, don't trigger shortcuts
      const activeEl = document.activeElement?.tagName.toLowerCase();
      if (activeEl === 'input' || activeEl === 'textarea' || activeEl === 'select') {
        return;
      }

      const activeIndex = pendingActions.findIndex((a) => a.id === selectedActionId);

      switch (e.key.toLowerCase()) {
        // Navigate Down
        case 'j':
          e.preventDefault();
          if (pendingActions.length === 0) return;
          if (activeIndex === -1 || activeIndex === pendingActions.length - 1) {
            setSelectedActionId(pendingActions[0].id);
          } else {
            setSelectedActionId(pendingActions[activeIndex + 1].id);
          }
          break;

        // Navigate Up
        case 'k':
          e.preventDefault();
          if (pendingActions.length === 0) return;
          if (activeIndex === -1 || activeIndex === 0) {
            setSelectedActionId(pendingActions[pendingActions.length - 1].id);
          } else {
            setSelectedActionId(pendingActions[activeIndex - 1].id);
          }
          break;

        // Approve Active Item
        case 'a':
          e.preventDefault();
          if (selectedActionId) {
            approveActiveItem(selectedActionId);
          }
          break;

        // Reject Active Item
        case 'r':
          e.preventDefault();
          if (selectedActionId) {
            // Rejects action immediately for hotkey, or slides details pane to prompt reason
            triggerToast(
              'Justification Required', 
              'Please write a rejection reason in the detail panel to reject.', 
              'warning'
            );
          }
          break;

        // Toggle Batch Checkbox
        case ' ':
          e.preventDefault();
          if (selectedActionId) {
            const current = pendingActions.find((a) => a.id === selectedActionId);
            const isHighRisk = current?.risk_level === 'high' || current?.risk_level === 'critical';
            if (current && current.status === 'pending' && !isHighRisk) {
              toggleSelectedActionId(selectedActionId);
            } else {
              triggerToast('Selection Warning', 'Cannot select high risk items for batch actions.', 'warning');
            }
          }
          break;

        // Close details panel
        case 'escape':
          e.preventDefault();
          setSelectedActionId(null);
          break;

        // Toggle help overlay
        case '?':
        case '/':
          if (e.key === '?' || (e.key === '/' && e.shiftKey)) {
            e.preventDefault();
            setKeyboardHelpOpen(!keyboardHelpOpen);
          }
          break;

        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedActionId, pendingActions]);

  const approveActiveItem = async (id: string) => {
    try {
      await approveAction({ id });
      triggerToast('Action Approved', 'Successfully executing action.', 'success');
      if (selectedActionId === id) setSelectedActionId(null);
    } catch (e) {
      console.error(e);
      triggerToast('Error', 'Failed to approve action.', 'error');
    }
  };

  const rejectActiveItem = async (id: string) => {
    // Open panel to force rejection reason input
    setSelectedActionId(id);
    triggerToast('Justification Needed', 'Please specify a rejection reason in the detail panel.', 'info');
  };

  return (
    <div className="h-full flex flex-col overflow-hidden relative">
      {/* 1. Header Toolbar */}
      <div className="flex justify-between items-center mb-6 select-none">
        <div>
          <h1 className="text-xl font-black text-slate-100 flex items-center tracking-tight">
            <Inbox className="w-5 h-5 mr-3 text-accent" />
            Operations Queue
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Review proposed system adjustments before execution. Use hotkeys (J/K/A/?) for lightning-fast management.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setKeyboardHelpOpen(true)}
          className="inline-flex items-center text-xs text-slate-300 hover:text-white"
        >
          <Keyboard className="w-4 h-4 mr-1.5" />
          Keyboard Hotkeys
        </Button>
      </div>

      {/* 2. Filters Row */}
      <QueueFilters />

      {/* 3. Main Split Workspace */}
      <div className="flex flex-1 overflow-hidden gap-6">
        {/* Left Hand Card List */}
        <div className="flex-1 overflow-y-auto pr-2 pb-24">
          {isLoading ? (
            // Skeleton state
            [1, 2, 3].map((i) => <CardSkeleton key={i} />)
          ) : actions.length === 0 ? (
            // Empty state
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-card/30 border border-white/5 backdrop-blur-md rounded-xl p-12 text-center max-w-lg mx-auto mt-8 select-none shadow-2xl"
            >
              <div className="bg-accent/10 p-4 rounded-full text-accent border border-accent/10 w-16 h-16 flex items-center justify-center mx-auto mb-4 animate-pulse">
                <FileCheck className="w-8 h-8" />
              </div>
              <h3 className="text-sm font-bold text-slate-100">All caught up!</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                No pending approval actions match the current filter criteria. Run the pipeline in the top header to fetch new decisions.
              </p>
            </motion.div>
          ) : (
            // Render Cards
            <motion.div 
              layout
              className="space-y-4"
            >
              <AnimatePresence mode="popLayout">
                {actions.map((action) => (
                  <ApprovalCard
                    key={action.id}
                    action={action}
                    onApprove={approveActiveItem}
                    onReject={rejectActiveItem}
                  />
                ))}
              </AnimatePresence>
            </motion.div>
          )}
        </div>

        {/* Right Hand Slideout Panel */}
        <ActionDetailPanel onToast={triggerToast} />
      </div>

      {/* 4. Batch Actions Float menu */}
      <BatchActions onToast={triggerToast} />

      {/* Keyboard Shortcuts Overlay Modal */}
      <AnimatePresence>
        {keyboardHelpOpen && (
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
              {/* Premium Glow effect */}
              <div className="absolute -top-10 -right-10 w-32 h-32 bg-accent/10 rounded-full blur-2xl pointer-events-none" />

              <div className="flex justify-between items-center text-accent relative z-10">
                <h3 className="text-base font-bold text-slate-100 flex items-center">
                  <Keyboard className="w-5 h-5 mr-2" />
                  Keyboard Shortcuts Guide
                </h3>
                <button 
                  onClick={() => setKeyboardHelpOpen(false)}
                  className="text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <p className="text-xs text-slate-400 leading-relaxed relative z-10">
                Use these global hotkey shortcuts to quickly manage pending queue actions without lifting your hands from the keyboard:
              </p>

              <hr className="border-white/5 relative z-10" />

              <div className="space-y-3 text-xs relative z-10">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Navigate down queue list</span>
                  <kbd className="px-2 py-0.5 rounded bg-black/40 border border-white/10 font-mono text-[10px] text-slate-300 font-bold uppercase shadow">J</kbd>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Navigate up queue list</span>
                  <kbd className="px-2 py-0.5 rounded bg-black/40 border border-white/10 font-mono text-[10px] text-slate-300 font-bold uppercase shadow">K</kbd>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Approve selected action</span>
                  <kbd className="px-2 py-0.5 rounded bg-black/40 border border-white/10 font-mono text-[10px] text-slate-300 font-bold uppercase shadow">A</kbd>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Reject selected action</span>
                  <kbd className="px-2 py-0.5 rounded bg-black/40 border border-white/10 font-mono text-[10px] text-slate-300 font-bold uppercase shadow">R</kbd>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Toggle batch checkbox selection</span>
                  <kbd className="px-2.5 py-0.5 rounded bg-black/40 border border-white/10 font-mono text-[10px] text-slate-300 font-bold uppercase shadow">Space</kbd>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Close details side panel</span>
                  <kbd className="px-2 py-0.5 rounded bg-black/40 border border-white/10 font-mono text-[10px] text-slate-300 font-bold uppercase shadow">Esc</kbd>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Toggle this help popup</span>
                  <kbd className="px-2 py-0.5 rounded bg-black/40 border border-white/10 font-mono text-[10px] text-slate-300 font-bold uppercase shadow">?</kbd>
                </div>
              </div>

              <div className="flex justify-end pt-4 relative z-10">
                <Button
                  onClick={() => setKeyboardHelpOpen(false)}
                  className="px-4 py-2 text-xs font-semibold"
                >
                  Close Help
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Dashboard;
