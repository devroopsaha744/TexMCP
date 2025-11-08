"""FastMCP server exposing tools to render LaTeX documents to PDF."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import anyio
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from fastmcp.utilities.types import File
from jinja2 import TemplateNotFound

from .latex_renderer import LatexCompileError, LatexRenderer, ensure_directory
from .service import LatexService
from .templating import LatexTemplateEngine


BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = ensure_directory(BASE_DIR.parent / "artifacts")
TEMPLATE_DIR = ensure_directory(BASE_DIR / "templates")


mcp = FastMCP(
    name="FastMCP-LaTeX-Server",
    instructions=(
        "Generate LaTeX sources and render them to PDF. "
        "Use render_latex_document for raw LaTeX, or render_template_document "
        "to populate a template before rendering."
    ),
)


renderer = LatexRenderer(work_dir=ARTIFACTS_DIR)
template_engine = LatexTemplateEngine(template_dir=TEMPLATE_DIR)
service = LatexService(renderer=renderer, template_engine=template_engine)


def _build_structured_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "jobname": result["jobname"],
        "tex_path": str(result["tex_path"]),
        "pdf_path": str(result["pdf_path"]) if result["pdf_path"] else None,
    }
    return payload


@mcp.tool(
    name="render_latex_document",
    description="Write LaTeX to disk and optionally compile it to PDF.",
    tags={"latex", "render"},
    annotations={"title": "Render LaTeX"},
)
async def render_latex_document(
    tex: str,
    jobname: str | None = None,
    compile_pdf: bool = True,
    runs: int = 1,
    ctx: Context | None = None,
) -> ToolResult:
    """Persist LaTeX source and optionally compile to PDF."""

    async def _render() -> dict[str, Any]:
        return await anyio.to_thread.run_sync(
            service.render_tex,
            tex,
            jobname,
            compile_pdf,
            runs,
        )

    try:
        result = await _render()
    except FileNotFoundError as err:
        if not compile_pdf:
            raise ToolError(str(err)) from err

        if ctx:
            await ctx.warning("pdflatex not found; returning .tex artifact only.")
        result = await anyio.to_thread.run_sync(
            service.render_tex,
            tex,
            jobname,
            False,
            runs,
        )
        summary = "LaTeX saved, but pdflatex was unavailable."
    except LatexCompileError as err:
        raise ToolError(f"pdflatex compilation failed: {err}") from err
    else:
        summary = "LaTeX rendered successfully."

    files: list[Any] = [File(path=result["tex_path"])]
    if result["pdf_path"]:
        files.append(File(path=result["pdf_path"]))

    return ToolResult(
        content=[summary, *files],
        structured_content=_build_structured_payload(result),
    )


@mcp.tool(
    name="render_template_document",
    description="Render a stored template with context and optionally compile to PDF.",
    tags={"latex", "template"},
    annotations={"title": "Render Template"},
)
async def render_template_document(
    template_name: str,
    context: Mapping[str, Any],
    jobname: str | None = None,
    compile_pdf: bool = True,
    runs: int = 1,
    ctx: Context | None = None,
) -> ToolResult:
    """Render a LaTeX template using provided context and optionally compile it."""

    try:
        result = await anyio.to_thread.run_sync(
            service.render_template,
            template_name,
            context,
            jobname,
            compile_pdf,
            runs,
        )
    except TemplateNotFound as err:
        raise ToolError(f"Template '{template_name}' not found") from err
    except FileNotFoundError as err:
        if not compile_pdf:
            raise ToolError(str(err)) from err
        if ctx:
            await ctx.warning("pdflatex not found; returning LaTeX only.")
        result = await anyio.to_thread.run_sync(
            service.render_template,
            template_name,
            context,
            jobname,
            False,
            runs,
        )
        summary = "Template rendered but pdflatex was unavailable."
    except LatexCompileError as err:
        raise ToolError(f"pdflatex compilation failed: {err}") from err
    else:
        summary = "Template rendered successfully."

    files: list[Any] = [File(path=result["tex_path"])]
    if result["pdf_path"]:
        files.append(File(path=result["pdf_path"]))

    return ToolResult(
        content=[summary, *files],
        structured_content=_build_structured_payload(result),
    )


@mcp.tool(
    name="list_templates",
    description="List available LaTeX templates.",
    tags={"latex", "template"},
    annotations={"title": "List Templates", "readOnlyHint": True},
)
def list_templates() -> list[str]:
    """Return the list of templates that can be rendered."""

    return sorted(
        str(path.relative_to(TEMPLATE_DIR))
        for path in TEMPLATE_DIR.glob("*.tex.j2")
    )


__all__ = ["mcp"]


if __name__ == "__main__":
    mcp.run()
