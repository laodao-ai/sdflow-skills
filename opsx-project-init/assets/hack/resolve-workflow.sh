#!/usr/bin/env bash
# resolve-workflow.sh — workflow 规则根解析器（三步链的确定性执行体）
# 契约（minimize-repo-footprint R-MRF-2 / adr-0006 机队锚定：机械协议脚本化，skill 只调用）：
#   stdout : 规则根路径（唯一 stdout 输出）
#   exit 0 : 解析成功（本地 pin 或全局 canonical）
#   exit 2 : 全局 bundle 不可达/不完整 → 调用方显式降级通用评审 + 转发本脚本 stderr 告警
#   exit 64: 用法错误
# env: SDFLOW_HOME（缺省 ~/.sdflow；测试用它重定向，绝不写真实 $HOME）
set -euo pipefail

SDFLOW_HOME="${SDFLOW_HOME:-$HOME/.sdflow}"
ROOT=""
EXPLAIN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --root)    ROOT="${2:-}"; shift 2 ;;
    --explain) EXPLAIN=1; shift ;;
    *) echo "resolve-workflow: unknown arg: $1" >&2; exit 64 ;;
  esac
done

if [ -z "$ROOT" ]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

explain() {
  if [ "$EXPLAIN" -eq 1 ]; then echo "resolve-workflow: source=$1 path=$2" >&2; fi
}

# 步1：查本地"规则文件本体"（any-of 即 pin）。不查 openspec/workflow/ 目录——tools/ 使其恒存在。
LOCAL="$ROOT/openspec/workflow"
has_wf=0; has_spec=0; has_code=0
[ -f "$LOCAL/workflow.md" ] && has_wf=1
[ -d "$LOCAL/spec-checklists" ] && has_spec=1
[ -d "$LOCAL/code-checklists" ] && has_code=1
total=$((has_wf + has_spec + has_code))
if [ "$total" -gt 0 ]; then
  if [ "$total" -lt 3 ]; then
    echo "resolve-workflow: ⚠ 本仓规则副本部分残留（workflow.md=$has_wf spec-checklists=$has_spec code-checklists=$has_code）——按 pin 处理；想跟全局请删净、想 pin 请补齐" >&2
  fi
  explain "local-pin" "$LOCAL"
  echo "$LOCAL"
  exit 0
fi

# 步2：全局 canonical——试目录（Unix 软链透明命中）→ 否则读指针文件（Windows）。平台判断在此，skill 不判平台。
CANON=""
if [ -d "$SDFLOW_HOME/workflow" ]; then
  CANON="$SDFLOW_HOME/workflow"
elif [ -f "$SDFLOW_HOME/workflow-path" ]; then
  CANON="$(head -n1 "$SDFLOW_HOME/workflow-path" | tr -d '\r' | sed -e 's/[[:space:]]*$//')"
fi

sane() {  # 最小健全性检查：防 pull 半坏态静默广播（spec-review D2）
  [ -n "$1" ] && [ -s "$1/workflow.md" ] && [ -d "$1/spec-checklists" ] && [ -d "$1/code-checklists" ]
}

if sane "$CANON"; then
  explain "global-canonical" "$CANON"
  echo "$CANON"
  exit 0
fi

# 步3：显式降级（反静默守卫）——绝不静默当"本项目无此评审层"
echo "resolve-workflow: ✗ 全局 workflow bundle 不可达或不完整（SDFLOW_HOME=$SDFLOW_HOME）。skill 应显式降级为通用评审并告警。修复：在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh" >&2
exit 2
