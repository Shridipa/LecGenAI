@echo off
echo ===================================================
echo   Setting up Environment for PyTesseract OCR
echo ===================================================

echo [1/2] Installing pytesseract in the current environment...
python -m pip install pytesseract

echo.
echo [2/2] Starting Server...
echo (Please stop any other running uvicorn instance first!)
echo.
python -m uvicorn api.main:app --reload --port 8000
