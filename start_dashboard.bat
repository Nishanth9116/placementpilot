@echo off
title PlacementPilot - Web Dashboard
echo =====================================================================
echo  PlacementPilot Web Dashboard
echo  Local AI Placement Platform - http://127.0.0.1:8000
echo =====================================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please run: python -m venv .venv ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

echo Initializing database checks...
python -c "from src.db.init_db import initialize_database, seed_sample_data; initialize_database(); seed_sample_data()"

echo.
echo Launching Starlette server on http://127.0.0.1:8000 ...
echo Press Ctrl+C to stop the server.
echo.

python -m src.web.app

pause

