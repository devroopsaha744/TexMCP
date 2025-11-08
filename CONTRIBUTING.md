# Contributing

Thanks for your interest in contributing to tex-mcp. We welcome bug reports, feature requests and
pull requests. Below are a few guidelines to make collaboration smooth.

1) Reporting issues
- Use the issue templates in `.github/ISSUE_TEMPLATE/` when opening new issues.
- Include a short description, steps to reproduce, expected vs actual behavior, and any logs or traceback.

2) Working on a fix or feature
- Fork the repository and create a feature branch named `feat/<short-name>` or `fix/<issue-number>`.
- Keep changes focused and small.
- Add tests for new behavior where applicable.

3) Run tests locally

```powershell
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

4) Style
- Use clear commit messages. Prefer `feat:`, `fix:`, `docs:`, `chore:` prefixes.
- Keep code readable and add comments where non-obvious.

5) Pull request checklist
- [ ] Branch is up to date with `main`
- [ ] Tests pass locally
- [ ] Added/updated documentation if needed
- [ ] Provide a clear PR description linking any issues

6) Code of Conduct

Be respectful and follow the `CODE_OF_CONDUCT.md`.
