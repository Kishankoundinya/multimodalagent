import React, { useState, useEffect } from 'react';
import {
  Settings,
  Save,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Sliders,
  Key,
  ExternalLink,
  Eye,
  EyeOff,
  Sparkles,
  Cloud,
  Database,
} from 'lucide-react';
import { api } from '../services/api';

export default function SettingsPage() {
  const [config, setConfig] = useState(null);
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [chromaKey, setChromaKey] = useState('');
  const [showChromaKey, setShowChromaKey] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setConfig(data);
    } catch (err) {
      setError(err.message || 'Failed to load settings.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    setError('');

    try {
      const payload = {
        llm_model: config.llm_model,
        temperature: parseFloat(config.temperature),
        max_new_tokens: parseInt(config.max_new_tokens, 10),
        chunk_size: parseInt(config.chunk_size, 10),
        chunk_overlap: parseInt(config.chunk_overlap, 10),
        top_k: parseInt(config.top_k, 10),
        max_retrieval_steps: parseInt(config.max_retrieval_steps, 10),
      };

      if (apiKey.trim()) {
        payload.gemini_api_key = apiKey.trim();
      }

      if (chromaKey.trim()) {
        payload.chroma_db_api_key = chromaKey.trim();
      }

      const updated = await api.updateSettings(payload);
      setConfig(updated);
      setApiKey('');
      setChromaKey('');
      setMessage('Settings, Google Gemini, and Chroma Cloud configuration saved successfully.');
    } catch (err) {
      setError(err.message || 'Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400 text-xs">
        Loading system configuration...
      </div>
    );
  }

  const isConfigured = config?.gemini_api_key_configured;

  return (
    <div className="max-w-3xl space-y-6">
      {/* Gemini Integration Section */}
      <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-semibold text-slate-900">Google Gemini LLM (Free Tier)</h3>
          </div>
          <div
            className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 ${
              isConfigured
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-amber-50 text-amber-700 border border-amber-200'
            }`}
          >
            {isConfigured ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>API Key Configured</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5" />
                <span>API Key Required</span>
              </>
            )}
          </div>
        </div>

        <p className="text-xs text-slate-500 mb-5">
          Powered by Google Gemini cloud models. Replaces local TinyLlama to eliminate heavy RAM overhead,
          PyTorch model downloads, and slow CPU latency.
        </p>

        <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-slate-500" />
                Gemini API Key
              </label>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-blue-600 hover:text-blue-800 flex items-center gap-1 font-medium"
              >
                <span>Get Free API Key at Google AI Studio</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={isConfigured ? '•••••••••••••••••••••••• (API Key Saved)' : 'Enter AIzaSy...'}
                className="w-full text-xs border border-slate-300 rounded px-3 py-2 pr-10 text-slate-800 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
              >
                {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              Free tier includes 15 Requests Per Minute (RPM) and 1,500 Requests Per Day. Keys are stored safely in .env.
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Gemini Model</label>
            <select
              value={config?.llm_model || 'gemini-1.5-flash'}
              onChange={(e) => setConfig({ ...config, llm_model: e.target.value })}
              className="w-full text-xs border border-slate-300 rounded px-3 py-2 text-slate-800 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
            >
              <option value="gemini-flash-lite-latest">gemini-flash-lite-latest (Recommended • Ultra Fast & High Availability)</option>
              <option value="gemini-3.5-flash-lite">gemini-3.5-flash-lite (Stable Free Tier)</option>
              <option value="gemini-3.1-flash-lite">gemini-3.1-flash-lite (Lightweight Fast)</option>
              <option value="gemini-3.5-flash">gemini-3.5-flash (Advanced Reasoning)</option>
            </select>
          </div>
        </div>
      </div>

      {/* ChromaDB Cloud Vector Store Section */}
      <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Cloud className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-semibold text-slate-900">ChromaDB Cloud Vector Store</h3>
          </div>
          <div
            className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 ${
              config?.chroma_db_api_key_configured
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-slate-100 text-slate-700 border border-slate-200'
            }`}
          >
            {config?.chroma_db_api_key_configured ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Chroma Cloud Active</span>
              </>
            ) : (
              <>
                <Database className="w-3.5 h-3.5 text-slate-500" />
                <span>Local Persistent ChromaDB</span>
              </>
            )}
          </div>
        </div>

        <p className="text-xs text-slate-500 mb-5">
          Offloads vector indexing and embeddings to Chroma Cloud. Completely prevents container memory limit spikes
          on Render free tier (512MB RAM) when uploading multi-page PDF documents.
        </p>

        <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-slate-500" />
                Chroma Cloud API Key
              </label>
              <a
                href="https://cloud.trychroma.com"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-blue-600 hover:text-blue-800 flex items-center gap-1 font-medium"
              >
                <span>Chroma Cloud Console (cloud.trychroma.com)</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <div className="relative">
              <input
                type={showChromaKey ? 'text' : 'password'}
                value={chromaKey}
                onChange={(e) => setChromaKey(e.target.value)}
                placeholder={config?.chroma_db_api_key_configured ? '•••••••••••••••••••••••• (Chroma Cloud Active)' : 'Enter ck-...'}
                className="w-full text-xs border border-slate-300 rounded px-3 py-2 pr-10 text-slate-800 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowChromaKey(!showChromaKey)}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
              >
                {showChromaKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              Current vector store mode: <strong className="text-slate-700 font-mono">{config?.chroma_mode || 'Local Persistent ChromaDB'}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* System RAG Parameters */}
      <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <Sliders className="w-5 h-5 text-blue-600" />
          <h3 className="text-base font-semibold text-slate-900">RAG & Generation Parameters</h3>
        </div>
        <p className="text-xs text-slate-500 mb-6">
          Fine-tune LangChain RAG chunking and Gemini temperature values for deterministic financial analysis.
        </p>

        {message && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded text-emerald-700 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{message}</span>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Embedding Model</label>
              <input
                type="text"
                value={config?.embedding_model || ''}
                disabled
                className="w-full text-xs border border-slate-200 bg-slate-50 text-slate-500 rounded px-3 py-2 cursor-not-allowed font-mono"
              />
              <span className="text-[10px] text-slate-400">Lightweight Local Sentence Transformers</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Temperature (Deterministic)</label>
              <input
                type="number"
                step="0.05"
                min="0.0"
                max="1.0"
                value={config?.temperature ?? 0.2}
                onChange={(e) => setConfig({ ...config, temperature: e.target.value })}
                className="w-full text-xs border border-slate-300 rounded px-3 py-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <span className="text-[10px] text-slate-400">Default: 0.2 for strict, grounded answers</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Max Output Tokens</label>
              <input
                type="number"
                step="64"
                min="64"
                max="4096"
                value={config?.max_new_tokens || 1024}
                onChange={(e) => setConfig({ ...config, max_new_tokens: e.target.value })}
                className="w-full text-xs border border-slate-300 rounded px-3 py-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <span className="text-[10px] text-slate-400">Default: 1024 tokens</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Top K Retrieved Chunks</label>
              <input
                type="number"
                min="1"
                max="15"
                value={config?.top_k || 4}
                onChange={(e) => setConfig({ ...config, top_k: e.target.value })}
                className="w-full text-xs border border-slate-300 rounded px-3 py-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <span className="text-[10px] text-slate-400">Default: 4 chunks passed to context</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Chunk Size (Characters)</label>
              <input
                type="number"
                step="50"
                min="200"
                max="4000"
                value={config?.chunk_size || 1000}
                onChange={(e) => setConfig({ ...config, chunk_size: e.target.value })}
                className="w-full text-xs border border-slate-300 rounded px-3 py-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <span className="text-[10px] text-slate-400">Default: 1000 characters per chunk</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Chunk Overlap</label>
              <input
                type="number"
                step="10"
                min="0"
                max="500"
                value={config?.chunk_overlap || 150}
                onChange={(e) => setConfig({ ...config, chunk_overlap: e.target.value })}
                className="w-full text-xs border border-slate-300 rounded px-3 py-2 text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <span className="text-[10px] text-slate-400">Default: 150 characters overlap</span>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-200 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'Saving...' : 'Save Settings'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
