"""Chat handler: plain messages -> LLM + tool calling (localized)."""

from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from ..brain.ollama import chat_with_tools
from ..i18n import t
from ..state import state
from ..ui import format as fmt

router = Router(name="chat")


@router.message(F.text & ~F.text.startswith("/"))
async def on_chat(message: Message) -> None:
    chat_id = message.chat.id
    lang = state.lang(chat_id)
    await message.bot.send_chat_action(chat_id, "typing")

    history = state.get(chat_id)
    history.append({"role": "user", "content": message.text})

    try:
        answer, new_history = await asyncio.wait_for(
            chat_with_tools(history), timeout=180
        )
    except asyncio.TimeoutError:
        await message.answer(t(lang, "chat.timeout"), parse_mode="HTML")
        return
    except Exception as exc:  # noqa: BLE001
        await message.answer(t(lang, "chat.error", err=exc), parse_mode="HTML")
        return

    state.set(chat_id, new_history)
    if not answer:
        answer = t(lang, "chat.empty")

    # Markdown from the LLM -> Telegram HTML; fall back to plain text on parse errors
    formatted = fmt.md_to_tg_html(answer)
    try:
        await message.answer(formatted, parse_mode="HTML")
    except TelegramBadRequest:
        await message.answer(answer)
