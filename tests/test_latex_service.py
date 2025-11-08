from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mcp_server.latex_renderer import LatexRenderer, sanitize_jobname
from mcp_server.service import LatexService
from mcp_server.templating import LatexTemplateEngine


def test_sanitize_jobname_replaces_invalid_chars() -> None:
    assert sanitize_jobname("My Doc!") == "My_Doc"
    assert sanitize_jobname("..doc..") == "doc"


@pytest.mark.parametrize("compile_pdf", [False])
def test_render_template_writes_tex(tmp_path: Path, compile_pdf: bool) -> None:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "simple.tex.j2"
    template_file.write_text("\\section*{ {{ title }} }", encoding="utf-8")

    output_dir = tmp_path / "out"
    renderer = LatexRenderer(work_dir=output_dir)
    engine = LatexTemplateEngine(template_dir=template_dir)
    service = LatexService(renderer=renderer, template_engine=engine)

    result = service.render_template(
        template_name="simple.tex.j2",
        context={"title": "Example"},
        jobname="example",
        compile_pdf=compile_pdf,
    )

    tex_path = result["tex_path"]
    assert tex_path.exists(), "Expected .tex file to be written"
    content = tex_path.read_text(encoding="utf-8").strip()
    assert content == "\\section*{ Example }"
    assert result["pdf_path"] is None
