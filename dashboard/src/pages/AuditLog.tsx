import React, { useState } from 'react';
import { History, ChevronLeft, ChevronRight, Eye, AlertCircle, FileCheck, X, Download, Loader2 } from 'lucide-react';
import { useAuditLog } from '../hooks/useAuditLog';
import { getAgentColors, getAgentLabel, getActionTypeLabel } from '../utils/riskColors';
import { formatCurrency, formatDateTime } from '../utils/formatters';
import { TableRowSkeleton } from '../components/common/SkeletonLoader';
import type { AuditEntry } from '../types/audit';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { motion, AnimatePresence } from 'framer-motion';
import apiClient from '../api/client';

export const AuditLog: React.FC = () => {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    agent: 'all',
    decision: 'all',
    operator: 'all',
    action_type: 'all',
  });
  const [selectedAudit, setSelectedAudit] = useState<AuditEntry | null>(null);
  const [exporting, setExporting] = useState(false);

  const handleExportCSV = async () => {
    setExporting(true);
    try {
      const response = await apiClient.get('/api/audit/export', {
        params: { format: 'csv' },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'audit_log.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      // silently fail
    } finally {
      setExporting(false);
    }
  };

  const limit = 15;
  const { entries, total, isLoading } = useAuditLog(filters, page, limit);
  const totalPages = Math.ceil(total / limit);

  const handleFilterChange = (key: keyof typeof filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1); // Reset page to 1 on filter changes
  };

  const getDecisionBadgeVariant = (decision: string): 'default' | 'success' | 'destructive' | 'warning' | 'outline' => {
    switch (decision) {
      case 'approved':
        return 'success';
      case 'auto-approved':
        return 'default';
      case 'rejected':
        return 'destructive';
      case 'shadow':
        return 'warning';
      default:
        return 'outline';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="select-none flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 flex items-center tracking-tight">
            <History className="w-6 h-6 mr-3 text-blue-500" />
            Immutable Audit Trail
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Historical ledger of all autonomous decisions and manual operator interventions.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleExportCSV}
          disabled={exporting}
          className="flex items-center text-xs"
        >
          {exporting ? (
            <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
          ) : (
            <Download className="w-3.5 h-3.5 mr-1.5" />
          )}
          {exporting ? 'Exporting...' : 'Export CSV'}
        </Button>
      </div>

      {/* Filter Toolbar */}
      <Card className="bg-slate-900/40 border-white/5 p-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 select-none">
        {/* Agent Filter */}
        <div className="flex flex-col space-y-1.5">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Agent</label>
          <select
            value={filters.agent}
            onChange={(e) => handleFilterChange('agent', e.target.value)}
            className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-colors"
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
        <div className="flex flex-col space-y-1.5">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Decision</label>
          <select
            value={filters.decision}
            onChange={(e) => handleFilterChange('decision', e.target.value)}
            className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          >
            <option value="all">All Decisions</option>
            <option value="approved">Approved</option>
            <option value="auto-approved">Auto-Approved</option>
            <option value="rejected">Rejected</option>
            <option value="shadow">Shadow Sim</option>
          </select>
        </div>

        {/* Action Type Filter */}
        <div className="flex flex-col space-y-1.5">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Action Type</label>
          <select
            value={filters.action_type}
            onChange={(e) => handleFilterChange('action_type', e.target.value)}
            className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-colors"
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
        <div className="flex flex-col space-y-1.5">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Reviewer</label>
          <select
            value={filters.operator}
            onChange={(e) => handleFilterChange('operator', e.target.value)}
            className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          >
            <option value="all">All Operators</option>
            <option value="admin_operator">Admin Operator</option>
            <option value="system">Autonomous System</option>
          </select>
        </div>
      </Card>

      {/* Main Table Card */}
      <Card className="bg-slate-900/20 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] font-bold tracking-widest border-b border-white/5 select-none">
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
            <tbody className="divide-y divide-white/5 bg-slate-900/5">
              {isLoading ? (
                Array.from({ length: 10 }, (_, i) => <TableRowSkeleton key={i} />)
              ) : entries.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                    <AlertCircle className="w-8 h-8 mx-auto mb-3 text-slate-600" />
                    <span className="text-sm font-semibold">No audit entries found</span>
                    <p className="text-xs text-slate-600 mt-1">Try resetting filter options to locate historic decisions.</p>
                  </td>
                </tr>
              ) : (
                entries.map((entry) => {
                  const agentCol = getAgentColors(entry.agent);

                  return (
                    <tr key={entry.id} className="hover:bg-white/5 transition-colors">
                      {/* Timestamp */}
                      <td className="px-6 py-4 text-slate-400 font-medium whitespace-nowrap">
                        {formatDateTime(entry.timestamp)}
                      </td>
                      
                      {/* Agent */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase border ${agentCol.bg} ${agentCol.text} ${agentCol.border}`}>
                          {getAgentLabel(entry.agent)}
                        </span>
                      </td>

                      {/* Action Type */}
                      <td className="px-6 py-4 text-slate-200 font-semibold whitespace-nowrap">
                        {getActionTypeLabel(entry.action_type)}
                      </td>

                      {/* Decision */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={getDecisionBadgeVariant(entry.decision)}>
                          {entry.decision}
                        </Badge>
                      </td>

                      {/* Operator */}
                      <td className="px-6 py-4 font-mono text-slate-400 whitespace-nowrap">
                        {entry.operator || 'Autonomous System'}
                      </td>

                      {/* Impact */}
                      <td className="px-6 py-4 text-right font-mono font-bold text-slate-200 whitespace-nowrap">
                        {entry.financial_impact !== null ? formatCurrency(entry.financial_impact) : '—'}
                      </td>

                      {/* Action button */}
                      <td className="px-6 py-4 text-center whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setSelectedAudit(entry)}
                          className="h-8 w-8 text-slate-400 hover:text-slate-200"
                          title="Inspect JSON Payload"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
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
          <div className="px-6 py-4 border-t border-white/5 bg-slate-900/40 flex items-center justify-between select-none">
            <span className="text-xs text-slate-400">
              Showing <span className="font-semibold text-slate-350">{(page - 1) * limit + 1}</span> to{' '}
              <span className="font-semibold text-slate-350">
                {Math.min(page * limit, total)}
              </span>{' '}
              of <span className="font-semibold text-slate-350">{total}</span> records
            </span>

            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page === 1}
                className="h-8 w-8 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                disabled={page === totalPages}
                className="h-8 w-8 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* JSON Payload Inspection Dialog */}
      <AnimatePresence>
        {selectedAudit && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedAudit(null)}
              className="absolute inset-0 bg-slate-950/60 backdrop-blur-md"
            />
            {/* Modal Card */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              transition={{ type: "spring", duration: 0.4 }}
              className="relative bg-slate-900 border border-white/10 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 flex flex-col max-h-[85vh] overflow-hidden"
            >
              <div className="flex justify-between items-center text-blue-400 select-none">
                <h3 className="text-base font-bold text-slate-100 flex items-center">
                  <FileCheck className="w-5 h-5 mr-2" />
                  Audit Trail Payload Inspector
                </h3>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedAudit(null)}
                  className="h-8 w-8 text-slate-400 hover:text-slate-200"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs border border-white/5 rounded-xl p-3 bg-slate-950/50 select-none">
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

              <div className="flex-1 overflow-y-auto bg-slate-950 border border-white/5 rounded-xl p-4 font-mono text-[11px] text-blue-300 select-all">
                <pre>{JSON.stringify(selectedAudit.details || {}, null, 2)}</pre>
              </div>

              <div className="flex justify-end pt-2 select-none">
                <Button
                  variant="secondary"
                  onClick={() => setSelectedAudit(null)}
                  className="text-xs"
                >
                  Close Inspector
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AuditLog;
