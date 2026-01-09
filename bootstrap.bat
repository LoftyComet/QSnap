@echo off
setlocal
set "BACKEND_TITLE=QSnap-Backend"
set "FRONTEND_TITLE=QSnap-Frontend"

echo ==========================================
echo           Starting QSnap Project
echo ==========================================

REM Check if .venv exists
if not exist ".venv" (
    echo Error: .venv not found. Please create a virtual environment first.
    pause
    exit /b 1
)

echo [1/2] Starting Backend...
start "%BACKEND_TITLE%" cmd /c "title %BACKEND_TITLE% && cd backend && ..\.venv\Scripts\activate && uvicorn app.main:app --reload --port 8001"

echo [2/2] Starting Frontend...
start "%FRONTEND_TITLE%" cmd /c "title %FRONTEND_TITLE% && cd frontend && npm run dev"

echo.
echo ==========================================
echo Services are running.
echo Frontend: http://localhost:3001
echo Backend:  http://localhost:8001
echo.
echo Press any key in this window to continue.
echo ==========================================

pause > nul

exit
