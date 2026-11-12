@echo off
title PlacementPilot - Test Suite Runner
echo =====================================================================
echo  Running PlacementPilot Automated Test Suite
echo =====================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" goto no_venv

call .venv\Scripts\activate.bat
goto run_tests

:no_venv
echo [ERROR] Virtual environment (.venv) not found.
pause
exit /b 1

:run_tests
pytest -v

echo.
echo =====================================================================
echo  Test run complete.
echo =====================================================================
pause
