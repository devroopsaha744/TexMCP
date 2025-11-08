# FastMCP LaTeX Server (tex-mcp)

A small FastMCP-based Microservice that renders LaTeX to PDF. The server exposes MCP tools
to render raw LaTeX or templates and produces artifacts (a .tex file and  .pdf)
under `src/artifacts/`.

This repository is prepared to run locally and to be loaded by Claude Desktop (via the
Model Context Protocol). The default entrypoint is `run_server.py`.

## Demo
![Demo screenshot](assets/demo-1.png)
![Demo screenshot](assets/demo-2.png)
![Demo screenshot](assets/demo-3.png)
---

## Quick features
- Render raw LaTeX to `.tex` and (optionally) `.pdf` using pdflatex
- Render Jinja2 templates and compile to PDF
- Designed to run as an MCP server for Claude Desktop and other MCP-capable clients

Tools exposed by this MCP server
- Total tools: 5
  - render_latex_document — write LaTeX and optionally compile to PDF
  - render_template_document — render a Jinja2 template and optionally compile
  - list_templates — list available templates
  - list_artifacts — list files produced in `src/artifacts/`
  - get_template — return the raw contents of a template file so clients can inspect it before rendering
---

## Getting started (local development)

Prerequisites
- Python 3.10+ (the project uses modern pydantic/fastapi stack)
- LaTeX toolchain (pdflatex) for PDF compilation (optional; if missing, server returns .tex only)

1) Create a project virtualenv and install deps

Clone from GitHub

If you want to work from the canonical repository on GitHub, clone it first:

```powershell
git clone https://github.com/devroopsaha744/TexMCP.git
cd TexMCP
```

After cloning you can follow the venv creation and install steps below.


```powershell
python -m venv .venv
. .\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2) Run the server directly (stdio mode - used by Claude Desktop)

```powershell
. .\\.venv\\Scripts\\Activate.ps1
python .\\run_server.py
# or run the venv python explicitly if you don't activate
.# .venv\\Scripts\\python.exe run_server.py
```

If run in stdio mode the server will speak MCP over stdin/stdout (this is what Claude Desktop
expects when it spawns the process). If you prefer HTTP, edit `run_server.py` and switch the
transport to `http` (see commented code) and run via `uv run` or `uvicorn`.

3) Artifacts

Rendered outputs are placed in `src/artifacts/`. For each job you should see a `.tex` file and
— if `pdflatex` is available — a matching `.pdf`.

Templates
 - Several example templates live in `src/mcp_server/templates/`. There are 15 templates included (for example `sample_invoice.tex.j2`, `sample_letter.tex.j2`, `sample_resume.tex.j2`). Use `list_templates` to get the full list programmatically. The templates are deliberately simple and ready to customize — add your own `.tex.j2` files to that folder to expand the catalog.

Included templates (in `src/mcp_server/templates/`)

- `default.tex.j2` (base example template)
- `sample_invoice.tex.j2`
- `sample_invoice2.tex.j2`
- `sample_letter.tex.j2`
- `sample_report.tex.j2`
- `sample_resume.tex.j2`
- `sample_presentation.tex.j2`
- `sample_certificate.tex.j2`
- `sample_coverletter.tex.j2`
- `sample_poster.tex.j2`
- `sample_thesis.tex.j2`
- `sample_receipt.tex.j2`
- `sample_recipe.tex.j2`
- `sample_poem.tex.j2`
- `sample_cv.tex.j2`

---

## Integration with Claude Desktop (quick)

Recommended: use the `fastmcp` CLI installer which will set things up to run from the project directory and use the project venv.

From your project root (with the venv already created and deps installed):

```powershell
fastmcp install claude-desktop run_server.py --project C:\\Users\\DEVROOP\\Desktop\\tex-mcp
```

This ensures `uv` runs inside the project directory and uses the project's environment. After the installer runs, fully quit and restart Claude Desktop.

Manual Claude Desktop config
If you edit Claude's config yourself (Windows: `%APPDATA%\\Claude\\claude_desktop_config.json`), add a single server entry that points to the project Python executable. Example (replace paths if needed):

```json
{
  "mcpServers": {
    "FastMCP-LaTeX-Server": {
      "command": "C:\\\\Users\\\\DEVROOP\\\\Desktop\\\\tex-mcp\\\\venv\\\\Scripts\\\\python.exe",
      "args": [
        "C:\\\\Users\\\\DEVROOP\\\\Desktop\\\\tex-mcp\\\\run_server.py"
      ],
      "cwd": "C:\\\\Users\\\\DEVROOP\\\\Desktop\\\\tex-mcp",
      "transport": "stdio"
    }
  }
}
```

Notes
- Do NOT point Claude at the virtualenv `activate` script — it is a shell helper and not an executable. Point Claude to the `python.exe` inside the venv (or to `uv.exe` inside the venv if you installed `uv`).
- After any config changes, fully restart Claude Desktop.

---

## Docker

This project includes a Dockerfile so you can run the MCP server in a container.

Build (no LaTeX):

```bash
docker build -t fastmcp-latex:latest .
```

Build with LaTeX (larger image):

```bash
docker build --build-arg INSTALL_TEX=1 -t fastmcp-latex:with-tex .
```

Run (HTTP mode exposed on port 8000):

```bash
docker run -p 8000:8000 --rm --name fastmcp-latex fastmcp-latex:latest
```

Notes
- The container sets `MCP_TRANSPORT=http` by default. Inside the container the server binds to `0.0.0.0:8000`.
- If you want to run the server in `stdio` mode in a container you can override the env var:

```bash
docker run -e MCP_TRANSPORT=stdio ...
```

Artifact persistence
- To persist rendered artifacts on the host, bind mount the `src/artifacts` directory:

```bash
docker run -p 8000:8000 -v $(pwd)/src/artifacts:/app/src/artifacts fastmcp-latex:latest
```

---

## Using the MCP server with the OpenAI Responses API (overview)

You can use this MCP server as a rendering tool inside a custom AI agent or orchestration built on the OpenAI Responses API. There are two common patterns:

1) Agent calls this MCP server as an external tool

- Run this server in HTTP mode (e.g. in Docker as above) so it is reachable from your agent process.
- When your agent decides it needs to render LaTeX, call the MCP server's HTTP endpoint and pass the rendering parameters (template name or raw LaTeX source, jobname, compile flag).

Simple example (HTTP JSON-RPC style; exact MCP client libraries may vary):

```bash
curl -X POST http://localhost:8000/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"call","params":{"tool":"render_latex_document","args":{"tex":"\\\documentclass{article}\\n\\begin{document}Hello\\end{document}","compile_pdf":true}},"id":1}'
```

If your agent uses the OpenAI Responses API to produce content, it can detect when a rendered PDF is useful and then call this MCP server as a tool to produce the artifact. Once the server finishes the job you can attach the resulting PDF (from `src/artifacts`) to the agent's response or further process it.

2) Embed the MCP client into an agent workflow

- Use a Model Context Protocol / FastMCP client library in your agent code to call tools programmatically. For example, in Python you can use the `mcp` or `fastmcp` client (see library docs) to connect to `http://localhost:8000/mcp` and call `render_latex_document` with arguments.

Security notes
- If you expose the HTTP endpoint beyond localhost, secure it (TLS, firewall, or authentication) — rendering arbitrary LaTeX can pose risks (shell commands in templates, large resource use).

---


## Running tests

Run the unit tests with pytest:

```powershell
. .\\.venv\\Scripts\\Activate.ps1
pytest -q
```

---

## Contributing

Thanks for wanting to contribute! See `CONTRIBUTING.md` for the development workflow, commit style, and how to open issues and pull requests.

---

## License

This project is released under the MIT License — see `LICENSE`.

If you need a different license, update the `LICENSE` file as desired.
# tex-mcp — Fast MCP LaTeX PDF server

This project is a minimal, modular MCP server scaffold that generates and renders LaTeX documents to PDF. It uses the FastMCP SDK and exposes tools that clients can call over the Model Context Protocol.

Key features
- Modular LaTeX renderer with safe write/compile helpers
- Template-based document generation using Jinja2 templates

Requirements
- Python 3.9+
- pdflatex (TeX Live or MikTeX) on PATH for PDF compilation

Quick start
1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

2. Run the MCP server over HTTP:

```powershell
python run_server.py
```

   The server exposes three tools via the Model Context Protocol:
   - `render_latex_document`: store raw LaTeX and optionally compile a PDF
   - `render_template_document`: render a Jinja2 template with structured context
   - `list_templates`: discover available templates

   Clients can also call `python -m mcp_server.server` to start the default STDIO transport.

3. Test the server using the professional CLI tool:

```powershell
# Set your API key
$env:OPENAI_API_KEY = "your-openai-api-key"

# Run all tests
python latex_mcp_cli.py --test

# Interactive mode
python latex_mcp_cli.py --start-server --interactive

# Direct tool calls
python latex_mcp_cli.py --tool render_latex_document --tex "\documentclass{article}\begin{document}Hello World\end{document}"
python latex_mcp_cli.py --tool list_templates
```

4. Example usage with OpenAI Responses API:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4o-mini",
    tools=[{
        "type": "mcp",
        "server_label": "tex-mcp",
        "server_url": "http://127.0.0.1:8000/mcp",
        "require_approval": "never",
    }],
    input="Create a LaTeX document about mathematics and render it to PDF",
)

print(response.output_text)
```

Notes
- If `pdflatex` is not installed, PDF compilation falls back gracefully and returns the `.tex` artifact only.
- Templates live in `src/mcp_server/templates/`. Add new `.tex.j2` files to expand the catalog.

## Claude Code Integration

To use this MCP server with Claude Code, create a `.claude.json` file in your project root:

```json
{
  "mcpServers": {
    "tex-mcp": {
      "command": ".\\venv\\Scripts\\python.exe",
      "args": ["run_server.py"],
      "cwd": "."
    }
  }
}
```

This will make the LaTeX rendering tools available in Claude Code conversations.
