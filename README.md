# MCP Server Builder — A Claude Skill

> A [Claude Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that turns Claude into a guided MCP server builder. Stop debugging stdout pollution and schema errors — let Claude scaffold, configure, and troubleshoot for you.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Skill](https://img.shields.io/badge/Claude-Skill-orange)](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)

## What it does

When this skill is active, Claude walks you step-by-step through building a production-grade [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server — from picking a language to wiring it into Claude Desktop or Claude Code.

Triggers automatically when you say things like:

- *"Build me an MCP server that wraps my REST API"*
- *"Expose my database to Claude"*
- *"Convert this Telegram bot to MCP"*
- *"Make a custom tool for Claude Desktop"*
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

### Claude.ai (Claude Desktop / web / mobile)

Download the [`.skill` file from the latest release](../../releases/latest) and install it through the Claude interface: **Settings → Capabilities → Skills → Upload skill**.

Web, mobile, and Claude Desktop all sync from your claude.ai account — install once, available everywhere.

### Claude Code (CLI)

Clone directly into your Claude skills directory:

**macOS / Linux**

```bash
git clone https://github.com/drashrafsaiyed-cyber/claude-skill-mcp-server-builder \
  ~/.claude/skills/mcp-server-builder
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/drashrafsaiyed-cyber/claude-skill-mcp-server-builder `
  "$env:USERPROFILE\.claude\skills\mcp-server-builder"
```

Restart Claude Code — the skill loads automatically from the skills directory.

## Skill covers

| Topic | Details |
|-------|---------|
| Languages | Python (FastMCP 3.x), TypeScript (@modelcontextprotocol/sdk v2) |
| Transports | stdio (local), Streamable HTTP (remote/cloud) |
| Auth | None, API key (env vars), OAuth 2.1 |
| Integrations | Claude Desktop, Claude Code, Cursor, n8n, VS Code |
| Debugging | MCP Inspector, structured error handling |
| Deployment | Railway, Fly.io, Docker, local |

## What this skill won't do

- **Won't write your business logic.** It scaffolds the MCP protocol layer. The actual data/API work is yours.
- **Won't deploy for you.** It tells you the options but doesn't push code.
- **Won't replace reading the FastMCP / TS SDK docs** for advanced features (resources, sampling, elicitation). It covers ~90% of typical builds.

## Requirements

- A Claude account (free tier works for claude.ai install)
- Python 3.10+ for Python templates, or Node 18+ for TypeScript
- `uv` recommended for Python projects

## Contributing

Contributions welcome. Particularly useful additions:

- More templates (specific API wrappers, vector DB, MQ patterns)
- Improvements to the troubleshooting reference based on new failure modes
- Real-world example projects built with the skill

Open an issue first for significant changes so we can discuss approach.

## Related

- [Model Context Protocol spec](https://modelcontextprotocol.io)
- [FastMCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [TypeScript MCP SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)

## License

MIT — see [LICENSE](LICENSE).

## Author

Built by [Dr. Ashraf Saiyed](https://github.com/drashrafsaiyed-cyber) ([VR AI Automations](https://github.com/drashrafsaiyed-cyber)).

Not affiliated with or endorsed by Anthropic.
