@echo off
setlocal EnableDelayedExpansion

set "SOURCE_DIR=%~dp0.."
set "DIST_DIR=%~dp0..\dist"
set "RELEASE_DIR=%DIST_DIR%\HEAC_Release"

echo [INFO] Preparing Release Package...
echo [INFO] Source: %SOURCE_DIR%
echo [INFO] Dest:   %RELEASE_DIR%

REM Clean previous release
if exist "%RELEASE_DIR%" (
    echo [INFO] Cleaning old release...
    rmdir /s /q "%RELEASE_DIR%"
)
mkdir "%RELEASE_DIR%"

REM Robocopy options: /E (recursive), /XD (exclude dirs), /XF (exclude files)
REM Exclude dev folders and large temporary folders
set "EXCLUDE_DIRS=.venv __pycache__ .git .pytest_cache tests catboost_info dist .gemini .vscode .idea"
set "EXCLUDE_FILES=*.pyc *.pyo *.pyd .gitignore"

echo [INFO] Copying files...
robocopy "%SOURCE_DIR%" "%RELEASE_DIR%" /E /XD %EXCLUDE_DIRS% /XF %EXCLUDE_FILES% /NFL /NDL /NJH /NJS

REM Copy the launcher script to root as run.bat
copy "%~dp0launcher.bat" "%RELEASE_DIR%\run.bat" >nul

REM Create README
echo HEAC Deployment Package > "%RELEASE_DIR%\README.txt"
echo ======================= >> "%RELEASE_DIR%\README.txt"
echo. >> "%RELEASE_DIR%\README.txt"
echo 1. Ensure Python 3.8+ is installed. >> "%RELEASE_DIR%\README.txt"
echo 2. Run 'run.bat' to start the application. >> "%RELEASE_DIR%\README.txt"
echo 3. The first run will install necessary dependencies automatically. >> "%RELEASE_DIR%\README.txt"

echo.
echo [SUCCESS] Release package created at:
echo %RELEASE_DIR%
echo.
pause
