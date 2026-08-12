#!/usr/bin/env bash
# render-review-prefix.sh — 评审 SKILL 镜 dispatch prompt「段① 稳定前缀」渲染器
# （implement-workflow-optimization-2026-08-p4，spec Requirement「评审镜 dispatch prompt
#  按三段组装序构造，稳定前缀为脚本输出原文」）。
#
# 契约：
#   参数  : --layer code-review|spec-review（必填）
#   stdout: 固定序 = ① 通则区块全文（skill-principles.md）
#                  + ② 内嵌通用契约段（本脚本 heredoc：结构化 findings schema / 引文纪律 /
#                       T103 输出封顶句 / 不问人）
#                  + ③ 该层 base checklist 全文（$RULES_ROOT 经 resolve-workflow.sh 解析）
#   exit 0 : 成功
#   exit 64: 用法错误（缺 --layer / 值非法 / 未知参数）
#   exit 2 : 任一源不可达（通则文件缺失 / resolver 缺失或解析失败 / base checklist 缺失）
#            ⇒ fail-loud，stderr 含 problem+cause+fix 三段，stdout 恒为空
#            （MUST NOT 输出半段前缀——全部源校验完毕才开始 cat，任何失败必发生在首次输出之前）
# env: SDFLOW_HOME（缺省 ~/.sdflow；测试用它重定向，绝不写真实 $HOME，同 resolve-workflow.sh 契约）
set -euo pipefail

SDFLOW_HOME="${SDFLOW_HOME:-$HOME/.sdflow}"
LAYER=""

while [ $# -gt 0 ]; do
  case "$1" in
    --layer)
      [ $# -ge 2 ] || { echo "render-review-prefix: ✗ --layer requires a value" >&2; exit 64; }
      LAYER="$2"; shift 2 ;;
    *)
      echo "render-review-prefix: ✗ unknown arg: $1" >&2; exit 64 ;;
  esac
done

case "$LAYER" in
  code-review|spec-review) ;;
  "")
    echo "render-review-prefix: ✗ problem=缺少必填参数 --layer cause=未传值 fix=加 --layer code-review 或 --layer spec-review" >&2
    exit 64 ;;
  *)
    echo "render-review-prefix: ✗ problem=--layer 值非法「${LAYER}」 cause=仅接受 code-review|spec-review fix=改用合法值重跑" >&2
    exit 64 ;;
esac

# ── 源①：通则区块 ──────────────────────────────────────────────
PRINCIPLES="$SDFLOW_HOME/hack/skill-principles.md"
if [ ! -s "$PRINCIPLES" ]; then
  echo "render-review-prefix: ✗ problem=通则区块源缺失 cause=$PRINCIPLES 不存在或为空 fix=在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh 铺设 ~/.sdflow/hack/" >&2
  exit 2
fi

# ── 源③ 的解析器：resolve-workflow.sh（同布署链，与本脚本同目录部署） ──────
RESOLVER="$SDFLOW_HOME/hack/resolve-workflow.sh"
if [ ! -x "$RESOLVER" ]; then
  echo "render-review-prefix: ✗ problem=resolve-workflow.sh 缺失或不可执行 cause=$RESOLVER fix=在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh 铺设 ~/.sdflow/hack/" >&2
  exit 2
fi

if ! RULES_ROOT="$(SDFLOW_HOME="$SDFLOW_HOME" "$RESOLVER")"; then
  echo "render-review-prefix: ✗ problem=resolve-workflow.sh 解析失败 cause=全局 workflow bundle 不可达或不完整（SDFLOW_HOME=${SDFLOW_HOME}，详见上方 resolve-workflow.sh 自身 stderr） fix=在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh" >&2
  exit 2
fi

case "$LAYER" in
  code-review) CHECKLIST="$RULES_ROOT/code-checklists/code-review-base.md" ;;
  spec-review) CHECKLIST="$RULES_ROOT/spec-checklists/spec-quality-base.md" ;;
esac

if [ ! -s "$CHECKLIST" ]; then
  echo "render-review-prefix: ✗ problem=base checklist 缺失（layer=${LAYER}） cause=${CHECKLIST} 不存在或为空 fix=检查 sdflow-init/assets/workflow bundle 是否完整，或在消费仓重跑 sdflow-init update" >&2
  exit 2
fi

# ── 全部源已就位——从这里开始才允许输出，前面任何一步失败都不会走到这行 ──

cat "$PRINCIPLES"

cat <<'COMMON_REVIEW_CONTRACT'

## 评审子代理通用契约（render-review-prefix.sh 内嵌 · 两评审层共用 · 唯一源在本脚本）

### 结构化 findings schema

每条 finding MUST 以结构化字段返回，MUST NOT 只写散文结论：

- `id`：本条 finding 的唯一标识（镜内自增即可）
- `file` / `line`：触发该 finding 的具体代码/文档位置
- `quote`：该 file:line 处原文引用；无法给单行引文的非局部 finding（缺失校验 /
  跨文件数据流 / 时序竞态 / absence 类）改用 `evidence_pack`（多处 file:line 逐字
  引文，或「应在而不在」的缺失对照）
- `severity`：严重度（用于报告排序与截优先）
- `suggestion`：具体可执行的修复建议
- `confidence`：自报置信（0–100，仅供报告排序，不作裁决判据）

### 引文纪律

每条 finding 携带的 `quote` 或 `evidence_pack` MUST 可复核定位（路径存在 / file:line
界内 / 引文命中该行）。两者皆无的 finding 在机械引用核会被判 `fail` 并直接裁掉，
不进二元裁决——**先证伪，引用必须真打开过**，不得凭记忆转述代码内容。

### 输出封顶

回传目标 ≤2k token，超出按严重度截优先（先保留高严重度 finding，低严重度可省略
细节仅留一句摘要）。

### 不问人

**不要 AskUserQuestion。** 撞到「≥2 方案 / 核验不了的事实」不中途打断，把决策点
或不确定项写进结构化 findings（供上游合并/裁决/登记），继续跑完并返回结果。
COMMON_REVIEW_CONTRACT

cat "$CHECKLIST"
