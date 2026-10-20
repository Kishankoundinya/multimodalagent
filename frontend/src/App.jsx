import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import ResearchPage from './pages/ResearchPage';
import MetricsPage from './pages/MetricsPage';
import RedFlagsPage from './pages/RedFlagsPage';
import ComparePage from './pages/ComparePage';
import ReportsPage from './pages/ReportsPage';
import HistoryPage from './pages/HistoryPage';
import SettingsPage from './pages/SettingsPage';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [documents, setDocuments] = useState([]);
  const [history, setHistory] = useState([]);
  const [reports, setReports] = useState([]);
  const [health, setHealth] = useState(null);

  const fetchData = async () => {
    try {
      const [docsData, histData, repData, healthData] = await Promise.all([
        api.getDocuments().catch(() => []),
        api.getResearchHistory().catch(() => []),
        api.getReports().catch(() => []),
        api.getHealth().catch(() => null),
      ]);
      setDocuments(Array.isArray(docsData) ? docsData : []);
      setHistory(Array.isArray(histData) ? histData : []);
      setReports(Array.isArray(repData) ? repData : []);
      setHealth(healthData);
    } catch (e) {
      console.error('Failed to fetch initial application state:', e);
      setDocuments([]);
      setHistory([]);
      setReports([]);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Poll while any document is actively processing
  useEffect(() => {
    const isProcessing = Array.isArray(documents) && documents.some((d) =>
      d.processing_status && !['Completed', 'Failed'].includes(d.processing_status)
    );

    if (isProcessing) {
      const interval = setInterval(async () => {
        try {
          const docs = await api.getDocuments();
          if (Array.isArray(docs)) {
            setDocuments(docs);
          }
        } catch (e) {
          // ignore transient poll error
        }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [documents]);

  const getPageTitle = () => {
    switch (activeTab) {
      case 'dashboard':
        return 'Executive Overview & Activity';
      case 'documents':
        return 'Disclosure Document Repository';
      case 'research':
        return 'Grounded Financial Research';
      case 'metrics':
        return 'Primary Financial Metrics & Ratios';
      case 'redflags':
        return 'Financial Red Flags & Risk Indicators';
      case 'compare':
        return 'Peer Entity Financial Comparison';
      case 'reports':
        return 'Analyst Research Reports';
      case 'history':
        return 'Research & Query History';
      case 'settings':
        return 'System & Model Configuration';
      default:
        return 'Financial AI Platform';
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar title={getPageTitle()} health={health} />

        <main className="flex-1 overflow-y-auto p-8">
          {activeTab === 'dashboard' && (
            <DashboardPage
              documents={documents}
              history={history}
              reports={reports}
              setActiveTab={setActiveTab}
            />
          )}
          {activeTab === 'documents' && (
            <DocumentsPage documents={documents} onRefresh={fetchData} />
          )}
          {activeTab === 'research' && (
            <ResearchPage documents={documents} onQueryComplete={fetchData} />
          )}
          {activeTab === 'metrics' && (
            <MetricsPage documents={documents} />
          )}
          {activeTab === 'redflags' && (
            <RedFlagsPage documents={documents} />
          )}
          {activeTab === 'compare' && (
            <ComparePage documents={documents} />
          )}
          {activeTab === 'reports' && (
            <ReportsPage documents={documents} reports={reports} onRefresh={fetchData} />
          )}
          {activeTab === 'history' && (
            <HistoryPage history={history} />
          )}
          {activeTab === 'settings' && (
            <SettingsPage />
          )}
        </main>
      </div>
    </div>
  );
}
