"""
Read-only database MCP server template.

Exposes a database for Claude to query. Read-only by design — no INSERT/UPDATE/DELETE.
Works with Postgres, MySQL, SQLite via SQLAlchemy.

Setup:
    uv add "fastmcp>=3.0" sqlalchemy psycopg2-binary  # postgres
    # or: uv add "fastmcp>=3.0" sqlalchemy             # sqlite

Set DATABASE_URL env var:
    postgres://user:pass@host:5432/dbname
    sqlite:///path/to/db.sqlite

Run:
    uv run server.py
"""

import os
import re
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field
from sqlalchemy import create_engine, text, inspect

mcp = FastMCP("db-readonly")

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./local.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Safety: reject anything that looks like a write
WRITE_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE|REPLACE|MERGE)\b",
    re.IGNORECASE,
)


@mcp.tool()
def list_tables() -> list[str]:
    """List all tables in the database. Use this first to discover schema."""
    inspector = inspect(engine)
    return inspector.get_table_names()


@mcp.tool()
def describe_table(
    table_name: Annotated[str, Field(description="Table to describe")],
) -> dict:
    """Get column names, types, and primary keys for a table.

    Use this before writing queries to understand the schema.
    """
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        raise ValueError(f"Table '{table_name}' not found. Use list_tables to see available tables.")

    columns = [
        {"name": c["name"], "type": str(c["type"]), "nullable": c["nullable"]}
        for c in inspector.get_columns(table_name)
    ]
    pks = inspector.get_pk_constraint(table_name).get("constrained_columns", [])
    return {"table": table_name, "columns": columns, "primary_keys": pks}


@mcp.tool()
def query(
    sql: Annotated[str, Field(description="A SELECT statement. Writes are rejected.")],
    limit: Annotated[int, Field(ge=1, le=1000, default=100, description="Max rows to return")] = 100,
) -> dict:
    """Run a read-only SQL query and return results.

    Only SELECT and WITH (CTE) statements are allowed. Any write keyword is rejected.
    Use list_tables and describe_table first to understand the schema.

    Returns: {columns: [...], rows: [[...]], row_count: N}
    """
    sql_stripped = sql.strip().rstrip(";")

    # Reject writes
    if WRITE_PATTERNS.search(sql_stripped):
        raise ValueError(
            "Write operations are not allowed. This server is read-only. "
            "Use only SELECT or WITH statements."
        )

    # Must start with SELECT or WITH
    first_word = sql_stripped.split(None, 1)[0].upper() if sql_stripped else ""
    if first_word not in ("SELECT", "WITH"):
        raise ValueError(f"Query must start with SELECT or WITH, got '{first_word}'.")

    # Add LIMIT if not present (best-effort, not bulletproof)
    if "LIMIT" not in sql_stripped.upper():
        sql_stripped = f"{sql_stripped} LIMIT {limit}"

    with engine.connect() as conn:
        result = conn.execute(text(sql_stripped))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]

    return {"columns": columns, "rows": rows, "row_count": len(rows)}


if __name__ == "__main__":
    mcp.run()
