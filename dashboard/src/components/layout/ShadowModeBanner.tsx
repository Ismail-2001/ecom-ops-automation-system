import React from 'react';
import { Eye, ShieldAlert } from 'lucide-react';
import { useSettings } from '../../hooks/useSettings';

export const ShadowModeBanner: React.FC = () => {
  const { settings, isLoading } = useSettings();

  if (isLoading || !settings || !settings.shadow_mode) return null;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '7px 20px',
      background: 'linear-gradient(90deg, rgba(245,158,11,0.12) 0%, rgba(245,158,11,0.07) 50%, rgba(245,158,11,0.12) 100%)',
      borderBottom: '1px solid rgba(245,158,11,0.2)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(8px)',
      userSelect: 'none',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '0 auto', fontSize: '11px', fontWeight: 600, color: '#fbbf24', letterSpacing: '0.03em' }}>
        {/* Pulse dot */}
        <span style={{ position: 'relative', display: 'inline-flex', width: '8px', height: '8px' }}>
          <span style={{
            position: 'absolute', inset: 0, borderRadius: '50%',
            background: '#f59e0b', opacity: 0.5,
            animation: 'pulse-ring 1.5s ease-out infinite',
          }} />
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#fbbf24', position: 'relative', zIndex: 1 }} />
        </span>
        <ShieldAlert size={13} color="#fbbf24" />
        SHADOW MODE ACTIVE: ALL COMPLETED APPROVALS ARE LOGGED AS SIMULATIONS AND WILL NOT MUTATE LIVE SHOPIFY STORE DATA
      </div>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '4px',
        fontSize: '10px', fontWeight: 700, color: '#92400e',
        padding: '3px 8px', borderRadius: '6px',
        background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.2)',
        letterSpacing: '0.06em',
      }}>
        <Eye size={11} /> MONITOR MODE
      </div>
    </div>
  );
};

export default ShadowModeBanner;
