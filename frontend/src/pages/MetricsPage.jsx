import React, { useState, useEffect } from 'react';
import { BarChart3, RefreshCw, Calculator, ShieldCheck, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function MetricsPage({ documents }) {
  const docList = Array.isArray(documents) ? documents : [];
  const [selectedDocId, setSelectedDocId] = useState('');
  const [metricsData, setMetricsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const completedDocs = docList.filter((d) => d.processing_status === 'Completed');

  useEffect(() => {
    if (completedDocs.length > 0 && !selectedDocId) {
      setSelectedDocId(completedDocs[0].id);
    }
  }, [documents]);

  useEffect(() => {
    if (selectedDocId) {
      fetchMetrics(selectedDocId);
    }
  }, [selectedDocId]);

  const fetchMetrics = async (docId) => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getMetrics(docId);
      setMetricsData(data);
    } catch (err) {
      setError(err.message || 'Failed to load financial metrics.');
      setMetricsData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleForceExtract = async () => {
    if (!selectedDocId) return;
    setLoading(true);
    try {
      const data = await api.forceExtractMetrics(selectedDocId);
      setMetricsData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold text-slate-700">Select Document:</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="text-xs border border-slate-300 rounded px-3 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {completedDocs.length === 0 ? (
              <option value="">No completed documents available</option>
            ) : (
              completedDocs.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.company} — {doc.fiscal_year} ({doc.filename})
                </option>
              ))
            )}
          </select>
        </div>

        <button
          onClick={handleForceExtract}
          disabled={loading || !selectedDocId}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 disabled:opacity-50 text-slate-700 rounded text-xs font-medium flex items-center gap-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Re-Extract Metrics</span>
        </button>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Extracted Core Metrics Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Extracted Primary Financial Metrics</h3>
            <p className="text-xs text-slate-500">
              Directly extracted from disclosed financial statements with verified page citations.
            </p>
          </div>
          <div className="flex items-center gap-1 text-[11px] text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Exact Disclosed Values</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Metric</th>
                <th className="px-6 py-3">Reported Value</th>
                <th className="px-6 py-3">Unit</th>
                <th className="px-6 py-3">Period</th>
                <th className="px-6 py-3">Entity</th>
                <th className="px-6 py-3">Source Page</th>
                <th className="px-6 py-3">Source Document</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-8 text-center text-slate-400">
                    Extracting grounded metrics via Extraction Agent...
                  </td>
                </tr>
              ) : !metricsData || metricsData.metrics?.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-8 text-center text-slate-400">
                    No primary metrics extracted yet. Ensure the document contains text-based financial statements.
                  </td>
                </tr>
              ) : (
                metricsData.metrics.map((m, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-6 py-3 font-semibold text-slate-900">{m.metric}</td>
                    <td className="px-6 py-3 font-mono text-blue-700 font-medium">{m.value || 'null'}</td>
                    <td className="px-6 py-3 text-slate-500">{m.unit || 'USD'}</td>
                    <td className="px-6 py-3">{m.period || metricsData.fiscal_year}</td>
                    <td className="px-6 py-3">{m.company}</td>
                    <td className="px-6 py-3">
                      <span className="bg-slate-100 px-2 py-0.5 rounded font-mono text-[11px]">
                        p. {m.page || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-slate-500 truncate max-w-xs">{m.source_document}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Calculated Financial Ratios */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-semibold text-slate-900">Calculated Financial Ratios</h3>
          </div>
          <span className="text-[11px] font-medium text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
            Calculated from source values
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Ratio</th>
                <th className="px-6 py-3">Calculated Value</th>
                <th className="px-6 py-3">Formula & Source Base Values</th>
                <th className="px-6 py-3">Source Pages</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {!metricsData || metricsData.calculated_ratios?.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-6 py-8 text-center text-slate-400">
                    Ratios are computed strictly when underlying base metrics (Debt, Equity, Revenue, Assets) are available.
                  </td>
                </tr>
              ) : (
                metricsData.calculated_ratios.map((r, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-6 py-3 font-semibold text-slate-900">{r.metric}</td>
                    <td className="px-6 py-3 font-mono font-bold text-indigo-700">{r.value}</td>
                    <td className="px-6 py-3 text-slate-600 font-mono text-[11px]">
                      {r.calculation_formula || r.source_text}
                    </td>
                    <td className="px-6 py-3">
                      <span className="bg-slate-100 px-2 py-0.5 rounded font-mono text-[11px]">
                        p. {r.page || 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
