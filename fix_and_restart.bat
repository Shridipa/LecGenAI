@echo off
echo ===================================================
echo   FIXING PYQ ANALYSIS SERVER
echo ===================================================

echo [1/3] Stopping any stuck server processes...
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq api.main:app" >nul 2>&1
echo Done.

echo.
echo [2/3] Verifying Dependencies...
python -m pip install pytesseract pdfplumber pypdfium2 --disable-pip-version-check
echo Done.

echo.
echo [3/3] Starting Server in CORRECT Environment...
echo (Please wait for 'Application startup complete')
echo.
python -m uvicorn api.main:app --reload --port 8000
