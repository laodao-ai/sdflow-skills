#!/usr/bin/env bash
# resolve-models.sh — 宿主判定 + 机队档位解析器（纯 shell，ADR-1；无 Python 依赖）
#
# 用法：eval "$(resolve-models.sh [--root <repo_root>])"
# 导出六变量（export，经 printf %q 编码，可安全 eval）：
#   SDFLOW_HOST          claude | codex | unknown
#   SDFLOW_TIER_STRONG   当前宿主所属机队的强档模型 id（覆盖优先，无覆盖回落机队缺省）
#   SDFLOW_TIER_MID      同上，中档
#   SDFLOW_TIER_LIGHT    同上，弱档
#   SDFLOW_VOICE_RUNNER  另一机队名（claude|codex）；HOST=unknown 时为空——不跑 voice
#   SDFLOW_VOICE_MODEL   voice runner 机队的强档模型 id；HOST=unknown 时为空
#
# 宿主判定（正信号，spec「宿主判定靠正信号」）：
#   Claude = CLAUDECODE=1；Codex = CODEX_THREAD_ID 非空。
#   两者皆无 / 两者皆有 ⇒ HOST=unknown（fail-loud，stderr 明示），MUST NOT「缺失即另一方」推断。
#
# 档位来源（ADR-1 MUST NOT 内联模型名）：workflow bundle 的 model-tiers.md 机读块
#   `model-tier-defaults`（经 resolve-workflow.sh 定位规则根，同源单一实现，无漂移）。
# 覆盖（ADR-8）：消费仓 openspec/config.yaml 的 model-tiers 段按机队分键
#   `model-tiers.{claude,codex}.{strong,mid,light}`；扁平旧格式
#   `model-tiers.{strong,mid,light}` 兼容读作 Claude 机队覆盖，仅在 Claude 机队生效
#   （Codex 机队 MUST NOT 读扁平覆盖，回落 Codex 机队缺省）。
#   解析按有界键路径（6 条：2 机队×3 档）行锚定提取，MUST NOT 写通用 YAML 解析器（基准 5）。
#
# eval 注入加固（GC-6/D5）：覆盖值先过模型 ID 字符集校验（仅 [A-Za-z0-9._-]，
#   拒绝换行/控制字符/shell 元字符 `$ ` ` " ' ; | & ( ) < > 空白等），校验失败即丢弃覆盖、
#   stderr 告警、回落缺省——恶意值永不进入输出。最终输出仍额外经 printf %q 编码
#   （纵深防御，非唯一防线）。
set -u

ROOT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --root)
      [ $# -ge 2 ] || { echo "resolve-models: --root requires a value" >&2; exit 64; }
      case "$2" in -*) echo "resolve-models: --root requires a value" >&2; exit 64;; esac
      ROOT="$2"; shift 2 ;;
    *) echo "resolve-models: unknown arg: $1" >&2; exit 64 ;;
  esac
done
if [ -z "$ROOT" ]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd 2>/dev/null || true)"
  [ -n "$ROOT" ] || ROOT="."
fi

_rm_dir="$(cd "$(dirname "$0")" && pwd)"

# ────────────────────────────── 1. 宿主判定（正信号） ──────────────────────────────
_claude_sig=0; _codex_sig=0
[ "${CLAUDECODE:-}" = "1" ] && _claude_sig=1
[ -n "${CODEX_THREAD_ID:-}" ] && _codex_sig=1

if [ "$_claude_sig" -eq 1 ] && [ "$_codex_sig" -eq 1 ]; then
  echo "resolve-models: ⚠ 宿主信号冲突（CLAUDECODE=1 且 CODEX_THREAD_ID 非空同时出现）——HOST=unknown，MUST NOT 静默取其一" >&2
  HOST="unknown"
elif [ "$_claude_sig" -eq 1 ]; then
  HOST="claude"
elif [ "$_codex_sig" -eq 1 ]; then
  HOST="codex"
else
  echo "resolve-models: ⚠ 宿主判不出（CLAUDECODE 与 CODEX_THREAD_ID 均未设置）——HOST=unknown，MUST NOT 猜测" >&2
  HOST="unknown"
fi

# ────────────────────── 2. 定位 model-tiers.md（复用 resolve-workflow.sh 规则根解析） ──────────────────────
WORKFLOW_ROOT=""
if [ -x "$_rm_dir/resolve-workflow.sh" ]; then
  WORKFLOW_ROOT="$("$_rm_dir/resolve-workflow.sh" --root "$ROOT" 2>/dev/null || true)"
fi
MT_FILE=""
if [ -n "$WORKFLOW_ROOT" ] && [ -f "$WORKFLOW_ROOT/model-tiers.md" ]; then
  MT_FILE="$WORKFLOW_ROOT/model-tiers.md"
else
  echo "resolve-models: ✗ model-tiers.md 不可达（workflow bundle 未安装/未解析，修：sdflow-init update 或 setup.sh）——档位将回落为空并如实告警" >&2
fi

# ────────────────────────────── 3. 机读缺省块读取 ──────────────────────────────
_default_get() {  # $1 = "<fleet>.<tier>"；stdout=值（trim 后），找不到/无文件 → 空 + return 1
  local key="$1" line
  [ -n "$MT_FILE" ] && [ -f "$MT_FILE" ] || return 1
  while IFS= read -r line; do
    line="${line%$'\r'}"
    case "$line" in
      "$key":*)
        line="${line#*:}"
        line="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        printf '%s' "$line"
        return 0
        ;;
    esac
  done < <(awk '/^```model-tier-defaults$/{f=1;next} /^```$/{f=0} f' "$MT_FILE" 2>/dev/null)
  return 1
}

# ────────────────────────────── 4. 模型 ID 字符集校验（eval 注入闸门） ──────────────────────────────
_valid_model_id() {  # $1=candidate；仅 [A-Za-z0-9._-]、首字符字母数字、非空
  case "$1" in
    '') return 1 ;;
    *[!A-Za-z0-9._-]*) return 1 ;;
    [!A-Za-z0-9]*) return 1 ;;
    *) return 0 ;;
  esac
}

# ────────────────────────────── 5. 消费仓 config.yaml 覆盖读取（有界键路径，基准 5） ──────────────────────────────
OV_CLAUDE_STRONG=""; OV_CLAUDE_MID=""; OV_CLAUDE_LIGHT=""
OV_CODEX_STRONG=""; OV_CODEX_MID=""; OV_CODEX_LIGHT=""
OV_FLAT_STRONG=""; OV_FLAT_MID=""; OV_FLAT_LIGHT=""

_read_config_overrides() {
  local cfg="$ROOT/openspec/config.yaml"
  [ -f "$cfg" ] || return 0
  local in_block=0 fleet="" line key val trimmed
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    line="$(printf '%s' "$line" | sed -e 's/[[:space:]]*$//')"
    if [ "$in_block" -eq 0 ]; then
      [ "$line" = "model-tiers:" ] && { in_block=1; fleet=""; }
      continue
    fi
    # 先剥一层：leading-space trim 后的内容（判空行/注释行，MUST NOT reset fleet——
    # 块内空行/注释是合法的、不该打断 fleet 上下文）。
    trimmed="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//')"
    case "$trimmed" in
      ""|"#"*)
        continue ;;   # 空行 / 任意缩进的注释行 —— 保持 fleet 不变
    esac
    case "$line" in
      "    "*)
        # 4-space 缩进 = 机队子块下的叶子键（须先于 2-space 通配匹配，否则被后者截胡）。
        key="${line%%:*}"; key="$(printf '%s' "$key" | sed -e 's/^[[:space:]]*//')"
        val="${line#*:}"
        val="$(printf '%s' "$val" | sed -e 's/[[:space:]]*#.*$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        if [ -n "$fleet" ]; then
          case "$fleet:$key" in
            claude:strong) OV_CLAUDE_STRONG="$val" ;;
            claude:mid)    OV_CLAUDE_MID="$val" ;;
            claude:light)  OV_CLAUDE_LIGHT="$val" ;;
            codex:strong)  OV_CODEX_STRONG="$val" ;;
            codex:mid)     OV_CODEX_MID="$val" ;;
            codex:light)   OV_CODEX_LIGHT="$val" ;;
          esac
        fi
        continue ;;
      "  "*)
        # 2-space 缩进 = 机队头（claude:/codex:，值须空）或扁平叶子键（strong:/mid:/light:）。
        # 〔Task 6 复评 Critical〕机队头匹配 MUST 容忍尾随注释（剥注释后值为空 = 合法块头），
        # 且**非空尾随内容**（如 `claude: rogue`，fleet 名当标量误用）= 畸形 ⇒ reset fleet=""，
        # 不让 stale fleet 跨该行续命把后续叶子读进错机队（opus 塞进 codex 的根因）。
        # 与 config_lint（init.py::_parse_model_tiers_block）同口径：同输入同 fleet 归属（GC-6/D10）。
        key="${line%%:*}"; key="$(printf '%s' "$key" | sed -e 's/^[[:space:]]*//')"
        val="${line#*:}"
        val="$(printf '%s' "$val" | sed -e 's/[[:space:]]*#.*$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        case "$key" in
          claude|codex)
            if [ -z "$val" ]; then fleet="$key"; else fleet=""; fi ;;   # 空值=合法头；带值=畸形→reset
          strong) OV_FLAT_STRONG="$val"; fleet="" ;;
          mid)    OV_FLAT_MID="$val"; fleet="" ;;
          light)  OV_FLAT_LIGHT="$val"; fleet="" ;;
          *)      fleet="" ;;                                            # 未知 2-space 键 → reset
        esac
        continue ;;
      " "*|"	"*)
        # 其它缩进（3/5+ 空格等奇异缩进）——有界解析不认。reset fleet 防 stale 续命
        # （option ①：遇未识别缩进行 MUST 重置，与上方带值机队头同一防线）。
        fleet=""
        continue ;;
      *)
        in_block=0; fleet=""
        continue ;;
    esac
  done < "$cfg"
}
_read_config_overrides

# ────────────────────────────── 6. 档位解析（覆盖 → 缺省，值经字符集校验） ──────────────────────────────
_resolve_tier() {  # $1=fleet(claude|codex) $2=tier(strong|mid|light) $3=use_override(0|1) → stdout
  local fleet="$1" tier="$2" use_ov="$3" ov="" def=""
  if [ "$use_ov" -eq 1 ]; then
    case "$fleet:$tier" in
      claude:strong) ov="$OV_CLAUDE_STRONG" ;;
      claude:mid)    ov="$OV_CLAUDE_MID" ;;
      claude:light)  ov="$OV_CLAUDE_LIGHT" ;;
      codex:strong)  ov="$OV_CODEX_STRONG" ;;
      codex:mid)     ov="$OV_CODEX_MID" ;;
      codex:light)   ov="$OV_CODEX_LIGHT" ;;
    esac
    # 扁平旧格式仅在 Claude 机队生效（ADR-8）——Codex 机队 MUST NOT 读扁平覆盖
    if [ -z "$ov" ] && [ "$fleet" = "claude" ]; then
      case "$tier" in
        strong) ov="$OV_FLAT_STRONG" ;;
        mid)    ov="$OV_FLAT_MID" ;;
        light)  ov="$OV_FLAT_LIGHT" ;;
      esac
    fi
  fi
  if [ -n "$ov" ]; then
    if _valid_model_id "$ov"; then
      printf '%s' "$ov"
      return 0
    fi
    echo "resolve-models: ⚠ model-tiers.${fleet}.${tier} 覆盖值含非法字符（拒绝，防 eval 注入），忽略覆盖、回落缺省" >&2
  fi
  def="$(_default_get "${fleet}.${tier}")"
  if [ -n "$def" ] && _valid_model_id "$def"; then
    printf '%s' "$def"
    return 0
  fi
  echo "resolve-models: ✗ ${fleet}.${tier} 缺省档位不可读（model-tiers.md 缺失/机读块缺失或含非法值），该档位留空" >&2
  return 1
}

if [ "$HOST" = "unknown" ]; then
  # ADR-7：判不出宿主 ⇒ 档位回落 canonical 缺省，不套用任何覆盖（既不知道当前机队，不猜哪段覆盖适用）
  TIER_STRONG="$(_resolve_tier claude strong 0)"
  TIER_MID="$(_resolve_tier claude mid 0)"
  TIER_LIGHT="$(_resolve_tier claude light 0)"
  VOICE_RUNNER=""
  VOICE_MODEL=""
else
  TIER_STRONG="$(_resolve_tier "$HOST" strong 1)"
  TIER_MID="$(_resolve_tier "$HOST" mid 1)"
  TIER_LIGHT="$(_resolve_tier "$HOST" light 1)"
  case "$HOST" in
    claude) VOICE_RUNNER="codex";  VOICE_MODEL="$(_resolve_tier codex strong 1)" ;;
    codex)  VOICE_RUNNER="claude"; VOICE_MODEL="$(_resolve_tier claude strong 1)" ;;
  esac
fi

# ────────────────────────────── 7. eval-safe 输出（printf %q 编码，纵深防御） ──────────────────────────────
printf 'export SDFLOW_HOST=%q\n' "$HOST"
printf 'export SDFLOW_TIER_STRONG=%q\n' "$TIER_STRONG"
printf 'export SDFLOW_TIER_MID=%q\n' "$TIER_MID"
printf 'export SDFLOW_TIER_LIGHT=%q\n' "$TIER_LIGHT"
printf 'export SDFLOW_VOICE_RUNNER=%q\n' "$VOICE_RUNNER"
printf 'export SDFLOW_VOICE_MODEL=%q\n' "$VOICE_MODEL"
