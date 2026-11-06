@echo off
REM ==============================================================================
REM ConsensusProbe - Automated Local Setup Script for Windows
REM ==============================================================================

echo ==============================================================================
echo [ConsensusProbe] Initializing Automated Environment Setup...
echo ==============================================================================
echo.

REM 1. Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.10+ and re-run.
    pause
    exit /b 1
)

REM 2. Check Node.js installation
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not found in PATH. Please install Node.js 18+ and re-run.
    pause
    exit /b 1
)

echo [Step 1/4] Installing Python Backend Dependencies via requirements.txt:
echo   - FastAPI ^& Uvicorn (REST API Server)
echo   - Python-Multipart ^& Pydantic (Form Uploads ^& Schemas)
echo   - SQLAlchemy (SQLite Database ORM)
echo   - Pandas, NumPy, SciPy ^& OpenPyXL (20+ Column Matrix Normalization)
echo   - ReportLab ^& Matplotlib (Audit PDF Report Generation)
echo   - HTTPX ^& Requests (HTTP API Clients)
echo   - Pytest, AnyIO ^& Selenium (Testing Suites)
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)

echo.
echo [Step 2/4] Installing Frontend Node Dependencies via package.json:
echo   - React 18 ^& React-DOM (Reactive UI Components)
echo   - Vite ^& TypeScript (Fast Bundler ^& Type System)
echo   - Tailwind CSS, PostCSS, Autoprefixer (Styling System)
echo   - Firebase SDK (Authentication ^& Cloud Firestore Sync)
echo   - Lucide-React (Icons)
echo   - jsPDF ^& jsPDF-AutoTable (Client-side PDF Generation)
echo   - Vitest ^& Playwright (Frontend Testing Suites)
echo.
cd frontend
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install frontend npm packages.
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo [Step 3/4] Initializing Environment Variables (.env)...
if not exist .env (
    copy .env.example .env >nul
    echo Created root .env from .env.example
) else (
    echo Root .env already exists.
)
if not exist frontend\.env (
    copy frontend\.env.example frontend\.env >nul
    echo Created frontend\.env from frontend\.env.example
) else (
    echo Frontend .env already exists.
)

echo.
echo [Step 4/4] Verifying Frontend Production Build...
cd frontend
call npm run build
if errorlevel 1 (
    echo [WARNING] Build check had warnings or errors. Check console output above.
)
cd ..

echo.
echo ==============================================================================
echo [SUCCESS] All Python and Node packages installed successfully!
echo.
echo To run the project locally:
echo   1. Start Backend Server: python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
echo   2. Start Frontend UI:    cd frontend ^& npm run dev
echo   3. Open Browser:         http://127.0.0.1:5173
echo ==============================================================================
pause
