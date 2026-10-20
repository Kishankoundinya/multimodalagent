import React, { useState } from 'react';
import { History, Search, BookOpen, ShieldCheck, ChevronRight } from 'lucide-react';

export default function HistoryPage({ history }) {
  const histList = Array.isArray(history) ? history : [];
  const [selectedItem, setSelectedItem] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredHistory = histList.filter(
    (h) =>
      h.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (h.company && h.company.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-8.5rem)]">
      {/* Left List of Queries */}
      <div className="lg:col-span-1 bg-white rounded-lg border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        <div className="p-4 border-b border-slate-200 space-y-3">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-semibold text-slate-900">Analysis History</h3>
          </div>
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search previous queries..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
          {filteredHistory.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs">
              No analysis queries found in history.
            </div>
          ) : (
            filteredHistory.map((item) => {
              const isSelected = selectedItem?.id === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setSelectedItem(item)}
                  className={`w-full text-left p-3.5 transition-colors flex items-center justify-between ${
                    isSelected ? 'bg-blue-50/70 border-l-4 border-blue-600' : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="min-w-0 flex-1 pr-2">
                    <p className="text-xs font-semibold text-slate-900 truncate">{item.question}</p>
                    <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-1">
                      <span>{item.company || 'All Companies'}</span>
                      <span>•</span>
                      <span>{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Right Detail Viewer */}
      <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 shadow-sm overflow-y-auto p-6 flex flex-col">
        {!selectedItem ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 text-xs">
            <BookOpen className="w-8 h-8 text-slate-300 mb-2" />
            <p>Select a past research query from the list to view its verified answer and citations.</p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="border-b border-slate-200 pb-4">
              <span className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                {selectedItem.company || 'General Analysis'}
              </span>
              <h2 className="text-base font-bold text-slate-900 mt-2">{selectedItem.question}</h2>
              <p className="text-xs text-slate-400 mt-1">
                Executed on {new Date(selectedItem.created_at).toLocaleString()}
              </p>
            </div>

            {/* Answer Content */}
            <div className="prose prose-xs text-slate-800 max-w-none whitespace-pre-line leading-relaxed bg-slate-50 p-4 rounded-lg border border-slate-200">
              {selectedItem.answer}
            </div>

            {/* Citations List */}
            {selectedItem.sources && selectedItem.sources.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-900">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Grounding Source Evidence ({selectedItem.sources.length} Verified Sources)</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {selectedItem.sources.map((src, i) => (
                    <div key={i} className="bg-white p-3 rounded border border-slate-200 text-xs">
                      <div className="flex items-center justify-between font-semibold text-slate-800">
                        <span className="truncate max-w-[180px]">{src.source_document}</span>
                        <span className="text-blue-700 bg-blue-50 px-2 py-0.5 rounded font-mono text-[11px]">
                          Page {src.page}
                        </span>
                      </div>
                      {src.snippet && (
                        <p className="text-slate-500 text-[11px] mt-2 italic font-serif leading-normal line-clamp-3">
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
    </div>
  );
}
