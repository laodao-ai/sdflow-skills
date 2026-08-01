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

# ─── `set -e` 面治：外部命令**裸调用**失败 = 整个 setup.sh 当场中止 ─────────
# 🔴 后果不是「少装一件」，而是【这一趟什么都没装完】：stdout 只剩一行裸 `ln:`/`cp:` 错误，
#   没有汇总，且 `~/.sdflow/` 的 canonical 与 hack 脚本（resolve-models.sh /
#   outside-voice.sh / checkpoint-commit.sh）全不在位 —— 所有 sdflow skill 的第零步都依赖它们。
# 触发面不止「权限/只读」：`ln -sf` **不是单一系统调用**（内部 unlink → symlink 两步），
#   两个 setup.sh 并发铺同一个 HOME 时后者拿到 EEXIST（实测 4 轮命中 2 轮，
#   一个进程 EXIT:1 + 一行 `ln: …: File exists`）。并发是真实场景：`/sdflow-upgrade`
#   与手敲 setup 撞上、两个 checkout 同时装。
# ∴ 全文取向统一为 `install_agents()` 早已用的那一条：**失败降级为 skipped[] + 汇总**，
#   MUST NOT 让 `set -e` 把整条安装链带崩。[impl-review-fix]
# ⚠️ 这**不是**放宽所有权守卫：谁能被覆盖仍由上面的 `-L` / marker / readlink 判据决定，
#   本节只管「判定放行之后，那条命令跑挂了怎么办」。

# ─── Install all skills into one destination ─────────────────
install_into() {
  local dest="$1"
  if ! mkdir -p "$dest" 2>/dev/null; then
    skipped+=("skills @ $dest — 落点建不出来（被占为普通文件？权限？），未铺设")
    return 0
  fi
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
        if ! rm -rf "$target" 2>/dev/null; then
          skipped+=("$skill_name @ $dest — 旧拷贝删不掉（只读？占用？），未更新")
          continue
        fi
      fi
      if ! cp -r "$skill_dir" "$target" 2>/dev/null; then
        skipped+=("$skill_name @ $dest — 拷贝失败（落点只读？磁盘满？），未铺设")
        continue
      fi
      git -C "$REPO_DIR" rev-parse HEAD 2>/dev/null > "$target/.sdflow-skills" || echo "unknown" > "$target/.sdflow-skills"
      installed+=("$skill_name @ $dest")
    else
      # Unix: absolute symlink. Only ever replace symlinks or our own marker
      # copies — never clobber a real directory we don't own (e.g. another
      # tool's skill of the same name).
      if [ -e "$target" ] && [ ! -L "$target" ]; then
        if is_our_marker_copy "$target"; then
          if ! rm -rf "$target" 2>/dev/null; then
            skipped+=("$skill_name @ $dest — 旧 marker 拷贝删不掉（只读？占用？），未接管")
            continue
          fi
        else
          skipped+=("$skill_name @ $dest")
          continue
        fi
      fi
      # 裸 `ln -snf` 在此失败即中止全脚本（并发 EEXIST / 落点只读）——见本节顶部注释。
      if ! ln -snf "$REPO_DIR/$skill_name" "$target" 2>/dev/null; then
        skipped+=("$skill_name @ $dest — 软链建不出来（落点只读？与另一个 setup 并发？），未铺设")
        continue
      fi
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
        if ! rm -rf "$dest/$entry_name" 2>/dev/null; then
          skipped+=("$entry_name @ $dest — 孤儿链清不掉（落点只读？权限？），未清理")
          continue
        fi
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
#
# 【为什么还要一份 installer-owned manifest】[impl-review-fix]
#   上面两条判据（接管「当前源里还在的名字」+ 清理「悬空的链」）合起来仍漏掉一格：
#   **旧 checkout 里那个 .md 还在、而新 checkout 已经把它删了** —— 名字不在当前源集合里
#   ⇒ 进不了接管循环；链指向的文件仍存在 ⇒ 进不了悬空清理。于是一份**已被废弃**、
#   却仍持有 `Bash`/`Write` 的定义，对这台机器上所有项目继续可见，且永远不会被撤下。
#   ∴ 每趟把「本安装器铺出去的名字」写进 `$dest/.sdflow-agents`，下一趟撤掉
#   「manifest 里有、当前源集合里没有」的那些。
#   🔴 判据 MUST 是「**我们装的**」而不是「路径形状像我们的」：别人仓里同布局的**有效**链
#     MUST NOT 被碰（那是真实数据丢失，见 cleanup_agent_orphans 的「承认的代价」）。
#   诚实边界：**首趟**（升级到本版本后的第一次运行）盘上还没有 manifest ⇒ 撤不出任何废弃项；
#     一趟之后自愈。人手删掉 manifest 亦然。这是可接受的一次性窗口，MUST NOT 声称零窗口。
AGENTS_MANIFEST=".sdflow-agents"

install_agents() {
  local src_dir="$REPO_DIR/sdflow-spec/agents"
  local dest="$HOME/.claude/agents"

  # 🔴 【源目录不存在 ≠ 无事可做】—— MUST NOT 在这里 `return 0`。
  #   「整个 sdflow-spec/agents/ 被删掉」正是**孤儿清理最该跑**的那一刻：上一次 setup 铺出去的
  #   软链此刻全部悬空，而在源目录上早退会把它们**永久留在全局命名空间里**。
  #   （实测：早退版本下「删目录 + 重跑新版 setup」⇒ 3 条悬空链原样存活；见
  #   openspec/changes/add-sdflow-spec/impl-reports/task6-stage3-conditional.md 的回滚演练 C 组。）
  #   ∴ 铺设循环按 src_dir 有无条件执行，**清理无条件走到底**。
  #   这也让 design Migration Plan 要求的「先移除 agents 再 revert」有了可执行的落地动作
  #   （删源目录 + 跑一次新版 setup），无需另造 uninstall 开关。

  if [ "$IS_WINDOWS" -eq 1 ]; then
    # 散装 .md 【没有 marker 落点】——marker 是「目录里放一个标记文件」，对单文件做不出来。
    # ⇒ Windows 下不铺 agents。/sdflow-spec 在该宿主走主 session 亲查/亲写路径（D3 的降级方向）。
    # MUST NOT 在这里写「copy + 所有权守卫」——那是做不出来的东西。
    # （Windows 从不铺软链 ⇒ 也没有悬空链要清，故这里仍是唯一一处合法的整体早退。）
    # ⚠️ 用 if/fi 而非 `[ … ] && …`：后者在条件为假时整条语句退出码为 1，`set -e` 会当场中止 setup。
    if [ -d "$src_dir" ]; then
      skipped+=("agents @ $dest — Windows：散装 .md 无 marker 落点，不铺设；/sdflow-spec 走主 session 亲查/亲写")
    fi
    return 0
  fi

  # 源目录整体消失（人手删掉 / 被回滚掉一半）⇒ 不铺设，但**清理照跑**。
  # 当前源集合为空 ⇒ manifest 里记着的全都是废弃项，一并撤下。
  if [ ! -d "$src_dir" ]; then
    cleanup_agent_orphans "$dest" ""
    write_agents_manifest "$dest"
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
  local -a laid=()          # 本趟真正铺出去的名字 → 写进 manifest（skip 掉的不算）
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

    # 落点存在但不可写（只读目录 / 别人的 ACL）⇒ ln 失败。set -e 下那会【中止整个 setup.sh】，
    # 与上面 mkdir 那一格同族（mkdir -p 对已存在目录返回 0，控制流会一路走到这里）⇒ 同样降级为 skip。
    if ! ln -snf "$f" "$target" 2>/dev/null; then
      skipped+=("agents/$name @ $dest — 软链建不出来（落点只读？权限？），未铺设")
      continue
    fi
    installed+=("agents/$name @ $dest")
    laid+=("$name")
  done

  # 顺序不可换：清理先读【上一趟的】 manifest，写入才覆盖成这一趟的。
  cleanup_agent_orphans "$dest" "$src_dir"
  write_agents_manifest "$dest" "${laid[@]}"
}

# 名册快照：把「本安装器这一趟铺出去的名字」原子写进 $dest/.sdflow-agents（每行一个）。
# 写不成 ⇒ 记一笔并继续：后果只是下一趟识别不出废弃定义（退回本次修复前的行为），
# MUST NOT 让 `set -e` 把整条安装链带崩（同「set -e 面治」节）。
write_agents_manifest() {
  local dest="$1"; shift
  [ -d "$dest" ] || return 0          # 落点不存在 ⇒ 无名册可言，也不该为它凭空建目录
  local tmp="$dest/$AGENTS_MANIFEST.tmp$$"
  if printf '%s\n' "$@" > "$tmp" 2>/dev/null && mv -f "$tmp" "$dest/$AGENTS_MANIFEST" 2>/dev/null; then
    return 0
  fi
  rm -f "$tmp" 2>/dev/null || true
  skipped+=("agents manifest @ $dest — 写不出来（落点只读？权限？），下一趟识别不出废弃定义")
}

# 孤儿清理：本仓装出去的软链，源 .md 已删 ⇒ 悬空 ⇒ 清掉。
# 🔴 **独立成函数、由 install_agents 的两条出路各调一次**——因为「源目录整体没了」
#   恰恰是它最该跑的那一刻（见 install_agents 开头）。
cleanup_agent_orphans() {
  local dest="$1" src_dir="$2"     # $2 = 当前源目录（空串 = 源集合为空）
  # 落点本身不存在 ⇒ 无链可清（且不该为清理而凭空建目录）。
  [ -d "$dest" ] || return 0

  # ── (0) manifest 驱动：本安装器上一趟铺过、而**当前源集合里已没有**的名字 ⇒ 撤下 ──
  #   这一格专治「链仍有效」的废弃定义（旧 checkout 的 .md 还在），下面那一格只管悬空链。
  #   三道守卫缺一不可：① 名字必须是**裸文件名**（manifest 被写坏时不许变成任意路径删除）；
  #   ② 落点必须是**软链**（真实文件 = 别人后来放的，不碰）；③ 链指向必须是本仓布局
  #   （与接管判据同一条路径形状）。
  local manifest="$dest/$AGENTS_MANIFEST" mname mtarget mlink
  if [ -f "$manifest" ]; then
    while IFS= read -r mname; do
      [ -n "$mname" ] || continue
      case "$mname" in */*|.|..) continue ;; esac
      if [ -n "$src_dir" ] && [ -f "$src_dir/$mname" ]; then continue; fi   # 当前源里还有 ⇒ 不是废弃项
      mtarget="$dest/$mname"
      [ -L "$mtarget" ] || continue
      mlink="$(readlink "$mtarget" 2>/dev/null || true)"
      case "$mlink" in
        */sdflow-spec/agents/"$mname") : ;;
        *) continue ;;
      esac
      if ! rm -f "$mtarget" 2>/dev/null; then
        skipped+=("agents/$mname @ $dest — 废弃定义撤不掉（落点只读？权限？），未清理")
        continue
      fi
      cleaned+=("agents/$mname @ $dest")
    done < "$manifest"
  fi

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
    # 清不掉（落点只读等）⇒ 与 install_agents 的 mkdir / ln 同一取向：skip + 汇总，
    # MUST NOT 让 `set -e` 把整个 setup.sh 带崩（本函数的调用点都在 install_sdflow 之前）。
    if ! rm -f "$entry" 2>/dev/null; then
      skipped+=("agents/$(basename "$entry") @ $dest — 悬空链清不掉（落点只读？权限？），未清理")
      continue
    fi
    cleaned+=("agents/$(basename "$entry") @ $dest")
  done < <(find "$dest" -mindepth 1 -maxdepth 1)
}

# ─── sdflow global home: canonical bundle anchor + hack scripts ──
# canonical 只接管自属软链/指针（对齐 skills 的所有权守卫）；~/.sdflow 其余视为本工具独占命名空间。
install_sdflow() {
  local sdflow="${SDFLOW_HOME:-$HOME/.sdflow}"
  local bundle="$REPO_DIR/sdflow-init/assets/workflow"
  if ! mkdir -p "$sdflow/hack" 2>/dev/null; then
    skipped+=("sdflow home @ $sdflow — 建不出来（被占为普通文件？权限？），整段未铺设")
    return 0
  fi

  if [ "$IS_WINDOWS" -eq 1 ]; then
    if ! printf '%s\n' "$bundle" > "$sdflow/workflow-path" 2>/dev/null; then
      skipped+=("workflow-path @ $sdflow — 写不进去（只读？磁盘满？），未铺设")
    else
      installed+=("workflow-path @ $sdflow")
    fi
  else
    if [ -e "$sdflow/workflow" ] && [ ! -L "$sdflow/workflow" ]; then
      skipped+=("workflow @ $sdflow — 真实目录非本工具软链，未接管")
    else
      local old_target=""
      if [ -L "$sdflow/workflow" ]; then
        old_target="$(readlink "$sdflow/workflow" 2>/dev/null || true)"
      fi
      # 同 install_into：裸 `ln -snf` 失败即中止全脚本 —— 见「set -e 面治」节。
      if ! ln -snf "$bundle" "$sdflow/workflow" 2>/dev/null; then
        skipped+=("workflow @ $sdflow — canonical 软链建不出来（只读？与另一个 setup 并发？），未铺设")
      elif [ -n "$old_target" ] && [ "$old_target" != "$bundle" ]; then
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
  # 删不掉（落点只读等）⇒ 记一笔并**继续**装：新脚本 + 陈旧 manifest 会被 preflight 判 skew
  # 而 fail-closed（诚实降级）；反过来「因为删不掉就整段不装」留下的是旧脚本 + 旧 manifest
  # 这一份**自洽而陈旧**的快照 —— 恰恰是本段注释要防的那一个。[impl-review-fix]
  local cap_broken_pre=0
  if ! rm -f "$sdflow/hack/capability-manifest.json" 2>/dev/null; then
    skipped+=("hack/capability-manifest.json @ $sdflow — 陈旧快照删不掉，后台 voice 通道将 fail-closed 降级")
    cap_broken_pre=1
  fi

  # 🔴 **本趟只要有一个 capability 成员没装上，就 MUST NOT 写 manifest**〔F5 接缝 · impl-review-fix〕：
  #   把 cp/chmod 从「裸调用 + set -e 中止」改成「skip + 汇总」之后，控制流会继续往下走到
  #   写 manifest 那一步 —— 而它算的是【当前盘上的字节】⇒ 会给一份「新旧混装」的现场签一个
  #   自洽的名，preflight 从此判绿。那正是本段注释要防的「自洽但陈旧」。
  #   ∴ 用 cap_broken 记账：有成员没装上 ⇒ 跳过写 manifest ⇒ 现场无 manifest ⇒ preflight
  #   fail-closed 降级（与中止时同一个终态，但这一趟其余东西照样装完、失败也进了汇总）。
  local cap_broken=0
  local f base
  for f in "$REPO_DIR/sdflow-init/assets/hack/"*.sh; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    if ! cp "$f" "$sdflow/hack/$base" 2>/dev/null || ! chmod +x "$sdflow/hack/$base" 2>/dev/null; then
      skipped+=("hack/$base @ $sdflow — 装不上（落点只读？磁盘满？），未安装")
      cap_broken=1
      continue
    fi
    installed+=("hack/$base @ $sdflow")
  done

  # 脚本要读的【数据文件】（非 .sh）—— 如 skill-principles.md：outside-voice.sh 的 FRAME 要 cat 它。
  # 漏拷不会报错，只会让 outside-voice 静默走降级分支（少一段纪律，但仍跑）——正因为不报错，所以必须有这个循环。
  for f in "$REPO_DIR/sdflow-init/assets/hack/"*.md; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    if ! cp "$f" "$sdflow/hack/$base" 2>/dev/null; then
      skipped+=("hack/$base @ $sdflow — 装不上（落点只读？磁盘满？），未安装")
      cap_broken=1
      continue
    fi
    installed+=("hack/$base @ $sdflow")
  done

  # Python helper（outside-voice-job.py：Codex 宿主后台通道的执行面）。装漏 ≠ 静默降级——
  # dispatch 直接找不到文件，整条通道死；故与 .sh 同样设 exec 位、同样进 manifest。
  for f in "$REPO_DIR/sdflow-init/assets/hack/"*.py; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    if ! cp "$f" "$sdflow/hack/$base" 2>/dev/null || ! chmod +x "$sdflow/hack/$base" 2>/dev/null; then
      skipped+=("hack/$base @ $sdflow — 装不上（落点只读？磁盘满？），未安装")
      cap_broken=1
      continue
    fi
    installed+=("hack/$base @ $sdflow")
  done

  # 快照收尾：manifest 由 job helper 自己算（**单一计算源**——写与验共用
  # `compute_manifest()`；MUST NOT 在 shell 里抄第二份 hash 口径）。
  # 写不成不中止安装：其后果是 preflight 红 ⇒ 后台通道走同族 fallback，这是诚实降级。
  # 归因分开写：跳过的两个成因（无合格解释器 / helper 没装上）修法完全不同，
  # 合取成一条 else 会把「helper 未装」误报成「PATH 无 Python」，把人指到错误的方向。
  if [ "$cap_broken" -eq 1 ] || [ "$cap_broken_pre" -eq 1 ]; then
    echo "  ⚠ capability-manifest 跳过（本趟有成员没装上，见 skipped 汇总）——MUST NOT 给一份不完整/新旧混装的现场签名；后台 voice 通道会 fail-closed 降级"
  elif [ -z "$_py" ]; then
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

# ─── 运行依赖预检（shared-yaml-subset-parser · R1/R2）────────────────────
# 统一检测并报告全部运行依赖：python3 >= 3.7 / git / yq(mikefarah) / openspec（可选）/
# pytest（开发可选）。**不中止 setup.sh**——降级汇报，与全文既定的 skipped[] 范式一致
# （同「set -e 面治」节的取向：检测本身不是安装的必要步，缺失只影响下游脚本能不能跑）。
#
# yq 最低版本 4.16.0 = `--front-matter` 选项的支持下限 [spec-review-amendment F5]——
# 低于此版本即便是 mikefarah/yq 也用不了本 change 引入的 frontmatter 读写路径。
_YQ_MIN_VERSION="4.16.0"

# 版本号大小比较（"X.Y.Z" 形式，缺位按 0 补）。不用 `sort -V`——那是把判定外包给
# coreutils 的另一种手搓，两行整数比较就能穷举 semver 三段，犯不上多一个工具依赖。
_version_ge() {
  local IFS=.
  local -a v1=($1) v2=($2)
  local i a b
  for i in 0 1 2; do
    a="${v1[i]:-0}"; b="${v2[i]:-0}"
    case "$a" in ''|*[!0-9]*) a=0 ;; esac
    case "$b" in ''|*[!0-9]*) b=0 ;; esac
    if [ "$a" -gt "$b" ]; then return 0; fi
    if [ "$a" -lt "$b" ]; then return 1; fi
  done
  return 0
}

check_dependencies() {
  echo ""
  echo "运行依赖预检："
  local missing=()

  # python3 >= 3.7 —— 复用上面 [T48] 已选出的 $_py，这里只统一【报告】，不重新检测。
  # （_py 的候选选择必须留在此处**之前**：install_sdflow 与 retire-hooks 都消费它，
  #  两者都跑在 check_dependencies 调用点之前，把选择本身挪到这里会让它们拿不到 $_py。）
  if [ -n "$_py" ]; then
    echo "  ✓ python3 ($("$_py" --version 2>&1))"
  else
    echo "  ✗ python3 >= 3.7 — 未找到"
    missing+=("python3>=3.7")
  fi

  # git
  if command -v git >/dev/null 2>&1; then
    echo "  ✓ git ($(git --version 2>&1))"
  else
    echo "  ✗ git — 未找到"
    missing+=("git")
  fi

  # yq（mikefarah/yq，>= 4.16.0）
  if command -v yq >/dev/null 2>&1; then
    local yqv yqnum
    yqv="$(yq --version 2>&1)" || true
    if printf '%s' "$yqv" | grep -q "mikefarah"; then
      yqnum="$(printf '%s' "$yqv" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
      if [ -n "$yqnum" ] && _version_ge "$yqnum" "$_YQ_MIN_VERSION"; then
        echo "  ✓ yq ($yqv)"
      else
        echo "  ⚠ yq 版本过低（$yqv，需 >= $_YQ_MIN_VERSION —— --front-matter 支持下限）"
        echo "    升级：macOS brew upgrade yq | Windows winget upgrade --id MikeFarah.yq | Linux snap refresh yq"
        missing+=("yq>=$_YQ_MIN_VERSION")
      fi
    else
      echo "  ⚠ yq 已安装但不是 mikefarah/yq（可能是 kislyuk/yq，jq 语法不兼容）——请卸载后安装正确版本"
      missing+=("yq(mikefarah)")
    fi
  else
    echo "  ✗ yq — 未找到"
    missing+=("yq")
  fi

  # openspec（部分 skill 需要，setup.sh 本身不强依赖）
  if command -v openspec >/dev/null 2>&1; then
    echo "  ✓ openspec ($(openspec --version 2>&1))"
  else
    echo "  · openspec — 未找到（部分 skill 需要：npm i -g @fission-ai/openspec）"
  fi

  # pytest（开发可选，跑测试才需要）
  if [ -n "$_py" ] && "$_py" -m pytest --version >/dev/null 2>&1; then
    echo "  ✓ pytest ($("$_py" -m pytest --version 2>&1))"
  else
    echo "  · pytest — 未找到（跑测试需要：pip install pytest）"
  fi

  if [ ${#missing[@]} -gt 0 ]; then
    echo ""
    echo "  缺少/不满足必要依赖：${missing[*]}"
    for m in "${missing[@]}"; do
      case "$m" in
        python3*)
          echo "  python3 安装：https://python.org 或系统包管理器（apt/brew/winget 等）"
          ;;
        git)
          echo "  git 安装：https://git-scm.com 或系统包管理器（apt/brew/winget 等）"
          ;;
        yq*)
          echo "  yq 安装／升级："
          echo "    macOS:   brew install yq          （升级：brew upgrade yq）"
          echo "    Windows: winget install --id MikeFarah.yq   （升级：winget upgrade --id MikeFarah.yq）"
          echo "    Linux:   snap install yq          （升级：snap refresh yq）"
          ;;
      esac
    done
  fi
}

for d in "${TARGET_DIRS[@]}"; do
  install_into "$d"
  cleanup_orphans "$d"
done
install_agents
install_sdflow
check_dependencies

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
# 版本由 git 自报（最近 tag + 领先提交数 + 短 SHA + 是否脏），不维护 VERSION 文件：
# 手工维护的版本号必然过期（曾停在 v0.10.0 而 HEAD 已领先 391 个提交）。
version="$(git -C "$REPO_DIR" describe --tags --always --dirty 2>/dev/null || echo "unknown")"
echo ""
echo "sdflow-skills ${version} ready → ${TARGET_DIRS[*]}"
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

# 四个编排 SKILL（implement/done/code-review/spec-review）的宿主/档位解析核心段必须逐字节相同 ——
# 漂了 = 某个 skill 的档位解析静默行为分叉。独立守卫，同上不挂在 sync_principles.py 条件下。
if command -v python3 >/dev/null 2>&1 && \
   [ -f "$REPO_DIR/hack/check_tier_resolution_parity.py" ]; then
  if ! python3 "$REPO_DIR/hack/check_tier_resolution_parity.py"; then
    echo "  ⚠️ 宿主/档位解析核心段漂移（上面指了首个不同行）。修：以一侧为准整段原样复制"
  fi
fi

# 第五道机械门：每个 Python 入口都必须在模块顶层重配 stdout/stderr，避免 Windows
# GBK 控制台在打印 Unicode 状态信息时把真实成功误报为崩溃。它与其余四门独立：
# 不依赖任何别的门是否存在或是否通过，失败详情由检查器逐文件列出并指向 CLAUDE.md 模板。
if command -v python3 >/dev/null 2>&1 && \
   [ -f "$REPO_DIR/hack/check_encoding_hygiene.py" ]; then
  if ! python3 "$REPO_DIR/hack/check_encoding_hygiene.py"; then
    echo "  ⚠️ Python 入口编码前导缺失（上面列了逐文件修复项）。修：按 CLAUDE.md“修改本仓库的注意”中的 4 行模板补齐。"
  fi
fi
