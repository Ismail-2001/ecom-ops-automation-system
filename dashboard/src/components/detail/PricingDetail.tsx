import React from 'react';
import { Tag, TrendingDown, ArrowDownRight, ArrowUpRight } from 'lucide-react';
import type { PricingPayload } from '../../types/action';
import { formatCurrency, formatPercentage } from '../../utils/formatters';

interface PricingDetailProps {
  payload: PricingPayload;
}

export const PricingDetail: React.FC<PricingDetailProps> = ({ payload }) => {
  const changePercent = payload.change_percent || 
    (((payload.proposed_price - payload.current_price) / payload.current_price) * 100);
  const isReduction = changePercent < 0;

  return (
    <div className="space-y-6 select-none">
      {/* Pricing Change Preview */}
      <div className="bg-slate-900 border border-slate-850 p-6 rounded-xl flex items-center justify-between">
        <div>
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Price Adjustments</span>
          <div className="flex items-center space-x-4">
            <div className="text-center">
              <span className="text-xs text-slate-500 block">Current</span>
              <span className="text-lg font-bold text-slate-400 line-through">
                {formatCurrency(payload.current_price)}
              </span>
            </div>
            <div className={`p-1.5 rounded-lg border ${isReduction ? 'bg-red-500/10 border-red-500/10 text-red-400' : 'bg-emerald-500/10 border-emerald-500/10 text-emerald-400'}`}>
              {isReduction ? <ArrowDownRight className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
            </div>
            <div className="text-center">
              <span className="text-xs text-slate-400 block font-semibold">Proposed</span>
              <span className="text-2xl font-black text-slate-100">
                {formatCurrency(payload.proposed_price)}
              </span>
            </div>
          </div>
        </div>

        <div className="text-right">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Percentage Change</span>
          <span className={`text-xl font-black ${isReduction ? 'text-red-400' : 'text-emerald-400'}`}>
            {formatPercentage(changePercent)}
          </span>
        </div>
      </div>

      {/* Reasoning Info Card */}
      <div className="bg-slate-900 border border-slate-850 rounded-xl p-4 space-y-2">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
          <Tag className="w-4 h-4 mr-2 text-slate-400" />
          Pricing Rationale
        </h4>
        <hr className="border-slate-850" />
        <p className="text-xs text-slate-300 leading-relaxed pt-1">
          {payload.reasoning || 'Analyzing product price elasticity and competitor values to maintain profit margins.'}
        </p>
      </div>

      {/* Competitor Scrapes Table */}
      {payload.competitor_prices && payload.competitor_prices.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
            <TrendingDown className="w-4 h-4 mr-2 text-slate-400" />
            Competitor Intelligence Match
          </h4>
          
          <div className="border border-slate-850 rounded-xl overflow-hidden">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-900 text-slate-400 uppercase text-[9px] font-bold tracking-widest border-b border-slate-850">
                <tr>
                  <th className="px-4 py-3">Competitor Channel</th>
                  <th className="px-4 py-3 text-right">Selling Price</th>
                  <th className="px-4 py-3 text-right">Discrepancy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850 bg-slate-900/40">
                {payload.competitor_prices.map((comp, idx) => {
                  const diff = payload.current_price - comp.price;
                  const diffPercent = (diff / comp.price) * 100;
                  
                  return (
                    <tr key={idx}>
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
          </div>
        </div>
      )}
    </div>
  );
};

export default PricingDetail;
