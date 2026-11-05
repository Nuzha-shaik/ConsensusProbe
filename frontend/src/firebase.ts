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

// Initialize Firestore (Database)
export const db = getFirestore(app);

// Initialize Analytics conditionally (only in supported browser environments)
export const analyticsPromise = isSupported().then((yes) => yes ? getAnalytics(app) : null);

// Database helper: save cleaning run to Firestore
export async function recordCleaningRun(runData: {
  datasetId: string;
  filename: string;
  rows: number;
  cols: number;
  consensusScore: number | null;
  status: string;
  patchSummary?: any;
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
