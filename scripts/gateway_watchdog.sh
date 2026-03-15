#!/usr/bin/env bash
# Gateway Watchdog — runs from OS crontab (NOT openclaw cron)
# Checks if gateway process is alive. If dead, alerts via Telegram.
# systemd will auto-restart it, this just sends the notification.

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"

# Read config from secrets (create these files with your values)
BOT_TOKEN_FILE="$WORKSPACE/secrets/telegram_bot_token.txt"
CHAT_ID_FILE="$WORKSPACE/secrets/telegram_chat_id.txt"

# Fallback: read from env or exit
if [[ -f "$BOT_TOKEN_FILE" ]]; then
  BOT_TOKEN=$(cat "$BOT_TOKEN_FILE")
elif [[ -n "$GATEWAY_WATCHDOG_BOT_TOKEN" ]]; then
  BOT_TOKEN="$GATEWAY_WATCHDOG_BOT_TOKEN"
else
  exit 0  # No config, skip silently
fi

if [[ -f "$CHAT_ID_FILE" ]]; then
  CHAT_ID=$(cat "$CHAT_ID_FILE")
elif [[ -n "$GATEWAY_WATCHDOG_CHAT_ID" ]]; then
  CHAT_ID="$GATEWAY_WATCHDOG_CHAT_ID"
else
  exit 0
fi

# Check if gateway process is running
if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
  exit 0  # All good
fi

# Gateway is down — send alert
MSG="⚠️ OpenClaw gateway is DOWN on $(hostname)! systemd should auto-restart in 5s. Time: $(date '+%Y-%m-%d %H:%M:%S')"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "text=${MSG}" \
  -d "parse_mode=HTML" > /dev/null 2>&1
