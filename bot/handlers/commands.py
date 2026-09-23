"""Commands and main menu (localized: EN / RU)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from ..i18n import language_kb, lang_label, main_kb, t
from ..state import state
from ..ui import format as fmt

router = Router(name="commands")


async def _edit(call: CallbackQuery, text: str, kb: dict | None = None) -> None:
    """edit_text that tolerates repeated presses (message is not modified)."""
    try:
        await call.message.edit_text(
            text, reply_markup=kb, parse_mode="HTML"
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise
        await call.answer()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    lang = state.lang(message.chat.id)
    await message.answer(
        t(lang, "start.text"), reply_markup=main_kb(lang), parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    lang = state.lang(message.chat.id)
    await message.answer(
        t(lang, "help.text"), reply_markup=main_kb(lang), parse_mode="HTML"
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    lang = state.lang(message.chat.id)
    state.reset(message.chat.id)
    await message.answer(
        t(lang, "reset.done"), reply_markup=main_kb(lang), parse_mode="HTML"
    )


@router.message(Command("language"))
async def cmd_language(message: Message) -> None:
    lang = state.lang(message.chat.id)
    await message.answer(
        t(lang, "lang.current", lang=lang_label(lang)),
        reply_markup=language_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "about")
async def cb_about(call: CallbackQuery) -> None:
    lang = state.lang(call.message.chat.id)
    await call.answer()
    await _edit(call, t(lang, "about.text"), main_kb(lang))


@router.callback_query(F.data == "summary")
async def cb_summary(call: CallbackQuery) -> None:
    from ..connectome.tools import graph_summary

    lang = state.lang(call.message.chat.id)
    await call.answer()
    await _edit(
        call,
        f"{t(lang, 'summary.header')}<code>{fmt.escape(graph_summary())}</code>",
        main_kb(lang),
    )


@router.callback_query(F.data == "hubs")
async def cb_hubs(call: CallbackQuery) -> None:
    from ..connectome.tools import hub_neurons

    import json

    lang = state.lang(call.message.chat.id)
    await call.answer()
    data = json.loads(hub_neurons(10))
    lines = [t(lang, "hubs.header")]
    for i, h in enumerate(data, 1):
        lines.append(
            f"{i}. <code>{h['bodyId']}</code> {fmt.escape(str(h['type']))} "
            f"({fmt.escape(str(h['instance']))}) deg={h['degree']}"
        )
    await _edit(call, "\n".join(lines), main_kb(lang))


@router.callback_query(F.data == "reset")
async def cb_reset(call: CallbackQuery) -> None:
    lang = state.lang(call.message.chat.id)
    state.reset(call.message.chat.id)
    await call.answer(t(lang, "reset.cb"))
    await _edit(call, t(lang, "reset.done"), main_kb(lang))


@router.callback_query(F.data == "home")
async def cb_home(call: CallbackQuery) -> None:
    lang = state.lang(call.message.chat.id)
    await call.answer()
    await _edit(call, t(lang, "start.text"), main_kb(lang))


@router.callback_query(F.data == "language")
async def cb_language(call: CallbackQuery) -> None:
    lang = state.lang(call.message.chat.id)
    await call.answer()
    await _edit(
        call,
        t(lang, "lang.current", lang=lang_label(lang)),
        language_kb(),
    )


@router.callback_query(F.data.in_({"lang_en", "lang_ru"}))
async def cb_lang_set(call: CallbackQuery) -> None:
    new_lang = "en" if call.data == "lang_en" else "ru"
    state.set_lang(call.message.chat.id, new_lang)
    await call.answer(t(new_lang, "lang.set"))
    await _edit(
        call,
        t(new_lang, "start.text"),
        main_kb(new_lang),
    )
