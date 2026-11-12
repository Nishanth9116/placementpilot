@echo off
title PlacementPilot - MCP Server (STDIO)
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" goto no_venv

call .venv\Scripts\activate.bat
goto run_server

:no_venv
echo [ERROR] Virtual environment (.venv) not found.
pause
exit /b 1

:run_server
python -m src.mcp_server.server
