import React from 'react';
import { Play, Loader2, Sparkles, Inbox, ShieldAlert } from 'lucide-react';
import { useApprovalQueue } from '../../hooks/useApprovalQueue';

interface TopBarProps {
  isPipelineRunning: boolean;
  onToast: (title: string, message: string, type: 'info' | 'success' | 'warning' | 'error') => void;
}

export const TopBar: React.FC<TopBarProps> = ({ isPipelineRunning, onToast }) => {
  const { actions, runPipeline, isPipelineTriggering } = useApprovalQueue();

  const pendingCount = actions.filter((a) => a.status === 'pending').length;
  const criticalCount = actions.filter(
    (a) => a.status === 'pending' && (a.risk_level === 'critical' || a.risk_level === 'high')
  ).length;

  const handleRunPipeline = async () => {
    try {
      await runPipeline();
      onToast('Pipeline Scheduled', 'AI agents are scanning store data now.', 'info');
    } catch {
      onToast('Pipeline Error', 'Failed to trigger agent pipeline.', 'error');
    }
  };

  const busy = isPipelineRunning || isPipelineTriggering;

  return (
    <header
      style={{
        height: '60px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px',
        background: 'rgba(7,9,18,0.85)',
        backdropFilter: 'blur(24px) saturate(180%)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        position: 'sticky',
        top: 0,
        zIndex: 20,
        gap: '16px',
      }}
    >
      {/* Left: title + stats */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0', letterSpacing: '-0.01em', whiteSpace: 'nowrap' }}>
          Active Approval Queue
        </span>

        {/* Pending chip */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          padding: '4px 10px', borderRadius: '999px',
          background: 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.08)',
          fontSize: '12px',
        }}>
          <Inbox size={12} color="#64748b" />
          <span style={{ color: '#64748b' }}>Pending Review:</span>
          <span style={{ color: '#f1f5f9', fontWeight: 700 }}>{pendingCount}</span>
        </div>

        {/* High risk chip */}
        {criticalCount > 0 && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '4px 10px', borderRadius: '999px',
            background: 'rgba(245,158,11,0.1)',
            border: '1px solid rgba(245,158,11,0.25)',
            boxShadow: '0 0 14px rgba(245,158,11,0.15)',
            fontSize: '12px',
          }}>
            <ShieldAlert size={12} color="#fbbf24" />
            <span style={{ color: '#fbbf24', fontWeight: 700 }}>{criticalCount} High Risk</span>
          </div>
        )}

        {busy && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '4px 10px', borderRadius: '999px',
            background: 'rgba(59,130,246,0.1)',
            border: '1px solid rgba(59,130,246,0.25)',
            fontSize: '11px', color: '#60a5fa', fontWeight: 600,
          }}>
            <Loader2 size={11} color="#60a5fa" className="animate-spin" />
            AGENTS SYNCING
          </div>
        )}
      </div>

      {/* Right: CTA button */}
      <button
        onClick={handleRunPipeline}
        disabled={busy}
        style={{
          display: 'flex', alignItems: 'center', gap: '7px',
          padding: '8px 18px',
          borderRadius: '999px',
          border: 'none',
          fontSize: '12px',
          fontWeight: 600,
          letterSpacing: '0.01em',
          cursor: busy ? 'not-allowed' : 'pointer',
          opacity: busy ? 0.6 : 1,
          background: busy
            ? 'rgba(255,255,255,0.05)'
            : 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
          color: busy ? '#64748b' : '#fff',
          boxShadow: busy ? 'none' : '0 0 0 1px rgba(59,130,246,0.3), 0 4px 16px rgba(37,99,235,0.35)',
          transition: 'all 0.2s ease',
          whiteSpace: 'nowrap',
        }}
        onMouseEnter={(e) => {
          if (!busy) {
            (e.currentTarget as HTMLElement).style.boxShadow = '0 0 0 1px rgba(59,130,246,0.5), 0 8px 24px rgba(37,99,235,0.45)';
            (e.currentTarget as HTMLElement).style.transform = 'translateY(-1px)';
          }
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.boxShadow = busy ? 'none' : '0 0 0 1px rgba(59,130,246,0.3), 0 4px 16px rgba(37,99,235,0.35)';
          (e.currentTarget as HTMLElement).style.transform = 'translateY(0)';
        }}
      >
        {busy ? (
          <><Loader2 size={13} className="animate-spin" /> Agents Running...</>
        ) : (
          <><Play size={12} fill="currentColor" /> Force Operations Sync <Sparkles size={12} style={{ opacity: 0.7 }} /></>
        )}
      </button>
    </header>
  );
};

export default TopBar;
