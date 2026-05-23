# Troubleshooting

When an MCP server "doesn't work," the cause is almost always one of these. Diagnose by symptom.

## Symptom: Server doesn't appear in Claude Desktop

1. **Did you fully quit Claude Desktop?** Closing the window isn't enough — use Cmd+Q (macOS) or right-click the system tray icon → Quit (Windows). Then reopen.
2. **Is the config file in the right place?**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
3. **Is the JSON valid?** A trailing comma or missing brace silently breaks the whole file. Validate with `cat claude_desktop_config.json | python -m json.tool`.
4. **Are paths absolute?** Relative paths fail because Claude Desktop launches from `/`.

## Symptom: Server appears but tools don't show up

Check logs first:
- macOS: `~/Library/Logs/Claude/mcp-server-*.log` and `~/Library/Logs/Claude/mcp.log`
- Windows: `%APPDATA%\Claude\logs\mcp*.log`

Common causes:

1. **Server crashed on startup** — log will show the Python/Node traceback. Usually a missing import or env var.
2. **Wrong Python interpreter** — if you used `python` in config but your packages are in a uv project, use `uv` instead:
   ```json
   "command": "uv",
   "args": ["--directory", "/abs/path/to/server", "run", "server.py"]
   ```
3. **stdout pollution** — see next section.
4. **Tool registration failed** — start the server manually (`uv run server.py`) and watch for errors.

## Symptom: Tools listed but calls hang or return garbage

This is almost always **stdout pollution**. In stdio transport, the JSON-RPC protocol uses stdout. Any `print()` call corrupts the stream.

Fix:
```python
# WRONG — breaks stdio
print("Loading config...")

# RIGHT — use stderr or a logger
import sys
print("Loading config...", file=sys.stderr)

# Or use logging configured to stderr
import logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Loading config...")
```

Also check: any third-party library that prints to stdout (some HTTP clients, ML libs) will break things. Capture or redirect.

## Symptom: "Tool not found" when Claude tries to call it

1. **Description too vague** — Claude picks tools by description. "Get data" loses to a better-described competing tool.
2. **Schema validation failing silently** — open MCP Inspector and try calling the tool there. Pydantic/Zod errors will be explicit.
3. **Tool name has invalid characters** — stick to `[a-z0-9_]`. No hyphens, no camelCase.

## Symptom: HTTP server returns 404 on /mcp

1. **Wrong path** — newer SDK defaults are `/mcp` (Streamable HTTP), older versions used `/sse`. Check your SDK version.
2. **Express middleware order** — auth/body parsers must come before the MCP route handler.
3. **Reverse proxy stripping path** — nginx/Caddy needs to preserve the `/mcp` prefix.

## Symptom: HTTP server works locally but not when deployed

1. **Binding to 127.0.0.1** instead of `0.0.0.0` — Docker containers and most PaaS need `0.0.0.0`.
2. **Wrong PORT env var** — most platforms inject `PORT`; read from it: `port=int(os.environ["PORT"])`.
3. **Missing CORS headers** — some clients send preflight OPTIONS. The SDK's HTTP transport handles this; if you wrote your own, you need to.
4. **TLS not terminated** — Claude requires HTTPS for remote connectors. Use platform's TLS or put Caddy/Cloudflare in front.

## Symptom: Inspector won't connect

```bash
npx @modelcontextprotocol/inspector uv run server.py
```

If this hangs or errors:

1. **Wrong Node version** — Inspector needs Node 18+
2. **Server printing to stdout** before Inspector reads — same fix as above
3. **Port conflict** — Inspector uses 6274; if occupied, set `CLIENT_PORT=6275`
4. **Server takes long to start** — Inspector has a default timeout. Set `MCP_TIMEOUT=30000` (ms)

## Symptom: Async/sync errors in Python

FastMCP supports both sync and async tools, but **don't mix patterns within a single tool**:

```python
# WRONG
@mcp.tool()
def fetch(url: str) -> str:
    response = httpx.get(url)  # sync
    return await response.aread()  # await in sync function

# RIGHT — fully async
@mcp.tool()
async def fetch(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

# OR RIGHT — fully sync
@mcp.tool()
def fetch(url: str) -> str:
    response = httpx.get(url)
    return response.text
```

## Symptom: Env vars not loading

Claude Desktop launches your server with a clean env. Pass them explicitly in config:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["--directory", "/path", "run", "server.py"],
      "env": {
        "MY_API_KEY": "xxx",
        "DATABASE_URL": "postgres://..."
      }
    }
  }
}
```

Or load a `.env` file from inside your server (with `python-dotenv` or `dotenv` in Node).

## Symptom: Works in dev, fails for users

1. **uv/Python not in PATH** for the user — use absolute path: `"command": "/Users/me/.local/bin/uv"`
2. **Different OS line endings** — `.bat` vs shell scripts
3. **Permissions** — server file not executable; or write paths not user-writable

## Last resort: nuclear debugging

If nothing works:

```bash
# 1. Run the server manually, exactly as Claude Desktop would
cd /abs/path/to/server
/Users/me/.local/bin/uv run server.py

# 2. Should hang waiting for stdin — that's correct
# 3. Paste this and press Enter:
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}

# 4. Should get a JSON response back. If not, server is broken at startup.
```

If step 4 returns valid JSON, the server itself works — the problem is in the Claude config.
