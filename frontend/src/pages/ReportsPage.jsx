import React, { useState } from 'react';
import { FileBarChart, Download, FileText, CheckCircle2, Clock, AlertCircle, Plus } from 'lucide-react';
import { api } from '../services/api';

export default function ReportsPage({ documents, reports, onRefresh }) {
  const docList = Array.isArray(documents) ? documents : [];
  const repList = Array.isArray(reports) ? reports : [];
  const [selectedDocId, setSelectedDocId] = useState('');
  const [customTitle, setCustomTitle] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const completedDocs = docList.filter((d) => d.processing_status === 'Completed');

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!selectedDocId) {
      setError('Please select an indexed document.');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      await api.generateReport({
        document_id: selectedDocId,
        title: customTitle.trim() || undefined,
      });
      setCustomTitle('');
      onRefresh();
    } catch (err) {
      setError(err.message || 'Report generation failed.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Generate Report Card */}
      <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-1">Generate Equity Research PDF Report</h3>
        <p className="text-xs text-slate-500 mb-4">
          Runs the full Report Agent multi-step pipeline (Extraction, Red Flag analysis, Executive Summary, Table generation) and compiles an analyst-grade PDF with ReportLab.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleGenerate} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div className="md:col-span-1">
            <label className="block text-xs font-semibold text-slate-700 mb-1">Target Document</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            >
              <option value="">Select Indexed Filing</option>
              {completedDocs.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.company} ({doc.fiscal_year}) — {doc.filename}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-1">
            <label className="block text-xs font-semibold text-slate-700 mb-1">Report Title (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Comprehensive Annual Equity Report"
              value={customTitle}
              onChange={(e) => setCustomTitle(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded px-3 py-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="md:col-span-1">
            <button
              type="submit"
              disabled={generating || !selectedDocId}
              className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-colors"
            >
              {generating ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  <span>Synthesizing PDF...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Generate Report</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Generated Reports Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h3 className="text-sm font-semibold text-slate-900">Generated Research Reports</h3>
          <p className="text-xs text-slate-500">
            Reports are generated strictly on-demand. Click "Download PDF" to save the verified analyst report.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Report Title</th>
                <th className="px-6 py-3">Entity</th>
                <th className="px-6 py-3">Period</th>
                <th className="px-6 py-3">Generated Date</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {repList.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-slate-400">
                    No reports generated yet. Select a document above to create your first report.
                  </td>
                </tr>
              ) : (
                repList.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50">
                    <td className="px-6 py-3 font-semibold text-slate-900 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      <span>{r.title}</span>
                    </td>
                    <td className="px-6 py-3 font-medium text-slate-800">{r.company}</td>
                    <td className="px-6 py-3">{r.fiscal_year}</td>
                    <td className="px-6 py-3 text-slate-500">
                      {new Date(r.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-3 text-right">
                      <a
                        href={api.getReportDownloadUrl(r.id)}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded text-xs font-semibold border border-blue-200 transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download PDF</span>
                      </a>
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
