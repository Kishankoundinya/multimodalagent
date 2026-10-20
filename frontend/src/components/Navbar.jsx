import React from 'react';
import { Activity, Cpu, Database } from 'lucide-react';

export default function Navbar({ title, health }) {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between flex-shrink-0">
      <div>
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h2>
      </div>

      <div className="flex items-center gap-4 text-xs">
        {/* Device & Model Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
          <Cpu className="w-3.5 h-3.5 text-blue-600" />
          <span className="font-medium">{health?.llm_model || 'Gemini 1.5 Flash'}</span>
        </div>

        {/* Database Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
          <Database className="w-3.5 h-3.5 text-indigo-600" />
          <span>ChromaDB Vector Store</span>
        </div>

        {/* System Health */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-medium">System Online</span>
        </div>
      </div>
    </header>
  );
}
