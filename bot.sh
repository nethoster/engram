#!/usr/bin/env bash
# Engram-Bot service manager: start / stop / status / restart
set -euo pipefail

APP_DIR="/home/user/Projects/engram"
PY="$APP_DIR/venv/bin/python"
PID_FILE="/tmp/engram-bot.pid"
LOG_FILE="/tmp/engram-bot.log"

start() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "already running: pid=$(cat "$PID_FILE")"
    return 0
  fi
  cd "$APP_DIR"
  : > "$LOG_FILE"
  setsid "$PY" -m bot.main </dev/null >>"$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  echo "started pid=$(cat "$PID_FILE")"
}

stop() {
  if [ -f "$PID_FILE" ]; then
    pid="$(cat "$PID_FILE")"
    kill "$pid" 2>/dev/null || true
    sleep 1
    kill -9 "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "stopped pid=$pid"
  else
    echo "not running (no pid file)"
  fi
}

status() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "running pid=$(cat "$PID_FILE")"
    tail -5 "$LOG_FILE"
  else
    echo "not running"
    tail -10 "$LOG_FILE" 2>/dev/null || true
  fi
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  *) echo "usage: $0 {start|stop|restart|status}"; exit 1 ;;
esac
