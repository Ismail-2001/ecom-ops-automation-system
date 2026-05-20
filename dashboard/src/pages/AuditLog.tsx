import React, { useState } from 'react';
import { History, ChevronLeft, ChevronRight, Eye, AlertCircle, FileCheck, X } from 'lucide-react';
import { useAuditLog } from '../hooks/useAuditLog';
import { getAgentColors, getAgentLabel, getActionTypeLabel } from '../utils/riskColors';
import { formatCurrency, formatDateTime } from '../utils/formatters';
import { TableRowSkeleton } from '../components/common/SkeletonLoader';
import type { AuditEntry } from '../types/audit';

export const AuditLog: React.FC = () => {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    agent: 'all',
    decision: 'all',
    operator: 'all',
    action_type: 'all',
  });
  const [selectedAudit, setSelectedAudit] = useState<AuditEntry | null>(null);

  const limit = 15;
  const { entries, total, isLoading } = useAuditLog(filters, page, limit);
  const totalPages = Math.ceil(total / limit);

  const handleFilterChange = (key: keyof typeof filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1); // Reset page to 1 on filter changes
  };

  const getDecisionBadgeClasses = (decision: string) => {
    switch (decision) {
      case 'approved':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'auto-approved':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'rejected':
        return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'shadow':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="select-none">
        <h1 className="text-xl font-black text-slate-100 flex items-center">
          <History className="w-6 h-6 mr-3 text-blue-500" />
          Immutable Audit Log Trail
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Historical registry of all automated and manual system operations actions for compliance auditing.
        </p>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 select-none">
        {/* Agent Filter */}
        <div className="flex flex-col space-y-1">
          <label className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Agent</label>
          <select
            value={filters.agent}
            onChange={(e) => handleFilterChange('agent', e.target.value)}
            className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-xs text-slate-350 focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Agents</option>
            <option value="FraudAgent">Fraud Agent</option>
            <option value="InventoryAgent">Inventory Agent</option>
            <option value="PricingAgent">Pricing Agent</option>
            <option value="ReviewsAgent">Reviews Agent</option>
            <option value="MarketingAgent">Marketing Agent</option>
          </select>
        </div>

        {/* Decision Filter */}
        <div className="flex flex-col space-y-1">
          <label className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Decision</label>
          <select
            value={filters.decision}
            onChange={(e) => handleFilterChange('decision', e.target.value)}
            className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-xs text-slate-350 focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Decisions</option>
            <option value="approved">Approved</option>
            <option value="auto-approved">Auto-Approved</option>
            <option value="rejected">Rejected</option>
            <option value="shadow">Shadow Sim</option>
          </select>
        </div>

        {/* Action Type Filter */}
        <div className="flex flex-col space-y-1">
          <label className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Action Type</label>
          <select
            value={filters.action_type}
            onChange={(e) => handleFilterChange('action_type', e.target.value)}
            className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-xs text-slate-355 focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Action Types</option>
            <option value="fraud_hold">Hold Order</option>
            <option value="purchase_order">Create PO</option>
            <option value="price_change">Price Change</option>
            <option value="review_response">Review Response</option>
            <option value="marketing_campaign">Marketing Campaign</option>
          </select>
        </div>

        {/* Operator Filter */}
        <div className="flex flex-col space-y-1">
          <label className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Reviewing Operator</label>
          <select
            value={filters.operator}
            onChange={(e) => handleFilterChange('operator', e.target.value)}
            className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-xs text-slate-350 focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Operators</option>
            <option value="admin_operator">Admin Operator</option>
            <option value="system">Autonomous System</option>
          </select>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-900/80 text-slate-450 uppercase text-[9px] font-bold tracking-widest border-b border-slate-800/80 select-none">
              <tr>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Agent Name</th>
                <th className="px-6 py-4">Action Request</th>
                <th className="px-6 py-4">Decision Taken</th>
                <th className="px-6 py-4">Reviewed By</th>
                <th className="px-6 py-4 text-right">Impact Value</th>
                <th className="px-6 py-4 text-center">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-850 bg-slate-900/25">
              {isLoading ? (
                // Skeletons
                Array.from({ length: 10 }, (_, i) => <TableRowSkeleton key={i} />)
              ) : entries.length === 0 ? (
                // Empty state
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                    <AlertCircle className="w-8 h-8 mx-auto mb-3 text-slate-600" />
                    <span className="text-sm font-semibold">No audit entries found</span>
                    <p className="text-xs text-slate-600 mt-1">Try resetting filter options to locate historic decisions.</p>
                  </td>
                </tr>
              ) : (
                // Data rows
                entries.map((entry) => {
                  const agentCol = getAgentColors(entry.agent);
                  const decisionCol = getDecisionBadgeClasses(entry.decision);

                  return (
                    <tr key={entry.id} className="hover:bg-slate-850/30 transition-colors">
                      {/* Timestamp */}
                      <td className="px-6 py-4 text-slate-400 font-medium whitespace-nowrap">
                        {formatDateTime(entry.timestamp)}
                      </td>
                      
                      {/* Agent */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase border ${agentCol.bg} ${agentCol.text} ${agentCol.border}`}>
                          {getAgentLabel(entry.agent)}
                        </span>
                      </td>

                      {/* Action Type */}
                      <td className="px-6 py-4 text-slate-200 font-semibold whitespace-nowrap">
                        {getActionTypeLabel(entry.action_type)}
                      </td>

                      {/* Decision */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase border ${decisionCol}`}>
                          {entry.decision}
                        </span>
                      </td>

                      {/* Operator */}
                      <td className="px-6 py-4 font-mono text-slate-450 whitespace-nowrap">
                        {entry.operator || 'Autonomous System'}
                      </td>

                      {/* Impact */}
                      <td className="px-6 py-4 text-right font-mono font-bold text-slate-200 whitespace-nowrap">
                        {entry.financial_impact !== null ? formatCurrency(entry.financial_impact) : '—'}
                      </td>

                      {/* Action button */}
                      <td className="px-6 py-4 text-center whitespace-nowrap">
                        <button
                          onClick={() => setSelectedAudit(entry)}
                          className="p-1 rounded bg-slate-850 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors inline-flex"
                          title="Inspect JSON Payload"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Toolbar */}
        {!isLoading && totalPages > 1 && (
          <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/40 flex items-center justify-between select-none">
            <span className="text-xs text-slate-400">
              Showing <span className="font-semibold text-slate-350">{(page - 1) * limit + 1}</span> to{' '}
              <span className="font-semibold text-slate-350">
                {Math.min(page * limit, total)}
              </span>{' '}
              of <span className="font-semibold text-slate-350">{total}</span> records
            </span>

            <div className="flex space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page === 1}
                className="p-2 rounded-lg bg-slate-850 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed text-slate-400 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                disabled={page === totalPages}
                className="p-2 rounded-lg bg-slate-850 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed text-slate-400 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* JSON Payload Inspection Dialog */}
      {selectedAudit && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 shadow-2xl space-y-4 flex flex-col max-h-[85vh]">
            <div className="flex justify-between items-center text-blue-400 select-none">
              <h3 className="text-base font-bold text-slate-100 flex items-center">
                <FileCheck className="w-5 h-5 mr-2" />
                Audit Trail Payload Inspector
              </h3>
              <button 
                onClick={() => setSelectedAudit(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs border border-slate-850 rounded-xl p-3 bg-slate-950/50 select-none">
              <div>
                <span className="text-slate-500">Audit ID:</span>{' '}
                <span className="font-mono text-slate-350">{selectedAudit.id}</span>
              </div>
              <div>
                <span className="text-slate-500">Related Action ID:</span>{' '}
                <span className="font-mono text-slate-350">{selectedAudit.action_id || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500">Decision Outcome:</span>{' '}
                <span className="font-semibold text-slate-300 uppercase">{selectedAudit.decision}</span>
              </div>
              <div>
                <span className="text-slate-500">Review Operator:</span>{' '}
                <span className="font-mono text-slate-300">{selectedAudit.operator || 'Autonomous System'}</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto bg-slate-950 border border-slate-850 rounded-xl p-4 font-mono text-[11px] text-blue-300">
              <pre>{JSON.stringify(selectedAudit.details || {}, null, 2)}</pre>
            </div>

            <div className="flex justify-end pt-2 select-none">
              <button
                onClick={() => setSelectedAudit(null)}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-750 text-slate-350 transition-colors"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLog;
