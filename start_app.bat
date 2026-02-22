@echo off
echo Starting LecGen AI Workspace...

:: Cleanup old processes
taskkill /F /IM node.exe /T 2>nul
taskkill /F /IM python.exe /T 2>nul

echo Initializing Backend Engine...
start cmd /k "venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000"

echo Initializing Frontend Studio...
start cmd /k "cd frontend && npm run dev"

echo.
echo --------------------------------------
echo  Neural Engine: http://localhost:8000
echo  User Interface: http://localhost:5173
echo --------------------------------------
echo.
pause
