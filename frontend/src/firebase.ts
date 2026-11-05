import { initializeApp } from 'firebase/app';
import { getAnalytics, isSupported } from 'firebase/analytics';
import {
  getFirestore,
  collection,
  addDoc,
  getDocs,
  query,
  orderBy,
  limit,
  serverTimestamp
} from 'firebase/firestore';
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User
} from 'firebase/auth';

export const firebaseConfig = {
  apiKey: "AIzaSyAjoXPfYkcee6or90W0MyiTd0oaAX-8pBM",
  authDomain: "ai-powered-multi-agents.firebaseapp.com",
  projectId: "ai-powered-multi-agents",
  storageBucket: "ai-powered-multi-agents.firebasestorage.app",
  messagingSenderId: "634255760892",
  appId: "1:634255760892:web:20a788bbed7ade776c2679",
  measurementId: "G-DSDLWKN71J"
};

// Initialize Firebase App
export const app = initializeApp(firebaseConfig);

// Initialize Firebase Auth
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

// Initialize Firestore (Database)
export const db = getFirestore(app);

// Initialize Analytics conditionally
export const analyticsPromise = isSupported().then((yes) => yes ? getAnalytics(app) : null);

// Auth helper functions
export async function signInWithGoogle() {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    return { user: result.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
}

export async function loginWithEmail(email: string, pass: string) {
  try {
    const res = await signInWithEmailAndPassword(auth, email, pass);
    return { user: res.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
}

export async function registerWithEmail(email: string, pass: string) {
  try {
    const res = await createUserWithEmailAndPassword(auth, email, pass);
    return { user: res.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
}

export async function logoutUser() {
  await signOut(auth);
}

export function subscribeToAuth(callback: (user: User | null) => void) {
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
