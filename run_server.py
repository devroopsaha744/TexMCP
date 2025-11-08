"""Entry point to run the FastMCP LaTeX server via uvicorn."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src directory to Python path
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastmcp import FastMCP

from mcp_server.server import mcp


def main() -> None:
    # Use stdio transport for desktop integrations. HTTP mode was removed to
    # keep the server behavior deterministic when launched by Claude Desktop.
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
