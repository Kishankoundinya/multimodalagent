import React, { useState, useEffect } from 'react';
import { Upload, FileText, CheckCircle2, Clock, AlertCircle, RefreshCw, Trash2, FolderPlus, ArrowUpRight } from 'lucide-react';
import { api } from '../services/api';

export default function DocumentsPage({ documents, onRefresh }) {
  const docList = Array.isArray(documents) ? documents : [];
  const [file, setFile] = useState(null);
  const [company, setCompany] = useState('');
  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear().toString());
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [seedDocs, setSeedDocs] = useState([]);
  const [indexingSeed, setIndexingSeed] = useState({});

  useEffect(() => {
    loadSeedDocs();
  }, [documents]);

  const loadSeedDocs = async () => {
    try {
      const seeds = await api.getSeedDocuments();
      setSeedDocs(Array.isArray(seeds) ? seeds : []);
    } catch (e) {
      console.warn('Could not load seed docs:', e);
      setSeedDocs([]);
    }
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setUploadError('Only PDF files are supported.');
        setFile(null);
        return;
      }
      setFile(selected);
      setUploadError('');
      // Guess company name from filename
      const clean = selected.name.replace(/\.pdf$/i, '').replace(/[\-_]/g, ' ');
      if (!company) {
        setCompany(clean.split(' ')[0].toUpperCase());
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !company || !fiscalYear) {
      setUploadError('Please provide a PDF file, company name, and fiscal year.');
      return;
    }

    setUploading(true);
    setUploadError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('company', company);
    formData.append('fiscal_year', fiscalYear);
    formData.append('auto_process', 'true');

    try {
      await api.uploadDocument(formData);
      setFile(null);
      setCompany('');
      onRefresh();
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleProcessAgain = async (docId) => {
    try {
      await api.processDocument(docId);
      onRefresh();
    } catch (err) {
      alert(`Processing error: ${err.message}`);
    }
  };

  const handleDelete = async (docId) => {
    if (!confirm('Are you sure you want to delete this document and remove its indexed vectors?')) return;
    try {
      await api.deleteDocument(docId);
      onRefresh();
    } catch (err) {
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  const handleIndexSeed = async (seed) => {
    setIndexingSeed((prev) => ({ ...prev, [seed.filename]: true }));
    try {
      await api.indexSeedDocument({
        filename: seed.filename,
        company: seed.detected_company,
        fiscal_year: seed.detected_year,
      });
      onRefresh();
      loadSeedDocs();
    } catch (err) {
      alert(`Error indexing seed document: ${err.message}`);
    } finally {
      setIndexingSeed((prev) => ({ ...prev, [seed.filename]: false }));
    }
  };

  const renderStatus = (status, errorMsg) => {
    if (status === 'Completed') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
          <CheckCircle2 className="w-3.5 h-3.5" /> Indexed
        </span>
      );
    }
    if (status === 'Failed') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-100 text-rose-800" title={errorMsg}>
          <AlertCircle className="w-3.5 h-3.5" /> Failed
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
        <Clock className="w-3.5 h-3.5 animate-spin" /> {status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Upload Box */}
      <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900 mb-1">Upload Financial Document</h3>
        <p className="text-xs text-slate-500 mb-4">
          Upload company annual reports (10-K, Integrated Reports) in PDF format. Text is extracted via PyMuPDF and indexed directly into ChromaDB.
        </p>

        {uploadError && (
          <div className="mb-4 p-3 rounded bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        <form onSubmit={handleUpload} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div className="md:col-span-1">
            <label className="block text-xs font-medium text-slate-700 mb-1">Company Name</label>
            <input
              type="text"
              placeholder="e.g. Apple Inc."
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            />
          </div>

          <div className="md:col-span-1">
            <label className="block text-xs font-medium text-slate-700 mb-1">Fiscal Year</label>
            <input
              type="text"
              placeholder="e.g. 2024"
              value={fiscalYear}
              onChange={(e) => setFiscalYear(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
              required
            />
          </div>

          <div className="md:col-span-1">
            <label className="block text-xs font-medium text-slate-700 mb-1">PDF File</label>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="w-full text-xs text-slate-500 file:mr-2 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
              required
            />
          </div>

          <div className="md:col-span-1">
            <button
              type="submit"
              disabled={uploading}
              className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-md text-sm font-medium flex items-center justify-center gap-2 shadow-sm transition-colors"
            >
              {uploading ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" /> Processing...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" /> Upload & Index
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Detected Seed Documents Banner (if any unindexed files exist in data/seed) */}
      {seedDocs.some((s) => !s.is_indexed) && (
        <div className="bg-amber-50/70 border border-amber-200 rounded-lg p-5">
          <div className="flex items-center gap-2 mb-2">
            <FolderPlus className="w-4 h-4 text-amber-700" />
            <h4 className="text-sm font-semibold text-amber-900">Detected Seed Filings (data/seed/)</h4>
          </div>
          <p className="text-xs text-amber-800 mb-3">
            The system detected local filings in the seed folder. Click "Index Filing" to index them into ChromaDB.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {seedDocs
              .filter((s) => !s.is_indexed)
              .map((seed) => (
                <div key={seed.filename} className="bg-white p-3 rounded border border-amber-200 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-800">{seed.filename}</p>
                    <p className="text-[11px] text-slate-500">
                      Entity: {seed.detected_company} ({seed.detected_year}) • {(seed.file_size / 1024).toFixed(0)} KB
                    </p>
                  </div>
                  <button
                    onClick={() => handleIndexSeed(seed)}
                    disabled={indexingSeed[seed.filename]}
                    className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-300 text-white rounded text-xs font-medium flex items-center gap-1"
                  >
                    {indexingSeed[seed.filename] ? 'Indexing...' : 'Index Filing'}
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Indexed Documents Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Tracked Disclosure Documents</h3>
            <p className="text-xs text-slate-500">All PDF reports indexed with exact page-level chunk boundaries.</p>
          </div>
          <button
            onClick={onRefresh}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded transition-colors"
            title="Refresh document list"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Company</th>
                <th className="px-6 py-3">Period</th>
                <th className="px-6 py-3">Filename</th>
                <th className="px-6 py-3">Pages</th>
                <th className="px-6 py-3">Chunks</th>
                <th className="px-6 py-3">Processing Status</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {docList.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-8 text-center text-slate-400">
                    No documents indexed yet. Upload a PDF annual report above.
                  </td>
                </tr>
              ) : (
                docList.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/80">
                    <td className="px-6 py-3 font-semibold text-slate-900">{doc.company}</td>
                    <td className="px-6 py-3">{doc.fiscal_year}</td>
                    <td className="px-6 py-3 text-slate-600 font-mono text-[11px] max-w-xs truncate" title={doc.filename}>
                      {doc.filename}
                    </td>
                    <td className="px-6 py-3">{doc.num_pages || '—'}</td>
                    <td className="px-6 py-3">{doc.num_chunks || '—'}</td>
                    <td className="px-6 py-3">{renderStatus(doc.processing_status, doc.error_message)}</td>
                    <td className="px-6 py-3 text-right space-x-2">
                      {doc.processing_status === 'Failed' && (
                        <button
                          onClick={() => handleProcessAgain(doc.id)}
                          className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium"
                        >
                          Retry
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors"
                        title="Delete Document"
                      >
                        <Trash2 className="w-4 h-4 inline" />
                      </button>
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
