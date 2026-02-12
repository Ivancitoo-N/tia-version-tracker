@echo off
REM TIA Version Tracker - Auto-start script
REM This script initializes and starts the application

REM Change to the script's directory
cd /d "%~dp0"

echo =====================================
echo  TIA Version Tracker
echo =====================================
echo.
echo [INFO] Working directory: %CD%
echo.

REM Check if database exists
if not exist "database\tia_tracker.db" (
    echo [SETUP] Database not found. Initializing...
    python -m src.tia_tracker.database.db_manager init
    if errorlevel 1 (
        echo [ERROR] Database initialization failed!
        pause
        exit /b 1
    )
    echo.
)

REM Check if dependencies are installed
echo [INFO] Checking dependencies...
python -c "import flask, flask_cors, reportlab, pydantic" 2>nul
if errorlevel 1 (
    echo [SETUP] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed!
        pause
        exit /b 1
    )
    echo.
)

REM Start the application
echo [START] Starting TIA Version Tracker...
echo [INFO] The application will be available at: http://localhost:5000
echo [INFO] Press Ctrl+C to stop the server
echo.

python -m src.tia_tracker.main

if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start!
    echo [ERROR] Please check the error messages above.
    pause
    exit /b 1
)

pause
