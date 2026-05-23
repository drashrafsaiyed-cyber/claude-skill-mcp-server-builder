# Authentication

Three patterns by scope:

## 1. No auth (local stdio)

For personal tools on your own machine. No work needed — stdio servers are trusted by Claude Desktop because the user launched them.

Still: never log secrets, never echo credentials in tool responses.

## 2. API key via env var (single-tenant remote)

Simplest pattern for a remote server you control. Best when there's effectively one user (you) or a small known team.

### Python

```python
import os
from fastmcp import FastMCP

mcp = FastMCP("my-server")

API_KEY = os.environ.get("MY_SERVICE_API_KEY")
if not API_KEY:
    raise RuntimeError("MY_SERVICE_API_KEY env var required")

@mcp.tool()
def fetch_data(query: str) -> dict:
    """Fetch data from the upstream service."""
    import httpx
    resp = httpx.get(
        "https://api.example.com/data",
        params={"q": query},
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    resp.raise_for_status()
    return resp.json()
```

For incoming auth (client → your server), use a shared secret header:

```python
from fastmcp.server.auth import BearerAuthProvider

mcp = FastMCP(
    "my-server",
    auth=BearerAuthProvider(token=os.environ["MCP_SHARED_SECRET"]),
)
```

Client adds `Authorization: Bearer <secret>` when calling.

### TypeScript

```typescript
import express from 'express';

const REQUIRED_TOKEN = process.env.MCP_SHARED_SECRET;
if (!REQUIRED_TOKEN) throw new Error('MCP_SHARED_SECRET required');

app.use('/mcp', (req, res, next) => {
  const auth = req.headers.authorization;
  if (auth !== `Bearer ${REQUIRED_TOKEN}`) {
    return res.status(401).json({ error: 'unauthorized' });
  }
  next();
});
```

## 3. OAuth 2.1 (multi-tenant remote)

Required when:
- Multiple distinct users sign in to your MCP server
- Your server accesses third-party APIs on behalf of each user (Gmail, Slack, etc.)
- You're publishing to the MCP Registry for public use

MCP uses OAuth 2.1 with Dynamic Client Registration (RFC 7591). This means MCP clients (like Claude) auto-register with your auth server — you don't manage client IDs manually.

### Python (FastMCP 3.x)

FastMCP ships OAuth helpers but the actual auth server (Authorization Server) is usually delegated to a provider like Auth0, Clerk, or your own.

```python
from fastmcp import FastMCP
from fastmcp.server.auth import OAuthProvider

mcp = FastMCP(
    "my-server",
    auth=OAuthProvider(
        authorization_server_url="https://your-tenant.auth0.com",
        # Resource server config
        required_scopes=["read:data"],
    ),
)

@mcp.tool()
def get_my_data(ctx) -> dict:
    """Fetch data for the authenticated user."""
    user_id = ctx.auth.user_id  # extracted from validated JWT
    return fetch_for_user(user_id)
```

### TypeScript

```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { createOAuthMiddleware } from '@modelcontextprotocol/sdk/server/auth.js';

const oauth = createOAuthMiddleware({
  authorizationServerUrl: 'https://your-tenant.auth0.com',
  requiredScopes: ['read:data'],
});

app.use('/mcp', oauth);
```

### Setting up the auth server

Realistically, you have three options:

1. **Use a hosted provider** (Auth0, Clerk, WorkOS) — easiest. They handle DCR, token issuance, user management. ~$0–$25/mo for low usage.
2. **Self-host** (Keycloak, Ory Hydra) — more control, more ops.
3. **Build your own** — only do this if you have specific reasons. OAuth is easy to get subtly wrong in ways that create security holes.

## Security must-dos (regardless of pattern)

- **Validate all tool inputs** with strict schemas (Pydantic/Zod), `additionalProperties: false`
- **Never trust the LLM** — tool inputs come from a model, not a vetted human
- **Rate limit** per session — a misbehaving agent can hammer your server
- **Log auth failures**, not auth successes (no PII in logs)
- **Rotate secrets** at least quarterly
- **Use TLS** end-to-end — no plain HTTP except `localhost`
- **Pin SDK versions** in production — supply chain attacks on MCP packages have been documented

## What NOT to do

- Hardcode API keys in source — even for "just testing"
- Commit `.env` files — add `.env` to `.gitignore` immediately
- Return raw upstream credentials in tool outputs — the model will surface them
- Skip auth on a deployed server "because it's just for me" — bots find these in hours
- Use shared bearer tokens for multi-user scenarios — use OAuth instead
