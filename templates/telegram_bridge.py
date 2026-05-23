"""
Telegram bridge MCP server template.

Exposes a Telegram bot as MCP tools. Claude can send messages, read recent updates,
and forward content. Useful for the ShortBot / TPA SaaS pattern.

Setup:
    uv add "fastmcp>=3.0" python-telegram-bot

Set env vars:
    TELEGRAM_BOT_TOKEN=<your bot token>
    TELEGRAM_DEFAULT_CHAT_ID=<your chat ID>   # optional default recipient

Run:
    uv run server.py
"""

import os
import sys
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field
from telegram import Bot
from telegram.constants import ParseMode

mcp = FastMCP("telegram-bridge")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DEFAULT_CHAT_ID = os.environ.get("TELEGRAM_DEFAULT_CHAT_ID")

if not BOT_TOKEN:
    print("FATAL: TELEGRAM_BOT_TOKEN required", file=sys.stderr)
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)


@mcp.tool()
async def send_message(
    text: Annotated[str, Field(min_length=1, max_length=4000, description="Message text")],
    chat_id: Annotated[str | None, Field(default=None, description="Override default chat ID")] = None,
    parse_mode: Annotated[str, Field(default="Markdown", description="Markdown | HTML | None")] = "Markdown",
) -> dict:
    """Send a Telegram message to a chat.

    If chat_id is omitted, uses TELEGRAM_DEFAULT_CHAT_ID. Returns the sent message ID.
    Markdown supported: *bold*, _italic_, `code`, [link](url).
    """
    target = chat_id or DEFAULT_CHAT_ID
    if not target:
        raise ValueError("No chat_id provided and TELEGRAM_DEFAULT_CHAT_ID not set.")

    mode_map = {"Markdown": ParseMode.MARKDOWN, "HTML": ParseMode.HTML, "None": None}
    mode = mode_map.get(parse_mode, ParseMode.MARKDOWN)

    msg = await bot.send_message(chat_id=target, text=text, parse_mode=mode)
    return {"message_id": msg.message_id, "chat_id": msg.chat_id, "date": msg.date.isoformat()}


@mcp.tool()
async def get_updates(
    limit: Annotated[int, Field(ge=1, le=100, default=20, description="Max updates to fetch")] = 20,
) -> list[dict]:
    """Fetch recent updates (messages, callbacks) sent to the bot.

    Note: once consumed, updates are gone from Telegram's queue unless you set
    offset handling. Use this for reactive workflows.
    """
    updates = await bot.get_updates(limit=limit, timeout=5)
    results = []
    for u in updates:
        if not u.message:
            continue
        results.append({
            "update_id": u.update_id,
            "message_id": u.message.message_id,
            "chat_id": u.message.chat_id,
            "from_user": u.message.from_user.username if u.message.from_user else None,
            "text": u.message.text or "",
            "date": u.message.date.isoformat(),
        })
    return results


@mcp.tool()
async def send_photo(
    photo_url: Annotated[str, Field(description="Public URL of an image")],
    caption: Annotated[str | None, Field(default=None, max_length=1024)] = None,
    chat_id: Annotated[str | None, Field(default=None)] = None,
) -> dict:
    """Send a photo to a Telegram chat by URL. Returns message ID."""
    target = chat_id or DEFAULT_CHAT_ID
    if not target:
        raise ValueError("No chat_id provided and TELEGRAM_DEFAULT_CHAT_ID not set.")

    msg = await bot.send_photo(chat_id=target, photo=photo_url, caption=caption)
    return {"message_id": msg.message_id, "chat_id": msg.chat_id}


if __name__ == "__main__":
    mcp.run()
