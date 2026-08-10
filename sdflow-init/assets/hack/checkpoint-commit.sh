#!/usr/bin/env bash
# checkpoint-commit.sh —— 工作流「过场提交」：git add -A + 固定 Conventional message。
#
# 由 workflow step prompt / 编排 skill 在「某逻辑步骤完成」时调用，非交互、自动过场。
# 区别于交互式 /commit-message（那个是最终提交，human-in-loop）。见 design.md §5.2。
#
# 焊死本机三坑（design.md §5.2）：
#   ① commit message 禁 `\` 续行 + heredoc（本机 shell 会损坏 message）→ 只用单行 -m，参数化拼接
#   ② core.fileMode=false：过场提交只记内容变更，不主动 --chmod、不 churn 权限位
#   ③ CRLF：本脚本纯 add + commit，不碰行尾（交给仓库 .gitattributes / gofmt 各自负责）
#
# 用法：
#   checkpoint-commit.sh <step> [描述]
# 例：
#   checkpoint-commit.sh ff "生成 proposal/design/specs/tasks"
#     → commit: "checkpoint(ff): 生成 proposal/design/specs/tasks"
#   checkpoint-commit.sh spec-review
#     → commit: "checkpoint(spec-review)"
#
# 语义：无变更时静默跳过（过场提交不该因空提交中断流程）。

set -euo pipefail

if [ "$#" -lt 1 ] || [ -z "${1:-}" ]; then
  echo "用法: checkpoint-commit.sh <step> [描述]" >&2
  exit 2
fi

step="$1"
desc="${2:-}"

# 必须在 git 仓库内
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "checkpoint($step): 非 git 仓库，中止" >&2
  exit 2
fi

# 无任何变更（含未跟踪文件）则跳过——git status --porcelain 空 = 干净
if [ -z "$(git status --porcelain)" ]; then
  echo "checkpoint($step): 无变更，跳过"
  exit 0
fi

# token 快照采集（design.md D1）：只在「本次确定要提交」时机采，接线位置钉死在判空 gate 之后、
# git add -A 之前——保持干净树静默跳过、不建 commit 的既有语义逐字节不变。`|| true`：失败/缺席/
# 挂起（helper 内部自设超时）一律不得影响 checkpoint 主功能。
python3 ~/.sdflow/hack/token_snapshot.py --step "$step" || true

# 拼 message：坑① 决定只用单行 subject（无 `\` 续行、无 heredoc、无 body 多行拼接）
if [ -n "$desc" ]; then
  subject="checkpoint($step): $desc"
else
  subject="checkpoint($step)"
fi

git add -A
git commit -m "$subject"
echo "✓ $subject"
