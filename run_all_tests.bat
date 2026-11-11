@echo off
title PlacementPilot - Test Suite Runner
echo =====================================================================
echo  Running PlacementPilot Automated Test Suite
echo =====================================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment (.venv) not found.
    pause
    exit /b 1
)

pytest -v

echo.
echo =====================================================================
echo  Test run complete.
echo =====================================================================
pause

