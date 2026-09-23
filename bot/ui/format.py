"""Telegram formatting helpers: HTML escaping, Markdown -> Telegram HTML."""

from __future__ import annotations

import html
import re

EMOJI_INFO = "🧠"
EMOJI_GRAPH = "🕸️"
EMOJI_PATH = "🛤️"
EMOJI_OK = "✅"
EMOJI_ERR = "⚠️"


def escape(text: str) -> str:
    return html.escape(text or "")


def md_to_tg_html(text: str) -> str:
    """Markdown (LLM output) -> Telegram HTML. Escape first, then inject tags."""
    t = html.escape(text or "")

    # code blocks ```lang ... ```
    t = re.sub(
        r"```(?:[a-zA-Z0-9_+-]*)\n?(.*?)```",
        lambda m: f"<pre>{m.group(1)}</pre>",
        t,
        flags=re.S,
    )
    # single-line code `...`
    t = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", t)

    # bold **...** / __...__
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.S)
    t = re.sub(r"__(.+?)__", r"<b>\1</b>", t, flags=re.S)

    # italic *...* (not part of **)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", t)
    # italic _..._ (not snake_case / __)
    t = re.sub(r"(?<![\w\\])_([^_\n]+)_(?![\w])", r"<i>\1</i>", t)

    # markdown headers ### / ## / # -> bold (no h1-h6 in Telegram)
    t = re.sub(r"^#{1,6}\s*(.+)$", r"<b>\1</b>", t, flags=re.M)

    # leftover unmatched ** / ` markers — strip them so they don't show as garbage
    t = t.replace("**", "").replace("__", "")

    return t


def wrap_code(text: str) -> str:
    return f"<code>{escape(text)}</code>"


def success(body: str) -> str:
    return f"{EMOJI_OK} {escape(body)}"


def error(body: str) -> str:
    return f"{EMOJI_ERR} {escape(body)}"
