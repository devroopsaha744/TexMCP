"""Utilities for writing LaTeX sources and compiling them to PDF."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


class LatexCompileError(RuntimeError):
    """Raised when pdflatex exits with a non-zero status."""

    def __init__(self, message: str, log: str | None = None) -> None:
        super().__init__(message)
        self.log = log


@dataclass(slots=True)
class LatexRenderer:
    """Render LaTeX documents to PDF using pdflatex."""

    work_dir: Path
    pdflatex_path: str = "pdflatex"
    tex_inputs: Sequence[Path] | None = None

    _pdflatex_available: bool = False

    def __post_init__(self) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self._pdflatex_available = shutil.which(self.pdflatex_path) is not None

    def write_tex(self, tex: str, name: str) -> Path:
        """Write raw LaTeX source to work_dir and return the file path."""

        safe_name = name.replace(" ", "_")
        tex_path = self.work_dir / f"{safe_name}.tex"
        tex_path.write_text(tex, encoding="utf-8")
        return tex_path

    def compile_pdf(self, tex_path: Path, runs: int = 1) -> Path:
        """Compile the provided .tex file to PDF and return the output path."""

        if not self._pdflatex_available:
            raise FileNotFoundError(
                f"pdflatex executable '{self.pdflatex_path}' not found on PATH"
            )

        env = None
        if self.tex_inputs:
            extra_inputs = [str(path) for path in self.tex_inputs]
            env = os.environ.copy()
            env["TEXINPUTS"] = self._join_tex_inputs(extra_inputs)

        try:
            for _ in range(max(runs, 1)):
                subprocess.run(
                    [
                        self.pdflatex_path,
                        "-halt-on-error",
                        "-interaction=nonstopmode",
                        tex_path.name,
                    ],
                    cwd=self.work_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=True,
                    text=True,
                )
        except subprocess.CalledProcessError as err:
            raise LatexCompileError(
                f"pdflatex failed for {tex_path.name}", log=err.stdout
            ) from err

        pdf_path = tex_path.with_suffix(".pdf")
        if not pdf_path.exists():
            raise LatexCompileError(f"pdflatex did not produce {pdf_path.name}")
        return pdf_path

    def render(self, tex: str, jobname: str, runs: int = 1) -> Path:
        """Write and compile LaTeX to PDF, returning the resulting path."""

        tex_path = self.write_tex(tex=tex, name=jobname)
        return self.compile_pdf(tex_path=tex_path, runs=runs)

    @staticmethod
    def _join_tex_inputs(paths: Iterable[str]) -> str:
        root = tempfile.gettempdir()
        entries = [*paths, "", root]
        return os.pathsep.join(entries)


def ensure_directory(path: Path) -> Path:
    """Ensure that a directory exists and return it."""

    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_jobname(value: str) -> str:
    """Return a filesystem-friendly jobname."""

    allowed = [c if c.isalnum() or c in ("-", "_") else "_" for c in value]
    return "".join(allowed).strip("._") or "document"
