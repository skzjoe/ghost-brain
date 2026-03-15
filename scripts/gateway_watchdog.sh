#!/usr/bin/env bash
# Gateway Watchdog — runs from OS crontab (NOT openclaw cron)
# Checks if gateway process is alive. If dead, alerts via Telegram.
# Cooldown: alerts once, then waits 30 minutes before alerting again.

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
COOLDOWN_FILE="/tmp/gateway_watchdog_last_alert"
COOLDOWN_SECONDS=1800  # 30 minutes

# Read config from secrets
BOT_TOKEN_FILE="$WORKSPACE/secrets/telegram_bot_token.txt"
CHAT_ID_FILE="$WORKSPACE/secrets/telegram_chat_id.txt"

if [[ -f "$BOT_TOKEN_FILE" ]]; then
  BOT_TOKEN=$(cat "$BOT_TOKEN_FILE")
elif [[ -n "$GATEWAY_WATCHDOG_BOT_TOKEN" ]]; then
  BOT_TOKEN="$GATEWAY_WATCHDOG_BOT_TOKEN"
else
  exit 0
fi

if [[ -f "$CHAT_ID_FILE" ]]; then
  CHAT_ID=$(cat "$CHAT_ID_FILE")
elif [[ -n "$GATEWAY_WATCHDOG_CHAT_ID" ]]; then
  CHAT_ID="$GATEWAY_WATCHDOG_CHAT_ID"
else
  exit 0
fi

# Check if gateway is running
if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
  # Gateway is up — clear cooldown so next downtime alerts immediately
  rm -f "$COOLDOWN_FILE"
  exit 0
fi

# Gateway is down — check cooldown
if [[ -f "$COOLDOWN_FILE" ]]; then
  LAST_ALERT=$(cat "$COOLDOWN_FILE")
  NOW=$(date +%s)
  ELAPSED=$(( NOW - LAST_ALERT ))
  if (( ELAPSED < COOLDOWN_SECONDS )); then
    exit 0  # Still in cooldown, don't spam
  fi
fi

# Send alert + set cooldown
date +%s > "$COOLDOWN_FILE"

MSG="⚠️ OpenClaw gateway is DOWN on $(hostname)! systemd should auto-restart in 5s. Time: $(date '+%Y-%m-%d %H:%M:%S')"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "text=${MSG}" \
  -d "parse_mode=HTML" > /dev/null 2>&1
