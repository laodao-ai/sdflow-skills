#!/usr/bin/env bash
# 历史重放部署门 harness（一次性，非常驻资产 —— design.md DD5）。
# 对 5 份归档评审报告重跑 findings_ref_check.py（DD4 机械前置层），验证部署门红线：
# ③类（协议缺陷/真误杀）= 0。
#
# 用法：从仓根跑 `bash openspec/changes/implement-workflow-optimization-2026-08-p2/impl-reports/replay/run-replay.sh`
# 会在系统 tmp 下建 5 个 detached worktree（各对应一份报告的 reviewed_sha），
# 对 findings/*.json 跑机械引用核，输出 *.refcheck.out.json + *.refcheck.log。
# 二元裁决与三类归因判断在 replay-report.md 中人工完成（脚本只做机械核验这一层）。
#
# 完成后可 `git worktree remove` 清理（脚本末尾附清理命令，默认不自动执行）。

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
REPLAY_DIR="$REPO_ROOT/openspec/changes/implement-workflow-optimization-2026-08-p2/impl-reports/replay"
FINDINGS_DIR="$REPLAY_DIR/findings"
SCRIPT="$REPO_ROOT/sdflow-init/assets/workflow/tools/findings_ref_check.py"
WT_ROOT="${TMPDIR:-/tmp}/sdflow-replay-worktrees"

mkdir -p "$WT_ROOT"

# name -> reviewed_sha（从对应归档报告 frontmatter 提取）
declare -A SHAS=(
  [r1-refactor-roadmap]=8761cf433a1d5352d991d2fe7c7680fa5beb791d
  [r2-autoplan-code]=35cbe388b816f0e5bc37953c4f0b2066f7050e01
  [r3-tickets-frontier]=8e284fd02186539f45ca6456890f840672de1395
  [r4-probe-scan]=5d9afb1a146fea1a2c574503cc9cf1ff28c2ae4f
  [r5-simplify-spec]=efba4a849658a4bd432727970f3e0b47cff89985
)

cd "$REPO_ROOT"
for name in "${!SHAS[@]}"; do
  sha="${SHAS[$name]}"
  wt="$WT_ROOT/$name"
  if [ ! -d "$wt" ]; then
    git worktree add --detach "$wt" "$sha"
  fi
  echo "=== $name (reviewed_sha=$sha) ==="
  python3 "$SCRIPT" --input "$FINDINGS_DIR/$name.json" --root "$wt" \
    > "$FINDINGS_DIR/$name.refcheck.out.json" 2> "$FINDINGS_DIR/$name.refcheck.log"
  cat "$FINDINGS_DIR/$name.refcheck.log"
done

echo
echo "机械核验完成。三态分布汇总见 replay-report.md 第二节。"
echo "清理 worktree（可选）： for n in \"\${!SHAS[@]}\"; do git worktree remove \"$WT_ROOT/\$n\" --force; done"
