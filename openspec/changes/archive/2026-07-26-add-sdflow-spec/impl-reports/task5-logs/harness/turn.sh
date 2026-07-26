#!/bin/bash
# usage: turn.sh <lane> <sid|NEW> <prompt-file>
# runs one claude -p turn in the lane's sandbox clone, logs full JSON, prints result+sid+cost
set -u
LANE="$1"; SID="$2"; PF="$3"
SB="/private/tmp/claude-501/-Users-cheneyzhao-Documents-04-sdflow-skills/49e41057-82a1-4963-9640-8a1b18500424/scratchpad/ab"
LOG="$SB/logs/$LANE"; mkdir -p "$LOG"
N=$(ls "$LOG" 2>/dev/null | grep -c '^turn.*\.json' || true)
N=$((N+1))
TAG="turn$(printf %02d "$N")"
OUT="$LOG/$TAG.json"
cd "$SB/$LANE" || exit 1
if [ "$SID" = "NEW" ]; then
  timeout 3000 claude -p --model opus --output-format json --permission-mode acceptEdits \
    --allowedTools Bash Read Write Edit Agent WebFetch WebSearch TodoWrite < "$PF" > "$OUT" 2>"$LOG/$TAG.err"
else
  timeout 3000 claude -p --model opus --output-format json --permission-mode acceptEdits -r "$SID" \
    --allowedTools Bash Read Write Edit Agent WebFetch WebSearch TodoWrite < "$PF" > "$OUT" 2>"$LOG/$TAG.err"
fi
RC=$?
/usr/bin/python3 - "$OUT" "$RC" <<'PY'
import json,sys
p,rc=sys.argv[1],sys.argv[2]
try:
    d=json.load(open(p))
except Exception as e:
    print("PARSE_FAIL rc=%s %s"%(rc,e)); print(open(p).read()[:3000]); sys.exit(0)
print(d.get("result",""))
print("\n===META=== rc=%s sid=%s cost=%.4f dur_ms=%s turns=%s err=%s denials=%s"%(
    rc,d.get("session_id"),d.get("total_cost_usd",0),d.get("duration_ms"),d.get("num_turns"),d.get("is_error"),d.get("permission_denials")))
u=d.get("usage",{})
print("usage in=%s out=%s cache_create=%s cache_read=%s"%(
    u.get("input_tokens"),u.get("output_tokens"),u.get("cache_creation_input_tokens"),u.get("cache_read_input_tokens")))
for m,v in d.get("modelUsage",{}).items():
    print("  model %s: in=%s out=%s cr=%s cc=%s cost=%.4f"%(m,v.get("inputTokens"),v.get("outputTokens"),v.get("cacheReadInputTokens"),v.get("cacheCreationInputTokens"),v.get("costUSD",0)))
PY
