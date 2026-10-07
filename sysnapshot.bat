@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found.
    echo Run start.bat first to install the project.
    exit /b 3
)

".venv\Scripts\python.exe" run.py %*
exit /b %errorlevel%
