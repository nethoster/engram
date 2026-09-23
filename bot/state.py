"""Per-chat dialog state: history + interface language."""

from __future__ import annotations

from collections import defaultdict

from .brain.prompt import system_prompt
from .i18n import DEFAULT_LANG


class DialogState:
    def __init__(self) -> None:
        self._histories: dict[int, list[dict]] = defaultdict(list)
        self._langs: dict[int, str] = {}

    def lang(self, chat_id: int) -> str:
        return self._langs.get(chat_id, DEFAULT_LANG)

    def set_lang(self, chat_id: int, lang: str) -> None:
        """Set interface language; switching language resets the dialog."""
        if self._langs.get(chat_id, DEFAULT_LANG) != lang:
            self.reset(chat_id)
        self._langs[chat_id] = lang

    def get(self, chat_id: int) -> list[dict]:
        """Full message list: system prompt (for current lang) + history."""
        lang = self.lang(chat_id)
        return [{"role": "system", "content": system_prompt(lang)}] + list(
            self._histories[chat_id]
        )

    def set(self, chat_id: int, messages: list[dict]) -> None:
        """Store history without the leading system message."""
        history = [m for m in messages if m.get("role") != "system"]
        self._histories[chat_id] = history

    def reset(self, chat_id: int) -> None:
        self._histories.pop(chat_id, None)


state = DialogState()
