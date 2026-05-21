import React from 'react';
import { Search, FilterX } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

export const QueueFilters: React.FC = () => {
  const { filters, sort, searchQuery, setFilter, setSort, setSearchQuery, resetFilters } = useUIStore();

  const isFiltered = 
    filters.agent !== 'all' || 
    filters.risk !== 'all' || 
    filters.status !== 'pending' || 
    searchQuery !== '';

  return (
    <Card className="bg-card/45 border-white/5 p-4 mb-6 space-y-4 select-none shadow-xl">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Left Side: Inputs */}
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {/* Search bar */}
          <div className="relative group">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500 group-hover:text-accent transition-colors duration-200" />
            <input
              type="text"
              placeholder="Search by SKU, Order ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-black/45 border border-white/10 rounded-lg pl-9 pr-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-accent hover:border-white/20 transition-all duration-200"
            />
          </div>

          {/* Status filter */}
          <select
            value={filters.status}
            onChange={(e) => setFilter('status', e.target.value)}
            className="bg-black/45 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-slate-300 focus:outline-none focus:border-accent hover:border-white/20 transition-all duration-200 cursor-pointer"
          >
            <option value="pending">Awaiting Review (Pending)</option>
            <option value="all">Historical Logs (All Decided)</option>
          </select>

          {/* Agent filter */}
          <select
            value={filters.agent}
            onChange={(e) => setFilter('agent', e.target.value)}
            className="bg-black/45 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-slate-300 focus:outline-none focus:border-accent hover:border-white/20 transition-all duration-200 cursor-pointer"
          >
            <option value="all">All Agents</option>
            <option value="FraudAgent">Fraud Agent</option>
            <option value="InventoryAgent">Inventory Agent</option>
            <option value="PricingAgent">Pricing Agent</option>
            <option value="ReviewsAgent">Reviews Agent</option>
            <option value="MarketingAgent">Marketing Agent</option>
          </select>

          {/* Risk filter */}
          <select
            value={filters.risk}
            onChange={(e) => setFilter('risk', e.target.value)}
            className="bg-black/45 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-slate-300 focus:outline-none focus:border-accent hover:border-white/20 transition-all duration-200 cursor-pointer"
          >
            <option value="all">All Risk Levels</option>
            <option value="critical">Critical Risk</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>
        </div>

        {/* Right Side: Sorting & Reset */}
        <div className="flex items-center space-x-3 justify-end">
          <div className="flex items-center space-x-2">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Sort by</span>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="bg-black/45 border border-white/10 rounded-lg px-3 py-2.5 text-xs text-slate-300 focus:outline-none focus:border-accent hover:border-white/20 transition-all duration-200 cursor-pointer"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="highest_risk">Highest Risk</option>
              <option value="expiring">Expiring Soon</option>
            </select>
          </div>

          {isFiltered && (
            <Button
              variant="outline"
              size="sm"
              onClick={resetFilters}
              className="inline-flex items-center text-xs text-slate-300 hover:text-white border-white/10"
            >
              <FilterX className="w-3.5 h-3.5 mr-1.5" />
              Reset Filters
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};

export default QueueFilters;
