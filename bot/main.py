#!/usr/bin/env python3
"""Engram-Bot: aiogram 3 + Ollama + local connectome."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher

from .config import TELEGRAM_BOT_TOKEN
from .connectome.loader import load_graph
from .handlers import chat, commands


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger("engram")

    # Warm the graph up before polling starts
    g = load_graph()
    log.info("graph warmed: %d nodes, %d edges", g.number_of_nodes(), g.number_of_edges())

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(commands.router)
    dp.include_router(chat.router)

    # Retry loop for transient network failures to api.telegram.org
    delay = 2
    for attempt in range(1, 11):
        try:
            log.info("starting polling (attempt %d)...", attempt)
            await dp.start_polling(bot)
            return
        except Exception as exc:  # noqa: BLE001
            log.warning("polling failed (attempt %d): %s", attempt, exc)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
