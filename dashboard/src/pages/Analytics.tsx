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
import { motion, type Variants } from 'framer-motion';
import { useAnalytics } from '../hooks/useAnalytics';
import { getAgentLabel } from '../utils/riskColors';
import { formatCurrency } from '../utils/formatters';
import { ChartSkeleton } from '../components/common/SkeletonLoader';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { cn } from '../utils/cn';

const PIE_COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'];
const AGENT_COLORS = {
  Fraud: '#ef4444',
  Inventory: '#f59e0b',
  Pricing: '#3b82f6',
  Reviews: '#8b5cf6',
  Marketing: '#14b8a6',
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card/95 border border-white/10 p-3 rounded-xl shadow-2xl backdrop-blur-md">
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">{label}</p>
        <div className="space-y-1.5">
          {payload.map((p: any, idx: number) => {
            const isCurrency = p.name.toLowerCase().includes('savings') || p.name.toLowerCase().includes('capital') || p.name.toLowerCase().includes('impact');
            const displayValue = isCurrency && typeof p.value === 'number' ? formatCurrency(p.value) : p.value;
            return (
              <div key={idx} className="flex items-center space-x-2.5 text-xs">
                <span className="w-2.5 h-2.5 rounded-full border border-white/10" style={{ backgroundColor: p.color || p.fill }} />
                <span className="text-slate-400 font-medium">{p.name}:</span>
                <span className="font-bold text-slate-100">{displayValue}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  return null;
};

export const Analytics: React.FC = () => {
  const { data, isLoading } = useAnalytics();

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-black text-slate-100 flex items-center">
            <BarChart3 className="w-6 h-6 mr-3 text-accent" />
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

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100, damping: 15 } }
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-8 select-none"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-xl font-black text-slate-100 flex items-center tracking-tight">
          <BarChart3 className="w-5 h-5 mr-3 text-accent" />
          Operations Analytics Desk
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Historical overview of agent pipeline accuracy, decision throughput, and team reaction metrics.
        </p>
      </motion.div>

      {/* Summary KPI Cards Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Decisions */}
        <Card className="p-4 flex items-center space-x-4 bg-card/45 hover:bg-card/60 transition-all duration-300 border-white/5 shadow-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-16 h-16 bg-accent/5 rounded-full blur-xl pointer-events-none group-hover:scale-150 transition-transform duration-500" />
          <div className="bg-accent/10 p-3 rounded-lg border border-accent/20 text-accent">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Total Decisions</span>
            <span className="text-xl font-black text-slate-200 mt-0.5 block">{summary.total_decisions}</span>
          </div>
        </Card>

        {/* Approval Rate */}
        <Card className="p-4 flex items-center space-x-4 bg-card/45 hover:bg-card/60 transition-all duration-300 border-white/5 shadow-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-16 h-16 bg-emerald-500/5 rounded-full blur-xl pointer-events-none group-hover:scale-150 transition-transform duration-500" />
          <div className="bg-emerald-500/10 p-3 rounded-lg border border-emerald-500/20 text-emerald-400">
            <Percent className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Approval Accuracy</span>
            <span className="text-xl font-black text-slate-200 mt-0.5 block">{summary.approval_rate}%</span>
          </div>
        </Card>

        {/* Capital Authorized */}
        <Card className="p-4 flex items-center space-x-4 bg-card/45 hover:bg-card/60 transition-all duration-300 border-white/5 shadow-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-16 h-16 bg-purple-500/5 rounded-full blur-xl pointer-events-none group-hover:scale-150 transition-transform duration-500" />
          <div className="bg-purple-500/10 p-3 rounded-lg border border-purple-500/20 text-purple-400">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Capital Authorized</span>
            <span className="text-xl font-black text-slate-200 mt-0.5 block">{formatCurrency(summary.total_financial_impact)}</span>
          </div>
        </Card>

        {/* Auto Approvals */}
        <Card className="p-4 flex items-center space-x-4 bg-card/45 hover:bg-card/60 transition-all duration-300 border-white/5 shadow-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-16 h-16 bg-amber-500/5 rounded-full blur-xl pointer-events-none group-hover:scale-150 transition-transform duration-500" />
          <div className="bg-amber-500/10 p-3 rounded-lg border border-amber-500/20 text-amber-400">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Auto Approvals</span>
            <span className="text-xl font-black text-slate-200 mt-0.5 block">{summary.actions_auto_approved}</span>
          </div>
        </Card>
      </motion.div>

      {/* Agent Graduation Streaks Dashboard Section */}
      <motion.div variants={itemVariants}>
        <Card className="bg-card/35 border-white/5 p-6 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-accent/5 rounded-full blur-3xl pointer-events-none -mr-32 -mt-32" />
          
          <h3 className="text-sm font-bold text-slate-200 flex items-center mb-6 relative z-10">
            <Award className="w-5 h-5 mr-2 text-accent" />
            Agent Graduation Streaks (Target: 50 Approvals)
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 relative z-10">
            {graduation.map((agent) => {
              const isAutonomous = agent.autonomy_level === 'autonomous';
              const progressPercent = Math.min((agent.streak / 50) * 100, 100);

              return (
                <div 
                  key={agent.agent_id}
                  className={cn(
                    "border p-4 rounded-xl flex flex-col justify-between h-[155px] transition-all duration-300 hover:scale-[1.02] shadow-lg bg-black/20",
                    isAutonomous 
                      ? 'border-emerald-500/30 bg-emerald-500/5 shadow-emerald-500/5' 
                      : 'border-white/5 hover:border-white/10'
                  )}
                >
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-xs font-bold text-slate-200 truncate max-w-[80px]" title={getAgentLabel(agent.agent_id)}>
                        {getAgentLabel(agent.agent_id).replace('Agent', '')}
                      </h4>
                      <Badge 
                        variant={isAutonomous ? 'success' : 'default'}
                        className="text-[8px] font-black uppercase px-1.5 py-0.5"
                      >
                        {agent.autonomy_level}
                      </Badge>
                    </div>

                    <span className="text-[10px] text-slate-500 font-bold block mb-1">
                      Graduation Streak
                    </span>
                    <div className="flex items-baseline space-x-1">
                      <span className={cn("text-2xl font-black", isAutonomous ? 'text-emerald-450' : 'text-slate-200')}>
                        {agent.streak}
                      </span>
                      <span className="text-xs text-slate-550">/ 50</span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-[9px] text-slate-500 font-semibold mb-1">
                      <span>Progress</span>
                      <span>{Math.round(progressPercent)}%</span>
                    </div>
                    <div className="w-full bg-black/40 h-1.5 rounded-full overflow-hidden border border-white/5">
                      <div 
                        className={cn("h-full rounded-full transition-all duration-500", isAutonomous ? 'bg-emerald-500' : 'bg-accent')}
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </motion.div>

      {/* Recharts Graphical Panels */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stacked Volumes Bar Chart */}
        <Card className="bg-card/35 border-white/5 p-6 shadow-xl">
          <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider mb-5">
            7-Day Operational Decision Volume (Stacked by Agent)
          </h4>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.volume_by_agent} margin={{ left: -10, right: 10 }}>
                <XAxis dataKey="day" stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: 10, paddingTop: 15 }} />
                <Bar dataKey="Fraud" stackId="a" fill={AGENT_COLORS.Fraud} radius={[0, 0, 0, 0]} />
                <Bar dataKey="Inventory" stackId="a" fill={AGENT_COLORS.Inventory} radius={[0, 0, 0, 0]} />
                <Bar dataKey="Pricing" stackId="a" fill={AGENT_COLORS.Pricing} radius={[0, 0, 0, 0]} />
                <Bar dataKey="Reviews" stackId="a" fill={AGENT_COLORS.Reviews} radius={[0, 0, 0, 0]} />
                <Bar dataKey="Marketing" stackId="a" fill={AGENT_COLORS.Marketing} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Approval Accuracy Timeline */}
        <Card className="bg-card/35 border-white/5 p-6 shadow-xl">
          <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider mb-5">
            Approval Accuracy Evolution (Last 7 Days)
          </h4>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={charts.approval_rate_over_time} margin={{ left: -10, right: 10 }}>
                <XAxis dataKey="date" stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis domain={[50, 100]} stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: 10, paddingTop: 15 }} />
                <Line type="monotone" name="Fraud Agent" dataKey="FraudAgent" stroke={AGENT_COLORS.Fraud} strokeWidth={2.5} dot={{ r: 3, strokeWidth: 1.5 }} activeDot={{ r: 5 }} />
                <Line type="monotone" name="Inventory Agent" dataKey="InventoryAgent" stroke={AGENT_COLORS.Inventory} strokeWidth={2.5} dot={{ r: 3, strokeWidth: 1.5 }} activeDot={{ r: 5 }} />
                <Line type="monotone" name="Pricing Agent" dataKey="PricingAgent" stroke={AGENT_COLORS.Pricing} strokeWidth={2.5} dot={{ r: 3, strokeWidth: 1.5 }} activeDot={{ r: 5 }} />
                <Line type="monotone" name="Reviews Agent" dataKey="ReviewsAgent" stroke={AGENT_COLORS.Reviews} strokeWidth={2.5} dot={{ r: 3, strokeWidth: 1.5 }} activeDot={{ r: 5 }} />
                <Line type="monotone" name="Marketing Agent" dataKey="MarketingAgent" stroke={AGENT_COLORS.Marketing} strokeWidth={2.5} dot={{ r: 3, strokeWidth: 1.5 }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Decision time distribution */}
        <Card className="bg-card/35 border-white/5 p-6 shadow-xl">
          <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider mb-5">
            Human Reaction Decision Latency Distribution
          </h4>
          <div className="h-72 flex flex-col sm:flex-row items-center justify-center">
            <div className="w-full sm:w-1/2 h-4/5">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} stroke="rgba(255,255,255,0.05)" strokeWidth={1} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div className="w-full sm:w-1/2 space-y-3.5 pl-0 sm:pl-6 select-none mt-4 sm:mt-0">
              {pieData.map((entry, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs border-b border-white/5 pb-1.5 last:border-0 last:pb-0">
                  <div className="flex items-center">
                    <span className="w-3 h-3 rounded-full mr-3 border border-white/10" style={{ backgroundColor: PIE_COLORS[idx] }} />
                    <span className="text-slate-400 font-medium">{entry.name}</span>
                  </div>
                  <span className="font-bold text-slate-200">{entry.value} decisions</span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Auto Approvals Volume Area Chart */}
        <Card className="bg-card/35 border-white/5 p-6 shadow-xl">
          <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider mb-5">
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
              ]} margin={{ left: -10, right: 10 }}>
                <XAxis dataKey="name" stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <defs>
                  <linearGradient id="colorSavings" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <Area type="monotone" name="Accumulated Savings" dataKey="savings" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorSavings)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
};

export default Analytics;
