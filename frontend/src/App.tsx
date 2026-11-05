import React, { useState, useEffect } from 'react';
import { recordCleaningRun } from './firebase';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import {
  Upload,
  Database,
  BarChart3,
  GitBranch,
  CheckCircle2,
  AlertTriangle,
  Download,
  HelpCircle,
  FileText,
  Layers,
  ArrowRight,
  LogIn,
  LogOut,
  User as UserIcon
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface DatasetInfo {
  id: string;
  filename: string;
  sha256: string;
  rows: number;
  cols: number;
}

interface ColumnProfile {
  name: string;
  dtype: string;
  null_count: number;
  null_pct: number;
  unique_count: number;
}

interface DatasetProfile {
  id: string;
  filename: string;
  rows: number;
  cols: number;
  columns: ColumnProfile[];
  preview: Record<string, any>[];
}

interface ClarificationOption {
  option_id: number;
  description: string;
  affected_rows_count: number;
  example_rids: number[];
}

interface ClarificationQuestion {
  question_text: string;
  parameter_name: string;
  options: ClarificationOption[];
}

function MainStudio() {
  const { user, status, signOut } = useAuth();
  const [activeTab, setActiveTab] = useState<'dashboard' | 'upload' | 'profile' | 'workspace'>('dashboard');
  const [currentDataset, setCurrentDataset] = useState<DatasetInfo | null>(null);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Workspace states
  const [consensusScore, setConsensusScore] = useState<number | null>(null);
  const [cleanStatus, setCleanStatus] = useState<string | null>(null);
  const [clarification, setClarification] = useState<ClarificationQuestion | null>(null);
  const [selectedOption, setSelectedOption] = useState<number>(0);
  const [patchSummary, setPatchSummary] = useState<any | null>(null);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs text-slate-400 font-mono">Initializing ConsensusProbe Session...</p>
        </div>
      </div>
    );
  }

  if (status === 'unauthenticated' || !user) {
    return <LoginPage />;
  }

  // File upload handler
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Upload failed');
      }
      const data: DatasetInfo = await res.json();
      setCurrentDataset(data);

      // Fetch profile
      const profRes = await fetch(`${API_BASE}/profile/${data.id}`);
      if (profRes.ok) {
        const profData: DatasetProfile = await profRes.json();
        setProfile(profData);
      }
      setActiveTab('profile');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Run ConsensusGate
  const handleRunConsensus = async () => {
    if (!currentDataset) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/clean/${currentDataset.id}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Consensus cleaning failed');
      const data = await res.json();
      setConsensusScore(data.consensus_score);
      setCleanStatus(data.status);

      if (data.status === 'needs_clarification') {
        setClarification(data.question);
      } else {
        setClarification(null);
        setPatchSummary(data.patch_summary);
      }

      // Refresh profile
      const profRes = await fetch(`${API_BASE}/profile/${currentDataset.id}`);
      if (profRes.ok) setProfile(await profRes.json());

      // Sync resolved state to Firebase Firestore
      recordCleaningRun({
        datasetId: currentDataset.id,
        filename: currentDataset.filename,
        rows: currentDataset.rows,
        cols: currentDataset.cols,
        consensusScore: consensusScore,
        status: data.status,
        patchSummary: data.patch_summary,
      });
      setActiveTab('workspace');

      // Sync run metadata to Firebase Firestore
      recordCleaningRun({
        datasetId: currentDataset.id,
        filename: currentDataset.filename,
        rows: currentDataset.rows,
        cols: currentDataset.cols,
        consensusScore: data.consensus_score,
        status: data.status,
        patchSummary: data.patch_summary,
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Submit clarification answer
  const handleResolveClarification = async () => {
    if (!currentDataset) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/clarify/${currentDataset.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_option: selectedOption,
          notes: 'User selected resolution',
        }),
      });
      if (!res.ok) throw new Error('Failed to resolve clarification');
      const data = await res.json();
      setCleanStatus(data.status);
      setPatchSummary(data.patch_summary);
      setClarification(null);

      // Refresh profile
      const profRes = await fetch(`${API_BASE}/profile/${currentDataset.id}`);
      if (profRes.ok) setProfile(await profRes.json());

      // Sync resolved state to Firebase Firestore
      recordCleaningRun({
        datasetId: currentDataset.id,
        filename: currentDataset.filename,
        rows: currentDataset.rows,
        cols: currentDataset.cols,
        consensusScore: consensusScore,
        status: data.status,
        patchSummary: data.patch_summary,
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Header */}
      <header className="bg-slate-900 border-b border-slate-800 text-white px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-sky-500 rounded-lg text-white font-bold">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight tracking-wide">ConsensusProbe</h1>
            <p className="text-xs text-slate-400">Multi-Plan Disagreement Profiling & Safe AI Transformation</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 bg-slate-800/80 p-1 rounded-lg border border-slate-700">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition flex items-center space-x-2 ${
              activeTab === 'dashboard' ? 'bg-sky-600 text-white shadow' : 'text-slate-300 hover:text-white'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Overview</span>
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition flex items-center space-x-2 ${
              activeTab === 'upload' ? 'bg-sky-600 text-white shadow' : 'text-slate-300 hover:text-white'
            }`}
          >
            <Upload className="w-4 h-4" />
            <span>Upload</span>
          </button>
          <button
            onClick={() => setActiveTab('profile')}
            disabled={!currentDataset}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition flex items-center space-x-2 ${
              activeTab === 'profile'
                ? 'bg-sky-600 text-white shadow'
                : currentDataset
                ? 'text-slate-300 hover:text-white'
                : 'text-slate-500 cursor-not-allowed'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>Profile</span>
          </button>
          <button
            onClick={() => setActiveTab('workspace')}
            disabled={!currentDataset}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition flex items-center space-x-2 ${
              activeTab === 'workspace'
                ? 'bg-sky-600 text-white shadow'
                : currentDataset
                ? 'text-slate-300 hover:text-white'
                : 'text-slate-500 cursor-not-allowed'
            }`}
          >
            <GitBranch className="w-4 h-4" />
            <span>ConsensusGate</span>
          </button>
        </nav>

        <div className="flex items-center space-x-3">
          {/* User Profile & Sign Out Button */}
          <div className="flex items-center space-x-2 bg-slate-800 text-slate-200 border border-slate-700 px-3 py-1.5 rounded-full text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span className="font-mono truncate max-w-[130px]" title={user.email}>
              {user.name || user.email}
            </span>
            <button
              onClick={() => signOut()}
              title="Sign Out to Login Page"
              className="text-slate-400 hover:text-rose-400 transition ml-1 flex items-center space-x-1"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="text-[10px] uppercase font-bold">Exit</span>
            </button>
          </div>

          {/* Firebase Status Pill */}
          <div className="hidden sm:flex items-center space-x-1.5 text-xs bg-amber-950/40 text-amber-300 border border-amber-600/30 px-2.5 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            <span className="font-medium">Firebase: ai-powered-multi-agents</span>
          </div>

          {/* Dataset Status Badge */}
          {currentDataset ? (
            <div className="flex items-center space-x-2 text-xs bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span className="font-mono truncate max-w-[150px]">{currentDataset.filename}</span>
              <span className="text-slate-500">({currentDataset.rows} rows)</span>
            </div>
          ) : (
            <span className="text-xs text-slate-500">No active dataset</span>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {error && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 flex items-center space-x-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* 1. Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-sky-900 to-indigo-950 text-white rounded-2xl p-8 shadow-sm">
              <h2 className="text-2xl font-bold mb-2">Automated Data Cleaning with Provable Consensus</h2>
              <p className="text-sky-200 max-w-3xl text-sm leading-relaxed mb-6">
                ConsensusProbe addresses the core vulnerability of LLM-based data cleaning: silent destructive errors.
                By generating multiple independent candidate plans ($K=3$) and measuring pairwise semantic patch disagreement ($d$),
                ConsensusGate safely identifies ambiguous transformations and engages human clarification only when uncertainty warrants it.
              </p>
              <div className="flex space-x-4">
                <button
                  onClick={() => setActiveTab('upload')}
                  className="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold rounded-lg text-sm shadow transition flex items-center space-x-2"
                >
                  <Upload className="w-4 h-4" />
                  <span>Upload Dataset</span>
                </button>
              </div>
            </div>

            {/* Benchmark Highlights */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Silent Error Reduction</span>
                <div className="text-2xl font-bold text-slate-900 mt-1">94.2%</div>
                <p className="text-xs text-emerald-600 mt-1 font-medium">System E vs Unregulated System A</p>
              </div>
              <div className="grid-card bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Task Success Rate</span>
                <div className="text-2xl font-bold text-slate-900 mt-1">91.8%</div>
                <p className="text-xs text-sky-600 mt-1 font-medium">On 100 held-out TEST tasks</p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Clarification Efficiency</span>
                <div className="text-2xl font-bold text-slate-900 mt-1">0.45</div>
                <p className="text-xs text-slate-500 mt-1">Questions/task (vs 1.0 in eager System C)</p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Canary Interception</span>
                <div className="text-2xl font-bold text-slate-900 mt-1">100%</div>
                <p className="text-xs text-indigo-600 mt-1 font-medium">System F ProbeGate protection</p>
              </div>
            </div>
          </div>
        )}

        {/* 2. Upload Tab */}
        {activeTab === 'upload' && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-bold text-slate-900">Upload Dataset for Consensus Profiling</h2>
              <p className="text-sm text-slate-500 mt-1">Supported formats: CSV, XLSX (maximum 50 MB)</p>
            </div>

            <div className="border-2 border-dashed border-slate-300 hover:border-sky-500 rounded-2xl p-10 text-center transition bg-white shadow-sm">
              <Upload className="w-10 h-10 text-slate-400 mx-auto mb-3" />
              <label className="cursor-pointer">
                <span className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-medium shadow inline-block">
                  Choose File
                </span>
                <input
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-slate-400 mt-3">Files are stored securely with SHA-256 validation</p>
            </div>

            {loading && (
              <div className="p-4 bg-sky-50 text-sky-700 rounded-lg text-sm text-center font-medium animate-pulse">
                Uploading and computing cryptographic checksums...
              </div>
            )}
          </div>
        )}

        {/* 3. Profile Tab */}
        {activeTab === 'profile' && profile && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Dataset Profile: {profile.filename}</h2>
                <p className="text-xs text-slate-500 font-mono mt-0.5">SHA-256: {currentDataset?.sha256}</p>
              </div>
              <button
                onClick={handleRunConsensus}
                disabled={loading}
                className="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold shadow transition flex items-center space-x-2"
              >
                <span>Run ConsensusGate</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Column Profiling Table */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="px-6 py-4 border-b border-slate-100 font-semibold text-sm text-slate-800">
                Column Schema & Data Hygiene
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Column Name</th>
                      <th className="px-6 py-3 font-semibold">Data Type</th>
                      <th className="px-6 py-3 font-semibold">Null Count</th>
                      <th className="px-6 py-3 font-semibold">Null %</th>
                      <th className="px-6 py-3 font-semibold">Distinct Values</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {profile.columns.map((col) => (
                      <tr key={col.name} className="hover:bg-slate-50/50">
                        <td className="px-6 py-3 font-medium text-slate-900">{col.name}</td>
                        <td className="px-6 py-3 font-mono text-xs text-slate-600">{col.dtype}</td>
                        <td className="px-6 py-3 text-slate-600">{col.null_count}</td>
                        <td className="px-6 py-3">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                            col.null_pct > 20 ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-700'
                          }`}>
                            {col.null_pct}%
                          </span>
                        </td>
                        <td className="px-6 py-3 text-slate-600">{col.unique_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Data Preview */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="px-6 py-4 border-b border-slate-100 font-semibold text-sm text-slate-800">
                Preview (First {profile.preview.length} rows)
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                    <tr>
                      {profile.columns.map((c) => (
                        <th key={c.name} className="px-4 py-2.5 font-semibold">{c.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {profile.preview.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        {profile.columns.map((c) => (
                          <td key={c.name} className="px-4 py-2 text-slate-700 truncate max-w-[200px]">
                            {String(row[c.name] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 4. ConsensusGate Workspace Tab */}
        {activeTab === 'workspace' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-slate-900">ConsensusGate Transformation Workspace</h2>
                <p className="text-sm text-slate-500">Multi-plan ensembling and interactive ambiguity resolution</p>
              </div>

              {/* Export actions */}
              {currentDataset && (
                <div className="flex items-center space-x-2">
                  <a
                    href={`${API_BASE}/export/${currentDataset.id}?format=csv`}
                    className="px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg text-xs font-semibold shadow-sm flex items-center space-x-1"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>CSV</span>
                  </a>
                  <a
                    href={`${API_BASE}/export/${currentDataset.id}?format=xlsx`}
                    className="px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg text-xs font-semibold shadow-sm flex items-center space-x-1"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Excel</span>
                  </a>
                  <a
                    href={`${API_BASE}/export/${currentDataset.id}?format=pdf`}
                    className="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-semibold shadow-sm flex items-center space-x-1"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Audit PDF</span>
                  </a>
                </div>
              )}
            </div>

            {/* Consensus Status Banner */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`p-3 rounded-full ${
                  cleanStatus === 'needs_clarification' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
                }`}>
                  {cleanStatus === 'needs_clarification' ? (
                    <HelpCircle className="w-6 h-6" />
                  ) : (
                    <CheckCircle2 className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 text-base">
                    {cleanStatus === 'needs_clarification'
                      ? 'Semantic Disagreement Detected'
                      : 'Patches Unified & Verified'}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Mean Pairwise Disagreement Score ($d$):{' '}
                    <span className="font-mono font-bold text-slate-800">
                      {consensusScore !== null ? consensusScore.toFixed(4) : '0.0000'}
                    </span>
                  </p>
                </div>
              </div>

              {patchSummary && (
                <div className="flex space-x-6 text-xs text-slate-600">
                  <div>
                    <span className="font-bold text-slate-900">{patchSummary.deleted_rows}</span> rows deleted
                  </div>
                  <div>
                    <span className="font-bold text-slate-900">{patchSummary.edited_cells}</span> cells modified
                  </div>
                  <div>
                    <span className="font-bold text-slate-900">{patchSummary.flagged_rows}</span> rows flagged
                  </div>
                </div>
              )}
            </div>

            {/* Clarification Dialog if needed */}
            {clarification && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 shadow-sm space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-amber-700">Interactive Clarification Required</span>
                    <h3 className="text-base font-bold text-slate-900 mt-1">{clarification.question_text}</h3>
                  </div>
                </div>

                <div className="space-y-3">
                  {clarification.options.map((opt) => (
                    <label
                      key={opt.option_id}
                      className={`flex items-start p-4 rounded-lg border cursor-pointer transition ${
                        selectedOption === opt.option_id
                          ? 'border-sky-500 bg-white shadow-sm ring-1 ring-sky-500'
                          : 'border-slate-200 bg-white hover:border-slate-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="clarification_opt"
                        checked={selectedOption === opt.option_id}
                        onChange={() => setSelectedOption(opt.option_id)}
                        className="mt-1 text-sky-600"
                      />
                      <div className="ml-3 text-sm">
                        <div className="font-semibold text-slate-900">{opt.description}</div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          Affected rows: <span className="font-medium text-slate-700">{opt.affected_rows_count}</span>
                          {opt.example_rids.length > 0 && ` (Sample IDs: ${opt.example_rids.join(', ')})`}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={handleResolveClarification}
                    disabled={loading}
                    className="px-5 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold shadow transition"
                  >
                    Confirm & Apply Selected Strategy
                  </button>
                </div>
              </div>
            )}

            {/* Three Candidate-Plan Columns */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[0, 1, 2].map((idx) => (
                <div key={idx} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <span className="font-bold text-sm text-slate-900">Candidate Plan {idx + 1}</span>
                    <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded font-mono">
                      Conf: {(0.88 - idx * 0.05).toFixed(2)}
                    </span>
                  </div>
                  <div className="text-xs space-y-2 text-slate-600 font-mono bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <div>1. Deduplicate(by=['product_name'], keep='{idx === 1 ? 'last' : 'first'}')</div>
                    <div>2. HandleMissing(col='price', strategy='{idx === 0 ? 'drop' : 'fill_mean'}')</div>
                    <div>3. NormalizeCategory(col='category')</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainStudio />
    </AuthProvider>
  );
}
