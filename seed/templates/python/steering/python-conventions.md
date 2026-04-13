# Python Conventions

## Language Version
- Target Python 3.10+ (use `from __future__ import annotations` for type hints)

## Code Style
- Follow PEP 8. Use `ruff` for linting and formatting if configured
- Use type hints for all public function signatures
- Prefer `pathlib.Path` over `os.path`
- Use `dataclasses` or `pydantic` for structured data, not raw dicts

## Project Structure
- Use `src/` layout or flat package layout — follow what the project already uses
- Keep `__init__.py` files minimal — avoid re-exporting everything
- One class per file for large classes; group related small functions in a module

## Testing
- Use `pytest` for testing
- Place tests in `tests/` mirroring the package structure
- Use fixtures for shared setup; prefer factory functions over complex fixture chains
- Name test files `test_<module>.py`, test functions `test_<behavior>`

## Dependencies
- Use `pyproject.toml` for project metadata and dependencies
- Use `uv` for dependency management when available
- Pin direct dependencies; let the lock file handle transitive ones

## Error Handling
- Use specific exceptions, not bare `except:` or `except Exception:`
- Define custom exception classes in a `exceptions.py` module for domain errors
- Let unexpected errors propagate — don't catch and swallow

## Common Patterns
- Use context managers (`with`) for resource management
- Prefer `enumerate()` over manual index tracking
- Use `collections.defaultdict` and `itertools` when they simplify code
- For CLI tools, use `click` or `argparse` — not `sys.argv` parsing
