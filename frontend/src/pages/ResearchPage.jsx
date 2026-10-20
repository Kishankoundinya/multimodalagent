import React, { useState } from 'react';
import { Search, Send, ShieldCheck, AlertCircle, FileText, CornerDownLeft, Sparkles, BookOpen } from 'lucide-react';
import { api } from '../services/api';

export default function ResearchPage({ documents, onQueryComplete }) {
  const docList = Array.isArray(documents) ? documents : [];
  const [question, setQuestion] = useState('');
  const [selectedCompany, setSelectedCompany] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState('');

  const uniqueCompanies = Array.from(new Set(docList.map((d) => d.company))).filter(Boolean);

  const sampleQuestions = [
    "What are the company's revenue, net income, total debt and major financial risks?",
    "What was the total revenue and how did it change year-over-year?",
    "What are the major debt maturities and liquidity commitments?",
    "What did the independent auditors report regarding internal controls?",
  ];

  const handleSearch = async (queryText) => {
    const q = queryText || question;
    if (!q || !q.trim()) return;

    setError('');
    setLoading(true);

    const userMessage = {
      role: 'user',
      content: q,
      company: selectedCompany || null,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuestion('');

    try {
      const response = await api.executeResearch({
        question: q,
        company: selectedCompany || undefined,
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        isGrounded: response.is_grounded,
        iterations: response.iterations_used,
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      if (onQueryComplete) onQueryComplete();
    } catch (err) {
      setError(err.message || 'Failed to execute research query.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] space-y-4">
      {/* Top Controls Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold text-slate-700">Target Entity Filter:</label>
          <select
            value={selectedCompany}
            onChange={(e) => setSelectedCompany(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Indexed Filings</option>
            {uniqueCompanies.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Strict Page-Grounded AI • Never Hallucinates</span>
        </div>
      </div>

      {/* Chat Messages Area */}
      <div className="flex-1 bg-white rounded-lg border border-slate-200 shadow-sm overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-lg mx-auto">
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-900">Financial Research Assistant</h3>
            <p className="text-xs text-slate-500 mt-1 mb-6">
              Ask deep questions about indexed company reports. The Research Agent retrieves relevant pages, synthesizes answers, and cites exact page numbers.
            </p>

            <div className="w-full space-y-2 text-left">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Suggested Questions</p>
              {sampleQuestions.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setQuestion(sq);
                    handleSearch(sq);
                  }}
                  className="w-full text-left p-2.5 rounded border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 text-xs text-slate-700 transition-colors flex items-center justify-between group"
                >
                  <span>{sq}</span>
                  <Sparkles className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 flex-shrink-0 ml-2" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, idx) => (
            <div key={idx} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div
                className={`max-w-3xl rounded-lg p-4 text-xs leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-slate-50 border border-slate-200 text-slate-800'
                }`}
              >
                {m.role === 'user' ? (
                  <p className="whitespace-pre-wrap font-medium">{m.content}</p>
                ) : (
                  <div className="space-y-3">
                    {/* Grounding Status Header */}
                    <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                      <div className="flex items-center gap-1.5 font-semibold text-slate-900">
                        <BookOpen className="w-4 h-4 text-blue-600" />
                        <span>Research Findings</span>
                      </div>
                      {m.isGrounded ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          <ShieldCheck className="w-3.5 h-3.5" /> Source Grounded
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                          <AlertCircle className="w-3.5 h-3.5" /> Disclosed Info Not Found
                        </span>
                      )}
                    </div>

                    {/* Answer Body */}
                    <div className="prose prose-xs text-slate-800 max-w-none whitespace-pre-line leading-relaxed">
                      {m.content}
                    </div>

                    {/* Source Citations Block */}
                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-200 space-y-2">
                        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                          Verified Document Sources
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {m.sources.map((src, sIdx) => (
                            <div key={sIdx} className="bg-white p-2.5 rounded border border-slate-200 text-[11px]">
                              <div className="flex items-center justify-between font-semibold text-slate-800">
                                <span className="truncate max-w-[180px]">{src.source_document}</span>
                                <span className="text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded font-mono">
                                  Page {src.page}
                                </span>
                              </div>
                              {src.snippet && (
                                <p className="text-slate-500 mt-1 line-clamp-2 italic font-serif">
                                  "{src.snippet}"
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 px-1">{m.timestamp}</span>
            </div>
          ))
        )}

        {loading && (
          <div className="flex items-start">
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 max-w-md text-xs text-slate-600 flex items-center gap-3">
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <span>Multi-agent retrieval & citation verification in progress...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Question Input Box */}
      <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask any financial research question (e.g. 'What was the total revenue, net income and debt?')..."
          rows={1}
          className="flex-1 text-xs resize-none focus:outline-none text-slate-800 placeholder-slate-400 py-1"
        />
        <button
          onClick={() => handleSearch()}
          disabled={loading || !question.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors flex-shrink-0"
        >
          <span>Ask</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
