import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import { getAnalytics, isSupported } from 'firebase/analytics';
import {
  getFirestore,
  collection,
  addDoc,
  getDocs,
  query,
  orderBy,
  limit,
  serverTimestamp,
  Firestore
} from 'firebase/firestore';
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User,
  Auth
} from 'firebase/auth';

export const firebaseConfig = {
  apiKey: (import.meta.env.VITE_FIREBASE_API_KEY || '') as string,
  authDomain: (import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '') as string,
  projectId: (import.meta.env.VITE_FIREBASE_PROJECT_ID || '') as string,
  storageBucket: (import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '') as string,
  messagingSenderId: (import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '') as string,
  appId: (import.meta.env.VITE_FIREBASE_APP_ID || '') as string,
  measurementId: (import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || '') as string,
};

let app: FirebaseApp | null = null;
let auth: Auth | null = null;
let googleProvider: GoogleAuthProvider | null = null;
let db: Firestore | null = null;

if (firebaseConfig.apiKey) {
  try {
    app = getApps().length > 0 ? getApps()[0] : initializeApp(firebaseConfig);
    auth = getAuth(app);
    googleProvider = new GoogleAuthProvider();
    db = getFirestore(app);
  } catch (err) {
    console.warn('[Firebase] Initialization error (running in fallback mode):', err);
  }
} else {
  console.warn('[Firebase] No VITE_FIREBASE_API_KEY configured. Running in offline/demo mode.');
}

export { app, auth, googleProvider, db };

// Initialize Analytics conditionally
export const analyticsPromise = (app && typeof window !== 'undefined')
  ? isSupported().then((yes) => (yes && app ? getAnalytics(app) : null)).catch(() => null)
  : Promise.resolve(null);

// Auth helper functions
export async function signInWithGoogle() {
  if (!auth || !googleProvider) {
    return { user: null, error: 'Firebase Auth is not configured. Please use Demo Login.' };
  }
  try {
    const result = await signInWithPopup(auth, googleProvider);
    return { user: result.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
}

export async function loginWithEmail(email: string, pass: string) {
  if (!auth) {
    return { user: null, error: 'Firebase Auth is not configured. Please use Demo Login.' };
  }
  try {
    const res = await signInWithEmailAndPassword(auth, email, pass);
    return { user: res.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
}

export async function registerWithEmail(email: string, pass: string) {
  if (!auth) {
    return { user: null, error: 'Firebase Auth is not configured. Please use Demo Login.' };
  }
  try {
    const res = await createUserWithEmailAndPassword(auth, email, pass);
    return { user: res.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
}

export async function logoutUser() {
  if (auth) {
    try {
      await signOut(auth);
    } catch (err) {
      console.warn('[Firebase] Sign out error:', err);
    }
  }
}

export function subscribeToAuth(callback: (user: User | null) => void) {
  if (!auth) {
    callback(null);
    return () => {};
  }
  return onAuthStateChanged(auth, callback);
}

// Database helper: save cleaning run to Firestore
export async function recordCleaningRun(runData: {
  datasetId: string;
  filename: string;
  rows: number;
  cols: number;
  consensusScore: number | null;
  status: string;
  patchSummary?: any;
  userEmail?: string | null;
}) {
  if (!db) {
    return null;
  }
  try {
    const colRef = collection(db, 'cleaning_runs');
    const docRef = await addDoc(colRef, {
      ...runData,
      createdAt: serverTimestamp(),
    });
    console.log('[Firebase] Cleaning run recorded with ID:', docRef.id);
    return docRef.id;
  } catch (err) {
    console.warn('[Firebase] Could not sync to Firestore (offline or rule restricted):', err);
    return null;
  }
}

// Database helper: fetch recent cleaning runs
export async function getRecentCleaningRuns(maxCount: number = 10) {
  if (!db) {
    return [];
  }
  try {
    const colRef = collection(db, 'cleaning_runs');
    const q = query(colRef, orderBy('createdAt', 'desc'), limit(maxCount));
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
  } catch (err) {
    console.warn('[Firebase] Could not fetch cleaning runs from Firestore:', err);
    return [];
  }
}

export type { User };
