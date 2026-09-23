"""Ollama client + tool-calling loop."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import aiohttp

from ..config import LLM_MODEL, OLLAMA_URL
from ..connectome import tools as conn_tools

SPECS_PATH = Path(__file__).resolve().parents[1] / "connectome" / "tool_specs.json"
_TOOL_SPECS = json.loads(SPECS_PATH.read_text()) if SPECS_PATH.exists() else []
_MAX_TURNS = 8

_DISPATCH = {
    "neuron_info": lambda **kw: conn_tools.neuron_info(int(kw["bodyId"])),
    "neuron_connections": lambda **kw: conn_tools.neuron_connections(
        int(kw["bodyId"]), int(kw.get("top_n", 5))
    ),
    "find_by_type": lambda **kw: conn_tools.find_by_type(
        str(kw["type_name"]), int(kw.get("limit", 20))
    ),
    "shortest_path": lambda **kw: conn_tools.shortest_path(int(kw["a"]), int(kw["b"])),
    "hub_neurons": lambda **kw: conn_tools.hub_neurons(int(kw.get("top_n", 10))),
    "graph_summary": lambda **kw: conn_tools.graph_summary(),
}


def _run_tool(name: str, arguments: dict) -> str:
    fn = _DISPATCH.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        return fn(**arguments)
    except Exception as exc:  # noqa: BLE001
        return f"Tool error {name}: {exc}"


async def chat_with_tools(
    messages: list[dict],
    model: str = LLM_MODEL,
    timeout_sec: int = 120,
) -> tuple[str, list[dict]]:
    """Tool-calling loop. Returns (reply text, updated messages)."""
    messages = list(messages)
    async with aiohttp.ClientSession() as session:
        for _ in range(_MAX_TURNS):
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.8, "top_p": 0.9},
                "think": False,
            }
            if _TOOL_SPECS:
                payload["tools"] = _TOOL_SPECS
            async with session.post(
                f"{OLLAMA_URL}/api/chat", json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout_sec),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

            msg = data.get("message", {})
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                content = (msg.get("content") or "").strip()
                messages.append({"role": "assistant", "content": content})
                return content, messages

            messages.append(msg)
            for call in tool_calls:
                fn = call.get("function", {})
                name = fn.get("name", "")
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                result = _run_tool(name, args)
                messages.append({"role": "tool", "content": result, "name": name})
        # Hit the turn limit — ask for a short final answer
        messages.append(
            {
                "role": "user",
                "content": "Give a short final answer without new tool calls.",
            }
        )
        async with session.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=aiohttp.ClientTimeout(total=timeout_sec),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        content = (data.get("message", {}).get("content") or "").strip()
        return content, messages
