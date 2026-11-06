import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Layers, AlertCircle, Loader2, CheckCircle2, Cpu, GitCompare } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { signInWithGoogleAuth, signInAsDemo } = useAuth();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await signInWithGoogleAuth();
      if (!res.success && res.error) {
        setErrorMsg(res.error);
      }
    } catch (err: any) {
      setErrorMsg(err?.message || 'Failed to authenticate with Google. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGuestSignIn = () => {
    setErrorMsg(null);
    signInAsDemo('guest@consensusprobe.internal');
  };

  return (
    <div className="min-h-screen w-full flex flex-col md:flex-row bg-slate-50 dark:bg-slate-950 font-sans">
      {/* Left Column: Brand & Data Integrity Motif Panel (Desktop Split) */}
      <div className="w-full md:w-5/12 lg:w-1/2 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white p-8 md:p-14 flex flex-col justify-between border-b md:border-b-0 md:border-r border-slate-800 relative overflow-hidden">
        {/* Subtle abstract consensus/matrix motif */}
        <div className="absolute inset-0 opacity-10 pointer-events-none bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:24px_24px]"></div>

        <div className="relative z-10">
          <div className="flex items-center space-x-2.5 mb-8">
            <div className="w-9 h-9 rounded-xl bg-sky-500/20 border border-sky-400/40 flex items-center justify-center text-sky-400 shadow-sm">
              <Layers className="w-5 h-5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white font-mono">ConsensusProbe</span>
          </div>

          <div className="max-w-md">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/20 mb-4">
              <Shield className="w-3.5 h-3.5" />
              <span>Provable Cleaning Governance</span>
            </div>
            <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-100 leading-tight">
              Disagreement-Driven Cleaning for Real-World Data
            </h1>
            <p className="mt-4 text-sm lg:text-base text-slate-300 leading-relaxed">
              ConsensusGate ensembles multiple LLM proposals, quantifies semantic divergence, and queries the analyst only when genuine ambiguity exists.
            </p>
          </div>
        </div>

        {/* Impeccable Multi-Agent Consensus & Security Widgets */}
        <div className="relative z-10 mt-8 pt-6 border-t border-slate-800/80 space-y-3">
          {/* Live Swarm Engine Status Widget */}
          <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 backdrop-blur-xs flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></div>
              <div>
                <div className="text-xs font-bold text-slate-200 flex items-center space-x-1.5">
                  <Cpu className="w-3.5 h-3.5 text-sky-400" />
                  <span>Multi-Agent Swarm (K=3)</span>
                </div>
                <div className="text-[11px] text-slate-400 font-mono">
                  Autonomous Plan Ensemble • Disagreement Gate d ≤ τ_d
                </div>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-400/30">
              Active
            </span>
          </div>

          {/* SHA-256 Provenance & Canary Sentinel */}
          <div className="flex items-center justify-between text-[11px] text-slate-400 px-1 font-mono">
            <div className="flex items-center space-x-1.5 text-slate-300">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Probe Sentinel Ground-Truth</span>
            </div>
            <div className="flex items-center space-x-1.5 text-sky-400">
              <Shield className="w-3.5 h-3.5" />
              <span>SHA-256 Verified</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: Sign-in Panel */}
      <div className="w-full md:w-7/12 lg:w-1/2 flex items-center justify-center p-6 md:p-12 lg:p-16">
        <div className="w-full max-w-sm space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
              Sign In to Your Workspace
            </h2>
            <p className="text-xs lg:text-sm text-slate-500 dark:text-slate-400 mt-1.5">
              Authenticate with your Google account to access ConsensusProbe
            </p>
          </div>

          {/* Network Offline Alert */}
          {!isOnline && (
            <div className="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl text-amber-800 dark:text-amber-200 text-xs flex items-center space-x-2" role="alert">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>You appear to be offline. Please reconnect to authenticate.</span>
            </div>
          )}

          {/* Error Banner */}
          {errorMsg && (
            <div className="p-3.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-rose-700 dark:text-rose-300 text-xs flex items-start justify-between" role="alert" aria-live="polite">
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
              <button
                onClick={() => setErrorMsg(null)}
                className="text-rose-500 hover:text-rose-700 dark:hover:text-rose-200 ml-2"
                aria-label="Dismiss error"
              >
                &times;
              </button>
            </div>
          )}

          {/* Google Sign In Container */}
          <div className="space-y-4 pt-2">
            <button
              onClick={handleGoogleSignIn}
              disabled={loading}
              className="w-full flex items-center justify-center space-x-3 py-3 px-4 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-xl text-sm font-semibold shadow-xs transition hover:shadow focus:outline-none focus:ring-2 focus:ring-sky-500 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin text-sky-600 dark:text-sky-400" />
              ) : (
                /* Official Google "G" Multi-color Brand SVG Icon */
                <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
              )}
              <span>{loading ? 'Signing in with Google...' : 'Sign in with Google'}</span>
            </button>

            {/* Quick Guest Access */}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200 dark:border-slate-800"></div>
              </div>
              <div className="relative flex justify-center text-[11px] uppercase">
                <span className="bg-slate-50 dark:bg-slate-950 px-2.5 text-slate-400 font-medium">Or</span>
              </div>
            </div>

            <button
              onClick={handleGuestSignIn}
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-semibold transition focus:outline-none focus:ring-2 focus:ring-slate-400"
            >
              <span>Continue as Guest</span>
            </button>
          </div>

          {/* Privacy & Terms */}
          <p className="text-[11px] text-center text-slate-400 dark:text-slate-500 pt-4 leading-relaxed">
            By continuing, you access the ConsensusProbe governance studio. Any Google account is authorized to sign in.
          </p>
        </div>
      </div>
    </div>
  );
};
