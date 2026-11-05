# ConsensusProbe

Disagreement-driven interactive gates for reliable LLM-based data cleaning with live full-stack web UI and Firebase Firestore cloud sync.

---

## Required Packages & Installation

To run this project from scratch, install the required Python, Node, and Firebase packages:

### 1. System & Global Tools
```bash
# Install Firebase CLI globally (if not already installed)
npm install -g firebase-tools
```

### 2. Backend Dependencies (Python 3.11+)
```bash
# Core backend, consensus engine, and automated browser testing libraries
pip install fastapi uvicorn sqlalchemy pandas pydantic openpyxl reportlab matplotlib numpy scipy httpx requests selenium
```

### 3. Frontend Dependencies (Node.js 18+)
```bash
cd frontend
npm install
npm install firebase
```

---

## Running the Project Locally

### Step 1: Start the Backend API Server
```bash
# From the project root
$env:PYTHONPATH = (Get-Location).Path   # on Windows PowerShell
# or: export PYTHONPATH=.               # on Linux/macOS
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
* API Documentation & Swagger UI: **http://127.0.0.1:8000/docs**

### Step 2: Start the Frontend UI
```bash
cd frontend
npm run dev
# or for production preview:
npm run build && npm run preview -- --port 5173
```
* Web Application: **http://127.0.0.1:5173**

---

## Automated Browser Testing (Auto Mode)

An automated end-to-end browser test script is included using Selenium and headless Google Chrome. It tests the complete pipeline end-to-end:
1. Uploads an ambiguous retail inventory CSV.
2. Profiles columns, missing values, and data types.
3. Triggers ConsensusGate multi-plan generation.
4. Detects plan disagreement and answers clarification questions via the UI.
5. Verifies the unified patch and downloads CSV, Excel, and Audit PDF exports.
6. Saves timestamped screenshots of every step.

```bash
python scripts/test_ui_e2e.py
```
* Output screenshots and exports are saved in `results/browser_screenshots/`.

---

## Firebase Cloud Deployment (Online Link & Database)

ConsensusProbe is integrated with Firebase Hosting and Cloud Firestore under project `ai-powered-multi-agents`.

### Configuration (`frontend/src/firebase.ts`)
```javascript
const firebaseConfig = {
  apiKey: "AIzaSyAjoXPfYkcee6or90W0MyiTd0oaAX-8pBM",
  authDomain: "ai-powered-multi-agents.firebaseapp.com",
  projectId: "ai-powered-multi-agents",
  storageBucket: "ai-powered-multi-agents.firebasestorage.app",
  messagingSenderId: "634255760892",
  appId: "1:634255760892:web:20a788bbed7ade776c2679",
  measurementId: "G-DSDLWKN71J"
};
```

### Deploying to Firebase
```bash
# 1. Login to your Firebase account
firebase login

# 2. Build the production frontend bundle
cd frontend && npm run build && cd ..

# 3. Deploy hosting and firestore rules
firebase deploy --only hosting,firestore
```
* **Live Online Web Link:** `https://ai-powered-multi-agents.web.app`
* **Cloud Database:** Firestore collection `cleaning_runs` automatically syncs dataset metadata, consensus scores, and resolved patch summaries.

---

## Project Structure

```
backend/          FastAPI application (upload, profile, clean, export)
frontend/         React + Vite + TypeScript + Tailwind UI + Firebase SDK
research/         ConsensusGate engine, policies, experiments
paper/            LaTeX manuscript and figures
results/          Experiment outputs (metrics.json, hypotheses.json, screenshots)
scripts/          Build, check, and automated testing scripts
configs/          Frozen experiment parameters
prereg/           Pre-registration and integrity lock
docs/             Charter, state, final report
```

## Reproduction & Verification

```bash
make verify_all    # runs tests, security, numbers check, determinism
make gate PHASE=N  # check a single phase
```

Expected runtime: ~60s for full experiment + verification.

## License

MIT
