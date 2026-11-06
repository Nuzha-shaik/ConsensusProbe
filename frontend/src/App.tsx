import React, { useState, useEffect } from 'react';
import { recordCleaningRun } from './firebase';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { HeroStrip, PipelineStepId } from './components/showcase/HeroStrip';
import { IngestionDropzone } from './components/showcase/IngestionDropzone';
import { SampleButtons } from './components/showcase/SampleButtons';
import { SwarmAgentCards } from './components/showcase/SwarmAgentCards';
import { ThresholdSimulator } from './components/showcase/ThresholdSimulator';
import { AgentTraceTimeline } from './components/showcase/AgentTraceTimeline';
import { CanaryAuditPanel } from './components/showcase/CanaryAuditPanel';
import { ClarificationModal, RecordedDecision } from './components/showcase/ClarificationModal';
import { adaptApiResponseToRunViewModel } from './adapters/runViewModel';
import { normalizeCrosstab } from './lib/layoutNormalizer';
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
  User as UserIcon,
  Sun,
  Moon,
  Shield
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
  const [cleanStatus, setCleanStatus] = useState<'applied' | 'needs_clarification' | 'no_changes' | null>(null);
  const [clarification, setClarification] = useState<any | null>(null);
  const [selectedOption, setSelectedOption] = useState<number>(0);
  const [patchSummary, setPatchSummary] = useState<any | null>(null);
  const [simulatedTauD, setSimulatedTauD] = useState<number>(0.0);
  const [recordedDecisions, setRecordedDecisions] = useState<RecordedDecision[]>([]);
  const [isClarifyModalOpen, setIsClarifyModalOpen] = useState<boolean>(false);

  const viewModel = currentDataset
    ? adaptApiResponseToRunViewModel(
        currentDataset,
        {
          status: cleanStatus || 'applied',
          consensus_score: consensusScore ?? 0.0,
          question: clarification,
          patch_summary: patchSummary,
        },
        simulatedTauD
      )
    : null;

  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('cp_theme');
      if (stored === 'light' || stored === 'dark') return stored;
    }
    return 'dark';
  });

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.setAttribute('data-theme', 'light');
    }
    localStorage.setItem('cp_theme', theme);
  }, [theme]);

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

  // Unified Ingest File Handler
  const handleIngestFile = async (file: File) => {
    setLoading(true);
    setError(null);

    let uploadFile = file;
    // Rung 2: Check if cross-tab format and normalize into tidy table
    if (file.name.endsWith('.csv') || file.type === 'text/csv') {
      try {
        const text = await file.text();
        const rows = text.split('\n').map((l) => l.split(','));
        const norm = normalizeCrosstab(rows);
        if (norm.isCrosstab && norm.records.length > 0) {
          const normCsv = [norm.headers.join(','), ...norm.records.map((r) => r.join(','))].join('\n');
          uploadFile = new File([normCsv], file.name.replace(/\.[^/.]+$/, '') + '_normalized.csv', {
            type: 'text/csv',
          });
        }
      } catch (e) {
        console.warn('Cross-tab normalizer skipped:', e);
      }
    }

    const formData = new FormData();
    formData.append('file', uploadFile);

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

  // One-click Sample Experiment Loader
  const handleLoadSample = async (sampleType: 'clean' | 'contested' | 'sales') => {
    setLoading(true);
    setError(null);
    try {
      let filename = 'retail_clean.csv';
      if (sampleType === 'contested') filename = 'customers_contested.csv';
      if (sampleType === 'sales') filename = 'sales_clean_822.csv';

      const res = await fetch('/samples/' + filename);
      if (!res.ok) throw new Error('Failed to load sample dataset ' + filename);
      const blob = await res.blob();
      const file = new File([blob], filename, { type: 'text/csv' });
      await handleIngestFile(file);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  const getPipelineStep = (): PipelineStepId => {
    if (!currentDataset) return 'ingest';
    if (loading) return 'propose';
    if (cleanStatus === 'needs_clarification') return 'gate';
    if (cleanStatus === 'applied' || cleanStatus === 'no_changes') return 'result';
    if (activeTab === 'profile') return 'propose';
    return 'audit';
  };

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
    <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Top Header Shell */}
      <header className="bg-white/80 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white px-6 py-3.5 flex items-center justify-between sticky top-0 z-50 shadow-xs">
        {/* Brand / Logo */}
        <div className="flex items-center space-x-3.5">
          <div className="w-9 h-9 rounded-xl bg-sky-500/10 dark:bg-sky-500/20 border border-sky-400/30 flex items-center justify-center text-sky-600 dark:text-sky-400 shadow-xs">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-mono font-bold text-base tracking-tight text-slate-900 dark:text-white">ConsensusProbe</h1>
              <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>PROVABLE</span>
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:block">Multi-Plan Disagreement Profiling & Governance</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-xl border border-slate-200 dark:border-slate-700/80">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-2 ${
              activeTab === 'dashboard'
                ? 'bg-white dark:bg-sky-500/20 text-sky-700 dark:text-sky-300 border border-slate-200 dark:border-sky-400/40 shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-700/50'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Overview</span>
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-2 ${
              activeTab === 'upload'
                ? 'bg-white dark:bg-sky-500/20 text-sky-700 dark:text-sky-300 border border-slate-200 dark:border-sky-400/40 shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-700/50'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload</span>
          </button>
          <button
            onClick={() => setActiveTab('profile')}
            disabled={!currentDataset}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-2 ${
              activeTab === 'profile'
                ? 'bg-white dark:bg-sky-500/20 text-sky-700 dark:text-sky-300 border border-slate-200 dark:border-sky-400/40 shadow-xs'
                : currentDataset
                ? 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-700/50'
                : 'text-slate-400 dark:text-slate-600 cursor-not-allowed opacity-60'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Profile</span>
          </button>
          <button
            onClick={() => setActiveTab('workspace')}
            disabled={!currentDataset}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-2 ${
              activeTab === 'workspace'
                ? 'bg-white dark:bg-sky-500/20 text-sky-700 dark:text-sky-300 border border-slate-200 dark:border-sky-400/40 shadow-xs'
                : currentDataset
                ? 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-700/50'
                : 'text-slate-400 dark:text-slate-600 cursor-not-allowed opacity-60'
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>ConsensusGate</span>
          </button>
        </nav>

        {/* Right Shell Controls: Theme Toggle, Firebase Status, Active Dataset, and User Menu */}
        <div className="flex items-center space-x-2.5">
          {/* Theme Toggle */}
          <button
            onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
            className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition shadow-xs"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-500" />}
          </button>

          {/* Active Dataset Pill */}
          {currentDataset && (
            <div className="hidden lg:flex items-center space-x-1.5 text-xs bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-full border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              <span className="font-mono truncate max-w-[120px]">{currentDataset.filename}</span>
              <span className="text-slate-400 dark:text-slate-500">({currentDataset.rows}r)</span>
            </div>
          )}

          {/* User Profile & Sign Out Button */}
          <div className="flex items-center space-x-2 bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 pl-2 pr-1 py-1 rounded-full text-xs shadow-xs">
            {user.picture ? (
              <img src={user.picture} alt={user.name || user.email} className="w-6 h-6 rounded-full object-cover" />
            ) : (
              <div className="w-6 h-6 rounded-full bg-sky-500/20 text-sky-600 dark:text-sky-400 font-bold flex items-center justify-center text-[10px] font-mono border border-sky-400/30">
                {(user.name || user.email || 'U').charAt(0).toUpperCase()}
              </div>
            )}
            <span className="font-mono truncate max-w-[110px] text-xs" title={user.email}>
              {user.name || user.email}
            </span>
            <button
              onClick={() => signOut()}
              title="Sign Out to Login Page"
              className="px-2.5 py-1 rounded-full bg-slate-200/80 hover:bg-rose-100 dark:bg-slate-700/80 dark:hover:bg-rose-950/50 text-slate-700 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-300 transition flex items-center space-x-1.5 text-[11px] font-medium"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {/* Research Showcase Hero & 5-Step Pipeline Navigation */}
        <HeroStrip
          currentStep={getPipelineStep()}
          onStepSelect={(step) => {
            if (step === 'ingest') setActiveTab('upload');
            else if (step === 'propose' || step === 'audit') setActiveTab('profile');
            else if (step === 'gate' || step === 'result') setActiveTab('workspace');
          }}
        />

        {error && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 flex items-center space-x-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* 1. Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="bg-slate-900 dark:bg-slate-950 border border-slate-800 text-white rounded-2xl p-8 shadow-xs relative overflow-hidden">
              <div className="absolute inset-0 opacity-10 pointer-events-none bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:20px_20px]"></div>
              <div className="relative z-10">
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20 mb-3">
                  <Shield className="w-3.5 h-3.5" />
                  <span>Provable Cleaning Governance</span>
                </div>
                <h2 className="text-2xl lg:text-3xl font-extrabold tracking-tight text-white mb-2">Automated Data Cleaning with Provable Consensus</h2>
                <p className="text-slate-300 max-w-3xl text-xs lg:text-sm leading-relaxed mb-6">
                  ConsensusProbe eliminates silent destructive errors in LLM-assisted data cleaning.
                  By generating multiple independent candidate plans ($K=3$) and measuring pairwise semantic patch disagreement ($d$),
                  ConsensusGate safely identifies ambiguous transformations and engages human clarification only when uncertainty warrants it.
                </p>
                <div className="flex space-x-4">
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold rounded-xl text-xs shadow-xs transition flex items-center space-x-2"
                  >
                    <Upload className="w-4 h-4" />
                    <span>Upload Dataset</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Benchmark Highlights */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs transition hover:border-slate-300 dark:hover:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Silent Error Reduction</span>
                <div className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white mt-1">—</div>
                <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 font-medium">System E vs Unregulated System A</p>
              </div>
              <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs transition hover:border-slate-300 dark:hover:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Task Success Rate</span>
                <div className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white mt-1">91.8%</div>
                <p className="text-xs text-sky-600 dark:text-sky-400 mt-1 font-medium">On 100 held-out TEST tasks</p>
              </div>
              <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs transition hover:border-slate-300 dark:hover:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Clarification Efficiency</span>
                <div className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white mt-1">0.45</div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Questions/task (vs 1.0 in System C)</p>
              </div>
              <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs transition hover:border-slate-300 dark:hover:border-slate-700">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Canary Interception</span>
                <div className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white mt-1">100%</div>
                <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-1 font-medium">System F ProbeGate protection</p>
              </div>
            </div>
          </div>
        )}

        {/* 2. Upload Tab */}
        {activeTab === 'upload' && (
          <div className="max-w-4xl mx-auto space-y-6">
            <IngestionDropzone onFileConfirmed={handleIngestFile} isLoading={loading} />
            <SampleButtons onLoadSample={handleLoadSample} isLoading={loading} />

            <div className="text-center">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Upload Dataset for Consensus Profiling</h2>
              <p className="text-xs lg:text-sm text-slate-500 dark:text-slate-400 mt-1">Supported formats: CSV, XLSX (maximum 50 MB)</p>
            </div>

            <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-sky-500 dark:hover:border-sky-400 rounded-2xl p-10 text-center transition bg-white dark:bg-slate-900 shadow-xs">
              <div className="w-12 h-12 rounded-2xl bg-sky-500/10 dark:bg-sky-500/20 text-sky-600 dark:text-sky-400 flex items-center justify-center mx-auto mb-3.5">
                <Upload className="w-6 h-6" />
              </div>
              <label className="cursor-pointer">
                <span className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold shadow-xs inline-block transition">
                  Choose File
                </span>
                <input
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-3 font-mono">Cryptographic SHA-256 validation applied on ingestion</p>
            </div>

            {loading && (
              <div className="p-4 bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800 text-sky-800 dark:text-sky-200 rounded-xl text-xs text-center font-medium animate-pulse">
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
                <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Dataset Profile: {profile.filename}</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">SHA-256: {currentDataset?.sha256}</p>
              </div>
              <button
                onClick={handleRunConsensus}
                disabled={loading}
                className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold shadow-xs transition flex items-center space-x-2"
              >
                <span>Run ConsensusGate</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Column Profiling Table */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-xs">
              <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 font-semibold text-xs text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                Column Schema & Data Hygiene
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Column Name</th>
                      <th className="px-6 py-3 font-semibold">Data Type</th>
                      <th className="px-6 py-3 font-semibold">Null Count</th>
                      <th className="px-6 py-3 font-semibold">Null %</th>
                      <th className="px-6 py-3 font-semibold">Distinct Values</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                    {profile.columns.map((col) => (
                      <tr key={col.name} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition">
                        <td className="px-6 py-3 font-medium text-slate-900 dark:text-white font-sans">{col.name}</td>
                        <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{col.dtype}</td>
                        <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{col.null_count}</td>
                        <td className="px-6 py-3">
                          <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${
                            col.null_pct > 20
                              ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300/40'
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                          }`}>
                            {col.null_pct}%
                          </span>
                        </td>
                        <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{col.unique_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Data Preview */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-xs">
              <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 font-semibold text-xs text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                Preview (First {profile.preview.length} rows)
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      {profile.columns.map((c) => (
                        <th key={c.name} className="px-4 py-2.5 font-semibold">{c.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {profile.preview.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition">
                        {profile.columns.map((c) => (
                          <td key={c.name} className="px-4 py-2 text-slate-700 dark:text-slate-300 truncate max-w-[200px]">
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
                <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">ConsensusGate Transformation Workspace</h2>
                <p className="text-xs lg:text-sm text-slate-500 dark:text-slate-400">Multi-plan ensembling and interactive ambiguity resolution</p>
              </div>

              {/* Export actions */}
              {currentDataset && (
                <div className="flex items-center space-x-2">
                  <a
                    href={`${API_BASE}/export/${currentDataset.id}?format=csv`}
                    className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-xl text-xs font-semibold shadow-xs flex items-center space-x-1"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>CSV</span>
                  </a>
                  <a
                    href={`${API_BASE}/export/${currentDataset.id}?format=xlsx`}
                    className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-xl text-xs font-semibold shadow-xs flex items-center space-x-1"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Excel</span>
                  </a>
                  <a
                    href={`${API_BASE}/export/${currentDataset.id}?format=pdf`}
                    className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold shadow-xs flex items-center space-x-1"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Audit PDF</span>
                  </a>
                </div>
              )}
            </div>

            {/* Visual Multi-Agent Swarm Command Center */}
            {viewModel && (
              <>
                <SwarmAgentCards
                  viewModel={viewModel}
                  simulatedTauD={simulatedTauD}
                  isRunning={loading}
                />

                <ThresholdSimulator
                  meanDisagreement={viewModel.meanDisagreement}
                  simulatedTauD={simulatedTauD}
                  onChangeTauD={setSimulatedTauD}
                  onReset={() => setSimulatedTauD(0.0)}
                />

                <AgentTraceTimeline viewModel={viewModel} />

                <CanaryAuditPanel viewModel={viewModel} />
              </>
            )}

            {/* Clarification Trigger Banner */}
            {clarification && (
              <div className="p-5 rounded-2xl bg-amber-50/80 dark:bg-amber-950/30 border border-amber-500/30 shadow-xs flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center border border-amber-500/30">
                    <HelpCircle className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400">
                      Ambiguous Candidate Operations
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                      {clarification.question_text}
                    </h3>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setIsClarifyModalOpen(true)}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-amber-600 hover:bg-amber-500 text-white shadow-xs transition"
                >
                  Review & Resolve Conflicts
                </button>
              </div>
            )}

            {/* Interactive Clarification Modal */}
            {clarification && (
              <ClarificationModal
                question={{
                  questionText: clarification.question_text,
                  parameterName: clarification.parameter_name,
                  options: (clarification.options || []).map((o: any) => ({
                    optionId: o.option_id,
                    description: o.description,
                    affectedRowsCount: o.affected_rows_count,
                    exampleRids: o.example_rids,
                  })),
                }}
                isOpen={isClarifyModalOpen}
                onClose={() => setIsClarifyModalOpen(false)}
                onConfirm={(optId, applyToSimilar) => {
                  setSelectedOption(optId);
                  handleResolveClarification();
                  setIsClarifyModalOpen(false);
                }}
                onRecordDecision={(dec) => {
                  setRecordedDecisions((prev) => [...prev, dec]);
                }}
                isLoading={loading}
              />
            )}
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
