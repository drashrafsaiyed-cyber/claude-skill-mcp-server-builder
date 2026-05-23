# Deployment

Local stdio servers don't need deployment — Claude Desktop launches them. This doc is for remote Streamable HTTP servers.

## Decision matrix

| Use case | Recommended host |
|----------|------------------|
| Personal tool, single user | **stdio (no hosting)** |
| Personal remote (use from anywhere) | **Fly.io** or **Railway** |
| Team tool, low traffic | **Railway** or **Render** |
| Production multi-tenant | **AWS ECS** / **GCP Cloud Run** / **Fly.io** |
| Edge / low-latency global | **Cloudflare Workers** (TS only) |
| Already on n8n/Docker | **Self-hosted Docker** |

## Python: Production-ready Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy and install deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source
COPY . .

# Run on Streamable HTTP
ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000

CMD ["uv", "run", "server.py"]
```

In `server.py`:

```python
import os
from fastmcp import FastMCP

mcp = FastMCP("my-server")

# ... tools ...

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 8000)),
    )
```

## TypeScript: Production setup

```typescript
import express from 'express';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';

const server = new McpServer({ name: 'my-server', version: '1.0.0' });
// ... register tools ...

const app = express();
app.use(express.json());

app.all('/mcp', async (req, res) => {
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => crypto.randomUUID(),
  });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});

const port = parseInt(process.env.PORT || '8000');
app.listen(port, () => console.log(`MCP server on :${port}/mcp`));
```

## Fly.io quick deploy

```bash
fly launch --no-deploy   # generates fly.toml
fly secrets set MY_API_KEY=xxx
fly deploy
```

In `fly.toml`, ensure:

```toml
[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

## Railway

1. Connect GitHub repo
2. Railway auto-detects Python/Node
3. Set env vars in the dashboard
4. Set start command: `uv run server.py` (Python) or `node dist/index.js` (TS)
5. Expose the port shown in Railway's networking tab

## AWS ECS (Mumbai region — recommended for India)

Best fit for production servers handling user data subject to Indian data residency. Pattern:

- ECR for image registry
- ECS Fargate for compute (start with 0.5 vCPU / 1 GB)
- ALB in front for TLS termination
- Secrets Manager for credentials
- CloudWatch for logs

A `t3.small` EC2 alternative works for low traffic at ~$15/month vs Fargate's ~$10/month minimum.

## Cloudflare Workers (TypeScript only)

For global edge deployment with sub-50ms cold starts. Requires the `@cloudflare/mcp-agent` package and a different transport wrapper. See the official Cloudflare MCP docs — pattern is non-trivial and changes frequently.

## Connecting deployed servers to Claude

For Claude.ai / Claude Desktop with a deployed HTTP server:

1. Go to **Settings → Connectors** (or Customize → Connectors on the desktop app)
2. Click **Add custom connector**
3. URL: `https://your-server.com/mcp`
4. Add auth if applicable (Bearer token or OAuth)

For Claude Code:

```bash
claude mcp add my-server --transport http https://your-server.com/mcp
```

## Cost rough cuts (May 2026)

| Host | Minimum | Notes |
|------|---------|-------|
| Fly.io | ~$2/mo | 256MB shared-cpu-1x free tier |
| Railway | $5/mo | Includes $5 usage credit |
| Render | Free | Free tier sleeps after 15min idle |
| Cloudflare Workers | Free | 100k requests/day free |
| AWS Fargate | ~$10/mo | 0.25 vCPU / 0.5 GB minimum |
| Self-hosted (Hetzner) | ~$4/mo | CX11 VPS, full control |

## Production checklist

- [ ] TLS terminated (Let's Encrypt or platform-provided)
- [ ] Secrets in env vars, not committed
- [ ] Health check endpoint (`/health` returning 200)
- [ ] Structured logging (JSON to stdout)
- [ ] Rate limiting per session
- [ ] OAuth or API key auth (never deploy a no-auth public MCP)
- [ ] OpenTelemetry tracing (FastMCP 3.x has built-in support)
- [ ] Backup/restore plan if server holds state
