import React, { useState } from 'react';
import { GitCompare, ArrowRight, ShieldCheck, AlertCircle, Sparkles } from 'lucide-react';
import { api } from '../services/api';

export default function ComparePage({ documents }) {
  const docList = Array.isArray(documents) ? documents : [];
  const uniqueCompanies = Array.from(new Set(docList.map((d) => d.company))).filter(Boolean);

  const [companyA, setCompanyA] = useState(uniqueCompanies[0] || '');
  const [companyB, setCompanyB] = useState(uniqueCompanies[1] || uniqueCompanies[0] || '');
  const [yearA, setYearA] = useState('');
  const [yearB, setYearB] = useState('');
  const [loading, setLoading] = useState(false);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [error, setError] = useState('');

  const handleCompare = async (e) => {
    e.preventDefault();
    if (!companyA || !companyB) {
      setError('Please select both Company A and Company B.');
      return;
    }

    setLoading(true);
    setError('');
    setComparisonResult(null);

    try {
      const res = await api.compareCompanies({
        company_a: companyA,
        company_b: companyB,
        fiscal_year_a: yearA || undefined,
        fiscal_year_b: yearB || undefined,
      });
      setComparisonResult(res);
    } catch (err) {
      setError(err.message || 'Comparison failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Selector Card */}
      <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-1">Company Peer Comparison</h3>
        <p className="text-xs text-slate-500 mb-4">
          Select two indexed companies to generate an objective, side-by-side metric comparison with exact source pages.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleCompare} className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-700 mb-1">Company A</label>
            <select
              value={companyA}
              onChange={(e) => setCompanyA(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            >
              <option value="">Select Company A</option>
              {uniqueCompanies.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className="hidden md:flex justify-center items-center pb-2 text-slate-400">
            <GitCompare className="w-5 h-5" />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-700 mb-1">Company B</label>
            <select
              value={companyB}
              onChange={(e) => setCompanyB(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            >
              <option value="">Select Company B</option>
              {uniqueCompanies.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-5 flex justify-end">
            <button
              type="submit"
              disabled={loading || !companyA || !companyB}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded text-xs font-semibold flex items-center gap-2 shadow-sm transition-colors"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Comparing Entities...</span>
                </>
              ) : (
                <>
                  <GitCompare className="w-4 h-4" />
                  <span>Execute Comparison</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Comparison Results */}
      {comparisonResult && (
        <div className="space-y-6">
          {/* Objective Narrative Synthesis */}
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3 mb-4">
              <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-600" />
                <span>Objective Synthesis Analysis</span>
              </h4>
              <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Factual & Non-Subjective
              </span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
              {comparisonResult.summary}
            </p>
          </div>

          {/* Side-by-Side Metrics Table */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="text-sm font-semibold text-slate-900">
                Side-by-Side Numerical Comparison: {comparisonResult.company_a} vs {comparisonResult.company_b}
              </h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3">Metric</th>
                    <th className="px-6 py-3">{comparisonResult.company_a}</th>
                    <th className="px-6 py-3">{comparisonResult.company_b}</th>
                    <th className="px-6 py-3">Factual Difference Note</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {comparisonResult.metrics_comparison?.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="px-6 py-8 text-center text-slate-400">
                        No overlapping metrics found between the selected companies.
                      </td>
                    </tr>
                  ) : (
                    comparisonResult.metrics_comparison.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-6 py-3 font-semibold text-slate-900">{row.metric}</td>
                        <td className="px-6 py-3">
                          <span className="font-mono text-slate-900 font-medium">{row.company_a_val}</span>
                          {row.company_a_page && (
                            <span className="ml-2 text-[10px] text-blue-600 font-mono bg-blue-50 px-1 py-0.5 rounded">
                              p. {row.company_a_page}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-3">
                          <span className="font-mono text-slate-900 font-medium">{row.company_b_val}</span>
                          {row.company_b_page && (
                            <span className="ml-2 text-[10px] text-blue-600 font-mono bg-blue-50 px-1 py-0.5 rounded">
                              p. {row.company_b_page}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-3 text-slate-600 text-[11px]">
                          {row.difference_note || '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
