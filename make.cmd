@echo off
setlocal

set TARGET=%1
if "%TARGET%"=="" set TARGET=verify_all

if "%TARGET%"=="verify_all" (
    python scripts\verify_all.py
    exit /b %ERRORLEVEL%
)

if "%TARGET%"=="tests" (
    python -m pytest -x -q research/ backend/
    exit /b %ERRORLEVEL%
)

if "%TARGET%"=="build" (
    cd frontend && npm run build
    exit /b %ERRORLEVEL%
)

if "%TARGET%"=="gate" (
    set PHASE=%2
    if "%PHASE%"=="" set PHASE=1
    python scripts\gate.py %PHASE%
    exit /b %ERRORLEVEL%
)

if "%TARGET%"=="security" (
    python scripts\check_security.py
    exit /b %ERRORLEVEL%
)

if "%TARGET%"=="lock_check" (
    python scripts\check_lock.py
    exit /b %ERRORLEVEL%
)

if "%TARGET%"=="numbers_check" (
    python scripts\check_numbers.py
    exit /b %ERRORLEVEL%
)

if "%TARGET%"=="ui_gate" (
    python scripts\ui_gate.py
    exit /b %ERRORLEVEL%
)

if "%TARGET%"=="paper" (
    echo latexmk not available (DEGRADED mode)
    exit /b 0
)

echo Unknown target: %TARGET%
exit /b 1
