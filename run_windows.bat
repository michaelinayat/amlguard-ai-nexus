@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Creating Python virtual environment...
  python -m venv .venv
  if errorlevel 1 goto :error
)
echo Installing/updating dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :error
echo Starting AMLGuard AI Nexus at http://127.0.0.1:8000/ui
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
exit /b 0
:error
echo Setup failed. Confirm Python 3.11 or 3.12 is installed and available as 'py'.
pause
exit /b 1
