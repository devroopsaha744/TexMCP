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
import os

from mcp_server.server import mcp


def main() -> None:
    # Allow choosing transport mode via the MCP_TRANSPORT env var.
    # - If MCP_TRANSPORT=stdio (default for Claude Desktop integrations), the
    #   server will speak MCP over stdin/stdout pipes.
    # - If MCP_TRANSPORT=http the server will host an HTTP endpoint on 0.0.0.0:8000
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        # bind to all interfaces inside containers
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
