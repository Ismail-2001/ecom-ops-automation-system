import React from 'react';
import { Tag, TrendingDown, ArrowDownRight, ArrowUpRight } from 'lucide-react';
import type { PricingPayload } from '../../types/action';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import { Card } from '../ui/Card';

interface PricingDetailProps {
  payload: PricingPayload;
}

export const PricingDetail: React.FC<PricingDetailProps> = ({ payload }) => {
  const changePercent = payload.change_percent || 
    (((payload.proposed_price - payload.current_price) / payload.current_price) * 100);
  const isReduction = changePercent < 0;

  return (
    <div className="space-y-6 select-none animate-fadeIn">
      {/* Pricing Change Preview */}
      <Card className="bg-slate-900/40 p-6 flex items-center justify-between">
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Price Adjustments</span>
          <div className="flex items-center space-x-4">
            <div className="text-center">
              <span className="text-[10px] text-slate-500 block font-medium">Current</span>
              <span className="text-lg font-bold text-slate-400 line-through">
                {formatCurrency(payload.current_price)}
              </span>
            </div>
            <div className={`p-1.5 rounded-lg border ${isReduction ? 'bg-red-500/10 border-red-500/20 text-red-400' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'}`}>
              {isReduction ? <ArrowDownRight className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
            </div>
            <div className="text-center">
              <span className="text-[10px] text-slate-400 block font-semibold">Proposed</span>
              <span className="text-2xl font-black text-slate-100">
                {formatCurrency(payload.proposed_price)}
              </span>
            </div>
          </div>
        </div>

        <div className="text-right">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Percentage Change</span>
          <span className={`text-xl font-black ${isReduction ? 'text-red-400' : 'text-emerald-400'}`}>
            {formatPercentage(changePercent)}
          </span>
        </div>
      </Card>

      {/* Reasoning Info Card */}
      <Card className="bg-slate-900/40 p-4 space-y-2">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
          <Tag className="w-4 h-4 mr-2 text-slate-400" />
          Pricing Rationale
        </h4>
        <hr className="border-white/5" />
        <p className="text-xs text-slate-300 leading-relaxed pt-1">
          {payload.reasoning || 'Analyzing product price elasticity and competitor values to maintain profit margins.'}
        </p>
      </Card>

      {/* Competitor Scrapes Table */}
      {payload.competitor_prices && payload.competitor_prices.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
            <TrendingDown className="w-4 h-4 mr-2 text-slate-400" />
            Competitor Intelligence Match
          </h4>
          
          <Card className="overflow-hidden bg-slate-900/20 border-white/5">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] font-bold tracking-widest border-b border-white/5">
                <tr>
                  <th className="px-4 py-3">Competitor Channel</th>
                  <th className="px-4 py-3 text-right">Selling Price</th>
                  <th className="px-4 py-3 text-right">Discrepancy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 bg-slate-900/5">
                {payload.competitor_prices.map((comp, idx) => {
                  const diff = payload.current_price - comp.price;
                  const diffPercent = (diff / comp.price) * 100;
                  
                  return (
                    <tr key={idx} className="hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3 text-slate-300 font-medium">{comp.competitor}</td>
                      <td className="px-4 py-3 text-right font-mono text-slate-200">{formatCurrency(comp.price)}</td>
                      <td className={`px-4 py-3 text-right font-semibold font-mono ${diff > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                        {diff > 0 ? `+${diffPercent.toFixed(1)}% higher` : `${diffPercent.toFixed(1)}% lower`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </div>
      )}
    </div>
  );
};

export default PricingDetail;
