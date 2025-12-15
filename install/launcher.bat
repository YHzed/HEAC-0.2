@echo off
setlocal

echo ==========================================
echo       HEAC 0.2 Application Launcher
echo ==========================================

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

REM Check/Create Virtual Environment
if not exist ".venv" (
    echo [INFO] First time setup: Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    
    echo [INFO] Activating environment...
    call .venv\Scripts\activate
    
    echo [INFO] Installing dependencies (this may take a while)...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    
    echo [INFO] Setup complete!
) else (
    echo [INFO] Activating environment...
    call .venv\Scripts\activate
)

REM Run App
echo [INFO] Launching Application...
streamlit run app.py

pause
