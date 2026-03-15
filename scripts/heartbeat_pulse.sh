#!/usr/bin/env bash
set -euo pipefail

# 👻 Ghost Heartbeat Pulse — bash-first, 0 tokens when nothing needs attention
# Cross-platform: macOS + Linux
#
# Design: all checks are pure bash/python. LLM is NEVER invoked by this script.
# If alerts are found, they're printed as plain text → OpenClaw handles the rest.
# Meeting prep requires LLM → printed as a signal for the agent to act on.

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
LOG_DIR="/tmp/openclaw"
LOG_FILE="$LOG_DIR/heartbeat-pulse-$(date +%F).log"
mkdir -p "$LOG_DIR"

log() { printf "[%s] %s\n" "$(date '+%Y-%m-%dT%H:%M:%S')" "$*" >> "$LOG_FILE"; }

# Cross-platform date helpers
now_epoch() {
  if date --version >/dev/null 2>&1; then
    date +%s  # GNU (Linux)
  else
    date +%s  # BSD (macOS) — same syntax, different implementation
  fi
}

date_diff_days() {
  # date_diff_days <YYYY-MM-DD> → days since that date
  local target="$1"
  local now target_epoch
  now=$(now_epoch)
  if date --version >/dev/null 2>&1; then
    target_epoch=$(date -d "$target" +%s 2>/dev/null || echo "$now")
  else
    target_epoch=$(date -j -f "%Y-%m-%d" "$target" +%s 2>/dev/null || echo "$now")
  fi
  echo $(( (now - target_epoch) / 86400 ))
}

hours_from_now() {
  # hours_from_now <N> → ISO datetime N hours from now
  if date --version >/dev/null 2>&1; then
    date -Is -d "+${1} hour"
  else
    date -v "+${1}H" "+%Y-%m-%dT%H:%M:%S%z"
  fi
}

# Lock to prevent overlapping runs
LOCK_DIR="/tmp/openclaw-heartbeat.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "HEARTBEAT_OK"
  exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

ALERTS=()

# ─── Config (read from secrets or env) ───
GOG_ACCOUNT_FILE="$WORKSPACE/secrets/gog_account.txt"
GOG_QUERY_FILE="$WORKSPACE/secrets/gog_email_query.txt"
GOG_CALENDAR_FILE="$WORKSPACE/secrets/gog_calendar_email.txt"

GOG_ACCOUNT="${HEARTBEAT_GOG_ACCOUNT:-}"
GOG_QUERY="${HEARTBEAT_GOG_QUERY:-}"
CALENDAR_EMAIL="${HEARTBEAT_CALENDAR_EMAIL:-}"

[[ -z "$GOG_ACCOUNT" ]] && [[ -f "$GOG_ACCOUNT_FILE" ]] && GOG_ACCOUNT=$(cat "$GOG_ACCOUNT_FILE")
[[ -z "$GOG_QUERY" ]] && [[ -f "$GOG_QUERY_FILE" ]] && GOG_QUERY=$(cat "$GOG_QUERY_FILE")
[[ -z "$CALENDAR_EMAIL" ]] && [[ -f "$GOG_CALENDAR_FILE" ]] && CALENDAR_EMAIL=$(cat "$GOG_CALENDAR_FILE")

# Find gog binary (cross-platform)
GOG_BIN=""
for p in /home/linuxbrew/.linuxbrew/bin/gog /opt/homebrew/bin/gog /usr/local/bin/gog; do
  [[ -x "$p" ]] && GOG_BIN="$p" && break
done
[[ -z "$GOG_BIN" ]] && command -v gog >/dev/null 2>&1 && GOG_BIN=$(command -v gog)

# ─── CHECK 1: Meeting in next 2 hours ───
if [[ -n "$GOG_BIN" ]] && [[ -n "$GOG_ACCOUNT" ]]; then
  FROM=$(date '+%Y-%m-%dT%H:%M:%S')
  TO=$(hours_from_now 2)
  
  CAL_JSON=""
  set +e
  CAL_JSON=$("$GOG_BIN" calendar events --all --from "$FROM" --to "$TO" --account "$GOG_ACCOUNT" --json 2>>"$LOG_FILE")
  rc=$?
  set -e
  log "calendar rc=$rc"

  if [[ $rc -eq 0 ]] && python3 -c 'import json,sys; json.loads(sys.stdin.read())' <<<"$CAL_JSON" 2>/dev/null; then
    FILTER_EMAIL="${CALENDAR_EMAIL:-$GOG_ACCOUNT}"
    EV_COUNT=$(python3 -c "
import json,sys
try:
    obj=json.loads(sys.stdin.read() or '{}')
    ev=obj.get('events', [])
    email='$FILTER_EMAIL'
    if email:
        print(sum(1 for e in ev if (e.get('calendar') or '').strip()==email))
    else:
        print(len(ev))
except: print(0)
" <<<"$CAL_JSON")
    
    if [[ "$EV_COUNT" != "0" ]]; then
      ALERTS+=("📅 Meeting: $EV_COUNT event(s) in next 2h — NEEDS_MEETING_PREP")
    fi
  fi
fi

# ─── CHECK 2: Commitment due within 2 days ───
COMMITMENTS_FILE="$WORKSPACE/memory/commitments.md"
if [[ -f "$COMMITMENTS_FILE" ]]; then
  TODAY=$(date +%Y-%m-%d)
  OVERDUE=$(python3 -c "
import sys, re
from datetime import datetime, timedelta
today = datetime.strptime('$TODAY', '%Y-%m-%d')
soon = today + timedelta(days=2)
count = 0
with open('$COMMITMENTS_FILE') as f:
    for line in f:
        m = re.search(r'Deadline.*?(\d{4}-\d{2}-\d{2})', line)
        if m:
            d = datetime.strptime(m.group(1), '%Y-%m-%d')
            if d <= soon:
                # Check it's not fulfilled
                count += 1
print(count)
" 2>/dev/null || echo "0")
  
  if [[ "$OVERDUE" != "0" ]]; then
    ALERTS+=("⏰ Commitments: $OVERDUE due within 2 days or overdue")
  fi
fi

# ─── CHECK 3: Stale follow-ups (>7 days, with cooldown) ───
FOLLOWUPS_FILE="$WORKSPACE/memory/follow-ups.md"
STATE_FILE="$WORKSPACE/memory/heartbeat-state.json"
if [[ -f "$FOLLOWUPS_FILE" ]]; then
  STALE_COUNT=$(python3 -c "
import sys, re
from datetime import datetime, timedelta
today = datetime.now()
threshold = today - timedelta(days=7)
count = 0
with open('$FOLLOWUPS_FILE') as f:
    for line in f:
        if 'Active' in line:
            m = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if m:
                d = datetime.strptime(m.group(1), '%Y-%m-%d')
                if d < threshold:
                    count += 1
print(count)
" 2>/dev/null || echo "0")

  if [[ "$STALE_COUNT" != "0" ]]; then
    # Cooldown: only nudge if last nudge was >3 days ago
    SHOULD_NUDGE="yes"
    if [[ -f "$STATE_FILE" ]]; then
      LAST_NUDGE=$(python3 -c "
import json
with open('$STATE_FILE') as f:
    s = json.load(f)
n = s.get('lastChecks',{}).get('followupNudge')
print(n or '')
" 2>/dev/null || echo "")
      
      if [[ -n "$LAST_NUDGE" ]]; then
        DAYS_SINCE=$(date_diff_days "$LAST_NUDGE")
        [[ "$DAYS_SINCE" -lt 3 ]] && SHOULD_NUDGE="no"
      fi
    fi

    if [[ "$SHOULD_NUDGE" == "yes" ]]; then
      ALERTS+=("🔔 Follow-ups: $STALE_COUNT item(s) stale >7 days")
      # Update state
      python3 -c "
import json
from datetime import date
f = '$STATE_FILE'
try:
    with open(f) as fh: s = json.load(fh)
except: s = {}
s.setdefault('lastChecks',{})['followupNudge'] = str(date.today())
s['lastRunAt'] = str(date.today())
with open(f,'w') as fh: json.dump(s, fh, indent=2)
" 2>/dev/null || true
    fi
  fi
fi

# ─── CHECK 4: Weather (only 7-9am or 4-6pm) ───
HOUR=$(date +%H)
if [[ "$HOUR" -ge 7 && "$HOUR" -le 9 ]] || [[ "$HOUR" -ge 16 && "$HOUR" -le 18 ]]; then
  WEATHER=$(curl -s --max-time 5 "wttr.in/Bangkok?format=%C+%t+%h+%p" 2>/dev/null || echo "")
  if [[ -n "$WEATHER" ]]; then
    if echo "$WEATHER" | grep -qiE "rain|thunder|storm|shower"; then
      ALERTS+=("🌧️ Weather: $WEATHER")
    fi
  fi
fi

# ─── CHECK 5: Unread important emails ───
if [[ -n "$GOG_BIN" ]] && [[ -n "$GOG_ACCOUNT" ]] && [[ -n "$GOG_QUERY" ]]; then
  GMAIL_JSON=""
  set +e
  GMAIL_JSON=$("$GOG_BIN" gmail search "$GOG_QUERY" --max 5 --account "$GOG_ACCOUNT" --json 2>>"$LOG_FILE")
  rc=$?
  set -e

  if [[ $rc -eq 0 ]] && python3 -c 'import json,sys; json.loads(sys.stdin.read())' <<<"$GMAIL_JSON" 2>/dev/null; then
    TH_COUNT=$(python3 -c "
import json,sys
obj=json.loads(sys.stdin.read() or '{}')
print(len(obj.get('threads',[])))
" <<<"$GMAIL_JSON" 2>/dev/null || echo "0")
    
    if [[ "$TH_COUNT" != "0" ]]; then
      ALERTS+=("📧 Inbox: $TH_COUNT unread thread(s)")
    fi
  fi
fi

# ─── Output ───
if (( ${#ALERTS[@]} )); then
  printf "%s\n" "${ALERTS[@]}"
else
  echo "HEARTBEAT_OK"
fi
