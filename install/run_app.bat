@echo off
setlocal

REM Change directory to the project root (parent of install)
pushd "%~dp0.."

echo ==========================================
echo       HEAC 0.2 Deployment Script
echo ==========================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

REM Check if .venv exists, if not create it
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created.
) else (
    echo [INFO] Found existing virtual environment.
)

REM Activate virtual environment
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
if exist "requirements.txt" (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    echo [WARNING] requirements.txt not found. Skipping dependency installation.
)

REM Run the Streamlit application
echo [INFO] Starting Streamlit application...
echo ==========================================
streamlit run app.py

if %errorlevel% neq 0 (
    echo [ERROR] Application crashed or failed to start.
    pause
)

popd
