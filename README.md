# Engram — Local Fly Connectome + LLM Telegram Bot

> A local Drosophila melanogaster connectome subgraph (2000 neurons, 225k edges) driven by a local uncensored LLM, exposed as a Telegram bot that "speaks" the connectome through tool calling.

## 📜 License — read this before you fork

Engram is **source-available**, not OSI open-source software. The full terms are in [LICENSE](LICENSE). What they mean for you:

- **You may** read and study the source code, and use, modify, and run the program for **personal, non-commercial** purposes.
- **You may NOT** fork, modify, publish, or redistribute the project, and **may NOT** use it commercially (selling it, offering it as a service, bundling it into a product) — **without prior written permission** from the author.
- Any permitted modification must retain the copyright notice and this license as-is.

In short: forking for a personal experiment is fine per the license; publishing your fork, redistributing it, or using it commercially requires asking first. To request permission, open an issue ([github.com/nethoster/engram/issues](https://github.com/nethoster/engram/issues)).

## What is Engram?

Engram is a fully local pipeline:

1. **Connectome data** — a subgraph of the `male-cns:v1.0` dataset fetched from neuPrint (Janelia) via `fetch_subgraph.py`, stored as local parquet files. No live API calls at runtime.
2. **Local LLM brain** — [Ollama](https://ollama.com) running `huihui_ai/qwen3-abliterated:0.6b-v2` (uncensored Qwen3, tool-calling capable).
3. **Telegram bot** — an [aiogram 3](https://aiogram.dev) bot that routes questions to the LLM, which calls graph tools (`neuron_info`, `shortest_path`, `hub_neurons`, ...) and answers from real data.

The bot has an **English / Russian** interface — switch with the 🌐 Language button or `/language`.

## Requirements

- Python 3.10+ (developed on 3.14)
- [Ollama](https://ollama.com) running locally with the model pulled:
  ```bash
  ollama pull huihui_ai/qwen3-abliterated:0.6b-v2
  ```
- A Telegram bot token from [@BotFather](https://t.me/BotFather) (create your own: `/newbot`)
- A neuPrint API token from [neuprint.janelia.org](https://neuprint.janelia.org) (free; only needed to fetch the connectome data)

## Install

### Option 1 — Universal (all OSes)

```bash
git clone https://github.com/nethoster/engram.git
cd engram
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements-bot.txt
```

### Option 2 — One command (Linux, macOS, Windows via Git Bash / WSL)

```bash
curl -fsSL https://raw.githubusercontent.com/nethoster/engram/main/install.sh | sh
```

The installer creates a virtualenv, installs dependencies, and walks you through entering your tokens (Telegram + neuPrint).

## Setup

### 1. Telegram token (required)

Create a bot with [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token. Put it in a `.env` file in the project root:

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
```

### 2. neuPrint token (for fetching data)

Register at [neuprint.janelia.org](https://neuprint.janelia.org), generate an API token, then:

```bash
export NEUPRINT_APPLICATION_CREDENTIALS=<your-token>
python fetch_subgraph.py            # writes data/*.parquet
```

> The fetched data (`data/*.parquet`) is local-only and not committed to git. Each user fetches it with their own token.

### 3. Run

```bash
./bot.sh start        # start polling
./bot.sh status       # check
./bot.sh stop         # stop
# or directly:
python -m bot.main
```

## Usage

Open your bot in Telegram and:

- `/start` — main menu
- `/language` — switch EN / RU
- `/reset` — clear the LLM dialog
- Ask questions: `who are the graph hubs?`, `path from 10009 to 10157`, `find type CT1`

## Project structure

```
engram/
├── bot/                    # Telegram bot (aiogram 3)
│   ├── brain/              # LLM client + system prompts (EN/RU)
│   │   ├── ollama.py       #   tool-calling loop
│   │   └── prompt.py       #   system prompts per language
│   ├── connectome/         # graph data + tools
│   │   ├── loader.py       #   parquet -> networkx DiGraph
│   │   ├── tools.py        #   6 tools exposed to the LLM
│   │   └── tool_specs.json #   Ollama tool schemas
│   ├── handlers/           # Telegram command & chat handlers
│   ├── ui/                 # formatting (Markdown -> Telegram HTML)
│   ├── i18n.py             # localization (EN/RU)
│   ├── state.py            # per-chat dialog + language
│   ├── config.py           # env / .env config
│   └── main.py             # entrypoint
├── data/                   # local subgraph (gitignored, fetch yourself)
├── fetch_subgraph.py       # neuPrint -> parquet (needs your token)
├── bot.sh                  # start / stop / status / restart
├── install.sh              # one-command installer
├── requirements-bot.txt    # Python dependencies
└── LICENSE                 # Source-Available License
```

## Tech stack

- **Python** + [aiogram 3](https://aiogram.dev) (Telegram)
- **Ollama** + `huihui_ai/qwen3-abliterated:0.6b-v2` (local LLM, tool calling)
- **networkx** + **pandas** + **pyarrow** (graph & data)
- **neuprint-python** (data fetch only; not needed at runtime)

## Notes

- Everything runs locally — no live neuPrint queries while the bot is running.
- The subgraph: 2000 neurons, 225085 directed edges, 1 weakly-connected component, density 0.056 (BFS from top-10 traced seeds by post).
- The default interface language for new chats is English; switch to Russian with 🌐 Language.
