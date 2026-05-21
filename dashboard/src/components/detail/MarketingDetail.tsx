import React from 'react';
import { Megaphone, Users, Sparkles } from 'lucide-react';
import type { MarketingPayload } from '../../types/action';
import { formatPercentage } from '../../utils/formatters';
import { Card } from '../ui/Card';

interface MarketingDetailProps {
  payload: MarketingPayload;
}

export const MarketingDetail: React.FC<MarketingDetailProps> = ({ payload }) => {
  return (
    <div className="space-y-6 select-none animate-fadeIn">
      {/* Campaign Banner callout */}
      <div className="p-4 rounded-xl bg-blue-600/10 border border-blue-500/20 text-blue-300 flex items-start space-x-3">
        <Megaphone className="w-5 h-5 flex-shrink-0 mt-0.5 text-blue-400" />
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider">Automated Marketing Push</h4>
          <p className="text-[11px] mt-1 leading-relaxed opacity-95">
            This campaign was dynamically triggered by low stock levels or slow stock velocity to stimulate sales volume and release inventory capital.
          </p>
        </div>
      </div>

      {/* Grid details */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="bg-slate-900/40 p-4">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Target Discount</span>
          <span className="text-2xl font-black text-slate-100">
            {formatPercentage(payload.discount_percent)}
          </span>
          <span className="text-[10px] text-slate-500 block mt-2">Applied to target products</span>
        </Card>

        <Card className="bg-slate-900/40 p-4">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Estimated Reach</span>
          <div className="flex items-center space-x-2 text-2xl font-black text-slate-100">
            <Users className="w-5 h-5 text-slate-400" />
            <span>{payload.estimated_reach.toLocaleString()}</span>
          </div>
          <span className="text-[10px] text-slate-500 block mt-2">Active subscribers target</span>
        </Card>
      </div>

      {/* Target SKUs */}
      <Card className="bg-slate-900/40 p-4 space-y-3">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
          <Sparkles className="w-4 h-4 mr-2 text-slate-400" />
          Target Products
        </h4>
        <hr className="border-white/5" />
        <div className="flex flex-wrap gap-2">
          {payload.target_skus && payload.target_skus.map((sku, index) => (
            <span 
              key={index}
              className="px-2.5 py-1 rounded-lg bg-slate-950 border border-white/5 text-slate-300 font-mono text-xs"
            >
              {sku}
            </span>
          ))}
        </div>
      </Card>

      {/* Draft Message Copy */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-slate-350 uppercase tracking-wider">Ad Copy Message</h4>
        <Card className="bg-slate-900/40 p-4 space-y-3">
          <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold uppercase tracking-wider">
            <span>Subject: {payload.campaign_name}</span>
            <span className="text-blue-400">EMAIL NEWSLETTER</span>
          </div>
          <hr className="border-white/5" />
          <p className="text-xs text-slate-300 leading-relaxed font-sans select-text">
            {payload.draft_message || 'Draft message content...'}
          </p>
        </Card>
      </div>
    </div>
  );
};

export default MarketingDetail;
