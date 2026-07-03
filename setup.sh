#!/usr/bin/env bash
# laodao-skills setup — install/update skills into BOTH:
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
      if [ -d "$target" ] && [ ! -f "$target/.laodao-skills" ] && [ ! -L "$target" ]; then
        skipped+=("$skill_name @ $dest")
        continue
      fi
      if [ -d "$target" ] && [ -f "$target/.laodao-skills" ]; then
        rm -rf "$target"
      fi
      cp -r "$skill_dir" "$target"
      git -C "$REPO_DIR" rev-parse HEAD 2>/dev/null > "$target/.laodao-skills" || echo "unknown" > "$target/.laodao-skills"
      installed+=("$skill_name @ $dest")
    else
      # Unix: absolute symlink. Only ever replace symlinks or our own marker
      # copies — never clobber a real directory we don't own (e.g. another
      # tool's skill of the same name).
      if [ -e "$target" ] && [ ! -L "$target" ]; then
        if [ -f "$target/.laodao-skills" ]; then
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
  for entry in "$dest"/*/; do
    [ -e "$entry" ] || continue
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
    [ -f "$entry/.laodao-skills" ] && is_ours=1

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
  done
}

# ─── sdflow global home: canonical bundle anchor + hack scripts ──
# canonical 只接管自属软链/指针（对齐 skills 的所有权守卫）；~/.sdflow 其余视为本工具独占命名空间。
install_sdflow() {
  local sdflow="${SDFLOW_HOME:-$HOME/.sdflow}"
  local bundle="$REPO_DIR/opsx-project-init/assets/workflow"
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

  local f base
  for f in "$REPO_DIR/opsx-project-init/assets/hack/"*.sh; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    cp "$f" "$sdflow/hack/$base"
    chmod +x "$sdflow/hack/$base"
    installed+=("hack/$base @ $sdflow")
  done
}

for d in "${TARGET_DIRS[@]}"; do
  install_into "$d"
  cleanup_orphans "$d"
done
install_sdflow

# ─── Summary ─────────────────────────────────────────────────
version="$(cat "$REPO_DIR/VERSION" 2>/dev/null || echo "unknown")"
echo ""
echo "laodao-skills v${version} ready → ${TARGET_DIRS[*]}"
echo ""

if [ ${#installed[@]} -gt 0 ]; then
  echo "  installed (${#installed[@]}):"
  for s in "${installed[@]}"; do echo "    ✓ $s"; done
fi

if [ ${#skipped[@]} -gt 0 ]; then
  echo ""
  echo "  skipped (${#skipped[@]}):"
  for s in "${skipped[@]}"; do echo "    ⚠ $s — already exists, not managed by laodao-skills"; done
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
