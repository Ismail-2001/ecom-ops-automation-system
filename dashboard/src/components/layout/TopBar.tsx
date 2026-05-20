import React from 'react';
import { Play, Loader2, Sparkles, Inbox } from 'lucide-react';
import { useApprovalQueue } from '../../hooks/useApprovalQueue';

interface TopBarProps {
  isPipelineRunning: boolean;
  onToast: (title: string, message: string, type: 'info' | 'success' | 'warning' | 'error') => void;
}

export const TopBar: React.FC<TopBarProps> = ({ isPipelineRunning, onToast }) => {
  const { actions, runPipeline, isPipelineTriggering } = useApprovalQueue();
  
  // Pending actions count
  const pendingCount = actions.filter((a) => a.status === 'pending').length;
  
  // High risk pending count
  const criticalCount = actions.filter(
    (a) => a.status === 'pending' && (a.risk_level === 'critical' || a.risk_level === 'high')
  ).length;

  const handleRunPipeline = async () => {
    try {
      await runPipeline();
      onToast('Pipeline Run Scheduled', 'Operations background workers have started checking store data.', 'info');
    } catch (e) {
      console.error(e);
      onToast('Pipeline Error', 'Failed to trigger agent pipeline. Please try again.', 'error');
    }
  };

  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-8 select-none">
      {/* Title & Stats */}
      <div className="flex items-center space-x-6">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center">
            Agent Approvals Desk
            {isPipelineRunning && (
              <span className="ml-3 inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                AGENTS ACTIVE
              </span>
            )}
          </h2>
        </div>

        {/* Stats chips */}
        <div className="hidden md:flex items-center space-x-3 text-xs">
          <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-850 flex items-center">
            <Inbox className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
            <span className="text-slate-400 mr-1.5">Pending queue:</span>
            <span className="font-semibold text-slate-200">{pendingCount}</span>
          </div>

          {criticalCount > 0 && (
            <div className="bg-orange-500/10 px-3 py-1.5 rounded-lg border border-orange-500/25 flex items-center">
              <span className="relative flex h-2 w-2 mr-1.5">
                <span className="animate-pulse absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
              </span>
              <span className="text-orange-400 font-medium">{criticalCount} high risk</span>
            </div>
          )}
        </div>
      </div>

      {/* Trigger Button */}
      <div>
        <button
          onClick={handleRunPipeline}
          disabled={isPipelineRunning || isPipelineTriggering}
          className={`relative inline-flex items-center justify-center px-4 py-2 text-xs font-semibold rounded-lg text-white shadow-lg transition-all duration-200 ${
            isPipelineRunning || isPipelineTriggering
              ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700'
              : 'bg-blue-600 hover:bg-blue-500 hover:scale-[1.02] active:scale-[0.98] shadow-blue-500/10 border border-blue-500/20'
          }`}
        >
          {isPipelineRunning || isPipelineTriggering ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin text-blue-400" />
              <span>Agents Running...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 mr-2 fill-current" />
              <span>Run Operations Cycle</span>
              <Sparkles className="w-3.5 h-3.5 ml-1.5 text-blue-200 animate-pulse" />
            </>
          )}
        </button>
      </div>
    </header>
  );
};

export default TopBar;
