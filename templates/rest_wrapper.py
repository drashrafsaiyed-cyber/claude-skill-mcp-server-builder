"""
REST API wrapper MCP server template.

Wraps an external REST API as MCP tools. Replace TODOs with your API details.

Setup:
    uv init my-server && cd my-server
    uv add "fastmcp>=3.0" httpx

Run:
    uv run server.py                              # stdio (Claude Desktop)
    uv run server.py --http                       # HTTP for remote use

Test:
    npx @modelcontextprotocol/inspector uv run server.py
"""

import os
import sys
from typing import Annotated

import httpx
from fastmcp import FastMCP
from pydantic import Field

# TODO: rename your server
mcp = FastMCP("rest-wrapper")

# TODO: set your base URL and auth
BASE_URL = os.environ.get("API_BASE_URL", "https://api.example.com")
API_KEY = os.environ.get("API_KEY")

if not API_KEY:
    print("WARNING: API_KEY env var not set", file=sys.stderr)


def _client() -> httpx.Client:
    """Build an HTTP client with auth headers."""
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {API_KEY}"} if API_KEY else {},
        timeout=30.0,
    )


# TODO: replace with your actual tools

@mcp.tool()
def list_items(
    limit: Annotated[int, Field(ge=1, le=100, default=20, description="Max items to return")] = 20,
    status: Annotated[str | None, Field(default=None, description="Filter by status (active|archived)")] = None,
) -> dict:
    """List items from the API. Returns a paginated list with `items` and `next_cursor`.

    Use this to browse available items before fetching details on a specific one.
    """
    params: dict = {"limit": limit}
    if status:
        params["status"] = status

    with _client() as client:
        resp = client.get("/items", params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def get_item(
    item_id: Annotated[str, Field(description="The item's unique ID")],
) -> dict:
    """Fetch full details for a single item by ID.

    Returns the complete item record including metadata, status, and related entities.
    Use list_items first if you don't know the ID.
    """
    with _client() as client:
        resp = client.get(f"/items/{item_id}")
        if resp.status_code == 404:
            raise ValueError(f"Item '{item_id}' not found. Use list_items to see available IDs.")
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def create_item(
    name: Annotated[str, Field(min_length=1, max_length=200, description="Item display name")],
    description: Annotated[str | None, Field(default=None, description="Optional details")] = None,
) -> dict:
    """Create a new item. This is a destructive action and cannot be undone.

    Returns the created item including its assigned ID.
    """
    payload = {"name": name}
    if description:
        payload["description"] = description

    with _client() as client:
        resp = client.post("/items", json=payload)
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run(
            transport="http",
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", 8000)),
        )
    else:
        mcp.run()  # stdio
