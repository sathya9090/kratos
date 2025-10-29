## Purpose

This repository is a minimal Python example containing a single script: `e.py`.
These instructions help an AI coding agent understand the repo layout, how to run and modify the code, and project-specific conventions so it can be productive immediately.

## Quick facts
- Language: Python
- Entry file: `e.py`
- Branch: `main` (current)
- No tests, build files, or dependency manifest detected

## How to run (Windows PowerShell)

Run the script directly with the repository root as current directory:

```powershell
python .\e.py
```

Expected output (current):

```
300
hello kratos
hi vinoth
```

## Big-picture / architecture notes

- This repo currently contains a single procedural script. There are no services, modules, or packages to navigate.
- The "why" is not encoded in repo files; treat this as a tiny demo or exercise script until more files are added.

## Project-specific conventions & patterns
- Variables are defined at top-level in `e.py` and printed directly. Example:

```python
a = 100
b = 200
c = a + b
print(c)
```

- No virtualenv/venv or requirements file: assume code uses the system Python interpreter.

## Developer workflows relevant to automation
- Run the script locally to validate changes (see "How to run").
- There are no automated tests or linters to invoke. When modifying behavior, include a short smoke test in the PR description demonstrating output.

## Integration points and external dependencies
- None detected. No external services, APIs, or packages referenced in repo files.

## Guidance for the AI agent when editing this repo
- Keep diffs minimal and self-contained; the repo is tiny.
- When adding new files, also add a one-line `README.md` at the repo root explaining purpose and a short `python` run example.
- If introducing dependencies, add `requirements.txt` and a short `README.md` with run instructions.
- For any behavioral change, show the before/after output for `python e.py` in the PR description.

## Files to inspect when asked about this repo
- `e.py` — the only source file. Any change to behavior will be visible here.

## When to ask the human
- If the requested change implies expanding the project (tests, packaging, services), ask whether to:
  - keep the repo minimal, or
  - scaffold a package layout, add tests, and include a `requirements.txt`.

If anything in this file is unclear or you want the instructions to emphasize other workflows, tell me what to expand and I will iterate.
