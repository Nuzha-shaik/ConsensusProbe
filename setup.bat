@echo off
REM ==============================================================================
REM ConsensusProbe - Automated Local Setup Script for Windows
REM ==============================================================================

echo [ConsensusProbe] Initializing Automated Environment Setup...
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

echo [Step 1/4] Installing Python Backend Dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)

echo.
echo [Step 2/4] Installing Frontend Node Dependencies...
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
)
if not exist frontend\.env (
    copy frontend\.env.example frontend\.env >nul
    echo Created frontend\.env from frontend\.env.example
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
echo [SUCCESS] ConsensusProbe environment setup is complete!
echo.
echo To run the project locally:
echo   1. Start Backend:  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
echo   2. Start Frontend: cd frontend ^& npm run dev
echo   3. Open Browser:   http://127.0.0.1:5173
echo ==============================================================================
pause
