import React from 'react';
import { Shield, Mail, Globe, AlertTriangle } from 'lucide-react';
import type { FraudPayload } from '../../types/action';
import { formatCurrency } from '../../utils/formatters';

interface FraudDetailProps {
  payload: FraudPayload;
}

export const FraudDetail: React.FC<FraudDetailProps> = ({ payload }) => {
  const isHighScore = payload.fraud_score >= 70;

  return (
    <div className="space-y-6 select-none">
      {/* Risk Alert Callout */}
      <div className={`p-4 rounded-xl border flex items-start space-x-3 ${
        isHighScore 
          ? 'bg-red-500/10 border-red-500/25 text-red-100' 
          : 'bg-amber-500/10 border-amber-500/25 text-amber-100'
      }`}>
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider">High Fraud Risk Flagged</h4>
          <p className="text-[11px] mt-1 leading-relaxed opacity-90">
            This order was automatically flagged for review. The transaction risk score is {payload.fraud_score}/100. Operational parameters recommend placing a hold.
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Risk Score</span>
          <div className="flex items-end space-x-2">
            <span className={`text-2xl font-black ${isHighScore ? 'text-red-400' : 'text-amber-400'}`}>
              {payload.fraud_score}
            </span>
            <span className="text-xs text-slate-500 pb-1">/100</span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-950 h-1.5 rounded-full mt-2 overflow-hidden">
            <div 
              className={`h-full rounded-full ${isHighScore ? 'bg-red-500' : 'bg-amber-500'}`}
              style={{ width: `${payload.fraud_score}%` }}
            />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-850 p-4 rounded-xl">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Transaction Value</span>
          <span className="text-2xl font-black text-slate-200">
            {formatCurrency(payload.order_total)}
          </span>
          <span className="text-[10px] text-slate-500 block mt-2">Paid via Stripe Integration</span>
        </div>
      </div>

      {/* Customer Info Card */}
      <div className="bg-slate-900 border border-slate-850 rounded-xl p-4 space-y-3">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
          <Shield className="w-4 h-4 mr-2 text-slate-400" />
          Customer Identity Data
        </h4>
        <hr className="border-slate-850" />
        
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-slate-500">Order Reference</span>
            <span className="font-mono text-slate-300 font-medium">{payload.order_id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Purchasing Name</span>
            <span className="text-slate-300 font-medium">{payload.customer_name}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Email Address</span>
            <span className="text-slate-300 font-medium flex items-center">
              <Mail className="w-3.5 h-3.5 mr-1 text-slate-500" />
              {payload.customer_email}
            </span>
          </div>
        </div>
      </div>

      {/* Risk Signals */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Flagged Risk Signals</h4>
        <div className="space-y-2">
          {payload.risk_signals.map((signal, index) => (
            <div 
              key={index}
              className="bg-slate-900/60 border border-slate-850 p-3 rounded-lg flex items-center text-xs text-slate-300"
            >
              <div className="bg-red-500/10 p-1.5 rounded mr-3 text-red-400 border border-red-500/10">
                <Globe className="w-3.5 h-3.5" />
              </div>
              <span className="font-medium">{signal}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FraudDetail;
