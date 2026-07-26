#!/bin/bash
set -u
LANE="$1"; CD="$2"
SB="/private/tmp/claude-501/-Users-cheneyzhao-Documents-04-sdflow-skills/49e41057-82a1-4963-9640-8a1b18500424/scratchpad/ab"
sed "s|CHANGE_DIR_PLACEHOLDER|$CD|" "$SB/prompts/review.txt" > "$SB/prompts/review-$LANE.txt"
cd "$SB/$LANE" || exit 1
timeout 3000 claude -p --model sonnet --output-format json --permission-mode acceptEdits \
  --allowedTools Bash Read < "$SB/prompts/review-$LANE.txt" > "$SB/logs/$LANE/review.json" 2>"$SB/logs/$LANE/review.err"
