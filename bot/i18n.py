"""Localization for the Telegram bot UI (Russian / English)."""

from __future__ import annotations

DEFAULT_LANG = "en"
LANGS = ("en", "ru")

# Button labels per language
_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # keyboard buttons
        "btn.about": "🧠 About Engram",
        "btn.summary": "🕸️ Graph summary",
        "btn.hubs": "🔝 Hubs",
        "btn.reset": "🧹 Reset dialog",
        "btn.home": "🏠 Home",
        "btn.language": "🌐 Language",
        "btn.lang_en": "🇬🇧 English",
        "btn.lang_ru": "🇷🇺 Russian",
        # /start
        "start.text": (
            "🧠 <b>Hi! I am Engram.</b>\n\n"
            "I speak the language of the fly connectome <i>male-cns:v1.0</i> — "
            "a local subgraph of <b>2000 neurons</b> and <b>225k connections</b>.\n\n"
            "Ask me:\n"
            "• <code>what does neuron 10009 do?</code>\n"
            "• <code>find type CT1</code>\n"
            "• <code>path from 10009 to 10157</code>\n"
            "• <code>who are the graph hubs?</code>"
        ),
        # /help
        "help.text": (
            "🧠 <b>Commands</b>\n"
            "/start — main menu\n"
            "/help — this help\n"
            "/language — switch interface language (EN / RU)\n"
            "/reset — clear the LLM dialog\n\n"
            "Or just type a question about neurons — I will call the tools myself."
        ),
        # /reset
        "reset.done": "Dialog reset. Starting over.",
        # about
        "about.text": (
            "🧠 <b>About Engram</b>\n\n"
            "Local brain: subgraph of 2000 neurons (BFS from top-seeds by post), "
            "225085 directed edges, density 0.056.\n"
            "Brain: qwen3-abliterated:0.6b-v2 (Ollama, tools).\n"
            "Data: local parquet, no external API calls at runtime."
        ),
        # summary
        "summary.header": "🕸️ <b>Subgraph summary</b>\n",
        # hubs
        "hubs.header": "🕸️ <b>Top-10 hubs</b>",
        # language
        "lang.current": "Interface language: {lang}.",
        "lang.set": "Language set to English.",
        # chat
        "chat.timeout": "⚠️ The brain did not answer in time (180s timeout). Try shorter.",
        "chat.error": "⚠️ LLM error: {err}",
        "chat.empty": "(empty answer)",
        # misc
        "reset.cb": "Dialog reset",
    },
    "ru": {
        "btn.about": "🧠 Про энграмм",
        "btn.summary": "🕸️ Сводка графа",
        "btn.hubs": "🔝 Хабы",
        "btn.reset": "🧹 Сбросить диалог",
        "btn.home": "🏠 Назад",
        "btn.language": "🌐 Язык",
        "btn.lang_en": "🇬🇧 English",
        "btn.lang_ru": "🇷🇺 Русский",
        "start.text": (
            "🧠 <b>Привет! Я — Энграмма.</b>\n\n"
            "Я говорю языком коннектома мухи <i>male-cns:v1.0</i> — "
            "локального подграфа на <b>2000 нейронов</b> и <b>225k связей</b>.\n\n"
            "Спроси меня:\n"
            "• <code>что делает нейрон 10009?</code>\n"
            "• <code>найди тип CT1</code>\n"
            "• <code>путь от 10009 до 10157</code>\n"
            "• <code>кто хабы графа?</code>"
        ),
        "help.text": (
            "🧠 <b>Команды</b>\n"
            "/start — главное меню\n"
            "/help — эта справка\n"
            "/language — переключить язык интерфейса (EN / RU)\n"
            "/reset — очистить диалог с LLM\n\n"
            "Или просто пиши вопрос про нейроны — я сам вызову нужные инструменты."
        ),
        "reset.done": "Диалог сброшен. Начинаем заново.",
        "about.text": (
            "🧠 <b>О Энграмме</b>\n\n"
            "Локальный мозг: подграф 2000 нейронов (BFS от топ-семян по post), "
            "225085 направленных связей, плотность 0.056.\n"
            "Мозг: qwen3-abliterated:0.6b-v2 (Ollama, tools).\n"
            "Данные: локальные parquet, без запросов к внешним API."
        ),
        "summary.header": "🕸️ <b>Сводка подграфа</b>\n",
        "hubs.header": "🕸️ <b>Топ-10 хабов</b>",
        "lang.current": "Язык интерфейса: {lang}.",
        "lang.set": "Язык переключён на русский.",
        "chat.timeout": "⚠️ Мозг не успел ответить (таймаут 180с). Попробуй короче.",
        "chat.error": "⚠️ Ошибка LLM: {err}",
        "chat.empty": "(пустой ответ)",
        "reset.cb": "Диалог сброшен",
    },
}

_LANG_LABELS = {"en": "English", "ru": "Русский"}


def t(lang: str, key: str, **fmt: object) -> str:
    """Translate key for lang; fall back to English."""
    table = _STRINGS.get(lang) or _STRINGS[DEFAULT_LANG]
    text = table.get(key) or _STRINGS[DEFAULT_LANG].get(key, key)
    return text.format(**fmt) if fmt else text


def lang_label(lang: str) -> str:
    return _LANG_LABELS.get(lang, lang)


def main_kb(lang: str) -> dict:
    """Main inline keyboard with labels in the given language."""
    return {
        "inline_keyboard": [
            [
                {"text": t(lang, "btn.about"), "callback_data": "about"},
                {"text": t(lang, "btn.summary"), "callback_data": "summary"},
            ],
            [
                {"text": t(lang, "btn.hubs"), "callback_data": "hubs"},
                {"text": t(lang, "btn.reset"), "callback_data": "reset"},
            ],
            [
                {"text": t(lang, "btn.language"), "callback_data": "language"},
                {"text": t(lang, "btn.home"), "callback_data": "home"},
            ],
        ]
    }


def language_kb() -> dict:
    """Language picker keyboard (labels always in their own language)."""
    return {
        "inline_keyboard": [
            [
                {"text": t("en", "btn.lang_en"), "callback_data": "lang_en"},
                {"text": t("ru", "btn.lang_ru"), "callback_data": "lang_ru"},
            ],
            [
                {"text": t("en", "btn.home"), "callback_data": "home"},
            ],
        ]
    }
