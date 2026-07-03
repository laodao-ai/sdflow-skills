#!/bin/sh
# Starts/stops a background static file server rooted at openspec/, regardless of the
# caller's cwd — review.html's root-relative asset paths (/workflow/tools/engine.js etc.) depend
# on the server root being exactly openspec/, so this always cd's to its own directory
# first. Runs the server detached (background) and prints a clickable link.
#
# Usage:
#   serve.sh start [port]     # no port -> OS picks a free ephemeral port (avoids
#                              # cross-project collisions); no-op (prints link) if
#                              # already running
#   serve.sh stop             # no-op if not running
#   serve.sh restart [port]   # stop then start; reuses the last ACTUAL bound port
#                              # if none given

set -eu

DIR="$(cd "$(dirname "$0")" && pwd)"
KEY=$(printf '%s' "$DIR" | tr '/' '_')
PIDFILE="/tmp/openspec-review-serve-${KEY}.pid"
LOGFILE="/tmp/openspec-review-serve-${KEY}.log"
# 0 = ask the OS for a free ephemeral port. Two different projects each running
# `serve.sh start` with no explicit port must not collide on the same fixed port.
DEFAULT_PORT=0
# How long to wait for http.server to print its "Serving HTTP on ... port N ..."
# line before giving up (PORT_WAIT_TRIES * PORT_WAIT_INTERVAL seconds, ~5s).
PORT_WAIT_TRIES=25
PORT_WAIT_INTERVAL=0.2

is_running() {
  [ -f "$PIDFILE" ] || return 1
  PID=$(sed -n '1p' "$PIDFILE")
  [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null
}

# Parses the actual bound port out of $LOGFILE, polling briefly since the
# background process's startup (and its "Serving HTTP on ... port N ..." line)
# doesn't appear instantly. Works uniformly whether $1 was 0 (auto-assigned) or
# an explicit port (also confirms the explicit port actually bound, since a
# failed bind never prints that line). Prints the detected port on success;
# prints nothing and returns 1 if it never showed up (startup failure or an
# explicit port that was already taken).
detect_bound_port() {
  PID_TO_WATCH="$1"
  TRIES=0
  while [ "$TRIES" -lt "$PORT_WAIT_TRIES" ]; do
    PORT_FOUND=$(grep -Eo 'port [0-9]+' "$LOGFILE" 2>/dev/null | head -n1 | grep -Eo '[0-9]+' || true)
    if [ -n "$PORT_FOUND" ]; then
      printf '%s\n' "$PORT_FOUND"
      return 0
    fi
    if ! kill -0 "$PID_TO_WATCH" 2>/dev/null; then
      # Process already died (e.g. failed to bind) — no point waiting further.
      return 1
    fi
    sleep "$PORT_WAIT_INTERVAL"
    TRIES=$((TRIES + 1))
  done
  return 1
}

do_start() {
  PORT="${1:-$DEFAULT_PORT}"
  if is_running; then
    PID=$(sed -n '1p' "$PIDFILE")
    RUNNING_PORT=$(sed -n '2p' "$PIDFILE")
    echo "already running (pid $PID) -> http://localhost:${RUNNING_PORT}/review.html"
    return 0
  fi
  cd "$DIR"
  # -u: unbuffered stdout. Without it, http.server's startup line sits in a
  # block-buffered pipe (stdout isn't a tty once redirected to $LOGFILE) and
  # may never flush before we've finished polling for it.
  nohup python3 -u -m http.server "$PORT" >"$LOGFILE" 2>&1 &
  NEWPID=$!
  if ACTUAL_PORT=$(detect_bound_port "$NEWPID"); then
    printf '%s\n%s\n' "$NEWPID" "$ACTUAL_PORT" >"$PIDFILE"
    echo "started (pid $NEWPID), log: $LOGFILE"
    echo "http://localhost:${ACTUAL_PORT}/review.html"
  else
    kill "$NEWPID" 2>/dev/null || true
    echo "failed to start: could not detect bound port (see $LOGFILE)" >&2
    exit 1
  fi
}

do_stop() {
  if ! is_running; then
    echo "not running"
    rm -f "$PIDFILE"
    return 0
  fi
  PID=$(sed -n '1p' "$PIDFILE")
  kill "$PID" 2>/dev/null || true
  rm -f "$PIDFILE"
  echo "stopped (pid $PID)"
}

do_restart() {
  PORT="${1:-}"
  if [ -z "$PORT" ] && [ -f "$PIDFILE" ]; then
    PORT=$(sed -n '2p' "$PIDFILE")
  fi
  do_stop
  do_start "${PORT:-$DEFAULT_PORT}"
}

case "${1:-}" in
  start) shift; do_start "${1:-}" ;;
  stop) do_stop ;;
  restart) shift; do_restart "${1:-}" ;;
  *)
    echo "usage: $0 {start [port]|stop|restart [port]}" >&2
    exit 2
    ;;
esac
