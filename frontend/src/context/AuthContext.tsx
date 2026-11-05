import React, { createContext, useContext, useState, useEffect } from 'react';
import { auth, googleProvider, logoutUser } from '../firebase';
import { signInWithPopup, onAuthStateChanged } from 'firebase/auth';

export interface UserProfile {
  name: string;
  email: string;
  picture: string;
  sub?: string;
}

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated';

interface AuthContextType {
  user: UserProfile | null;
  status: AuthStatus;
  token: string | null;
  signIn: (credentialToken: string) => boolean;
  signInWithGoogleAuth: () => Promise<{ success: boolean; error: string | null }>;
  signInAsDemo: (customEmail?: string) => void;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY_TOKEN = 'cp_auth_token';
const STORAGE_KEY_USER = 'cp_auth_user';

// Decode standard JWT payload using native atob (Rule: no external JWT library)
function decodeJwtPayload(jwt: string): any | null {
  try {
    const parts = jwt.split('.');
    if (parts.length !== 3) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (err) {
    console.warn('[Auth] Failed to decode JWT payload:', err);
    return null;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');

  const performSignOut = () => {
    localStorage.removeItem(STORAGE_KEY_TOKEN);
    localStorage.removeItem(STORAGE_KEY_USER);
    setToken(null);
    setUser(null);
    setStatus('unauthenticated');
    if (typeof window !== 'undefined' && (window as any).google?.accounts?.id?.disableAutoSelect) {
      try {
        (window as any).google.accounts.id.disableAutoSelect();
      } catch (e) {
        // Safe no-op
      }
    }
  };

  // Sync with Firebase Auth state on mount
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
      if (fbUser) {
        try {
          const idToken = await fbUser.getIdToken();
          const userProfile: UserProfile = {
            name: fbUser.displayName || fbUser.email?.split('@')[0] || 'User',
            email: fbUser.email || '',
            picture: fbUser.photoURL || '',
            sub: fbUser.uid,
          };
          localStorage.setItem(STORAGE_KEY_TOKEN, idToken);
          localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(userProfile));
          setToken(idToken);
          setUser(userProfile);
          setStatus('authenticated');
        } catch (e) {
          console.warn('[Auth] Failed to get Firebase token:', e);
          performSignOut();
        }
      } else {
        // Fallback: check stored local session (e.g. guest or standard JWT)
        const storedToken = localStorage.getItem(STORAGE_KEY_TOKEN);
        const storedUser = localStorage.getItem(STORAGE_KEY_USER);

        if (storedToken && storedUser) {
          try {
            const payload = decodeJwtPayload(storedToken);
            const parsedUser: UserProfile = JSON.parse(storedUser);

            if (payload && payload.exp) {
              const nowSeconds = Math.floor(Date.now() / 1000);
              if (payload.exp <= nowSeconds) {
                performSignOut();
                return;
              }
              const remainingMs = (payload.exp - nowSeconds) * 1000;
              const timer = setTimeout(() => {
                performSignOut();
              }, remainingMs);

              setToken(storedToken);
              setUser(parsedUser);
              setStatus('authenticated');
              return () => clearTimeout(timer);
            } else {
              setToken(storedToken);
              setUser(parsedUser);
              setStatus('authenticated');
              return;
            }
          } catch (e) {
            performSignOut();
          }
        } else {
          setStatus('unauthenticated');
        }
      }
    });

    return () => unsubscribe();
  }, []);

  const signIn = (credentialToken: string): boolean => {
    const payload = decodeJwtPayload(credentialToken);
    if (!payload || !payload.email) {
      console.error('[Auth] Invalid token payload');
      return false;
    }

    const userProfile: UserProfile = {
      name: payload.name || payload.email.split('@')[0],
      email: payload.email,
      picture: payload.picture || '',
      sub: payload.sub,
    };

    localStorage.setItem(STORAGE_KEY_TOKEN, credentialToken);
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(userProfile));
    setToken(credentialToken);
    setUser(userProfile);
    setStatus('authenticated');
    return true;
  };

  const signInWithGoogleAuth = async (): Promise<{ success: boolean; error: string | null }> => {
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const fbUser = result.user;
      const idToken = await fbUser.getIdToken();
      const userProfile: UserProfile = {
        name: fbUser.displayName || fbUser.email?.split('@')[0] || 'Google User',
        email: fbUser.email || '',
        picture: fbUser.photoURL || '',
        sub: fbUser.uid,
      };

      localStorage.setItem(STORAGE_KEY_TOKEN, idToken);
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(userProfile));
      setToken(idToken);
      setUser(userProfile);
      setStatus('authenticated');
      return { success: true, error: null };
    } catch (err: any) {
      console.error('[Auth] Google sign in error:', err);
      let msg = 'Google Sign-In failed.';
      if (err.code === 'auth/popup-closed-by-user') {
        msg = 'Sign-in cancelled. Popup was closed before completion.';
      } else if (err.code === 'auth/popup-blocked') {
        msg = 'Popup blocked by browser. Please enable popups for this site.';
      } else if (err.code === 'auth/unauthorized-domain') {
        const host = typeof window !== 'undefined' ? window.location.hostname : 'current domain';
        msg = `Domain "${host}" is not authorized in Firebase. Add "${host}" in Firebase Console -> Authentication -> Settings -> Authorized domains. (If running locally, open http://localhost:5173 instead of 127.0.0.1)`;
      } else if (err.message) {
        msg = err.message;
      }
      return { success: false, error: msg };
    }
  };

  const signInAsDemo = (customEmail: string = 'analyst@consensusprobe.internal') => {
    const demoUser: UserProfile = {
      name: customEmail.includes('@') ? customEmail.split('@')[0].toUpperCase() : 'Guest Analyst',
      email: customEmail,
      picture: '',
      sub: 'demo-local-analyst',
    };
    const demoToken = 'demo-session-token-' + Date.now();
    localStorage.setItem(STORAGE_KEY_TOKEN, demoToken);
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(demoUser));
    setToken(demoToken);
    setUser(demoUser);
    setStatus('authenticated');
  };

  const signOut = async () => {
    try {
      await logoutUser();
    } catch (e) {
      console.warn('[Auth] Firebase logout warning:', e);
    }
    performSignOut();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        status,
        token,
        signIn,
        signInWithGoogleAuth,
        signInAsDemo,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
