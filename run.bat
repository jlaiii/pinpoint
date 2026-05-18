@echo off
cd /d "%~dp0"

:: Check for Python
python --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in your PATH.
    echo.
    echo Please install Python from https://python.org and check "Add Python to PATH" during setup.
    echo.
    pause
    exit /b 1
)

:: Check for Pillow
echo Checking dependencies...
python -c "from PIL import ImageGrab" > nul 2>&1
if errorlevel 1 (
    echo Installing Pillow...
    python -m pip install Pillow
)

:: Launch
echo Starting Pinpoint...
start pythonw pinpoint.py
