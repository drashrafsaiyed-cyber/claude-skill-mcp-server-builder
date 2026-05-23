---
name: mcp-server-builder
description: Build, scaffold, debug, and deploy Model Context Protocol (MCP) servers in Python (FastMCP) or TypeScript. Use this skill ANY time the user mentions building an MCP server, creating MCP tools, exposing an API as MCP, connecting Claude/Cursor/VS Code to custom data sources, "make a connector", "wrap my API for Claude", n8n MCP integration, GrowwMCP-style integrations, Telegram-bot-to-MCP conversion, or anything involving the modelcontextprotocol SDK, FastMCP, @modelcontextprotocol/sdk, stdio/SSE/Streamable HTTP transports, MCP Inspector, or claude_desktop_config.json. Also trigger when the user wants to convert an existing tool, REST API, database, scraper, or automation into something Claude Desktop or Claude Code can call as a tool. If in doubt, USE THIS SKILL — undertriggering is the bigger risk.
---

# MCP Server Builder

A skill for building production-grade Model Context Protocol (MCP) servers. Covers Python (FastMCP 3.x) and TypeScript (@modelcontextprotocol/sdk v2), local stdio and remote Streamable HTTP transports, Claude Desktop/Claude Code integration, debugging via MCP Inspector, and deployment.

## When this skill applies

Trigger this skill for any of these intents:

- "Build/create/make an MCP server"
- "Expose my [API / database / script / scraper] to Claude"
- "Add a custom tool to Claude Desktop / Claude Code / Cursor"
- "Convert this Telegram bot / FastAPI app / n8n workflow into MCP"
- "Wrap [X service] so Claude can use it"
- Any reference to `modelcontextprotocol`, `FastMCP`, `mcp.tool()`, `@modelcontextprotocol/sdk`, `claude_desktop_config.json`, MCP Inspector, stdio transport, Streamable HTTP, SSE transport

## Core decision tree

Before writing any code, settle these four questions with the user (ask in one batch if unclear):

1. **Language**: Python or TypeScript?
   - Default to **Python + FastMCP** unless the user has a Node/TS codebase or specifically wants Cloudflare Workers/Vercel deployment.
2. **Transport**: Local (stdio) or remote (Streamable HTTP)?
   - **stdio** = runs on user's machine, launched by Claude Desktop. Simplest. Default for personal tools.
   - **Streamable HTTP** = runs as a web service. Required for: multi-user, cloud deployment, n8n/remote integration, anything beyond the user's own machine.
3. **What does it wrap?** Existing API, database, script, files, scraper, or net-new logic?
4. **Auth needed?** None (local), API key (env var), or OAuth 2.1 (remote multi-tenant)?

Once you have these, scaffold the project. Don't ask for more — get to working code fast.

## Quick scaffolding

### Python (FastMCP 3.x) — preferred default

```bash
# Setup with uv (recommended) or pip
uv init my-mcp-server
cd my-mcp-server
uv add "fastmcp>=3.0"
```

Minimal server (`server.py`):

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.tool()
def fetch_user(user_id: str) -> dict:
    """Fetch a user record by ID."""
    # your logic here
    return {"id": user_id, "name": "..."}

if __name__ == "__main__":
    mcp.run()  # defaults to stdio
```

Run for stdio: `uv run server.py`
Run for HTTP: `mcp.run(transport="http", host="0.0.0.0", port=8000)`

### TypeScript (@modelcontextprotocol/sdk)

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk zod
npm install -D typescript @types/node tsx
npx tsc --init
```

Minimal server (`src/index.ts`):

```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const server = new McpServer({ name: 'my-server', version: '1.0.0' });

server.registerTool(
  'add',
  {
    description: 'Add two numbers',
    inputSchema: z.object({ a: z.number(), b: z.number() }),
  },
  async ({ a, b }) => ({
    content: [{ type: 'text', text: String(a + b) }],
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

Run: `npx tsx src/index.ts`

## Connecting to Claude Desktop / Claude Code

**Claude Desktop** — edit `claude_desktop_config.json`:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/my-mcp-server", "run", "server.py"]
    }
  }
}
```

For remote HTTP servers, use the **Settings → Connectors** page in Claude.ai (Customize → Connectors) — not the desktop config file. Add the URL like `https://your-server.com/mcp`.

**Claude Code** — use the CLI:
```bash
claude mcp add my-server -- uv --directory /abs/path run server.py
```

After config changes, **fully quit and reopen Claude Desktop** (just closing the window isn't enough on macOS).

## Debugging — always use MCP Inspector first

Before connecting to Claude, verify the server works with Inspector:

```bash
# Python
npx @modelcontextprotocol/inspector uv run server.py

# TypeScript
npx @modelcontextprotocol/inspector npx tsx src/index.ts

# Against running HTTP server
npx @modelcontextprotocol/inspector --url http://localhost:8000/mcp
```

Inspector opens a browser UI where you can list/call tools, see raw JSON-RPC, and debug schemas. **Do not skip this step** — most "it doesn't work in Claude" issues are caught here in 30 seconds.

For Claude Desktop logs:
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Windows: `%APPDATA%\Claude\logs\mcp*.log`

## Three building blocks

MCP servers expose three primitive types. Most servers only need **tools**.

| Primitive | When to use | Example |
|-----------|-------------|---------|
| **Tool** | Action the model can call (read or write) | `send_telegram_message`, `query_db`, `fetch_oi` |
| **Resource** | Read-only data the model can request by URI | `file://logs/today.txt`, `db://users/{id}` |
| **Prompt** | Reusable prompt template the user invokes | `/summarize-emails`, `/triage-issue` |

**Rule of thumb**: if the model decides when to call it → tool. If the user explicitly references it → resource or prompt.

## Designing tools well

Tools are the contract between Claude and the world. Bad tool design is the #1 reason MCP servers underperform.

- **Names**: verb_noun, lowercase_with_underscores. `get_user_orders` ✓ — `usersOrdersList` ✗.
- **Descriptions**: write for the model, not for humans. Explain *when* to use the tool and what its output looks like. The model picks tools based on these descriptions.
- **Schemas**: every parameter typed, with descriptions. Use Pydantic (Python) or Zod (TS).
- **Cardinality**: under 30 tools per server. Servers dumping 40+ tools destroy agent performance (token bloat + decision paralysis). Group with subcommands or split into multiple servers if needed.
- **Errors**: return helpful messages — `"User ID 'abc' not found. IDs are 6-digit integers."` not `"404"`.
- **Side effects**: any tool that writes/sends/deletes should make that obvious in name and description. Models will avoid destructive tools unless confident.

See `references/tool_design.md` for a deeper checklist.

## Choosing transport

| Transport | Use when | Notes |
|-----------|----------|-------|
| **stdio** | Local personal tool, single user, your machine | Simplest. Default. |
| **Streamable HTTP** | Remote, multi-user, cloud, n8n integration | Requires hosting + (optionally) OAuth. The current spec-recommended HTTP transport. |
| **SSE** | Legacy compatibility only | Deprecated in favor of Streamable HTTP. Don't pick this for new servers. |

For remote deployment options, see `references/deployment.md`.

## Authentication

- **No auth**: local stdio servers. Fine for personal tools.
- **API key via env var**: simplest for single-tenant remote. Read from `os.environ["MY_API_KEY"]`.
- **OAuth 2.1**: required for multi-tenant remote. FastMCP 3.x and the TS SDK both ship OAuth helpers. See `references/auth.md`.

Never hardcode secrets. Never log them. Treat all tool inputs as untrusted — they come from an LLM, not directly from a human.

## Common server recipes

These are scaffolds for frequent patterns. Read the relevant one before coding from scratch.

- **Wrap an existing REST API** → `templates/rest_wrapper.py`
- **Wrap a database (read-only queries)** → `templates/db_readonly.py`
- **File/document search** → `templates/file_search.py`
- **Scraper / browser automation** → `templates/playwright_scraper.py`
- **Telegram bot bridge** → `templates/telegram_bridge.py`

Each template is runnable as-is after filling in credentials and tool names.

## End-to-end workflow

For any new MCP server build, follow this sequence — don't skip steps:

1. **Confirm intent** (language, transport, what it wraps, auth) — one batched question if unclear.
2. **Scaffold** using the minimal example above for chosen language.
3. **Add 1–2 tools** with proper types, descriptions, error handling.
4. **Test in MCP Inspector** — verify tools list, schemas correct, calls work.
5. **Connect to Claude Desktop/Code** with absolute paths in config.
6. **Iterate** — add remaining tools one at a time, test each in Inspector.
7. **Deploy** (if remote) — see `references/deployment.md`.

Don't write all 10 tools, then debug. Write one, test it end-to-end in Claude, *then* add more.

## Common pitfalls (read before debugging)

If something doesn't work, check these in order — 90% of issues are here. See `references/troubleshooting.md` for the full list.

1. **Relative paths in config** — Claude Desktop launches from `/`. Always use absolute paths.
2. **Wrong Python interpreter** — `uv` vs system `python3` vs venv. Be explicit with `--directory` and `uv run`.
3. **Stdio + print() statements** — anything printed to stdout corrupts the JSON-RPC stream. Use `stderr` or a proper logger.
4. **Tool description too vague** — model won't pick it. "Get data" is too vague; "Fetch the current open interest for an NSE F&O symbol" is good.
5. **Forgot to restart Claude Desktop** — config changes need a full quit, not just window close.
6. **Async/sync mismatch** — FastMCP supports both; TS SDK is async-only. Don't mix.
7. **Schema mismatch** — Pydantic/Zod validation errors silently break calls. Check Inspector for the actual error.

## Reference files

Load these when the task calls for them — don't load everything upfront.

- `references/tool_design.md` — Detailed tool-design checklist with good/bad examples
- `references/deployment.md` — Hosting options: Docker, Fly.io, Railway, Cloudflare Workers, AWS, self-hosted
- `references/auth.md` — API key and OAuth 2.1 patterns with code
- `references/troubleshooting.md` — Full debugging checklist by symptom
- `references/typescript_advanced.md` — TS-specific patterns: Express/Hono middleware, runtime selection
- `templates/` — Ready-to-edit server templates for common patterns

## What success looks like

A well-built MCP server has: ≤30 well-named tools with clear descriptions, full type schemas, helpful errors, an Inspector smoke test you can run in 10 seconds, a one-line install command, and a README that tells someone else how to wire it into Claude Desktop. If you've delivered those, you're done.
