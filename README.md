# mcp-server-builder

> A Claude Skill that turns Claude into a guided MCP server builder. Scaffolds, debugs, and configures MCP servers in Python or TypeScript.

[![Claude Skill](https://img.shields.io/badge/Claude-Skill-orange)](https://claude.ai)
[![License](https://img.shields.io/badge/license-Anthropic-blue)](#license)

## What it does

When this skill is active, Claude walks you step-by-step through building a production-grade [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server — from picking a language to wiring it into Claude Desktop or Claude Code.

**Triggers automatically when you say things like:**

- "Build me an MCP server that wraps my REST API"
- "Expose my database to Claude"
- "Convert this Telegram bot to MCP"
- "Make a custom tool for Claude Desktop"
- Anything involving `FastMCP`, `@modelcontextprotocol/sdk`, `claude_desktop_config.json`, MCP Inspector, stdio, or Streamable HTTP

## What's included

```
mcp-server-builder/
├── SKILL.md                          # Core skill instructions (loaded by Claude)
├── references/
│   ├── auth.md                       # OAuth 2.1 + API key auth patterns
│   ├── deployment.md                 # Cloud deployment (Railway, Fly.io, Docker)
│   ├── tool_design.md                # Tool naming, schemas, error handling
│   ├── troubleshooting.md            # Common errors and fixes
│   └── typescript_advanced.md        # Advanced TypeScript patterns
└── templates/
    ├── rest_wrapper.py               # Wrap any REST API
    ├── db_readonly.py                # Read-only database exposure
    ├── file_search.py                # Local file search tool
    ├── playwright_scraper.py         # Web scraping via Playwright
    └── telegram_bridge.py            # Telegram bot → MCP bridge
```

## Install

```bash
git clone https://github.com/drashrafsaiyed-cyber/claude-skill-mcp-server-builder
```

Then in Claude Code, point to the skill:

```jsonc
// .claude/settings.json
{
  "skills": [
    "./claude-skill-mcp-server-builder"
  ]
}
```

## Skill covers

| Topic | Details |
|-------|---------|
| **Languages** | Python (FastMCP 3.x), TypeScript (@modelcontextprotocol/sdk v2) |
| **Transports** | stdio (local), Streamable HTTP (remote/cloud) |
| **Auth** | None, API key (env vars), OAuth 2.1 |
| **Integrations** | Claude Desktop, Claude Code, Cursor, n8n, VS Code |
| **Debugging** | MCP Inspector, structured error handling |
| **Deployment** | Railway, Fly.io, Docker, local |

## License

© 2025 Anthropic, PBC. All rights reserved. See [LICENSE](LICENSE) for terms.
