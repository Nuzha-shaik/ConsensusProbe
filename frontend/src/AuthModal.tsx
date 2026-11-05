import React, { useState } from 'react';
import {
  signInWithGoogle,
  loginWithEmail,
  registerWithEmail,
  User
} from './firebase';
import { LogIn, Sparkles, AlertCircle, X, ShieldCheck } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setAuthError(null);
    const { user, error } = await signInWithGoogle();
    setLoading(false);
    if (error) {
      setAuthError(error);
    } else if (user) {
      onSuccess(user);
      onClose();
    }
  };

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setAuthError('Please provide both email and password.');
      return;
    }
    setLoading(true);
    setAuthError(null);
    const { user, error } = isRegister
      ? await registerWithEmail(email, password)
      : await loginWithEmail(email, password);
    setLoading(false);
    if (error) {
      setAuthError(error);
    } else if (user) {
      onSuccess(user);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-100 animate-in fade-in zoom-in-95 duration-150">
        {/* Header Banner */}
        <div className="bg-gradient-to-r from-sky-600 via-indigo-600 to-indigo-800 p-6 text-white relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-full hover:bg-white/20 transition text-white/80 hover:text-white"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
          <div className="flex items-center space-x-2 text-sky-200 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Firebase Authentication</span>
          </div>
          <h2 className="text-xl font-bold">Sign In to ConsensusProbe</h2>
          <p className="text-xs text-sky-100 mt-1">
            Sync datasets & consensus records to Firestore (ai-powered-multi-agents)
          </p>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {authError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{authError}</span>
            </div>
          )}

          {/* Google Sign In Button */}
          <button
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="w-full flex items-center justify-center space-x-3 py-2.5 px-4 bg-white hover:bg-slate-50 border border-slate-300 rounded-xl text-sm font-semibold text-slate-700 shadow-sm transition hover:shadow focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
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
            <span>Continue with Google</span>
          </button>

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-3 text-slate-400 font-medium">Or with Email</span>
            </div>
          </div>

          {/* Email / Password Form */}
          <form onSubmit={handleEmailAuth} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold shadow transition disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : isRegister ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          {/* Toggle Register / Sign In */}
          <div className="text-center pt-2">
            <button
              onClick={() => {
                setIsRegister(!isRegister);
                setAuthError(null);
              }}
              className="text-xs text-sky-600 hover:text-sky-700 font-medium hover:underline"
            >
              {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
            </button>
          </div>

          {/* Guest / Skip Option */}
          <div className="border-t border-slate-100 pt-3 text-center">
            <button
              onClick={onClose}
              className="text-xs text-slate-400 hover:text-slate-600"
            >
              Continue as Guest / Explore Demo
            </button>
          </div>
        </div>

        {/* Footer Security Badge */}
        <div className="bg-slate-50 px-6 py-2.5 border-t border-slate-100 flex items-center justify-center space-x-2 text-[11px] text-slate-500">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>Secured via Firebase Authentication OAuth 2.0</span>
        </div>
      </div>
    </div>
  );
};
