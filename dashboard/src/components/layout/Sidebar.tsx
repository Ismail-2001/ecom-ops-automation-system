import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, 
  History, 
  BarChart3, 
  Settings as SettingsIcon, 
  Terminal, 
  Cpu
} from 'lucide-react';
import { useAgentStatus } from '../../hooks/useAgentStatus';
import { getAgentLabel } from '../../utils/riskColors';
import { cn } from '../../utils/cn';

interface SidebarProps {
  wsConnected: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ wsConnected }) => {
  const { agents } = useAgentStatus();

  return (
    <aside className="w-64 bg-card/50 backdrop-blur-xl border-r border-white/5 flex flex-col h-full select-none z-10 shadow-2xl shadow-black/50">
      {/* Brand Header */}
      <div className="p-6 border-b border-white/5 flex items-center space-x-3">
        <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2 rounded-xl text-white shadow-lg shadow-blue-500/20 ring-1 ring-white/10">
          <Terminal className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-tight text-white">ECOMMERCE-OPS</h1>
          <p className="text-[10px] text-muted-foreground font-medium tracking-widest uppercase">Enterprise Panel</p>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5">
        {[
          { to: "/", icon: LayoutDashboard, label: "Approval Queue" },
          { to: "/audit", icon: History, label: "Audit Trail" },
          { to: "/analytics", icon: BarChart3, label: "Analytics" },
          { to: "/settings", icon: SettingsIcon, label: "Safety Settings" }
        ].map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "group relative flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 overflow-hidden",
                isActive
                  ? "text-white bg-white/5 shadow-sm ring-1 ring-white/10"
                  : "text-muted-foreground hover:bg-white/5 hover:text-white border border-transparent"
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 rounded-r-full shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  />
                )}
                <item.icon className={cn("w-4 h-4 mr-3 transition-colors", isActive ? "text-blue-400" : "text-muted-foreground group-hover:text-white")} />
                <span className="relative z-10">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Agents Autonomy Indicator List */}
      <div className="px-6 py-5 border-t border-white/5 bg-black/20">
        <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-4 flex items-center">
          <Cpu className="w-3.5 h-3.5 mr-1.5 text-muted-foreground" />
          Agent Autonomy Stems
        </h3>
        <div className="space-y-2.5">
          {agents.map((agent) => {
            const label = getAgentLabel(agent.agent_id);
            const isAutonomous = agent.autonomy_level === 'autonomous';
            const isShadow = agent.autonomy_level === 'shadow';

            return (
              <div key={agent.agent_id} className="flex justify-between items-center text-xs group">
                <span className="text-slate-400 transition-colors group-hover:text-slate-200 truncate max-w-[110px]" title={label}>{label}</span>
                <span 
                  className={cn(
                    "px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border backdrop-blur-md transition-all",
                    isAutonomous
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.1)]"
                      : isShadow
                      ? "bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_10px_rgba(245,158,11,0.1)]"
                      : "bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-[0_0_10px_rgba(59,130,246,0.1)]"
                  )}
                >
                  {agent.autonomy_level}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Connection Indicator footer */}
      <div className="p-4 border-t border-white/5 bg-black/40 flex items-center justify-between text-xs backdrop-blur-xl">
        <span className="text-muted-foreground font-medium">WebSocket Core</span>
        <div className="flex items-center space-x-2">
          <span className={cn(
            "w-2 h-2 rounded-full",
            wsConnected ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse" : "bg-red-500"
          )} />
          <span className="font-bold tracking-wide text-white">{wsConnected ? 'LIVE' : 'OFFLINE'}</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
