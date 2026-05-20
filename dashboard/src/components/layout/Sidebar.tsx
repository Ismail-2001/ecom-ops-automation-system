import React from 'react';
import { NavLink } from 'react-router-dom';
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

interface SidebarProps {
  wsConnected: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ wsConnected }) => {
  const { agents } = useAgentStatus();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full select-none">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-850 flex items-center space-x-3">
        <div className="bg-blue-600 p-2 rounded-lg text-white shadow-lg shadow-blue-500/10">
          <Terminal className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-tight">ECOMMERCE-OPS</h1>
          <p className="text-[10px] text-slate-400 font-medium">HITL SUPERVISOR PANEL</p>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5">
        <NavLink
          to="/"
          className={({ isActive }) =>
            `flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
              isActive
                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                : 'text-slate-400 hover:bg-slate-850 hover:text-slate-200 border border-transparent'
            }`
          }
        >
          <LayoutDashboard className="w-4 h-4 mr-3" />
          Approval Queue
        </NavLink>

        <NavLink
          to="/audit"
          className={({ isActive }) =>
            `flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
              isActive
                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                : 'text-slate-400 hover:bg-slate-850 hover:text-slate-200 border border-transparent'
            }`
          }
        >
          <History className="w-4 h-4 mr-3" />
          Audit Trail
        </NavLink>

        <NavLink
          to="/analytics"
          className={({ isActive }) =>
            `flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
              isActive
                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                : 'text-slate-400 hover:bg-slate-850 hover:text-slate-200 border border-transparent'
            }`
          }
        >
          <BarChart3 className="w-4 h-4 mr-3" />
          Analytics
        </NavLink>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
              isActive
                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                : 'text-slate-400 hover:bg-slate-850 hover:text-slate-200 border border-transparent'
            }`
          }
        >
          <SettingsIcon className="w-4 h-4 mr-3" />
          Safety Settings
        </NavLink>
      </nav>

      {/* Agents Autonomy Indicator List */}
      <div className="px-6 py-4 border-t border-slate-850 bg-slate-900/50">
        <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center">
          <Cpu className="w-3.5 h-3.5 mr-1 text-slate-400" />
          Agent Autonomy Stems
        </h3>
        <div className="space-y-2">
          {agents.map((agent) => {
            const label = getAgentLabel(agent.agent_id);
            const isAutonomous = agent.autonomy_level === 'autonomous';
            const isShadow = agent.autonomy_level === 'shadow';

            return (
              <div key={agent.agent_id} className="flex justify-between items-center text-xs">
                <span className="text-slate-400 truncate max-w-[110px]" title={label}>{label}</span>
                <span 
                  className={`px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wider border ${
                    isAutonomous
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : isShadow
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                  }`}
                >
                  {agent.autonomy_level}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Connection Indicator footer */}
      <div className="p-4 border-t border-slate-850 bg-slate-900/80 flex items-center justify-between text-xs">
        <span className="text-slate-400">WebSocket System</span>
        <div className="flex items-center space-x-1.5">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-500 shadow-lg shadow-emerald-500/20 animate-pulse' : 'bg-red-500'}`} />
          <span className="font-semibold">{wsConnected ? 'Connected' : 'Offline'}</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
