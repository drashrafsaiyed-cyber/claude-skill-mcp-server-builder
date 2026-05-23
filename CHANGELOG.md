# Changelog

All notable changes to this skill will be documented here.

---

## [1.0.0] — 2026-05-23

### Initial release

- Core skill (`SKILL.md`) covering Python (FastMCP 3.x) and TypeScript (@modelcontextprotocol/sdk v2) MCP server scaffolding
- Decision tree for language, transport, wrapping target, and auth selection
- 5 ready-to-use server templates:
  - `rest_wrapper.py` — wrap any REST API as MCP tools
  - `db_readonly.py` — expose a database (read-only) to Claude
  - `file_search.py` — local file search and retrieval
  - `playwright_scraper.py` — web scraping via Playwright
  - `telegram_bridge.py` — convert a Telegram bot to MCP
- 5 reference docs:
  - `auth.md` — API key and OAuth 2.1 patterns
  - `deployment.md` — Railway, Fly.io, Docker deployment
  - `tool_design.md` — naming conventions, schemas, error handling
  - `troubleshooting.md` — common errors and fixes
  - `typescript_advanced.md` — advanced TypeScript MCP patterns
- Covers stdio (local) and Streamable HTTP (remote) transports
- Claude Desktop, Claude Code, Cursor, and n8n integration guidance
- MCP Inspector debugging workflow
