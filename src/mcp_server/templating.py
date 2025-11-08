"""Jinja2-based helpers for assembling LaTeX documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from jinja2 import Environment, FileSystemLoader, Template


@dataclass(slots=True)
class LatexTemplateEngine:
    """Render LaTeX Jinja2 templates stored on disk."""

    template_dir: Path
    _env: Environment = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self._env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: Mapping[str, Any]) -> str:
        template = self._env.get_template(template_name)
        return template.render(**context)

    def get_template(self, template_name: str) -> Template:
        return self._env.get_template(template_name)
