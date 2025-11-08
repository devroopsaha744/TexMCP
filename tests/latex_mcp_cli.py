#!/usr/bin/env python3
"""Professional CLI tool for interacting with the LaTeX MCP server."""

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import time

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not available, continue without it
    pass

# Add src to path for imports
project_root = Path(__file__).parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from mcp.client.session_group import ClientSessionGroup, StreamableHttpParameters
except ImportError:
    print("ERROR: mcp package not installed. Install with: pip install mcp")
    sys.exit(1)


class LaTeXMCPClient:
    """Professional client for interacting with LaTeX MCP server."""

    def __init__(self, server_url: str = "http://127.0.0.1:8000/mcp"):
        self.server_url = server_url
        self.session_group = None
        self.session = None
        self.server_process = None

    async def connect(self):
        """Test connection to the MCP server."""
        try:
            # Test connection by creating a session and initializing
            session_group = ClientSessionGroup()
            async with session_group as group:
                server_params = StreamableHttpParameters(url=self.server_url)
                session = await group.connect_to_server(server_params)
                init_result = await session.initialize()
                print(f"✅ Connected to MCP server: {init_result.protocolVersion}")
                return True
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            return False

    def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session_group:
            # The session_group will be cleaned up by its async context manager
            pass

    def start_server(self) -> bool:
        """Start the MCP server in background."""
        try:
            print("🚀 Starting MCP server...")
            self.server_process = subprocess.Popen(
                [sys.executable, "server_launcher.py"],
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait a bit for server to start
            time.sleep(2)

            if self.server_process.poll() is None:
                print("✅ Server started successfully")
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                print(f"❌ Server failed to start: {stderr.decode()}")
                return False

        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    def stop_server(self):
        """Stop the MCP server."""
        if self.server_process:
            print("🛑 Stopping MCP server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
                print("✅ Server stopped")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                print("⚠️  Server force-killed")

    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a specific MCP tool."""
        try:
            # Create a new session for each call
            session_group = ClientSessionGroup()
            async with session_group as group:
                server_params = StreamableHttpParameters(url=self.server_url)
                session = await group.connect_to_server(server_params)
                await session.initialize()
                # Call the tool using MCP protocol
                result = await session.call_tool(tool_name, arguments=kwargs or {})
                return result.model_dump()

        except Exception as e:
            return {"error": str(e)}

    def interactive_mode(self):
        """Enter interactive mode for chatting with the MCP server."""
        print("💬 Interactive LaTeX MCP Mode")
        print("Type 'help' for commands, 'quit' to exit")
        print("-" * 50)

        while True:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower().startswith('tool '):
                    self._handle_tool_command(user_input[5:])
                    continue

                # Regular chat with MCP tools available
                response = self.client.responses.create(
                    model=self.model,
                    tools=[{
                        "type": "mcp",
                        "server_label": "tex-mcp",
                        "server_url": self.server_url,
                        "require_approval": "never",
                    }],
                    input=user_input,
                )

                print(f"Assistant: {response.output_text}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def _show_help(self):
        """Show help information."""
        print("""
Available commands:
  help                    Show this help
  quit/exit/q            Exit interactive mode
  tool <command>         Call specific tool directly

Available tools:
  render_latex_document  Render raw LaTeX to PDF
  render_template_document  Render template with context
  list_templates         List available templates

Examples:
  tool render_latex_document tex="\\documentclass{article}\\begin{document}Hello\\end{document}"
  tool list_templates
  Create a document about mathematics
        """)

    def _handle_tool_command(self, command: str):
        """Handle direct tool calls."""
        try:
            # Parse command like "tool_name param1=value1 param2=value2"
            parts = command.split()
            tool_name = parts[0]

            kwargs = {}
            for param in parts[1:]:
                if '=' in param:
                    key, value = param.split('=', 1)
                    # Try to parse as JSON, otherwise keep as string
                    try:
                        kwargs[key] = json.loads(value)
                    except json.JSONDecodeError:
                        kwargs[key] = value

            result = self.call_tool(tool_name, **kwargs)

            if "error" in result:
                print(f"❌ Tool call failed: {result['error']}")
            else:
                print(f"✅ Tool result: {result.get('output_text', 'No output')}")

        except Exception as e:
            print(f"❌ Failed to parse tool command: {e}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LaTeX MCP Server CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --tool render_latex_document --tex "\\documentclass{article}\\begin{document}Hello\\end{document}"
  %(prog)s --tool list_templates
  %(prog)s --test                           # Run all tests
        """
    )

    parser.add_argument(
        "--server-url",
        default="http://127.0.0.1:8000/mcp",
        help="MCP server URL (default: http://127.0.0.1:8000/mcp)"
    )

    parser.add_argument(
        "--start-server",
        action="store_true",
        help="Start the MCP server in background"
    )

    parser.add_argument(
        "--stop-server",
        action="store_true",
        help="Stop the running MCP server"
    )

    parser.add_argument(
        "--tool",
        help="Call a specific tool (use with tool arguments)"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run MCP server tests"
    )

    # Tool-specific arguments
    parser.add_argument("--tex", help="LaTeX content for rendering")
    parser.add_argument("--jobname", help="Job name for output files")
    parser.add_argument("--template-name", help="Template name to use")
    parser.add_argument("--context", help="JSON context for template rendering")

    args = parser.parse_args()

    client = LaTeXMCPClient(args.server_url)

    # Handle server management
    if args.start_server:
        if not client.start_server():
            sys.exit(1)

    if args.stop_server:
        client.stop_server()
        return

    # Handle testing
    if args.test:
        # Import and run tests
        sys.path.insert(0, str(project_root))
        from test_mcp import MCPServerTester
        tester = MCPServerTester(args.server_url)
        await tester.run_all_tests()
        return

    # Connect to server for tool calls
    if args.tool:
        if not await client.connect():
            sys.exit(1)

    # Handle tool calls
    if args.tool:
        kwargs = {}
        if args.tex:
            kwargs["tex"] = args.tex
        if args.jobname:
            kwargs["jobname"] = args.jobname
        if args.template_name:
            kwargs["template_name"] = args.template_name
        if args.context:
            try:
                kwargs["context"] = json.loads(args.context)
            except json.JSONDecodeError:
                print("❌ Invalid JSON for context")
                sys.exit(1)

        result = await client.call_tool(args.tool, **kwargs)
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")

        if isinstance(result, dict) and "error" in result:
            print(f"❌ Tool call failed: {result['error']}")
            sys.exit(1)
        elif hasattr(result, 'isError') and result.isError:
            print(f"❌ Tool call failed: {result.content}")
            sys.exit(1)
        else:
            # Handle complex result objects that can't be JSON serialized
            try:
                result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
                print(f"✅ Tool result: {json.dumps(result_dict, indent=2, default=str)}")
            except (TypeError, ValueError):
                print(f"✅ Tool result: {result}")
        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())