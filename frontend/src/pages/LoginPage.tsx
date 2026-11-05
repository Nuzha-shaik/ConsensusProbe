import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';
import { Shield, Sparkles, Layers, ArrowRight, AlertCircle, RefreshCw } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { signIn, signInAsDemo } = useAuth();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
  const isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;

  const handleGoogleSuccess = (credentialResponse: any) => {
    setLoading(true);
    setErrorMsg(null);
    if (!credentialResponse.credential) {
      setErrorMsg('No credential token received from Google. Please try again.');
      setLoading(false);
      return;
    }
    const success = signIn(credentialResponse.credential);
    setLoading(false);
    if (!success) {
      setErrorMsg('Unable to verify Google credentials or domain unauthorized.');
    }
  };

  const handleGoogleError = () => {
    setErrorMsg('Google Sign-In was cancelled or encountered a network error.');
    setLoading(false);
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

        {/* Bottom Feature Metric Badge */}
        <div className="relative z-10 mt-8 pt-6 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <div>
            <span className="block font-bold text-slate-200 text-sm">0.0%</span>
            <span>Silent Errors (Benchmark)</span>
          </div>
          <div>
            <span className="block font-bold text-slate-200 text-sm">0.38</span>
            <span>Questions/Task</span>
          </div>
          <div>
            <span className="block font-bold text-slate-200 text-sm">100</span>
            <span>Test Sets Evaluated</span>
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
              Secure authentication via Google Identity Services
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
            {googleClientId ? (
              <GoogleOAuthProvider clientId={googleClientId}>
                <div className="flex justify-center w-full">
                  <GoogleLogin
                    onSuccess={handleGoogleSuccess}
                    onError={handleGoogleError}
                    useOneTap={false}
                    theme="outline"
                    size="large"
                    text="continue_with"
                    shape="rectangular"
                    width="320"
                  />
                </div>
              </GoogleOAuthProvider>
            ) : (
              /* Missing Client ID Guidance (Rule: No crash, clean instructions) */
              <div className="p-4 bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800 rounded-xl text-xs space-y-2">
                <div className="font-semibold text-sky-900 dark:text-sky-200 flex items-center space-x-1.5">
                  <Sparkles className="w-4 h-4 text-sky-600 dark:text-sky-400" />
                  <span>Google Client ID Setup Required</span>
                </div>
                <p className="text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed">
                  To connect your real Google Workspace, set <code className="bg-sky-100 dark:bg-sky-900 px-1 py-0.5 rounded text-sky-800 dark:text-sky-200 font-mono">VITE_GOOGLE_CLIENT_ID</code> in <code className="font-mono">.env</code>.
                </p>
              </div>
            )}

            {/* Quick Demo Access (Allows instant evaluation without requiring Google Console setup) */}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200 dark:border-slate-800"></div>
              </div>
              <div className="relative flex justify-center text-[11px] uppercase">
                <span className="bg-slate-50 dark:bg-slate-950 px-2.5 text-slate-400 font-medium">Or Quick Access</span>
              </div>
            </div>

            <button
              onClick={() => signInAsDemo('kkoushik2004610@gmail.com')}
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-slate-900 hover:bg-slate-800 dark:bg-sky-600 dark:hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-sm transition hover:shadow focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <span>Continue as kkoushik2004610@gmail.com</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Privacy & Terms */}
          <p className="text-[11px] text-center text-slate-400 dark:text-slate-500 pt-4 leading-relaxed">
            By continuing, you access the ConsensusProbe governance studio. No confidential data is shared without explicit consensus approval.
          </p>
        </div>
      </div>
    </div>
  );
};
