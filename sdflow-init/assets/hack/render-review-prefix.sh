#!/usr/bin/env bash
# render-review-prefix.sh — 评审 SKILL 镜 dispatch prompt「段① 稳定前缀」渲染器
# （implement-workflow-optimization-2026-08-p4，spec Requirement「评审镜 dispatch prompt
#  按三段组装序构造，稳定前缀为脚本输出原文」；implement-optimize-codex-workflow-quickwins
#  增加 principles 变体、--no-principles、--out-dir）。
#
# 契约：
#   参数  : --layer code-review|spec-review|principles（必填）
#           --no-principles   去掉通则段（仅 code-review|spec-review 可用；与 principles 同用 exit 64）
#           --out-dir <dir>   正文写入 <dir>/prefix-<变体>.md，stdout 改为一行 JSON
#                             {"path": <绝对路径>, "version": "<变体>-<sha12>", "bytes": <整个文件字节数>}
#           任一参数重复、--out-dir 缺值、--no-principles/--out-dir 不带 --layer ⇒ exit 64
#   变体  : spec-review | spec-review-np | code-review | code-review-np | principles
#   文件  : 首行 `<!-- prefix-version: <变体>-<sha12> -->`，sha12 = 其后正文 sha256 前 12 位；
#           同目录临时文件 + rename 写入；同一规则集状态下重复渲染逐字节相同
#   stdout(无 --out-dir): 固定序 = ① 通则区块全文（skill-principles.md）
#                  + ② 内嵌通用契约段（本脚本 heredoc：结构化 findings schema / 引文纪律 /
#                       T103 输出封顶句 / 不问人）
#                  + ③ 该层 base checklist 全文（$RULES_ROOT 经 resolve-workflow.sh 解析）
#            --layer principles 的正文 = 仅通则段，只依赖通则源（不调 resolver、不读 checklist）；
#            --no-principles 的正文 = ② + ③
#   exit 0 : 成功
#   exit 64: 用法错误（缺 --layer / 值非法 / 未知参数 / 上述组合与重复错误）
#            未知参数 stderr 三段 problem/cause/fix（fix = 回运行 checkout 跑 bash setup.sh）
#   exit 2 : 任一源不可达（通则文件缺失 / resolver 缺失或解析失败 / base checklist 缺失）
#            ⇒ fail-loud，stderr 含 problem+cause+fix 三段，stdout 恒为空
#            （MUST NOT 输出半段前缀——全部源校验完毕才开始输出，任何失败必发生在首次输出之前）
#            --out-dir 目录不存在或不可写、或缺 python3，同为 exit 2（三段 stderr），不留半个文件
# env: SDFLOW_HOME（缺省 ~/.sdflow；测试用它重定向，绝不写真实 $HOME，同 resolve-workflow.sh 契约）
set -euo pipefail

SDFLOW_HOME="${SDFLOW_HOME:-$HOME/.sdflow}"
LAYER=""
OUT_DIR=""
NO_PRINCIPLES=0
SEEN_LAYER=0
SEEN_OUT=0

usage_dup() {
  echo "render-review-prefix: ✗ problem=参数重复或缺值「$1」 cause=每个参数只能出现一次且需带值 fix=去掉重复项或补上值后重跑" >&2
  exit 64
}

while [ $# -gt 0 ]; do
  case "$1" in
    --layer)
      [ "$SEEN_LAYER" -eq 0 ] || usage_dup "--layer"
      [ $# -ge 2 ] || usage_dup "--layer"
      SEEN_LAYER=1; LAYER="$2"; shift 2 ;;
    --out-dir)
      [ "$SEEN_OUT" -eq 0 ] || usage_dup "--out-dir"
      [ $# -ge 2 ] || usage_dup "--out-dir"
      # [impl-review-fix] 空串也算缺值：否则下方 -z 判断会静默退回 stdout 模式，调用方拿不到 JSON
      [ -n "$2" ] || usage_dup "--out-dir"
      SEEN_OUT=1; OUT_DIR="$2"; shift 2 ;;
    --no-principles)
      [ "$NO_PRINCIPLES" -eq 0 ] || usage_dup "--no-principles"
      NO_PRINCIPLES=1; shift ;;
    *)
      echo "render-review-prefix: ✗ problem=未知参数「$1」 cause=渲染器版本旧于调用它的 SKILL fix=在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh 更新 ~/.sdflow/hack/" >&2
      exit 64 ;;
  esac
done

case "$LAYER" in
  code-review|spec-review) ;;
  principles)
    if [ "$NO_PRINCIPLES" -eq 1 ]; then
      echo "render-review-prefix: ✗ problem=--layer principles 与 --no-principles 同用 cause=principles 变体正文只有通则段，去掉后为空 fix=去掉 --no-principles" >&2
      exit 64
    fi ;;
  "")
    echo "render-review-prefix: ✗ problem=缺少必填参数 --layer cause=未传值 fix=加 --layer code-review|spec-review|principles" >&2
    exit 64 ;;
  *)
    echo "render-review-prefix: ✗ problem=--layer 值非法「${LAYER}」 cause=仅接受 code-review|spec-review|principles fix=改用合法值重跑" >&2
    exit 64 ;;
esac

# ── 源①：通则区块 ──────────────────────────────────────────────
PRINCIPLES="$SDFLOW_HOME/hack/skill-principles.md"
if [ ! -s "$PRINCIPLES" ]; then
  echo "render-review-prefix: ✗ problem=通则区块源缺失 cause=$PRINCIPLES 不存在或为空 fix=在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh 铺设 ~/.sdflow/hack/" >&2
  exit 2
fi

# ── 源③：base checklist（principles 变体不需要，不调 resolver） ──────────
CHECKLIST=""
if [ "$LAYER" != "principles" ]; then
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
fi

# ── --out-dir 预检：目录须存在且可写（先于任何输出，失败不留文件）──
if [ -n "$OUT_DIR" ] && { [ ! -d "$OUT_DIR" ] || [ ! -w "$OUT_DIR" ]; }; then
  echo "render-review-prefix: ✗ problem=输出目录不存在或不可写 cause=${OUT_DIR} fix=先创建该目录并确认可写（评审入口第零步 mktemp -d 创建 run 目录）" >&2
  exit 2
fi

# [impl-review-fix] --out-dir 模式靠 python3 算 sha256 与写文件；缺它时给三段 stderr，不让 shell 报裸 127
if [ -n "$OUT_DIR" ] && ! command -v python3 >/dev/null 2>&1; then
  echo "render-review-prefix: ✗ problem=缺少 python3 cause=--out-dir 模式用 python3 计算版本哈希并写文件 fix=安装 python3 并确认在 PATH 中后重跑" >&2
  exit 2
fi

# ── 全部源已就位——从这里开始才允许输出，前面任何一步失败都不会走到这行 ──

emit_contract() {
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
}

emit_body() {
  if [ "$LAYER" = "principles" ]; then
    cat "$PRINCIPLES"
    return
  fi
  if [ "$NO_PRINCIPLES" -eq 0 ]; then
    cat "$PRINCIPLES"
  fi
  emit_contract
  cat "$CHECKLIST"
}

if [ -z "$OUT_DIR" ]; then
  emit_body
  exit 0
fi

# 变体名 = layer + (-np)；sha256 / JSON 一律 python3（不依赖 shasum，不手拼 JSON）
VARIANT="$LAYER"
if [ "$NO_PRINCIPLES" -eq 1 ]; then VARIANT="${LAYER}-np"; fi

emit_body | python3 -c '
import hashlib, json, os, sys, tempfile
variant, out_dir = sys.argv[1], sys.argv[2]
body = sys.stdin.buffer.read()
version = "%s-%s" % (variant, hashlib.sha256(body).hexdigest()[:12])
data = ("<!-- prefix-version: %s -->\n" % version).encode("utf-8") + body
out_dir = os.path.abspath(out_dir)
target = os.path.join(out_dir, "prefix-%s.md" % variant)
tmp = None
try:
    fd, tmp = tempfile.mkstemp(prefix=".prefix-", dir=out_dir)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(tmp, target)
    tmp = None
except OSError as e:
    sys.stderr.write("render-review-prefix: ✗ problem=写入前缀文件失败 cause=%s fix=确认输出目录可写且磁盘未满后重跑\n" % e)
    sys.exit(2)
finally:
    if tmp and os.path.exists(tmp):
        os.unlink(tmp)
sys.stdout.write(json.dumps({"path": target, "version": version, "bytes": len(data)}, ensure_ascii=False) + "\n")
' "$VARIANT" "$OUT_DIR"
