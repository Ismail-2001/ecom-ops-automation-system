import React from 'react';
import { 
  BarChart3, 
  Activity, 
  DollarSign, 
  Award,
  Zap, 
  Percent
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  Legend, 
  LineChart, 
  Line 
} from 'recharts';
import { useAnalytics } from '../hooks/useAnalytics';
import { getAgentLabel } from '../utils/riskColors';
import { formatCurrency } from '../utils/formatters';
import { ChartSkeleton } from '../components/common/SkeletonLoader';

const PIE_COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444'];

export const Analytics: React.FC = () => {
  const { data, isLoading } = useAnalytics();

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-black text-slate-100 flex items-center">
            <BarChart3 className="w-6 h-6 mr-3 text-blue-500" />
            Operations Analytics Dashboard
          </h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <ChartSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  const { summary, graduation, charts } = data;

  // Pie chart data prep
  const pieData = [
    { name: 'Under 1 min', value: charts.decision_time_dist.under_1m },
    { name: '1m - 5m', value: charts.decision_time_dist['1m_5m'] },
    { name: '5m - 30m', value: charts.decision_time_dist['5m_30m'] },
    { name: 'Over 30 min', value: charts.decision_time_dist.over_30m },
  ];

  return (
    <div className="space-y-8 select-none">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-black text-slate-100 flex items-center">
          <BarChart3 className="w-6 h-6 mr-3 text-blue-500" />
          Operations Analytics Desk
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Historical overview of agent pipeline accuracy, decision throughput, and team reaction metrics.
        </p>
      </div>

      {/* Summary KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Decisions */}
        <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl flex items-center space-x-4">
          <div className="bg-blue-600/10 p-3 rounded-lg border border-blue-500/20 text-blue-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Total Decisions</span>
            <span className="text-xl font-black text-slate-200">{summary.total_decisions}</span>
          </div>
        </div>

        {/* Approval Rate */}
        <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl flex items-center space-x-4">
          <div className="bg-emerald-600/10 p-3 rounded-lg border border-emerald-500/20 text-emerald-400">
            <Percent className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Approval Accuracy</span>
            <span className="text-xl font-black text-slate-200">{summary.approval_rate}%</span>
          </div>
        </div>

        {/* Capital Authorized */}
        <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl flex items-center space-x-4">
          <div className="bg-purple-600/10 p-3 rounded-lg border border-purple-500/20 text-purple-400">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Capital Authorized</span>
            <span className="text-xl font-black text-slate-200">{formatCurrency(summary.total_financial_impact)}</span>
          </div>
        </div>

        {/* Auto Approvals */}
        <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl flex items-center space-x-4">
          <div className="bg-amber-600/10 p-3 rounded-lg border border-amber-500/20 text-amber-400">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Auto Approvals</span>
            <span className="text-xl font-black text-slate-200">{summary.actions_auto_approved}</span>
          </div>
        </div>
      </div>

      {/* Agent Graduation Streaks Dashboard Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="text-sm font-bold text-slate-200 flex items-center mb-6">
          <Award className="w-5 h-5 mr-2 text-blue-500" />
          Agent Graduation Streaks (Target: 50 Approvals)
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {graduation.map((agent) => {
            const isAutonomous = agent.autonomy_level === 'autonomous';
            const progressPercent = Math.min((agent.streak / 50) * 100, 100);

            return (
              <div 
                key={agent.agent_id}
                className={`bg-slate-950 border p-4 rounded-xl flex flex-col justify-between h-[155px] ${
                  isAutonomous 
                    ? 'border-emerald-500/30 bg-emerald-500/5 shadow-md shadow-emerald-500/5' 
                    : 'border-slate-850'
                }`}
              >
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="text-xs font-bold text-slate-200 truncate max-w-[80px]" title={getAgentLabel(agent.agent_id)}>
                      {getAgentLabel(agent.agent_id).replace('Agent', '')}
                    </h4>
                    <span 
                      className={`text-[8px] font-black uppercase px-1.5 py-0.5 rounded border ${
                        isAutonomous 
                          ? 'bg-emerald-500/10 text-emerald-450 border-emerald-500/20' 
                          : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                      }`}
                    >
                      {agent.autonomy_level}
                    </span>
                  </div>

                  <span className="text-[10px] text-slate-500 font-bold block mb-1">
                    Graduation Streak
                  </span>
                  <div className="flex items-baseline space-x-1">
                    <span className={`text-2xl font-black ${isAutonomous ? 'text-emerald-400' : 'text-slate-200'}`}>
                      {agent.streak}
                    </span>
                    <span className="text-xs text-slate-500">/ 50</span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mt-4">
                  <div className="flex justify-between text-[9px] text-slate-500 font-semibold mb-1">
                    <span>Progress</span>
                    <span>{Math.round(progressPercent)}%</span>
                  </div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden border border-slate-850">
                    <div 
                      className={`h-full rounded-full ${isAutonomous ? 'bg-emerald-500' : 'bg-blue-600'}`}
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recharts Graphical Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stacked Volumes Bar Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4">
            7-Day Operational Decision Volume (Stacked by Agent)
          </h4>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.volume_by_agent}>
                <XAxis dataKey="day" stroke="#475569" fontSize={10} />
                <YAxis stroke="#475569" fontSize={10} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: 8, fontSize: 11 }}
                />
                <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: 10, paddingTop: 10 }} />
                <Bar dataKey="Fraud" stackId="a" fill="#EF4444" />
                <Bar dataKey="Inventory" stackId="a" fill="#F59E0B" />
                <Bar dataKey="Pricing" stackId="a" fill="#3B82F6" />
                <Bar dataKey="Reviews" stackId="a" fill="#8B5CF6" />
                <Bar dataKey="Marketing" stackId="a" fill="#14B8A6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Approval Accuracy Timeline */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4">
            Approval Accuracy Evolution (Last 7 Days)
          </h4>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={charts.approval_rate_over_time}>
                <XAxis dataKey="date" stroke="#475569" fontSize={10} />
                <YAxis domain={[50, 100]} stroke="#475569" fontSize={10} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: 8, fontSize: 11 }}
                />
                <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: 10, paddingTop: 10 }} />
                <Line type="monotone" dataKey="FraudAgent" stroke="#EF4444" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="InventoryAgent" stroke="#F59E0B" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="PricingAgent" stroke="#3B82F6" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="ReviewsAgent" stroke="#8B5CF6" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="MarketingAgent" stroke="#14B8A6" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Decision time distribution */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4">
            Human Reaction Decision Latency distribution
          </h4>
          <div className="h-72 flex items-center justify-center">
            <div className="w-1/2 h-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: 8, fontSize: 11 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div className="w-1/2 space-y-2 select-none">
              {pieData.map((entry, idx) => (
                <div key={idx} className="flex items-center text-xs">
                  <span className="w-3 h-3 rounded-full mr-2.5" style={{ backgroundColor: PIE_COLORS[idx] }} />
                  <span className="text-slate-400 mr-2">{entry.name}:</span>
                  <span className="font-bold text-slate-200">{entry.value} decisions</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Auto Approvals Volume Area Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4">
            System Autonomous Scaling Savings (Accumulated)
          </h4>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={[
                { name: 'Mon', savings: 450 },
                { name: 'Tue', savings: 850 },
                { name: 'Wed', savings: 1300 },
                { name: 'Thu', savings: 2100 },
                { name: 'Fri', savings: 2850 },
                { name: 'Sat', savings: 3200 },
                { name: 'Sun', savings: 3950 }
              ]}>
                <XAxis dataKey="name" stroke="#475569" fontSize={10} />
                <YAxis stroke="#475569" fontSize={10} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: 8, fontSize: 11 }}
                />
                <Area type="monotone" dataKey="savings" stroke="#3b82f6" fillOpacity={0.1} fill="url(#colorSavings)" />
                <defs>
                  <linearGradient id="colorSavings" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
