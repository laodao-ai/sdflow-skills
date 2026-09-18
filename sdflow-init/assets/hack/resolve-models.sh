#!/usr/bin/env bash
# resolve-models.sh — 宿主判定 + 机队档位解析器（纯 shell，ADR-1；无 Python 依赖）
#
# 用法：MODELS_ENV="$(resolve-models.sh --root <repo_root>)" || exit $?; eval "$MODELS_ENV"
# 导出九变量（export，经 printf %q 编码，可安全 eval）：
#   SDFLOW_HOST          claude | codex | unknown
#   SDFLOW_TIER_STRONG   当前宿主所属机队的强档模型 id（覆盖优先，无覆盖回落机队缺省）
#   SDFLOW_TIER_MID      同上，中档
#   SDFLOW_TIER_LIGHT    同上，弱档
#   SDFLOW_VOICE_RUNNER  另一机队名（claude|codex）；HOST=unknown 时为空——不跑 voice
#   SDFLOW_VOICE_MODEL   voice runner 机队的强档模型 id；HOST=unknown 时为空
#   SDFLOW_EFFORT_STRONG 当前宿主的强档 effort 值（覆盖优先，无覆盖回落缺省）；
#                        unknown 宿主显式空串，MUST NOT 猜测机队
#   SDFLOW_EFFORT_MID    同上，中档
#   SDFLOW_EFFORT_LIGHT  同上，弱档
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
#   YAML 语法交给 mikefarah/yq；Bash 仅负责有界业务键和值校验。
#
# eval 注入加固（GC-6/D5）：覆盖值先过模型 ID 字符集校验（主体仅 [A-Za-z0-9._-]，
#   可带单个尾部 [字母数字] 后缀如 `[1M]`——Claude Code 完整 model id 的上下文窗口标记；
#   拒绝换行/控制字符/shell 元字符 `$ ` ` " ' ; | & ( ) < > 空白等），校验失败即丢弃覆盖、
#   stderr 告警、回落缺省——恶意值永不进入输出。最终输出仍额外经 printf %q 编码
#   （纵深防御，非唯一防线；bracket 经 %q 转义后 eval 不触发 glob 展开）。
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
  echo "resolve-models: ✗ model-tiers.md 不可达（workflow bundle 未安装/未解析，修：回运行 checkout 跑 bash setup.sh）——档位将回落为空并如实告警" >&2
fi

# ────────────────────────────── 3. 机读缺省块读取 ──────────────────────────────
_default_get() {  # $1=fence(model-tier-defaults|effort-tier-defaults) $2="<key.path>"；
                   # stdout=值（trim 后），找不到/无文件 → 空 + return 1
  local fence="$1" key="$2" line in_block=0 marker='```'
  [ -n "$MT_FILE" ] && [ -f "$MT_FILE" ] || return 1
  while IFS= read -r line; do
    line="${line%$'\r'}"
    if [ "$line" = "$marker$fence" ]; then in_block=1; continue; fi
    if [ "$line" = "$marker" ]; then in_block=0; continue; fi
    [ "$in_block" -eq 1 ] || continue
    case "$line" in
      "$key":*)
        line="${line#*:}"
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        printf '%s' "$line"
        return 0
        ;;
    esac
  done < "$MT_FILE"
  return 1
}

# ────────────────────────────── 4. 模型 ID 字符集校验（eval 注入闸门） ──────────────────────────────
_valid_model_id() {  # $1=candidate；主体仅 [A-Za-z0-9._-]、首字符字母数字、非空；
                     # 可带单个尾部 [字母数字] 后缀（如 claude-opus-4-6[1M] 的上下文窗口标记，
                     # 完整 model id 的一部分——与 init.py::_valid_model_id 同一有界口径，D5/D10）。
                     # 输出侧 printf %q 会转义 bracket，eval 时不会被当 glob 展开（纵深防御）。
  local base="$1" suffix=""
  case "$1" in
    *\[*\])
      base="${1%\[*\]}"                          # 最短尾匹配剥离一层 [..]；残余括号留在 base 被拒
      suffix="${1##*\[}"; suffix="${suffix%]}"
      [ -n "$suffix" ] || return 1               # a[] → 拒
      case "$suffix" in *[!A-Za-z0-9]*) return 1 ;; esac
      ;;
  esac
  case "$base" in
    '') return 1 ;;
    *[!A-Za-z0-9._-]*) return 1 ;;
    [!A-Za-z0-9]*) return 1 ;;
    *) return 0 ;;
  esac
}

# ────────────────────── 4b. effort 值域校验（枚举闭集，非字符集——比字符集更严） ──────────────────────
_valid_effort_value() {  # $1=fleet；$2=candidate；按机队枚举校验
  case "$1:$2" in
    claude:low|claude:medium|claude:high|claude:xhigh|claude:max|codex:low|codex:medium|codex:high|codex:xhigh|codex:max|codex:ultra) return 0 ;;
    *) return 1 ;;
  esac
}

# ────────────────────────────── 5. 消费仓 config.yaml 覆盖读取（有界键路径，基准 5） ──────────────────────────────
OV_CLAUDE_STRONG=""; OV_CLAUDE_MID=""; OV_CLAUDE_LIGHT=""; OV_CODEX_STRONG=""; OV_CODEX_MID=""; OV_CODEX_LIGHT=""; OV_FLAT_STRONG=""; OV_FLAT_MID=""; OV_FLAT_LIGHT=""
OV_EFFORT_CLAUDE_STRONG=""; OV_EFFORT_CLAUDE_MID=""; OV_EFFORT_CLAUDE_LIGHT=""; OV_EFFORT_CODEX_STRONG=""; OV_EFFORT_CODEX_MID=""; OV_EFFORT_CODEX_LIGHT=""; YQ_BIN=""
require_yq() {
  [ -n "$YQ_BIN" ] && return 0
  YQ_BIN="${SDFLOW_YQ_BIN:-$(command -v yq 2>/dev/null || true)}"
  if [ -z "$YQ_BIN" ]; then echo "resolve-models: ✗ 请安装 mikefarah/yq（Windows: winget install --id MikeFarah.yq）后重试" >&2; return 1; fi
  local version; version="$("$YQ_BIN" --version 2>&1 || true)"
  case "$version" in
    *mikefarah/yq*) ;;
    *) echo "resolve-models: ✗ 请安装正确的 mikefarah/yq；当前版本输出: ${version:-无}" >&2; YQ_BIN=""; return 1 ;;
  esac
}
read_config_overrides() {
  local config="$ROOT/openspec/config.yaml" values line; local fields=()
  [ -f "$config" ] || return 0; require_yq || return 1
  if ! values="$("$YQ_BIN" -r '
    has("effort-tiers") as $has_effort |
    [
      ((select(tag == "!!map") | .["model-tiers"] | select(tag == "!!map") | .["claude"] | select(tag == "!!map") | .["strong"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["model-tiers"] | select(tag == "!!map") | .["claude"] | select(tag == "!!map") | .["mid"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["model-tiers"] | select(tag == "!!map") | .["claude"] | select(tag == "!!map") | .["light"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["model-tiers"] | select(tag == "!!map") | .["codex"] | select(tag == "!!map") | .["strong"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["model-tiers"] | select(tag == "!!map") | .["codex"] | select(tag == "!!map") | .["mid"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["model-tiers"] | select(tag == "!!map") | .["codex"] | select(tag == "!!map") | .["light"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["model-tiers"] | select(tag == "!!map") | .["strong"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["model-tiers"] | select(tag == "!!map") | .["mid"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["model-tiers"] | select(tag == "!!map") | .["light"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["effort-tiers"] | select(tag == "!!map") | .["claude"] | select(tag == "!!map") | .["strong"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["effort-tiers"] | select(tag == "!!map") | .["claude"] | select(tag == "!!map") | .["mid"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["effort-tiers"] | select(tag == "!!map") | .["claude"] | select(tag == "!!map") | .["light"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["effort-tiers"] | select(tag == "!!map") | .["codex"] | select(tag == "!!map") | .["strong"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["effort-tiers"] | select(tag == "!!map") | .["codex"] | select(tag == "!!map") | .["mid"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ((select(tag == "!!map") | .["effort-tiers"] | select(tag == "!!map") | .["codex"] | select(tag == "!!map") | .["light"] | select(tag == "!!str")) // "" | sub("[[:cntrl:]]"; "!")),
      ($has_effort and (."effort-tiers" | tag != "!!map")),
      "__SDFLOW_YQ_END__"
    ] | .[]
  ' "$config" 2>&1)"; then echo "resolve-models: ✗ yq could not parse $config: $values" >&2; return 1; fi
  while IFS= read -r line || [ -n "$line" ]; do fields+=("$line"); done <<< "$values"
  if [ "${#fields[@]}" -ne 17 ] || [ "${fields[16]}" != "__SDFLOW_YQ_END__" ]; then echo "resolve-models: ✗ yq returned an incomplete override record; 修复 config.yaml" >&2; return 1; fi
  if [ "${fields[15]}" = true ]; then echo "resolve-models: ⚠ effort-tiers 不是 mapping，忽略覆盖、回落缺省" >&2; fi
  OV_CLAUDE_STRONG="${fields[0]}"; OV_CLAUDE_MID="${fields[1]}"; OV_CLAUDE_LIGHT="${fields[2]}"; OV_CODEX_STRONG="${fields[3]}"; OV_CODEX_MID="${fields[4]}"; OV_CODEX_LIGHT="${fields[5]}"; OV_FLAT_STRONG="${fields[6]}"; OV_FLAT_MID="${fields[7]}"; OV_FLAT_LIGHT="${fields[8]}"
  OV_EFFORT_CLAUDE_STRONG="${fields[9]}"; OV_EFFORT_CLAUDE_MID="${fields[10]}"; OV_EFFORT_CLAUDE_LIGHT="${fields[11]}"; OV_EFFORT_CODEX_STRONG="${fields[12]}"; OV_EFFORT_CODEX_MID="${fields[13]}"; OV_EFFORT_CODEX_LIGHT="${fields[14]}"
}
read_config_overrides || exit 1

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
  def="$(_default_get model-tier-defaults "${fleet}.${tier}")"
  if [ -n "$def" ] && _valid_model_id "$def"; then
    printf '%s' "$def"
    return 0
  fi
  echo "resolve-models: ✗ ${fleet}.${tier} 缺省档位不可读（model-tiers.md 缺失/机读块缺失或含非法值），该档位留空" >&2
  return 1
}

# ────────────────────── 6c. effort 档位解析（覆盖 → 缺省，值经枚举域校验；MUST NOT 复用 _resolve_tier） ──────────────────────
# 独立函数——effort 的 unknown 处置（显式空串）与 model tier 的 unknown 回落语义
# （回落 claude canonical 缺省）完全不同，混用会把「不明宿主」误判成「给 Claude 缺省」。
_resolve_effort_tier() {  # $1=fleet(claude|codex) $2=tier(strong|mid|light) → stdout
  local fleet="$1" tier="$2" ov="" def=""
  case "$fleet:$tier" in
    claude:strong) ov="$OV_EFFORT_CLAUDE_STRONG" ;;
    claude:mid)    ov="$OV_EFFORT_CLAUDE_MID" ;;
    claude:light)  ov="$OV_EFFORT_CLAUDE_LIGHT" ;;
    codex:strong)  ov="$OV_EFFORT_CODEX_STRONG" ;;
    codex:mid)     ov="$OV_EFFORT_CODEX_MID" ;;
    codex:light)   ov="$OV_EFFORT_CODEX_LIGHT" ;;
  esac
  if [ -n "$ov" ]; then
    if _valid_effort_value "$fleet" "$ov"; then
      printf '%s' "$ov"
      return 0
    fi
    echo "resolve-models: ⚠ effort-tiers.${fleet}.${tier} 覆盖值不在合法值域，忽略覆盖、回落缺省" >&2
  fi
  def="$(_default_get effort-tier-defaults "${fleet}.${tier}")"
  if [ -n "$def" ] && _valid_effort_value "$fleet" "$def"; then
    printf '%s' "$def"
    return 0
  fi
  echo "resolve-models: ✗ ${fleet}.${tier} effort 缺省档位不可读（model-tiers.md 缺失/机读块缺失或含非法值），该档位留空" >&2
  return 1
}

# effort 三变量：显式初始化为空串。unknown 宿主不猜测机队；`set -u` 下若分支漏赋值会在
# 下方 printf 处中止整个 resolver，故已知宿主分支再覆盖。
EFFORT_STRONG=""
EFFORT_MID=""
EFFORT_LIGHT=""

if [ "$HOST" = "unknown" ]; then
  # ADR-7：判不出宿主 ⇒ 档位回落 canonical 缺省，不套用任何覆盖（既不知道当前机队，不猜哪段覆盖适用）
  TIER_STRONG="$(_resolve_tier claude strong 0)"
  TIER_MID="$(_resolve_tier claude mid 0)"
  TIER_LIGHT="$(_resolve_tier claude light 0)"
  VOICE_RUNNER=""
  VOICE_MODEL=""
  # effort：unknown 宿主留空串，不套用任一机队缺省（判不出宿主就不猜）
else
  TIER_STRONG="$(_resolve_tier "$HOST" strong 1)"
  TIER_MID="$(_resolve_tier "$HOST" mid 1)"
  TIER_LIGHT="$(_resolve_tier "$HOST" light 1)"
  case "$HOST" in
    claude)
      VOICE_RUNNER="codex";  VOICE_MODEL="$(_resolve_tier codex strong 1)"
      EFFORT_STRONG="$(_resolve_effort_tier claude strong)"
      EFFORT_MID="$(_resolve_effort_tier claude mid)"
      EFFORT_LIGHT="$(_resolve_effort_tier claude light)"
      ;;
    codex)
      VOICE_RUNNER="claude"; VOICE_MODEL="$(_resolve_tier claude strong 1)"
      EFFORT_STRONG="$(_resolve_effort_tier codex strong)"
      EFFORT_MID="$(_resolve_effort_tier codex mid)"
      EFFORT_LIGHT="$(_resolve_effort_tier codex light)"
      ;;
  esac
fi

# ────────────────────────────── 7. eval-safe 输出（printf %q 编码，纵深防御） ──────────────────────────────
printf 'export SDFLOW_HOST=%q\n' "$HOST"
printf 'export SDFLOW_TIER_STRONG=%q\n' "$TIER_STRONG"
printf 'export SDFLOW_TIER_MID=%q\n' "$TIER_MID"
printf 'export SDFLOW_TIER_LIGHT=%q\n' "$TIER_LIGHT"
printf 'export SDFLOW_VOICE_RUNNER=%q\n' "$VOICE_RUNNER"
printf 'export SDFLOW_VOICE_MODEL=%q\n' "$VOICE_MODEL"
printf 'export SDFLOW_EFFORT_STRONG=%q\n' "$EFFORT_STRONG"
printf 'export SDFLOW_EFFORT_MID=%q\n' "$EFFORT_MID"
printf 'export SDFLOW_EFFORT_LIGHT=%q\n' "$EFFORT_LIGHT"
