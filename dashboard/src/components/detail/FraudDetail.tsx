import React from 'react';
import { Shield, Mail, Globe, AlertTriangle } from 'lucide-react';
import type { FraudPayload } from '../../types/action';
import { formatCurrency } from '../../utils/formatters';
import { Card } from '../ui/Card';

interface FraudDetailProps {
  payload: FraudPayload;
}

export const FraudDetail: React.FC<FraudDetailProps> = ({ payload }) => {
  const isHighScore = payload.fraud_score >= 70;

  return (
    <div className="space-y-6 select-none animate-fadeIn">
      {/* Risk Alert Callout */}
      <div className={`p-4 rounded-xl border flex items-start space-x-3 transition-colors ${
        isHighScore 
          ? 'bg-red-500/10 border-red-500/20 text-red-300' 
          : 'bg-amber-500/10 border-amber-500/20 text-amber-300'
      }`}>
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider">High Fraud Risk Flagged</h4>
          <p className="text-[11px] mt-1 leading-relaxed opacity-95">
            This order was automatically flagged for review. The transaction risk score is {payload.fraud_score}/100. Operational parameters recommend placing a hold.
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="bg-slate-900/40 p-4">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Risk Score</span>
          <div className="flex items-end space-x-2">
            <span className={`text-2xl font-black ${isHighScore ? 'text-red-400' : 'text-amber-400'}`}>
              {payload.fraud_score}
            </span>
            <span className="text-xs text-slate-500 pb-1">/100</span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-950 h-1.5 rounded-full mt-2 overflow-hidden border border-white/5">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${isHighScore ? 'bg-red-500' : 'bg-amber-500'}`}
              style={{ width: `${payload.fraud_score}%` }}
            />
          </div>
        </Card>

        <Card className="bg-slate-900/40 p-4">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Transaction Value</span>
          <span className="text-2xl font-black text-slate-100 block">
            {formatCurrency(payload.order_total)}
          </span>
          <span className="text-[10px] text-slate-500 block mt-2">Paid via Stripe Integration</span>
        </Card>
      </div>

      {/* Customer Info Card */}
      <Card className="bg-slate-900/40 p-4 space-y-3">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
          <Shield className="w-4 h-4 mr-2 text-slate-400" />
          Customer Identity Data
        </h4>
        <hr className="border-white/5" />
        
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-slate-400">Order Reference</span>
            <span className="font-mono text-slate-200 font-semibold">{payload.order_id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Purchasing Name</span>
            <span className="text-slate-200 font-medium">{payload.customer_name}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Email Address</span>
            <span className="text-slate-200 font-medium flex items-center">
              <Mail className="w-3.5 h-3.5 mr-1 text-slate-400" />
              {payload.customer_email}
            </span>
          </div>
        </div>
      </Card>

      {/* Risk Signals */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Flagged Risk Signals</h4>
        <div className="space-y-2">
          {payload.risk_signals.map((signal, index) => (
            <div 
              key={index}
              className="bg-slate-900/40 border border-white/5 p-3 rounded-xl flex items-center text-xs text-slate-300"
            >
              <div className="bg-red-500/10 p-1.5 rounded-lg mr-3 text-red-400 border border-red-500/10">
                <Globe className="w-3.5 h-3.5" />
              </div>
              <span className="font-medium text-slate-200">{signal}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FraudDetail;
