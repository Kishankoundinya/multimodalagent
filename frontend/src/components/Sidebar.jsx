import React from 'react';
import {
  LayoutDashboard,
  FileText,
  Search,
  BarChart3,
  AlertTriangle,
  GitCompare,
  FileBarChart,
  History,
  Settings,
  ShieldCheck,
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'documents', label: 'Documents', icon: FileText },
    { id: 'research', label: 'Research', icon: Search },
    { id: 'metrics', label: 'Financial Metrics', icon: BarChart3 },
    { id: 'redflags', label: 'Red Flags', icon: AlertTriangle },
    { id: 'compare', label: 'Compare', icon: GitCompare },
    { id: 'reports', label: 'Reports', icon: FileBarChart },
    { id: 'history', label: 'History', icon: History },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 border-r border-slate-800">
      {/* Brand Header */}
      <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-800">
        <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center text-white font-bold text-base shadow-sm">
          AG
        </div>
        <div>
          <h1 className="text-sm font-semibold text-white tracking-wide">Financial AI</h1>
          <p className="text-xs text-slate-400">Multi-Agent System</p>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Grounding & Verification Indicator */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-slate-800/80 px-3 py-2 rounded border border-emerald-900/40">
          <ShieldCheck className="w-4 h-4 flex-shrink-0" />
          <span>Strict Page Grounding Enabled</span>
        </div>
        <div className="mt-2 text-[11px] text-slate-500 text-center">
          Google Gemini • Local RAG
        </div>
      </div>
    </aside>
  );
}
