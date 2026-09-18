#!/usr/bin/env bash
# resolve-workflow.sh — workflow 规则根解析器（两步链的确定性执行体，fix-probe-scan-precision
# 起本地 pin 步已删——规则解析只剩「全局 canonical → 显式降级」）
# 契约（minimize-repo-footprint R-MRF-2 / adr-0006 机队锚定：机械协议脚本化，skill 只调用）：
#   stdout : 规则根路径（唯一 stdout 输出）
#   exit 0 : 解析成功（全局 canonical）
#   exit 2 : 全局 bundle 不可达/不完整 → 调用方显式降级通用评审 + 转发本脚本 stderr 告警
#   exit 64: 用法错误
# env: SDFLOW_HOME（缺省 ~/.sdflow；测试用它重定向，绝不写真实 $HOME）
set -euo pipefail

SDFLOW_HOME="${SDFLOW_HOME:-$HOME/.sdflow}"
ROOT=""
EXPLAIN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --root)    [ $# -ge 2 ] || { echo "resolve-workflow: --root requires a value" >&2; exit 64; }
               case "$2" in -*) echo "resolve-workflow: --root requires a value" >&2; exit 64;; esac
               ROOT="$2"; shift 2 ;;
    --explain) EXPLAIN=1; shift ;;
    *) echo "resolve-workflow: unknown arg: $1" >&2; exit 64 ;;
  esac
done

if [ -z "$ROOT" ]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd 2>/dev/null || true)"
  if [ -z "$ROOT" ]; then
    echo "resolve-workflow: ✗ 无法确定仓根（cwd 可能已被删除），请用 --root 显式指定" >&2
    exit 64
  fi
fi

explain() {
  if [ "$EXPLAIN" -eq 1 ]; then echo "resolve-workflow: source=$1 path=$2" >&2; fi
}

# 步1：全局 canonical——试目录（Unix 软链透明命中）→ 否则读指针文件（Windows）。平台判断在此，skill 不判平台。
# 不查仓内 openspec/workflow/：本地副本（含仓内放全套规则副本）一律忽略，规则解析恒指全局 canonical。
CANON=""
case "$SDFLOW_HOME" in
  /*)
    if [ -d "$SDFLOW_HOME/workflow" ]; then
      CANON="$SDFLOW_HOME/workflow"
    elif [ -f "$SDFLOW_HOME/workflow-path" ]; then
      # 读失败(权限/不存在)→CANON 空→sane 判失败→步2显式降级
      CANON="$( (head -n1 "$SDFLOW_HOME/workflow-path" | tr -d '\r' | sed -e 's/[[:space:]]*$//') 2>/dev/null || true)"
    fi
    ;;
  *)
    echo "resolve-workflow: ⚠ SDFLOW_HOME 非绝对路径（${SDFLOW_HOME}），忽略全局 canonical" >&2
    ;;
esac

sane() {  # 最小健全性检查：防 pull 半坏态静默广播（spec-review D2）；两个清单目录须非空（CR-F1）；
  # tools/ 目录须非空 + lens-metric-contract.md 非空（fix-probe-scan-precision 扩面，形状级判据——
  # 只查目录/文件存在且非空，MUST NOT 枚举具体 .py 成员，防守卫里复活补丁螺旋）
  [ -n "$1" ] && [ -s "$1/workflow.md" ] \
    && [ -d "$1/spec-checklists" ] && [ -n "$(ls -A "$1/spec-checklists" 2>/dev/null)" ] \
    && [ -d "$1/code-checklists" ] && [ -n "$(ls -A "$1/code-checklists" 2>/dev/null)" ] \
    && [ -d "$1/tools" ] && [ -n "$(ls -A "$1/tools" 2>/dev/null)" ] \
    && [ -s "$1/lens-metric-contract.md" ]
}

if sane "$CANON"; then
  explain "global-canonical" "$CANON"
  echo "$CANON"
  exit 0
fi

# 步2：显式降级（反静默守卫）——绝不静默当"本项目无此评审层"
echo "resolve-workflow: ✗ 全局 workflow bundle 不可达或不完整（SDFLOW_HOME=${SDFLOW_HOME}）。skill 应显式降级为通用评审并告警。修复：在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh" >&2
exit 2
