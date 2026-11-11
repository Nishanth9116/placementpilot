@echo off
title PlacementPilot - MCP Server (STDIO)
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment (.venv) not found.
    pause
    exit /b 1
)

python -m src.mcp_server.server

