#!/usr/bin/env bash
# ==============================================================================
# ConsensusProbe - Automated Local Setup Script for Linux/macOS
# ==============================================================================

set -e

echo "[ConsensusProbe] Initializing Automated Environment Setup..."
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.10+."
    exit 1
fi

# 2. Check Node
if ! command -v node &> /dev/null; then
    echo "[ERROR] node could not be found. Please install Node.js 18+."
    exit 1
fi

echo "[Step 1/4] Installing Python Backend Dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo ""
echo "[Step 2/4] Installing Frontend Node Dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "[Step 3/4] Initializing Environment Variables (.env)..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created root .env from .env.example"
fi
if [ ! -f frontend/.env ]; then
    cp frontend/.env.example frontend/.env
    echo "Created frontend/.env from frontend/.env.example"
fi

echo ""
echo "[Step 4/4] Verifying Frontend Production Build..."
cd frontend
npm run build
cd ..

echo ""
echo "=============================================================================="
echo "[SUCCESS] ConsensusProbe environment setup is complete!"
echo ""
echo "To run the project locally:"
echo "  1. Start Backend:  export PYTHONPATH=. && python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"
echo "  2. Start Frontend: cd frontend && npm run dev"
echo "  3. Open Browser:   http://127.0.0.1:5173"
echo "=============================================================================="
