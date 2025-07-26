# Development Guidelines

This document contains critical information about working with this codebase. Follow these guidelines precisely.

## Core Development Rules

1. Package Management

   - ONLY use uv, NEVER pip
   - Installation: `uv add --group <function-name> package`
   - Running tools: `uv run tool`
   - Dependencies are organized by function groups in pyproject.toml:
     - gen-text, gen-img, select-img, edit-img, pub-img
   - FORBIDDEN: `uv pip install`, `@latest` syntax

2. Code Quality

   - Python 3.13 required
   - Type hints required for all code
   - Use Pydantic models for data validation
   - Functions must be focused and small
   - Follow existing patterns exactly
   - Line length: 88 characters maximum (ruff standard)

- For commits fixing bugs or adding features based on user reports add:

  ```bash
  git commit --trailer "Reported-by:<name>"
  ```

  Where `<name>` is the name of the user.

- For commits related to a Github issue, add

  ```bash
  git commit --trailer "Github-Issue:#<number>"
  ```

- NEVER ever mention a `co-authored-by` or similar aspects. In particular, never
  mention the tool used to create the commit message or PR.

## Pull Requests

- Create a detailed message of what changed. Focus on the high level description of
  the problem it tries to solve, and how it is solved. Don't go into the specifics of the
  code unless it adds clarity.

- Always add `jerome3o-anthropic` and `jspahrsummers` as reviewer.

- NEVER ever mention a `co-authored-by` or similar aspects. In particular, never
  mention the tool used to create the commit message or PR.

## Development Tools

### Available Commands (Makefile)

- `make format` - Run black and ruff formatting
- `make black` - Format code with black
- `make ruff` - Lint and fix code with ruff
- `make mypy` - Type checking with mypy
- `make test` - Run pytest tests

### Code Formatting

1. Black

   - Format: `uv run black src/*`
   - Enforces consistent code style

2. Ruff

   - Check: `uv run ruff check src/* --no-cache --fix`
   - Critical issues:
     - Line length (88 chars)
     - Import sorting (I001)
     - Unused imports
   - Line wrapping:
     - Strings: use parentheses
     - Function calls: multi-line with proper indent
     - Imports: split into multiple lines

3. Type Checking

   - Tool: `uv run mypy .`
   - Requirements:
     - Explicit None checks for Optional
     - Type narrowing for strings
     - All functions must have type hints

## Error Resolution

1. CI Failures

   - Fix order:
     1. Formatting
     2. Type errors
     3. Linting
   - Type errors:
     - Get full line context
     - Check Optional types
     - Add type narrowing
     - Verify function signatures

2. Common Issues

   - Line length:
     - Break strings with parentheses
     - Multi-line function calls
     - Split imports
   - Types:
     - Add None checks
     - Narrow string types
     - Match existing patterns

3. Best Practices
   - Check git status before commits
   - Run formatters before type checks
   - Keep changes minimal
   - Follow existing patterns

## Exception Handling

- **Always use `logger.exception()` instead of `logger.error()` when catching exceptions**
  - Don't include the exception in the message: `logger.exception("Failed")` not `logger.exception(f"Failed: {e}")`
- **Catch specific exceptions** where possible:
  - File ops: `except (OSError, PermissionError):`
  - JSON: `except json.JSONDecodeError:`
  - Network: `except (ConnectionError, TimeoutError):`
- **Only catch `Exception` for**:
  - Top-level handlers that must not crash
  - Cleanup blocks (log at debug level)
