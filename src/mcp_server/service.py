"""High-level orchestration for LaTeX generation and rendering."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .latex_renderer import LatexRenderer, sanitize_jobname
from .templating import LatexTemplateEngine


@dataclass(slots=True)
class LatexService:
    """Glue layer between templating and the LaTeX renderer."""

    renderer: LatexRenderer
    template_engine: LatexTemplateEngine

    def render_tex(
        self,
        tex: str,
        jobname: str | None = None,
        compile_pdf: bool = True,
        runs: int = 1,
    ) -> dict[str, Path | str]:
        job = sanitize_jobname(jobname or self._default_jobname())
        tex_path = self.renderer.write_tex(tex=tex, name=job)

        pdf_path: Path | None = None
        if compile_pdf:
            pdf_path = self.renderer.compile_pdf(tex_path, runs=runs)

        return {
            "jobname": job,
            "tex_path": tex_path,
            "pdf_path": pdf_path,
        }

    def render_template(
        self,
        template_name: str,
        context: Mapping[str, Any],
        jobname: str | None = None,
        compile_pdf: bool = True,
        runs: int = 1,
    ) -> dict[str, Path | str]:
        tex = self.template_engine.render(template_name, context)
        return self.render_tex(tex, jobname=jobname, compile_pdf=compile_pdf, runs=runs)

    @staticmethod
    def _default_jobname() -> str:
        return f"doc_{secrets.token_hex(4)}"
