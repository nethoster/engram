#!/usr/bin/env bash
# Engram one-command installer (Linux, macOS, Windows via Git Bash / WSL)
# Usage: curl -fsSL https://raw.githubusercontent.com/nethoster/engram/main/install.sh | sh
set -euo pipefail

REPO="https://github.com/nethoster/engram.git"
DIR="${ENGram_DIR:-$HOME/engram}"
PYTHON="${PYTHON:-python3}"

info() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
ok()   { printf '\033[1;32m ✓\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m !\033[0m %s\n' "$1"; }
die()  { printf '\033[1;31m ✗\033[0m %s\n' "$1" >&2; exit 1; }

# --- OS detection (informational) ---
detect_os() {
  case "$(uname -s)" in
    Linux*)  OS="Linux" ;;
    Darwin*) OS="macOS" ;;
    MINGW*|MSYS*|CYGWIN*) OS="Windows (Git Bash)" ;;
    *) OS="Unknown" ;;
  esac
  ok "Detected OS: $OS"
}

check_python() {
  command -v "$PYTHON" >/dev/null 2>&1 || die "$PYTHON not found. Install Python 3.10+ first."
  "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' \
    || die "Python 3.10+ required."
  ok "Python: $("$PYTHON" --version 2>&1)"
}

clone_repo() {
  if [ -d "$DIR" ]; then
    warn "Directory $DIR already exists — skipping clone."
  else
    info "Cloning $REPO -> $DIR"
    git clone "$REPO" "$DIR"
  fi
  ok "Repository ready at $DIR"
}

setup_venv() {
  cd "$DIR"
  if [ ! -d venv ]; then
    info "Creating virtualenv..."
    "$PYTHON" -m venv venv
  fi
  ok "Virtualenv ready"
}

install_deps() {
  cd "$DIR"
  info "Installing dependencies..."
  ./venv/bin/pip install --quiet -r requirements-bot.txt
  ok "Dependencies installed"
}

configure_tokens() {
  cd "$DIR"
  # Do not overwrite an existing .env
  if [ -f .env ]; then
    ok ".env already exists — keeping it."
    return
  fi

  info "Configure tokens (both are yours; nothing is shared)."
  echo "  1. Telegram: create a bot via @BotFather -> /newbot -> copy token"
  echo "  2. neuPrint: register at https://neuprint.janelia.org -> API token"
  echo "  (you can leave either blank and fill it in later)"
  echo

  printf 'Telegram bot token (or empty): '
  read -r tg_token
  printf 'neuPrint API token (or empty): '
  read -r nq_token

  {
    echo "# Engram configuration — do NOT commit this file"
    echo "TELEGRAM_BOT_TOKEN=${tg_token:-}"
    [ -n "${nq_token:-}" ] && echo "NEUPRINT_APPLICATION_CREDENTIALS=${nq_token}"
  } > .env
  chmod 600 .env 2>/dev/null || true

  ok ".env written (chmod 600)"
  [ -z "${tg_token:-}" ] && warn "Telegram token empty — edit .env before starting the bot."
  [ -z "${nq_token:-}" ] && warn "neuPrint token empty — run fetch_subgraph.py later."
}

print_next() {
  echo
  info "Done! Next steps:"
  echo "  cd $DIR"
  if ! grep -q '^TELEGRAM_BOT_TOKEN=..*' .env 2>/dev/null; then
    echo "  # 1. edit .env and set TELEGRAM_BOT_TOKEN"
  fi
  echo "  # Fetch connectome data (needs NEUPRINT_APPLICATION_CREDENTIALS in env):"
  echo "  set -a; source .env; set +a"
  echo "  ./venv/bin/python fetch_subgraph.py"
  echo "  # Start the bot:"
  echo "  ./bot.sh start   # or: ./venv/bin/python -m bot.main"
  echo
}

main() {
  info "Engram installer"
  detect_os
  check_python
  command -v git >/dev/null 2>&1 || die "git not found."
  clone_repo
  setup_venv
  install_deps
  configure_tokens
  print_next
  ok "Installation complete."
}

main "$@"
