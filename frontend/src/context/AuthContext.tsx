import React, { createContext, useContext, useState, useEffect } from 'react';

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
  signInAsDemo: (customEmail?: string) => void;
  signOut: () => void;
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

  // Check stored token and setup expiry timer on mount
  useEffect(() => {
    const storedToken = localStorage.getItem(STORAGE_KEY_TOKEN);
    const storedUser = localStorage.getItem(STORAGE_KEY_USER);

    if (storedToken && storedUser) {
      try {
        const payload = decodeJwtPayload(storedToken);
        const parsedUser: UserProfile = JSON.parse(storedUser);

        if (payload && payload.exp) {
          const nowSeconds = Math.floor(Date.now() / 1000);
          if (payload.exp <= nowSeconds) {
            console.log('[Auth] Token expired on boot, clearing session.');
            performSignOut();
            return;
          }
          // Schedule auto-signout when expired
          const remainingMs = (payload.exp - nowSeconds) * 1000;
          const timer = setTimeout(() => {
            console.log('[Auth] Token expired during active session, auto signing out.');
            performSignOut();
          }, remainingMs);

          setToken(storedToken);
          setUser(parsedUser);
          setStatus('authenticated');
          return () => clearTimeout(timer);
        } else {
          // Valid demo/mock session without standard exp
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
  }, []);

  const signIn = (credentialToken: string): boolean => {
    const payload = decodeJwtPayload(credentialToken);
    if (!payload || !payload.email) {
      console.error('[Auth] Invalid token payload');
      return false;
    }

    // Optional domain restriction
    const allowedDomain = import.meta.env.VITE_ALLOWED_EMAIL_DOMAIN;
    if (allowedDomain && !payload.email.endsWith(`@${allowedDomain}`)) {
      console.warn(`[Auth] Email ${payload.email} does not match allowed domain: ${allowedDomain}`);
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

  const signInAsDemo = (customEmail: string = 'analyst@consensusprobe.internal') => {
    const demoUser: UserProfile = {
      name: customEmail.split('@')[0].toUpperCase(),
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

  const signOut = () => {
    performSignOut();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        status,
        token,
        signIn,
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
