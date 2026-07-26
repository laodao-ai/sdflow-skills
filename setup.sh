#!/usr/bin/env bash
# sdflow-skills setup — install/update skills into BOTH:
#   - Claude  ~/.claude/skills/
#   - Codex   ~/.codex/skills/
# Idempotent. Unix: absolute symlink (layout-independent). Windows: copy + marker.
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_NAME="$(basename "$REPO_DIR")"

# Install destinations (explicit + absolute → independent of where the repo lives)
TARGET_DIRS=("$HOME/.claude/skills" "$HOME/.codex/skills")

# Platform detection
IS_WINDOWS=0
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*|Windows_NT) IS_WINDOWS=1 ;;
esac

# Counters (entries formatted "skill @ dest")
installed=()
skipped=()
cleaned=()

# marker 兼容收窄（D5）：.sdflow-skills 一律自属；.laodao-skills 仅限我方名单（防误伤 laodao misc 拷贝）
OUR_LEGACY_NAMES=" opsx-project-init opsx-done opsx-maintain opsx-roadmap-planner spec-review impl-review buglist-recorder todolist-recorder issues-recorder sdflow-init sdflow-done sdflow-maintain sdflow-roadmap sdflow-spec-review sdflow-code-review sdflow-buglist sdflow-todolist sdflow-issues embedded-test-sop openspec-upgrade sdflow-upgrade "
is_our_marker_copy() {  # $1 = 目录路径
  local name="$(basename "$1")"
  [ -f "$1/.sdflow-skills" ] && return 0
  [ -f "$1/.laodao-skills" ] && case "$OUR_LEGACY_NAMES" in *" $name "*) return 0 ;; esac
  return 1
}

# ─── Install all skills into one destination ─────────────────
install_into() {
  local dest="$1"
  mkdir -p "$dest"
  for skill_dir in "$REPO_DIR"/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    local skill_name target
    skill_name="$(basename "$skill_dir")"
    target="$dest/$skill_name"

    if [ "$IS_WINDOWS" -eq 1 ]; then
      # Windows: copy + marker file
      if [ -d "$target" ] && [ ! -L "$target" ] && ! is_our_marker_copy "$target"; then
        skipped+=("$skill_name @ $dest")
        continue
      fi
      if [ -d "$target" ] && is_our_marker_copy "$target"; then
        rm -rf "$target"
      fi
      cp -r "$skill_dir" "$target"
      git -C "$REPO_DIR" rev-parse HEAD 2>/dev/null > "$target/.sdflow-skills" || echo "unknown" > "$target/.sdflow-skills"
      installed+=("$skill_name @ $dest")
    else
      # Unix: absolute symlink. Only ever replace symlinks or our own marker
      # copies — never clobber a real directory we don't own (e.g. another
      # tool's skill of the same name).
      if [ -e "$target" ] && [ ! -L "$target" ]; then
        if is_our_marker_copy "$target"; then
          rm -rf "$target"
        else
          skipped+=("$skill_name @ $dest")
          continue
        fi
      fi
      ln -snf "$REPO_DIR/$skill_name" "$target"
      installed+=("$skill_name @ $dest")
    fi
  done
}

# ─── Remove our orphaned links (source skill deleted) ────────
cleanup_orphans() {
  local dest="$1"
  [ -d "$dest" ] || return 0
  # find 枚举一切一级条目（含悬空软链）——尾斜杠 glob "$dest"/*/ 在 POSIX 语义下
  # 匹配不到 dangling 软链（因为它不再解析为目录），孤儿清理对真悬空链是死代码。
  local entry
  while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    local entry_name="$(basename "$entry")"
    [ "$entry_name" = "$REPO_NAME" ] && continue

    local is_ours=0
    # Symlink pointing into our repo (absolute or relative form)
    if [ -L "$dest/$entry_name" ]; then
      local link_dest
      link_dest="$(readlink "$dest/$entry_name" 2>/dev/null || true)"
      case "$link_dest" in
        "$REPO_NAME"/*|*/"$REPO_NAME"/*) is_ours=1 ;;
      esac
    fi
    # Marker file (Windows copies)
    is_our_marker_copy "$entry" && is_ours=1

    # Ours, but the link now dangles (source skill removed) → clean up.
    # Use a resolve check (-e follows the symlink) so VALID links are kept,
    # including nested sub-skills like config-setup/config-plugins whose source
    # is not a top-level $REPO_DIR/<name> dir.
    if [ "$is_ours" -eq 1 ]; then
      local gone=0
      if [ -L "$dest/$entry_name" ]; then
        [ ! -e "$dest/$entry_name" ] && gone=1          # dangling symlink
      elif [ ! -d "$REPO_DIR/$entry_name" ]; then
        gone=1                                          # Windows marker copy, source gone
      fi
      if [ "$gone" -eq 1 ]; then
        rm -rf "$dest/$entry_name"
        cleaned+=("$entry_name @ $dest")
      fi
    fi
  done < <(find "$dest" -mindepth 1 -maxdepth 1)
}

# ─── Agent definitions → ~/.claude/agents/ (D11) ─────────────
# 【为什么是新写的一份，不能沿用 install_into】
#   ① install_into 只枚举【顶层目录】且必须含 SKILL.md（上面第 38-39 行），
#      而 agent 定义是 sdflow-spec/agents/ 下的【散装 .md】—— 进不了那个循环。
#   ② is_our_marker_copy() 的判据是 `[ -f "$1/.sdflow-skills" ]`：对一个【文件】做
#      目录拼接，恒 false —— 是路径谬误，不是「保守地判成不是我们的」。
#   ③ cleanup_orphans 的 `[ ! -d "$REPO_DIR/$entry_name" ]` 对 `xxx.md` 恒真。
#
# 【所有权守卫比 skills 那边更严，不是复用】
#   install_into 对任何同名 symlink 无条件 `ln -snf` 覆盖；install_sdflow 处理
#   $sdflow/workflow 时 readlink 的结果也只用于【打印告警】、不作判据。
#   这里必须 readlink 确认指向本仓才接管 —— 因为 ~/.claude/agents/ 是【全局命名空间】，
#   任何插件或别的工具都可能在里面放同名定义，覆盖掉就是数据丢失。
install_agents() {
  local src_dir="$REPO_DIR/sdflow-spec/agents"
  local dest="$HOME/.claude/agents"
  [ -d "$src_dir" ] || return 0

  if [ "$IS_WINDOWS" -eq 1 ]; then
    # 散装 .md 【没有 marker 落点】——marker 是「目录里放一个标记文件」，对单文件做不出来。
    # ⇒ Windows 下不铺 agents。/sdflow-spec 在该宿主走主 session 亲查/亲写路径（D3 的降级方向）。
    # MUST NOT 在这里写「copy + 所有权守卫」——那是做不出来的东西。
    skipped+=("agents @ $dest — Windows：散装 .md 无 marker 落点，不铺设；/sdflow-spec 走主 session 亲查/亲写")
    return 0
  fi

  # 落点被占为普通文件/不可写 ⇒ mkdir 失败。set -e 下那会【中止整个 setup.sh】——
  # 而本函数在 install_sdflow 之前，连 ~/.sdflow/ 的 canonical 与 hack 脚本都跟着装不上，
  # 用户只看到一行裸 `mkdir:` 错误。与本文件既定取向（外来同名条目 → skip + 汇总报告）一致：
  # 这里也降级为 skip。
  mkdir -p "$dest" 2>/dev/null || {
    skipped+=("agents @ $dest — 落点建不出来（被占为普通文件？权限？），未铺设")
    return 0
  }

  local f name target link
  for f in "$src_dir"/*.md; do
    [ -f "$f" ] || continue
    name="$(basename "$f")"
    target="$dest/$name"

    # -e 对悬空软链为 false，故必须 `-e || -L` 才能覆盖「存在」的全部形态
    if [ -e "$target" ] || [ -L "$target" ]; then
      if [ ! -L "$target" ]; then
        skipped+=("agents/$name @ $dest — 已存在真实文件，非本仓软链，未接管")
        continue
      fi
      link="$(readlink "$target" 2>/dev/null || true)"
      # 【自属判据 = 位置无关的路径后缀，不是当前 checkout 的前缀】
      #   前缀判据（"$REPO_DIR"/*）只认【当前】checkout ⇒ 从另一个 checkout 跑 setup 时，
      #   既有的自属链既不接管、也不进孤儿清理 ⇒ 名册裂脑（一条来自 A、其余来自 B），
      #   而 CLAUDE.md 的 dev/runtime 纪律明写「测完在运行 checkout 重跑 setup【还原】」
      #   「回滚 = 运行 checkout + 重跑 setup.sh」—— 前缀判据令这两条对 agent 定义静默失效。
      #   cleanup_orphans 的 */"$REPO_NAME"/* 子串 idiom 在这里也不够：两个 checkout 的
      #   目录名本就不同（~/.skills/sdflow-skills vs 04-sdflow-skills）。
      #   ∴ 判据取「链指向某个 sdflow-spec/agents/ 下的同名文件」——无第三方会用这个路径形状。
      #   ⚠️ MUST NOT 放宽成「是软链就覆盖」：~/.claude/agents/ 是全局命名空间，
      #   覆盖别人的同名定义就是数据丢失（上面 install_into 的同一条纪律）。
      case "$link" in
        */sdflow-spec/agents/"$name") : ;;   # 本仓（任一 checkout）装出去的，可以接管
        *) skipped+=("agents/$name @ $dest — 软链指向 ${link:-<读不到>}（非本仓），未接管"); continue ;;
      esac
    fi

    ln -snf "$f" "$target"
    installed+=("agents/$name @ $dest")
  done

  # 孤儿清理：本仓装出去的软链，源 .md 已删 ⇒ 悬空 ⇒ 清掉。
  # 用 find 枚举（而非 glob）：尾斜杠/普通 glob 在 POSIX 语义下匹配不到 dangling 软链。
  #
  # 【自属判据 = 与接管判据同一条**路径形状**，但**名字维度必然更宽**（这是设计，不是疏忽）】
  #   接管只对 `$src_dir/*.md` 里现存的名字（循环源就是它）；清理必须覆盖**已从本仓删掉的
  #   名字**——那正是「孤儿」的定义。把清理也限定成「名字 ∈ $src_dir」会击穿它的主用途：
  #   删掉一个 agent 定义后，它的名字恰恰已不在 $src_dir 里，那条悬空链将永远留着。
  #   （实测：加这条限定 ⇒ test_dangling_link_of_a_deleted_source_is_cleaned 当场红。）
  #   反过来判据也不能更窄到只认当前 checkout：指向另一 checkout 且源已删的链会永远留着
  #   ——既不接管也不清理，正是名册裂脑的另一半。
  #
  # 【承认的代价】一条指向 `<任意路径>/sdflow-spec/agents/<任意名>.md` 的**悬空**链会被清掉，
  #   即使那个名字从不属于本仓。判为可接受：① 该路径形状是本仓专有布局；② 只删悬空链——
  #   目标已不存在，零数据丢失，与 CLAUDE.md「绝不覆盖非本仓库拥有的同名目录」守的「真实内容」
  #   不是同一物（真实文件与**有效**外来软链一律不碰，见上面的接管守卫与 cleaned 用例）。
  local entry link2
  while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    [ -L "$entry" ] || continue
    link2="$(readlink "$entry" 2>/dev/null || true)"
    case "$link2" in
      */sdflow-spec/agents/*.md) : ;;
      *) continue ;;
    esac
    if [ -e "$entry" ]; then continue; fi   # 有效链接，留着
    rm -f "$entry"
    cleaned+=("agents/$(basename "$entry") @ $dest")
  done < <(find "$dest" -mindepth 1 -maxdepth 1)
}

# ─── sdflow global home: canonical bundle anchor + hack scripts ──
# canonical 只接管自属软链/指针（对齐 skills 的所有权守卫）；~/.sdflow 其余视为本工具独占命名空间。
install_sdflow() {
  local sdflow="${SDFLOW_HOME:-$HOME/.sdflow}"
  local bundle="$REPO_DIR/sdflow-init/assets/workflow"
  mkdir -p "$sdflow/hack"

  if [ "$IS_WINDOWS" -eq 1 ]; then
    printf '%s\n' "$bundle" > "$sdflow/workflow-path"
    installed+=("workflow-path @ $sdflow")
  else
    if [ -e "$sdflow/workflow" ] && [ ! -L "$sdflow/workflow" ]; then
      skipped+=("workflow @ $sdflow — 真实目录非本工具软链，未接管")
    else
      local old_target=""
      if [ -L "$sdflow/workflow" ]; then
        old_target="$(readlink "$sdflow/workflow" 2>/dev/null || true)"
      fi
      ln -snf "$bundle" "$sdflow/workflow"
      if [ -n "$old_target" ] && [ "$old_target" != "$bundle" ]; then
        installed+=("workflow @ $sdflow — 接管：$old_target → $bundle")
      else
        installed+=("workflow @ $sdflow")
      fi
    fi
  fi

  # ── 同代 capability 安装快照（OVBG-01）─────────────────────────────────────
  # 成员 = job helper + shell helper + 所需 data file，三者 MUST 同代；任一漂移由
  # `outside-voice-job.py preflight` fail-closed。
  # 🔴 **先删 manifest、最后才写**：安装中途失败（cp 权限 / 磁盘满，set -e 当场中止）时
  # 现场没有 manifest ⇒ preflight 红 ⇒ 后台通道诚实降级；MUST NOT 留一份「自洽但陈旧」的
  # 快照，那会让新旧混配悄悄跑起来（一半新一半旧，且没有任何人会看见）。
  rm -f "$sdflow/hack/capability-manifest.json"

  local f base
  for f in "$REPO_DIR/sdflow-init/assets/hack/"*.sh; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    cp "$f" "$sdflow/hack/$base"
    chmod +x "$sdflow/hack/$base"
    installed+=("hack/$base @ $sdflow")
  done

  # 脚本要读的【数据文件】（非 .sh）—— 如 skill-principles.md：outside-voice.sh 的 FRAME 要 cat 它。
  # 漏拷不会报错，只会让 outside-voice 静默走降级分支（少一段纪律，但仍跑）——正因为不报错，所以必须有这个循环。
  for f in "$REPO_DIR/sdflow-init/assets/hack/"*.md; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    cp "$f" "$sdflow/hack/$base"
    installed+=("hack/$base @ $sdflow")
  done

  # Python helper（outside-voice-job.py：Codex 宿主后台通道的执行面）。装漏 ≠ 静默降级——
  # dispatch 直接找不到文件，整条通道死；故与 .sh 同样设 exec 位、同样进 manifest。
  for f in "$REPO_DIR/sdflow-init/assets/hack/"*.py; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    cp "$f" "$sdflow/hack/$base"
    chmod +x "$sdflow/hack/$base"
    installed+=("hack/$base @ $sdflow")
  done

  # 快照收尾：manifest 由 job helper 自己算（**单一计算源**——写与验共用
  # `compute_manifest()`；MUST NOT 在 shell 里抄第二份 hash 口径）。
  # 写不成不中止安装：其后果是 preflight 红 ⇒ 后台通道走同族 fallback，这是诚实降级。
  # 归因分开写：跳过的两个成因（无合格解释器 / helper 没装上）修法完全不同，
  # 合取成一条 else 会把「helper 未装」误报成「PATH 无 Python」，把人指到错误的方向。
  if [ -z "$_py" ]; then
    echo "  ⚠ capability-manifest 跳过（PATH 无 Python 3.7+）——Codex 后台 voice 通道会 fail-closed 降级"
  elif [ ! -f "$sdflow/hack/outside-voice-job.py" ]; then
    echo "  ⚠ capability-manifest 跳过（job helper 未装到 $sdflow/hack/）——Codex 后台 voice 通道会 fail-closed 降级"
  elif "$_py" "$sdflow/hack/outside-voice-job.py" install-manifest \
         --dir "$sdflow/hack" >/dev/null; then
    installed+=("hack/capability-manifest.json @ $sdflow")
  else
    echo "  ⚠ capability-manifest 写入失败——Codex 后台 voice 通道会 fail-closed 降级"
  fi
}

# [T48] 挑一个 Python 3.7+ 解释器（capability manifest 与 retire-hooks 共用）——裸 `python`
# 可能是 Python2，喂进去会在 f-string 解析期崩（整模块编译先于任何语句执行，脚本内的版本
# 守卫无从拦截自身 parse），故版本把关只能在调用侧。**逐候选校验、取首个 3.7+**
# （不只看 python3：若 python3 恰是旧版而 python 合格，仍能用）。
# 下限为什么是 3.7 而非 init.py 所需的 3.6：这个 `_py` 还要跑 outside-voice-job.py，
# 而它用 `subprocess.run(capture_output=…)`（3.7 才有）——闸门取两个消费者的**上确界**。
_py=""
for _cand in python3 python; do
  if command -v "$_cand" >/dev/null 2>&1 \
     && "$_cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' >/dev/null 2>&1; then
    _py="$_cand"; break
  fi
done

for d in "${TARGET_DIRS[@]}"; do
  install_into "$d"
  cleanup_orphans "$d"
done
install_agents
install_sdflow

# ─── retire deregistered global hooks (T44) ─────────────────────
# 死 hook（change-review-stub.py）每次 Bash 调用都 fire 报错，直到被反注册。把自愈焊进
# 工具链升级路径，令 /sdflow-upgrade 即时清掉，不必等某项目跑 sdflow-init update。
# fail-safe：绝不中止 setup（清理是尽力而为，非安装必要步）。
# 解释器已在上面（install_sdflow 之前）挑好——manifest 与本步共用同一个 $_py。
if [ -z "$_py" ]; then
  echo "  ⚠ retire-hooks 跳过：PATH 无 Python 3.7+（init.py 需 f-string，非致命）"
else
  { "$_py" "$REPO_DIR/sdflow-init/scripts/init.py" retire-hooks ; } || echo "  ⚠ retire-hooks 跳过（非致命）"
fi

# ─── Summary ─────────────────────────────────────────────────
version="$(cat "$REPO_DIR/VERSION" 2>/dev/null || echo "unknown")"
echo ""
echo "sdflow-skills v${version} ready → ${TARGET_DIRS[*]}"
echo ""

if [ ${#installed[@]} -gt 0 ]; then
  echo "  installed (${#installed[@]}):"
  for s in "${installed[@]}"; do echo "    ✓ $s"; done
fi

if [ ${#skipped[@]} -gt 0 ]; then
  echo ""
  echo "  skipped (${#skipped[@]}):"
  for s in "${skipped[@]}"; do echo "    ⚠ $s — already exists, not managed by sdflow-skills"; done
fi

if [ ${#cleaned[@]} -gt 0 ]; then
  echo ""
  echo "  cleaned orphans (${#cleaned[@]}):"
  for s in "${cleaned[@]}"; do echo "    ✗ $s"; done
fi

echo ""
if [ "$IS_WINDOWS" -eq 1 ]; then
  echo "  mode: copy (Windows)"
else
  echo "  mode: symlink (Unix)"
fi

# ─── 四条通则一致性门（真相源在 sdflow-init/assets/，投放面数量由脚本自己报）───
# 【为什么放在 setup.sh 里】：一个「存在但没人跑」的门 = 不存在的门。
# 装的时候顺手跑一次 —— 漂了当场看见，而不是等到某个 skill 带着旧通则跑了半天。
if command -v python3 >/dev/null 2>&1 && [ -f "$REPO_DIR/hack/sync_principles.py" ]; then
  echo ""
  if ! python3 "$REPO_DIR/hack/sync_principles.py" --check; then
    echo ""
    echo "  ⚠️ 四条通则有漂移（上面列了）。修：python3 hack/sync_principles.py --apply"
  fi
  # 人读手册是 workflow.md + prompts/ 的生成物 —— 漂了就是「手册在教人跑一段已废的 prompt」
  if ! python3 "$REPO_DIR/hack/gen_workflow_guide.py" --check; then
    echo "  ⚠️ 修：python3 hack/gen_workflow_guide.py --write"
  fi
fi

# 两个评审 SKILL 的 async host 调度段必须逐字节相同 —— 漂了 = 一个宿主路径静默行为分叉。
# 【独立守卫】：本门只依赖自己那个脚本存在，MUST NOT 挂在 sync_principles.py 的条件下
# （否则 sync_principles.py 一缺失，本门就静默不跑 = 不存在的门）。
if command -v python3 >/dev/null 2>&1 && \
   [ -f "$REPO_DIR/hack/check_async_branch_parity.py" ]; then
  if ! python3 "$REPO_DIR/hack/check_async_branch_parity.py"; then
    echo "  ⚠️ async host 调度段漂移（上面指了首个不同行）。修：以一侧为准整段原样复制"
  fi
fi
