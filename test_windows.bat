@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Virtual environment missing. Run run_windows.bat once first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pytest -q
pause
