@echo off
title PlacementPilot - Web Dashboard
echo =====================================================================
echo  PlacementPilot Web Dashboard
echo  Local AI Placement Platform - http://127.0.0.1:8000
echo =====================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" goto no_venv

call .venv\Scripts\activate.bat
goto start_app

:no_venv
echo [ERROR] Virtual environment (.venv) not found.
echo Please run: python -m venv .venv ^&^& pip install -r requirements.txt
pause
exit /b 1

:start_app
echo Initializing database checks...
python -c "from src.db.init_db import initialize_database, seed_sample_data; initialize_database(); seed_sample_data()"

echo.
echo Launching Uvicorn server on http://127.0.0.1:8000 ...
echo Application Entrypoint: src.web.app:app
echo Press Ctrl+C to stop the server.
echo.

python -m uvicorn src.web.app:app --host 127.0.0.1 --port 8000

pause
