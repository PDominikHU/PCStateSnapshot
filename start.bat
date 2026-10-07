@echo off
setlocal
cd /d "%~dp0"

echo PC State Snapshot ^& Diff - setup

echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Installing required dependency...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo Setup complete.
echo.
echo Use the following command in PowerShell:
echo   .\sysnapshot --help
echo.
pause
