import React from 'react';
import { Play, Loader2, Sparkles, Inbox, ShieldAlert } from 'lucide-react';
import { useApprovalQueue } from '../../hooks/useApprovalQueue';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { cn } from '../../utils/cn';

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
    <header className="h-16 bg-card/40 backdrop-blur-md border-b border-white/5 flex items-center justify-between px-8 select-none z-20 sticky top-0">
      {/* Title & Stats */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center">
          <h2 className="text-sm font-semibold text-white flex items-center tracking-tight">
            Active Approval Queue
          </h2>
          {isPipelineRunning && (
            <Badge variant="outline" className="ml-3 bg-blue-500/10 text-blue-400 border-blue-500/20">
              <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />
              AGENTS SYNCING
            </Badge>
          )}
        </div>

        {/* Stats chips */}
        <div className="hidden md:flex items-center space-x-3 text-xs">
          <div className="bg-black/20 px-3 py-1.5 rounded-full border border-white/5 flex items-center shadow-inner">
            <Inbox className="w-3.5 h-3.5 mr-2 text-muted-foreground" />
            <span className="text-muted-foreground mr-1.5 font-medium">Pending Review:</span>
            <span className="font-bold text-white">{pendingCount}</span>
          </div>

          {criticalCount > 0 && (
            <div className="bg-amber-500/10 px-3 py-1.5 rounded-full border border-amber-500/20 flex items-center shadow-[0_0_15px_rgba(245,158,11,0.15)]">
              <ShieldAlert className="w-3.5 h-3.5 mr-1.5 text-amber-500" />
              <span className="text-amber-400 font-bold">{criticalCount} High Risk</span>
            </div>
          )}
        </div>
      </div>

      {/* Trigger Button */}
      <div>
        <Button
          onClick={handleRunPipeline}
          disabled={isPipelineRunning || isPipelineTriggering}
          variant={isPipelineRunning || isPipelineTriggering ? "secondary" : "default"}
          className={cn(
            "rounded-full px-5 py-2 text-xs",
            (isPipelineRunning || isPipelineTriggering) && "opacity-70 cursor-not-allowed"
          )}
        >
          {isPipelineRunning || isPipelineTriggering ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin text-muted-foreground" />
              <span>Agents Running...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 mr-2 fill-current" />
              <span>Force Operations Sync</span>
              <Sparkles className="w-3.5 h-3.5 ml-2 text-white/70" />
            </>
          )}
        </Button>
      </div>
    </header>
  );
};

export default TopBar;
