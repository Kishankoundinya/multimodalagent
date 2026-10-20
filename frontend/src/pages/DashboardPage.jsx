import React from 'react';
import { FileText, Building2, Search, FileBarChart, ArrowRight, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function DashboardPage({ documents, history, reports, setActiveTab }) {
  const docs = Array.isArray(documents) ? documents : [];
  const hist = Array.isArray(history) ? history : [];
  const reps = Array.isArray(reports) ? reports : [];

  const uniqueCompanies = Array.from(new Set(docs.map((d) => d.company))).filter(Boolean);

  const stats = [
    { label: 'Documents Indexed', value: docs.filter((d) => d.processing_status === 'Completed').length, icon: FileText, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Tracked Companies', value: uniqueCompanies.length, icon: Building2, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { label: 'Research Queries', value: hist.length, icon: Search, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Reports Generated', value: reps.length, icon: FileBarChart, color: 'text-amber-600', bg: 'bg-amber-50' },
  ];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Completed':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800"><CheckCircle2 className="w-3 h-3" /> Completed</span>;
      case 'Failed':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-100 text-rose-800"><AlertCircle className="w-3 h-3" /> Failed</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800"><Clock className="w-3 h-3 animate-spin" /> {status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {stats.map((s, idx) => {
          const Icon = s.icon;
          return (
            <div key={idx} className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{s.label}</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{s.value}</p>
              </div>
              <div className={`w-11 h-11 rounded-lg ${s.bg} ${s.color} flex items-center justify-center`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Sections Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Documents Card */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Recent Financial Filings</h3>
            <button
              onClick={() => setActiveTab('documents')}
              className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              View all <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="flex-1 divide-y divide-slate-100">
            {docs.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm">
                No documents uploaded yet. Upload a company annual report to begin analysis.
              </div>
            ) : (
              docs.slice(0, 5).map((doc) => (
                <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-slate-50">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{doc.company} ({doc.fiscal_year})</p>
                    <p className="text-xs text-slate-500">{doc.filename} • {doc.num_pages} pages • {doc.num_chunks} chunks</p>
                  </div>
                  <div>
                    {getStatusBadge(doc.processing_status)}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Research Activity Card */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">Recent Research Activity</h3>
            <button
              onClick={() => setActiveTab('history')}
              className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              View history <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="flex-1 divide-y divide-slate-100">
            {hist.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm">
                No research queries yet. Ask a question on the Research page.
              </div>
            ) : (
              hist.slice(0, 5).map((h) => (
                <div key={h.id} className="p-4 hover:bg-slate-50">
                  <p className="text-sm font-medium text-slate-800 line-clamp-1">{h.question}</p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                    <span>{h.company || 'All Companies'}</span>
                    <span>•</span>
                    <span>{h.sources?.length || 0} citations validated</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Quick Launch Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-lg p-6 text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h4 className="text-base font-semibold">Grounded Financial Research Multi-Agent Engine</h4>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            Powered by Google Gemini (Free Tier) and ChromaDB to analyze PDF annual reports with 100% verified page citations, instant cloud inference, and zero hallucination.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('documents')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md text-xs font-semibold text-white shadow-sm"
          >
            Upload Filing
          </button>
          <button
            onClick={() => setActiveTab('research')}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-md text-xs font-semibold text-white"
          >
            Query Research
          </button>
        </div>
      </div>
    </div>
  );
}
