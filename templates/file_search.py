"""
File search MCP server template.

Lets Claude search and read files in a designated directory. Useful for code repos,
notes, document collections.

Setup:
    uv add "fastmcp>=3.0"

Set ROOT_DIR env var to the directory you want exposed:
    ROOT_DIR=/Users/me/notes uv run server.py
"""

import os
import sys
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("file-search")

ROOT_DIR = Path(os.environ.get("ROOT_DIR", ".")).resolve()
if not ROOT_DIR.is_dir():
    print(f"FATAL: ROOT_DIR '{ROOT_DIR}' is not a directory", file=sys.stderr)
    sys.exit(1)

# Files we never expose
EXCLUDED_NAMES = {".git", ".env", ".venv", "node_modules", "__pycache__", ".DS_Store"}
MAX_FILE_BYTES = 1_000_000  # 1MB


def _safe_path(rel_path: str) -> Path:
    """Resolve a path under ROOT_DIR, rejecting traversal attempts."""
    target = (ROOT_DIR / rel_path).resolve()
    if ROOT_DIR not in target.parents and target != ROOT_DIR:
        raise ValueError(f"Path '{rel_path}' is outside the allowed directory.")
    return target


@mcp.tool()
def list_files(
    subdir: Annotated[str, Field(default="", description="Subdirectory relative to root, '' for root")] = "",
    pattern: Annotated[str, Field(default="*", description="Glob pattern, e.g. '*.md'")] = "*",
) -> list[str]:
    """List files in a subdirectory matching a glob pattern.

    Returns paths relative to the root. Hidden files and common build dirs are excluded.
    """
    base = _safe_path(subdir) if subdir else ROOT_DIR
    if not base.is_dir():
        raise ValueError(f"'{subdir}' is not a directory.")

    results = []
    for path in base.rglob(pattern):
        # Skip excluded
        if any(part in EXCLUDED_NAMES for part in path.parts):
            continue
        if path.is_file():
            results.append(str(path.relative_to(ROOT_DIR)))
    return sorted(results)


@mcp.tool()
def read_file(
    path: Annotated[str, Field(description="File path relative to root")],
) -> str:
    """Read the contents of a text file. Max 1MB.

    Use list_files first to discover available files. Binary files will error.
    """
    target = _safe_path(path)
    if not target.is_file():
        raise ValueError(f"File '{path}' not found.")
    if target.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"File '{path}' exceeds {MAX_FILE_BYTES} byte limit.")

    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"File '{path}' is not valid UTF-8 text. Binary files not supported.")


@mcp.tool()
def search_text(
    query: Annotated[str, Field(min_length=1, description="Text to search for (case-insensitive)")],
    pattern: Annotated[str, Field(default="*", description="Glob to filter files, e.g. '*.py'")] = "*",
    max_results: Annotated[int, Field(ge=1, le=100, default=20)] = 20,
) -> list[dict]:
    """Search for text across files. Returns matches with file, line number, and line content.

    Use this when you need to find specific content but don't know which file.
    Case-insensitive plain-text search (not regex).
    """
    q = query.lower()
    matches = []

    for path in ROOT_DIR.rglob(pattern):
        if any(part in EXCLUDED_NAMES for part in path.parts):
            continue
        if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                for lineno, line in enumerate(f, start=1):
                    if q in line.lower():
                        matches.append({
                            "file": str(path.relative_to(ROOT_DIR)),
                            "line": lineno,
                            "content": line.rstrip(),
                        })
                        if len(matches) >= max_results:
                            return matches
        except (UnicodeDecodeError, OSError):
            continue  # skip binaries / unreadable

    return matches


if __name__ == "__main__":
    mcp.run()
