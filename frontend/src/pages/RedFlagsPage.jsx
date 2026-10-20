import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldCheck, AlertCircle, RefreshCw, FileText } from 'lucide-react';
import { api } from '../services/api';

export default function RedFlagsPage({ documents }) {
  const docList = Array.isArray(documents) ? documents : [];
  const [selectedDocId, setSelectedDocId] = useState('');
  const [redFlags, setRedFlags] = useState([]);
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
      fetchRedFlags(selectedDocId);
    } else {
      fetchAllRedFlags();
    }
  }, [selectedDocId]);

  const fetchRedFlags = async (docId) => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getRedFlagsForDoc(docId);
      setRedFlags(data.items || []);
    } catch (err) {
      setError(err.message || 'Failed to load red flags.');
      setRedFlags([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllRedFlags = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getAllRedFlags();
      setRedFlags(data.items || []);
    } catch (err) {
      setError(err.message || 'Failed to load red flags.');
      setRedFlags([]);
    } finally {
      setLoading(false);
    }
  };

  const renderSeverityBadge = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800">
            HIGH
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
            MEDIUM
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
            LOW
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold text-slate-700">Filter by Filing:</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="text-xs border border-slate-300 rounded px-3 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Tracked Filings</option>
            {completedDocs.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.company} — {doc.fiscal_year} ({doc.filename})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Strictly Evidence-Supported • No Speculative Assumptions</span>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Red Flags Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Document-Supported Financial Warning Indicators</h3>
            <p className="text-xs text-slate-500">
              Auditor notes, covenant risks, liquidity concerns, and deteriorating margins directly evidenced in filings.
            </p>
          </div>
          <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2.5 py-1 rounded">
            {redFlags.length} Indicators Flagged
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Severity</th>
                <th className="px-6 py-3">Warning Indicator</th>
                <th className="px-6 py-3">Documented Evidence & Quote</th>
                <th className="px-6 py-3">Entity</th>
                <th className="px-6 py-3">Source Page</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-slate-400">
                    Scanning filing sections for grounded warning indicators...
                  </td>
                </tr>
              ) : redFlags.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-slate-400">
                    No material warning flags identified in the provided documents.
                  </td>
                </tr>
              ) : (
                redFlags.map((rf, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-6 py-3 align-top">{renderSeverityBadge(rf.severity)}</td>
                    <td className="px-6 py-3 align-top">
                      <p className="font-semibold text-slate-900">{rf.title}</p>
                      <p className="text-slate-500 text-[11px] mt-0.5">{rf.description}</p>
                    </td>
                    <td className="px-6 py-3 align-top max-w-md">
                      <p className="font-serif italic text-slate-700 bg-slate-50 p-2 rounded border border-slate-200 text-[11px] leading-relaxed">
                        "{rf.evidence}"
                      </p>
                    </td>
                    <td className="px-6 py-3 align-top font-medium text-slate-800">{rf.company}</td>
                    <td className="px-6 py-3 align-top">
                      <span className="bg-slate-100 px-2 py-0.5 rounded font-mono text-[11px]">
                        p. {rf.page || 'N/A'}
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
