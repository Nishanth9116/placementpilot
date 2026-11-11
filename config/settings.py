"""Application configuration and path settings for PlacementPilot."""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    """Settings for local-first execution without external cloud dependencies."""

    PROJECT_NAME: str = "PlacementPilot"
    VERSION: str = "0.1.0"

    # SQLite Database Path
    DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "placementpilot.db"))).resolve()

    # MCP Server settings
    MCP_SERVER_NAME: str = os.getenv("MCP_SERVER_NAME", "PlacementPilot")
    MCP_SERVER_VERSION: str = os.getenv("MCP_SERVER_VERSION", "0.1.0")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()

