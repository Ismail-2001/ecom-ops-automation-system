import React from 'react';
import { Truck, Calendar, ShoppingCart } from 'lucide-react';
import type { InventoryPayload } from '../../types/action';
import { formatCurrency } from '../../utils/formatters';

interface InventoryDetailProps {
  payload: InventoryPayload;
}

export const InventoryDetail: React.FC<InventoryDetailProps> = ({ payload }) => {
  const isStockoutRisk = payload.current_stock <= 5;

  return (
    <div className="space-y-6 select-none">
      {/* Stockout Risk Callout */}
      {isStockoutRisk && (
        <div className="p-4 rounded-xl bg-orange-500/10 border border-orange-500/25 text-orange-100 flex items-start space-x-3">
          <Calendar className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider">Critical Stockout Predicted</h4>
            <p className="text-[11px] mt-1 leading-relaxed opacity-90">
              This SKU has {payload.current_stock} units remaining. With a daily velocity of {payload.daily_velocity} units/day, supply will deplete in {payload.days_of_supply.toFixed(1)} days.
            </p>
          </div>
        </div>
      )}

      {/* Grid Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-850 p-3.5 rounded-xl">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Current Stock</span>
          <span className={`text-xl font-black ${isStockoutRisk ? 'text-orange-400' : 'text-slate-200'}`}>
            {payload.current_stock}
          </span>
          <span className="text-[9px] text-slate-500 block mt-1">units remaining</span>
        </div>

        <div className="bg-slate-900 border border-slate-850 p-3.5 rounded-xl">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Daily Velocity</span>
          <span className="text-xl font-black text-slate-200">
            {payload.daily_velocity}
          </span>
          <span className="text-[9px] text-slate-500 block mt-1">units / day avg</span>
        </div>

        <div className="bg-slate-900 border border-slate-850 p-3.5 rounded-xl">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1">Supply Limit</span>
          <span className="text-xl font-black text-slate-200">
            {payload.days_of_supply.toFixed(1)}
          </span>
          <span className="text-[9px] text-slate-500 block mt-1">days of supply</span>
        </div>
      </div>

      {/* Draft Purchase Order Card */}
      <div className="bg-slate-900 border border-slate-850 rounded-xl p-4 space-y-3">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center">
          <ShoppingCart className="w-4 h-4 mr-2 text-slate-400" />
          Proposed Purchase Order
        </h4>
        <hr className="border-slate-850" />
        
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-slate-500">Product Name</span>
            <span className="text-slate-300 font-medium truncate max-w-[180px]">{payload.product_name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">SKU Reference</span>
            <span className="font-mono text-slate-300 font-medium">{payload.sku}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Reorder Quantity</span>
            <span className="text-slate-300 font-medium font-mono">{payload.reorder_quantity} units</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Estimated Unit Cost</span>
            <span className="text-slate-300 font-medium">{formatCurrency(payload.unit_cost)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Supplier Name</span>
            <span className="text-slate-300 font-medium flex items-center">
              <Truck className="w-3.5 h-3.5 mr-1 text-slate-500" />
              {payload.supplier_name}
            </span>
          </div>
          <hr className="border-slate-850/80 my-1" />
          <div className="flex justify-between text-sm font-bold pt-1">
            <span className="text-slate-300">Total Purchase Value</span>
            <span className="text-blue-400">{formatCurrency(payload.total_po_value || (payload.reorder_quantity * payload.unit_cost))}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InventoryDetail;
