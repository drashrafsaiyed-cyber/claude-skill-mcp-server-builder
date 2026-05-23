# TypeScript Advanced Patterns

## Runtime selection

The TS SDK runs on Node 18+, Bun, and Deno. For most use cases:

- **Node.js** — default, widest ecosystem, all PaaS support it
- **Bun** — faster startup (~3x), use if you control the runtime
- **Deno** — pick only if you specifically want Deno features
- **Cloudflare Workers** — required for edge deployment, uses a different package (`@cloudflare/mcp-agent`)

## Express integration

For combining MCP with REST endpoints:

```typescript
import express from 'express';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { z } from 'zod';

const app = express();
app.use(express.json());

const mcp = new McpServer({ name: 'hybrid', version: '1.0.0' });

mcp.registerTool('greet', {
  description: 'Greet someone by name',
  inputSchema: z.object({ name: z.string() }),
}, async ({ name }) => ({
  content: [{ type: 'text', text: `Hello ${name}` }],
}));

// REST endpoint (non-MCP)
app.get('/health', (req, res) => res.json({ ok: true }));

// MCP endpoint
app.all('/mcp', async (req, res) => {
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => crypto.randomUUID(),
  });
  await mcp.connect(transport);
  await transport.handleRequest(req, res, req.body);
});

app.listen(8000);
```

## Hono integration (faster, edge-friendly)

```typescript
import { Hono } from 'hono';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

const app = new Hono();
const mcp = new McpServer({ name: 'hono-mcp', version: '1.0.0' });

// register tools...

app.all('/mcp', async (c) => {
  // adapter for Hono request/response
  // see @modelcontextprotocol/sdk/server/hono for helper
});

export default app;
```

## Session management

For stateful HTTP servers (tools that maintain context across calls):

```typescript
const sessions = new Map<string, SessionState>();

app.all('/mcp', async (req, res) => {
  const sessionId = req.headers['mcp-session-id'] as string;

  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => sessionId || crypto.randomUUID(),
    onSessionInitialized: (sid) => {
      sessions.set(sid, { startedAt: Date.now() });
    },
  });

  await mcp.connect(transport);
  await transport.handleRequest(req, res, req.body);
});
```

Sessions auto-expire after idle timeout (default 5 minutes). Configure with `sessionTimeoutMs`.

## Streaming responses

For long-running tool calls, stream progress back to the client:

```typescript
mcp.registerTool('long_task', {
  description: 'Run a task with progress updates',
  inputSchema: z.object({ steps: z.number() }),
}, async ({ steps }, { reportProgress }) => {
  for (let i = 0; i < steps; i++) {
    await new Promise(r => setTimeout(r, 1000));
    await reportProgress?.({ progress: i + 1, total: steps });
  }
  return { content: [{ type: 'text', text: 'Done' }] };
});
```

## Resource templates with parameters

```typescript
mcp.registerResource(
  'user-profile',
  {
    uriTemplate: 'user://{userId}/profile',
    description: 'User profile by ID',
    mimeType: 'application/json',
  },
  async (uri) => {
    const match = uri.match(/^user:\/\/(.+)\/profile$/);
    if (!match) throw new Error('Invalid URI');
    const userId = match[1];
    const profile = await db.users.findById(userId);
    return {
      contents: [{ uri, mimeType: 'application/json', text: JSON.stringify(profile) }],
    };
  }
);
```

## Multiple transports in one server

You can expose the same server over stdio AND HTTP:

```typescript
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const mcp = new McpServer({ name: 'dual', version: '1.0.0' });
// register tools...

if (process.argv.includes('--stdio')) {
  const transport = new StdioServerTransport();
  await mcp.connect(transport);
} else {
  // HTTP setup as before
  app.listen(8000);
}
```

Then in `claude_desktop_config.json`:
```json
{ "command": "node", "args": ["dist/index.js", "--stdio"] }
```

## TypeScript-specific gotchas

1. **ESM vs CJS** — MCP SDK is ESM only. Your `package.json` needs `"type": "module"` and imports need `.js` extensions even for `.ts` files.
2. **Zod v4** — SDK v2 requires Zod v4 (`zod/v4` imports). Zod v3 schemas won't work.
3. **`top-level await`** — required for the connect call. Make sure `"target": "ES2022"` or later in `tsconfig.json`.
4. **Strict mode** — the SDK's types are strict. Don't disable `strict: true` to silence errors; fix them.
5. **Bundling** — if using esbuild/tsup, mark `@modelcontextprotocol/sdk` as external. Don't bundle it.

## Recommended package.json

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "dev": "tsx watch src/index.ts",
    "start": "node dist/index.js",
    "inspect": "npx @modelcontextprotocol/inspector tsx src/index.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^2.0.0",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.5.0"
  }
}
```

## Recommended tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "Bundler",
    "esModuleInterop": true,
    "strict": true,
    "outDir": "dist",
    "declaration": true,
    "sourceMap": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"]
}
```
