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
  apiKey: "YOUR_FIREBASE_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.firebasestorage.app",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID",
  measurementId: "YOUR_MEASUREMENT_ID"
};
```

### Google OAuth 2.0 Setup

1. Open [Google Cloud Console](https://console.cloud.google.com/) -> **APIs & Services** -> **Credentials**.
2. Click **Create Credentials** -> **OAuth client ID**.
3. Select **Application type: Web application**.
4. Set **Authorized JavaScript origins**:
   - `http://localhost:5173`
   - `http://127.0.0.1:5173`
   - `https://ai-powered-multi-agents.web.app`
5. Set **OAuth consent screen** user type to **External** so any Google user can sign in.
6. Copy the generated Client ID and add it to your `.env` or `frontend/.env`:
   ```bash
   VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   ```
7. Rebuild the frontend (`cd frontend && npm run build`).

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
