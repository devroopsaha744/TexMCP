#!/usr/bin/env python3
"""Test the MCP LaTeX server using direct MCP client."""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import json

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


class MCPServerTester:
    """Test MCP server functionality using direct MCP client."""

    def __init__(self, server_url: str = "http://127.0.0.1:8000/mcp"):
        self.server_url = server_url
        self.session_group = None
        self.session = None

    async def connect(self):
        """Connect to the MCP server."""
        try:
            self.session_group = ClientSessionGroup()
            async with self.session_group as group:
                self.session_group = group
                server_params = StreamableHttpParameters(url=self.server_url)
                self.session = await group.connect_to_server(server_params)
                # Initialize the session
                init_result = await self.session.initialize()
                print(f"✅ Connected to MCP server: {init_result.protocolVersion}")
                return True
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            return False

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
        else:
            self.model = "gpt-4o-mini"

    async def test_list_tools(self) -> Dict[str, Any]:
        """Test listing available MCP tools."""
        print("🔧 Testing tool listing...")

        try:
            # Call list_templates tool to test connectivity
            result = await self.call_tool("list_templates")
            if "error" in result:
                print(f"❌ Tool listing failed: {result['error']}")
                return result
            else:
                templates = result.get("structuredContent", {}).get("result", [])
                print(f"✅ Found {len(templates)} templates: {templates}")
                return result

        except Exception as e:
            print(f"❌ Tool listing failed: {e}")
            return {"error": str(e)}

    async def test_render_latex(self, tex_content: str = None) -> Dict[str, Any]:
        """Test LaTeX rendering functionality."""
        if tex_content is None:
            tex_content = r"\documentclass{article}\begin{document}Hello \LaTeX!\end{document}"

        print(f"📄 Testing LaTeX rendering with content: {tex_content[:50]}...")

        try:
            result = await self.call_tool("render_latex_document", tex=tex_content, jobname="test_render")
            if "error" in result:
                print(f"❌ LaTeX rendering failed: {result['error']}")
                return result
            else:
                print("✅ LaTeX rendered successfully")
                return result

        except Exception as e:
            print(f"❌ LaTeX rendering failed: {e}")
            return {"error": str(e)}

    async def test_template_rendering(self) -> Dict[str, Any]:
        """Test template-based rendering."""
        print("📋 Testing template rendering...")

        try:
            context = {"title": "Test Document", "body": "This is a test document created using templates."}
            result = await self.call_tool("render_template_document",
                                        template_name="default.tex.j2",
                                        context=context,
                                        jobname="test_template")
            if "error" in result:
                print(f"❌ Template rendering failed: {result['error']}")
                return result
            else:
                print("✅ Template rendered successfully")
                return result

        except Exception as e:
            print(f"❌ Template rendering failed: {e}")
            return {"error": str(e)}

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all MCP server tests."""
        print("🚀 Starting MCP Server Tests")
        print(f"📡 Server URL: {self.server_url}")
        print("-" * 50)

        # Connect to server first
        if not await self.connect():
            return {"error": "Failed to connect to MCP server"}

        results = {
            "list_tools": await self.test_list_tools(),
            "render_latex": await self.test_render_latex(),
            "template_rendering": await self.test_template_rendering(),
        }

        print("-" * 50)
        print("📊 Test Results Summary:")

        success_count = 0
        for test_name, result in results.items():
            if "error" not in result:
                print(f"✅ {test_name}: PASSED")
                success_count += 1
            else:
                print(f"❌ {test_name}: FAILED - {result['error']}")

        print(f"\n🎯 Overall: {success_count}/{len(results)} tests passed")
        return results


async def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test MCP LaTeX Server")
    parser.add_argument(
        "--server-url",
        default="http://127.0.0.1:8000/mcp",
        help="MCP server URL (default: http://127.0.0.1:8000/mcp)"
    )
    parser.add_argument(
        "--test",
        choices=["all", "tools", "latex", "template"],
        default="all",
        help="Specific test to run"
    )
    parser.add_argument(
        "--tex",
        help="Custom LaTeX content for testing"
    )

    args = parser.parse_args()

    tester = MCPServerTester(args.server_url)

    if args.test == "all":
        results = await tester.run_all_tests()
    elif args.test == "tools":
        if not await tester.connect():
            results = {"error": "Failed to connect"}
        else:
            results = {"list_tools": await tester.test_list_tools()}
    elif args.test == "latex":
        if not await tester.connect():
            results = {"error": "Failed to connect"}
        else:
            results = {"render_latex": await tester.test_render_latex(args.tex)}
    elif args.test == "template":
        if not await tester.connect():
            results = {"error": "Failed to connect"}
        else:
            results = {"template_rendering": await tester.test_template_rendering()}

    # Save results to file
    output_file = project_root / "test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    main()