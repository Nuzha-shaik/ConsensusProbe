# ConsensusProbe: Disagreement-Driven Interactive Gates for Reliable LLM-Based Data Cleaning

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React: 18.3](https://img.shields.io/badge/React-18.3.1-61DAFB.svg?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6.3-3178C6.svg?logo=typescript)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4.11-646CFF.svg?logo=vite)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4.15-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Hosting%20%26%20Firestore-FFA611.svg?logo=firebase)](https://firebase.google.com/)
[![Build: Passing](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()

> **Live Web Application:** [https://ai-powered-multi-agents.web.app](https://ai-powered-multi-agents.web.app)  
> **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
> **Research Manuscript:** [Research_Paper.pdf](Research_Paper.pdf) (IEEE Conference Format)

---

## 1. Executive Project Explanation

### What is ConsensusProbe?
**ConsensusProbe** is an AI safety governance and multi-agent coordination system designed for automated data cleaning and tabular transformation.

### The Problem in Enterprise Data Engineering
When enterprises use Large Language Models (LLMs) or automated heuristics to clean messy, heterogeneous spreadsheets:
- **Silent Destructive Errors:** A single unregulated LLM will aggressively hallucinate and silently drop valid customer records, alter numeric currency figures, or overwrite missing entries with unverified defaults.
- **Analyst Fatigue:** Existing "human-in-the-loop" systems force data engineers to review every ambiguity manually ($1.00\text{ questions/task}$), causing severe operational bottlenecks.

### The ConsensusProbe Solution
ConsensusProbe enforces the principle: **Never trust a single LLM to alter business data alone.**

```
 Messy Data (CSV / XLSX)
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ 1. Ingestion & 20+ Column Matrix Normalization         │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. Tri-Agent Ensemble Proposer Swarm (K = 3)           │
│    • Agent Alpha (Type Inference & Normalization)      │
│    • Agent Beta  (Semantic Entity Reconciliation)      │
│    • Agent Gamma (Cross-Tab Pivot & Schema Alignment)  │
└──────────────────────────┬─────────────────────────────┘
                           │  Candidate Plans (P₁, P₂, P₃)
                           ▼
┌────────────────────────────────────────────────────────┐
│ 3. Disagreement Gate (Pairwise Dice Distance d)        │
│    d(P_i, P_j) = 1 - (2 |P_i ∩ P_j|) / (|P_i| + |P_j|)  │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    d ≤ τ_d (Unanimous / Safe)     d > τ_d (Ambiguity Detected)
             │                           │
             ▼                           ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│ Auto-Approved Execution  │   │ Interactive Gate Prompt  │
│ Zero analyst disruption  │   │ Human picks best plan    │
└────────────┬─────────────┘   └─────────────┬────────────┘
             │                               │
             └───────────────┬───────────────┘
                             ▼
┌────────────────────────────────────────────────────────┐
│ 4. Cryptographic Provenance Ledger & Audit Report      │
│    • SHA-256 Before/After Dataset Hash Verification    │
│    • Red-Border Outlined Reconciled Numbers Preview    │
│    • Export to Clean CSV, Multi-Sheet XLSX & Audit PDF │
└────────────────────────────────────────────────────────┘
```

---

## 2. Real-World Concrete Walkthrough

### Example 1: Unanimous Agreement ($d = 0.00 \to \text{Auto-Approved}$)
Suppose a dataset has an orphaned row where all primary fields (`Name`, `Email`, `Phone`) are empty:
- **Agent Alpha:** "Row contains zero identifiers. Delete row."
- **Agent Beta:** "Row contains zero identifiers. Delete row."
- **Agent Gamma:** "Row contains zero identifiers. Delete row."
- **ConsensusGate:** Pairwise semantic distance $d = 0.0000 \le \tau_d$. The row is cleaned automatically without interrupting the human engineer.

### Example 2: Contested Ambiguity ($d > 0.00 \to \text{Clarification Gate}$)
Suppose an ambiguous customer record exists:
`Row 1: John Smith | Email: john@gmail.com | Phone: 555-0199`  
`Row 2: John Smith | Email: john@gmail.com | Phone: (blank)`  
- **Agent Alpha (Aggressive):** "Row 2 has missing phone number. Drop Row 2."
- **Agent Beta (Merge Specialist):** "Both rows share `john@gmail.com`. Merge Row 2 into Row 1 to preserve order history."
- **Agent Gamma (Conservative):** "Keep both rows; impute phone on Row 2 from Row 1."
- **A Single AI would have silently deleted John Smith's order!**
- **ConsensusProbe:** The Supervisor detects semantic divergence ($d = 0.67 > \tau_d$), halts the pipeline, and presents a targeted multi-choice prompt to the analyst. The human confirms "Merge Rows", protecting corporate revenue.

### Example 3: 20+ Column Cross-Tab Normalization
Spreadsheets often arrive as complex pivot matrices (e.g. `CA-100293` with shipping modes like *First Class*, *Second Class*, *Standard Class* spread across horizontal columns).
- Traditional naive cleaners treat blank shipping cells as missing values and delete entire rows.
- ConsensusProbe's **20+ Column Scanner** automatically identifies pivot grids, unpivots shipping columns into a canonical schema (`Ship Mode`, `Segment`, `Order ID`, `Order Date`, `Sales`), preserving all 822 rows and highlighting reconciled currency figures in red-bordered audit boxes.

---

## 3. Empirical Research Benchmarks

Evaluated over **100 held-out tasks** across 300 experimental runs (documented in `Research_Paper.pdf`):

| Metric | System A (Unregulated 1-LLM) | System B (Majority Vote, No Gate) | System C (Always Ask Human) | ConsensusProbe (System F) |
|---|---|---|---|---|
| **Silent Error Rate** | 5.0% *(Data loss)* | 5.0% *(Shared error)* | 0.0% | **0.0% (100% Elimination)** |
| **Task Success Rate** | 70.3% | 71.3% | 92.0% | **91.8% (Pareto Optimal)** |
| **Human Questions / Task** | 0.00 | 0.00 | 1.00 *(Fatigue)* | **0.38 (62% Less Fatigue)** |
| **Canary Interception Rate** | 0.0% | 0.0% | 100% | **100% Protected** |

---

## 4. Package & Dependency Matrix

Every package and library required by this repository is cleanly managed across dedicated configuration files:

| Layer | Configuration File | Key Packages & Libraries Declared | Purpose |
|---|---|---|---|
| **Python Backend** | [`requirements.txt`](requirements.txt) | `fastapi`, `uvicorn`, `python-multipart`, `sqlalchemy`, `pydantic`, `pandas`, `openpyxl`, `reportlab`, `numpy`, `scipy`, `matplotlib`, `httpx`, `requests`, `pytest`, `selenium` | REST API, Multi-plan consensus engine, 20+ column normalization, SHA-256 hashing, PDF audit generation, and test suites. |
| **Frontend UI** | [`frontend/package.json`](frontend/package.json) | `react`, `react-dom`, `firebase`, `lucide-react`, `@react-oauth/google`, `jspdf`, `jspdf-autotable`, `tailwindcss`, `vite`, `typescript`, `vitest`, `@playwright/test` | Reactive single-page web app, live tri-agent swarm inspector, real-time threshold slider, interactive client-side fallback engine, and Tailwind design system. |
| **Cloud Hosting & DB** | [`firebase.json`](firebase.json), [`firestore.rules`](firestore.rules) | `firebase-tools` (CLI) | Global edge deployment, automated SPA rewrite rules, and Firestore database security policies. |
| **Editor / IDE** | [`.vscode/extensions.json`](.vscode/extensions.json) | Python (`ms-python.python`), Pylance, Tailwind CSS IntelliSense, ESLint, Prettier, Thunder Client | Uniform developer tooling, code formatting, syntax highlighting, and API testing inside VS Code. |

---

## 5. Step-by-Step Local Setup & Execution Guide

### System Prerequisites
Ensure you have the following installed on your machine:
- **Python**: Version `3.10`, `3.11`, `3.12`, or `3.13` (`python --version`)
- **Node.js**: Version `18.x` or `20.x+` (`node --version`)
- **Package Manager**: `npm` (`npm --version`)
- **Git**: (`git --version`)
- **Optional**: `firebase-tools` (`npm install -g firebase-tools`) for cloud deployment

---

### Method A: One-Click Automated Setup

#### On Windows (PowerShell or Command Prompt):
```cmd
setup.bat
```

#### On Linux or macOS:
```bash
chmod +x setup.sh
./setup.sh
```

---

### Method B: Manual Step-by-Step Setup

#### Step 1: Clone the Repository
```bash
git clone https://github.com/kgajula2/ConsensusProbe.git
cd ConsensusProbe
```

#### Step 2: Set Up Python Virtual Environment & Backend Packages
```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the virtual environment:
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows Command Prompt:
.\venv\Scripts\activate.bat
# On Linux / macOS:
source venv/bin/activate

# 3. Upgrade pip and install all Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Install Frontend NPM Packages
```bash
cd frontend
npm install
cd ..
```

#### Step 4: Configure Environment Variables
Copy the provided `.env.example` templates:
```bash
# In the root directory:
cp .env.example .env

# In the frontend directory:
cp frontend/.env.example frontend/.env
```
*(Default configuration runs completely out of the box with the built-in local SQLite database and mock LLM provider).*

#### Step 5: Start the Backend API Server
Open a terminal in the project root:
```bash
# On Windows PowerShell:
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# On Linux / macOS:
export PYTHONPATH=.
python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
* **API Server:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Interactive Swagger UI Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **API Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

#### Step 6: Start the Frontend UI Development Server
Open a second terminal window:
```bash
cd frontend
npm run dev
```
* **Frontend Dashboard:** [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 6. Running Tests & Quality Verification

ConsensusProbe includes automated unit, integration, and security test suites:

### 1. Backend Integration Tests (FastAPI + Consensus Engine)
```bash
python -m pytest backend/tests/test_api.py -v
```
Verifies formula injection neutralization (`=SUM`, `+`, `-`, `@`), file upload validation, and full end-to-end cleaning and export workflows.

### 2. Frontend Type Checking & Production Build
```bash
cd frontend
npm run build
cd ..
```
Executes TypeScript compile (`tsc`) and Vite bundling to ensure zero syntax or type regressions.

### 3. Security Hygiene & Leak Guard
```bash
python scripts/check_security.py
```
Audits project source files for unintended secret exposure, token leaks, or frozen path modifications.

### 4. Automated End-to-End Headless Browser Test
```bash
python scripts/test_ui_e2e.py
```
Uses Selenium and headless Google Chrome to ingest a sample, trigger consensus, answer clarifications, download reports, and save timestamped screenshots in `results/browser_screenshots/`.

---

## 7. Firebase Cloud Deployment (Production)

The live web application is hosted on Firebase Hosting with Cloud Firestore integration.

### Deployment Steps:
```bash
# 1. Authenticate with Firebase CLI
firebase login

# 2. Build the production frontend distribution
cd frontend
npm run build
cd ..

# 3. Deploy hosting assets and database security rules
firebase deploy --only "hosting,firestore"
```
* **Live Web App:** [https://ai-powered-multi-agents.web.app](https://ai-powered-multi-agents.web.app)
* **Firebase Console:** [https://console.firebase.google.com/project/ai-powered-multi-agents/overview](https://console.firebase.google.com/project/ai-powered-multi-agents/overview)

---

## 8. Repository Structure

```
ConsensusProbe/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI application & REST endpoints
│   │   ├── export.py             # CSV, XLSX, and ReportLab Audit PDF generator
│   │   └── models.py             # Database schemas & Pydantic models
│   └── tests/
│       └── test_api.py           # Backend integration and security tests
├── frontend/
│   ├── src/
│   │   ├── App.tsx               # Main Dashboard with Swarm Inspector & Metrics
│   │   ├── pages/LoginPage.tsx   # Impeccable Multi-Agent status login screen
│   │   ├── components/showcase/  # SwarmAgentCards, ThresholdSimulator, Timeline
│   │   ├── lib/                  # layoutNormalizer.ts, clientEngine.ts, gateDecision.ts
│   │   └── firebase.ts           # Firebase SDK initialization & Firestore sync
│   ├── package.json              # Frontend dependencies and build scripts
│   ├── tsconfig.json             # TypeScript compiler settings
│   └── vite.config.ts            # Vite bundler configuration
├── research/
│   ├── canary.py                 # Ground-truth canary injection and audit logic
│   └── run_experiments.py        # 100-task empirical evaluation pipeline
├── scripts/
│   ├── check_security.py         # Security and secret scanning guard
│   ├── layout_normalizer.py      # Python 20+ column matrix normalization
│   └── test_ui_e2e.py            # Automated Selenium headless browser test
├── .vscode/
│   └── extensions.json           # Recommended VS Code extensions
├── setup.bat                     # 1-Click setup script for Windows
├── setup.sh                      # 1-Click setup script for Linux / macOS
├── requirements.txt              # Complete Python dependencies
├── firebase.json                 # Firebase Hosting configuration
├── firestore.rules               # Cloud Firestore security rules
├── Research_Paper.pdf            # Full academic paper (IEEE format)
└── README.md                     # Comprehensive documentation & setup guide
```

---

## 9. Citation & Academic Reference

If you build upon this work or use ConsensusProbe in your research, please cite:

```bibtex
@inproceedings{consensusprobe2026,
  title={ConsensusProbe: Disagreement-Driven Interactive Gates for Reliable LLM-Based Data Cleaning},
  author={Gajula, Krishna and Contributors},
  booktitle={IEEE Conference Proceedings},
  year={2026}
}
```

---

## 10. License

This project is licensed under the [MIT License](LICENSE).
