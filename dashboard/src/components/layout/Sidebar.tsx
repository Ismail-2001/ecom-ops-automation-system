import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  History,
  BarChart3,
  Settings as SettingsIcon,
  Zap,
  Cpu,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useAgentStatus } from '../../hooks/useAgentStatus';
import { getAgentLabel } from '../../utils/riskColors';

interface SidebarProps {
  wsConnected: boolean;
}

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Approval Queue' },
  { to: '/audit', icon: History, label: 'Audit Trail' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/settings', icon: SettingsIcon, label: 'Safety Settings' },
];

const autonomyColor = (level: string) => {
  if (level === 'autonomous')
    return { bg: 'rgba(16,185,129,0.12)', color: '#34d399', border: 'rgba(16,185,129,0.25)' };
  if (level === 'shadow')
    return { bg: 'rgba(245,158,11,0.12)', color: '#fbbf24', border: 'rgba(245,158,11,0.25)' };
  return { bg: 'rgba(59,130,246,0.12)', color: '#60a5fa', border: 'rgba(59,130,246,0.25)' };
};

export const Sidebar: React.FC<SidebarProps> = ({ wsConnected }) => {
  const { agents } = useAgentStatus();

  return (
    <aside
      className="w-64 flex flex-col h-full select-none z-20 relative"
      style={{
        background: 'rgba(7,9,18,0.92)',
        backdropFilter: 'blur(32px) saturate(180%)',
        borderRight: '1px solid rgba(255,255,255,0.05)',
        boxShadow: '4px 0 24px rgba(0,0,0,0.4)',
      }}
    >
      {/* Brand */}
      <div style={{ padding: '24px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <div className="flex items-center gap-3">
          <div
            style={{
              background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
              borderRadius: '10px',
              padding: '8px',
              boxShadow: '0 0 20px rgba(37,99,235,0.4)',
            }}
          >
            <Zap size={16} color="#fff" />
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.01em' }}>
              ECOMMERCE-OPS
            </div>
            <div style={{ fontSize: '10px', color: '#475569', letterSpacing: '0.1em', textTransform: 'uppercase', fontWeight: 500 }}>
              Enterprise Panel
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            style={{ textDecoration: 'none' }}
          >
            {({ isActive }) => (
              <motion.div
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.98 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '9px 12px',
                  borderRadius: '10px',
                  fontSize: '13px',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? '#f1f5f9' : '#64748b',
                  background: isActive ? 'rgba(37,99,235,0.12)' : 'transparent',
                  border: `1px solid ${isActive ? 'rgba(59,130,246,0.25)' : 'transparent'}`,
                  boxShadow: isActive ? '0 0 12px rgba(37,99,235,0.12)' : 'none',
                  transition: 'all 0.15s ease',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                {isActive && (
                  <motion.div
                    layoutId="navIndicator"
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: '25%',
                      bottom: '25%',
                      width: '3px',
                      background: 'linear-gradient(180deg, #3b82f6, #7c3aed)',
                      borderRadius: '0 2px 2px 0',
                      boxShadow: '0 0 8px rgba(59,130,246,0.6)',
                    }}
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <item.icon
                  size={15}
                  color={isActive ? '#60a5fa' : '#475569'}
                  style={{ flexShrink: 0 }}
                />
                {item.label}
              </motion.div>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Agent Autonomy */}
      <div style={{ padding: '16px 16px 12px', borderTop: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
          <Cpu size={11} color="#475569" />
          <span style={{ fontSize: '10px', fontWeight: 700, color: '#475569', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            Agent Autonomy
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {agents.map((agent) => {
            const c = autonomyColor(agent.autonomy_level);
            return (
              <div key={agent.agent_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', color: '#94a3b8', maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {getAgentLabel(agent.agent_id)}
                </span>
                <span style={{
                  fontSize: '9px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  padding: '2px 7px',
                  borderRadius: '4px',
                  background: c.bg,
                  color: c.color,
                  border: `1px solid ${c.border}`,
                }}>
                  {agent.autonomy_level}
                </span>
              </div>
            );
          })}
        </div>

        {/* WebSocket Status */}
        <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.04)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '11px', color: '#475569' }}>WebSocket Core</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            {wsConnected ? (
              <>
                <div style={{ position: 'relative', width: '8px', height: '8px' }}>
                  <div style={{
                    position: 'absolute', inset: 0, borderRadius: '50%',
                    background: '#10b981', animation: 'pulse-ring 1.5s ease-out infinite',
                    opacity: 0.4,
                  }} />
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', position: 'relative', zIndex: 1 }} />
                </div>
                <Wifi size={11} color="#34d399" />
                <span style={{ fontSize: '10px', color: '#34d399', fontWeight: 600 }}>LIVE</span>
              </>
            ) : (
              <>
                <WifiOff size={11} color="#f43f5e" />
                <span style={{ fontSize: '10px', color: '#f43f5e', fontWeight: 600 }}>OFFLINE</span>
              </>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
