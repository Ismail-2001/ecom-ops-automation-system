import React, { useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { 
  Inbox, 
  Keyboard, 
  X,
  FileCheck
} from 'lucide-react';
import { useUIStore } from '../store/uiStore';
import { useApprovalQueue } from '../hooks/useApprovalQueue';

import QueueFilters from '../components/queue/QueueFilters';
import ApprovalCard from '../components/queue/ApprovalCard';
import ActionDetailPanel from '../components/detail/ActionDetailPanel';
import BatchActions from '../components/queue/BatchActions';
import { CardSkeleton } from '../components/common/SkeletonLoader';

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
          <h1 className="text-xl font-black text-slate-100 flex items-center">
            <Inbox className="w-6 h-6 mr-3 text-blue-500" />
            Operations Queue
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Review proposed system adjustments before execution. Use hotkeys (J/K/A/?) for lightning-fast management.
          </p>
        </div>

        <button
          onClick={() => setKeyboardHelpOpen(true)}
          className="inline-flex items-center text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          <Keyboard className="w-4 h-4 mr-1.5" />
          Keyboard Hotkeys
        </button>
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
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center max-w-lg mx-auto mt-8 select-none">
              <div className="bg-blue-600/10 p-4 rounded-full text-blue-400 border border-blue-500/10 w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <FileCheck className="w-8 h-8" />
              </div>
              <h3 className="text-sm font-bold text-slate-200">All caught up!</h3>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                No pending approval actions match the current filter criteria. Run the pipeline in the top header to fetch new decisions.
              </p>
            </div>
          ) : (
            // Render Cards
            actions.map((action) => (
              <ApprovalCard
                key={action.id}
                action={action}
                onApprove={approveActiveItem}
                onReject={rejectActiveItem}
              />
            ))
          )}
        </div>

        {/* Right Hand Slideout Panel */}
        <ActionDetailPanel onToast={triggerToast} />
      </div>

      {/* 4. Batch Actions Float menu */}
      <BatchActions onToast={triggerToast} />

      {/* Keyboard Shortcuts Overlay Modal */}
      {keyboardHelpOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center text-blue-400">
              <h3 className="text-base font-bold text-slate-100 flex items-center">
                <Keyboard className="w-5 h-5 mr-2" />
                Keyboard Shortcuts Guide
              </h3>
              <button 
                onClick={() => setKeyboardHelpOpen(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <p className="text-xs text-slate-400 leading-relaxed">
              Use these global hotkey shortcuts to quickly manage pending queue actions without lifting your hands from the keyboard:
            </p>

            <hr className="border-slate-850" />

            <div className="space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Navigate down queue list</span>
                <kbd className="px-2 py-0.5 rounded bg-slate-950 border border-slate-850 font-mono text-[10px] text-slate-300 font-bold uppercase">J</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Navigate up queue list</span>
                <kbd className="px-2 py-0.5 rounded bg-slate-950 border border-slate-850 font-mono text-[10px] text-slate-300 font-bold uppercase">K</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Approve selected action</span>
                <kbd className="px-2 py-0.5 rounded bg-slate-950 border border-slate-850 font-mono text-[10px] text-slate-300 font-bold uppercase">A</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Reject selected action</span>
                <kbd className="px-2 py-0.5 rounded bg-slate-950 border border-slate-850 font-mono text-[10px] text-slate-300 font-bold uppercase">R</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Toggle batch checkbox selection</span>
                <kbd className="px-2.5 py-0.5 rounded bg-slate-950 border border-slate-850 font-mono text-[10px] text-slate-300 font-bold uppercase">Space</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Close details side panel</span>
                <kbd className="px-2 py-0.5 rounded bg-slate-950 border border-slate-850 font-mono text-[10px] text-slate-300 font-bold uppercase">Esc</kbd>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Toggle this help popup</span>
                <kbd className="px-2 py-0.5 rounded bg-slate-950 border border-slate-850 font-mono text-[10px] text-slate-300 font-bold uppercase">?</kbd>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                onClick={() => setKeyboardHelpOpen(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-colors"
              >
                Close Help
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
