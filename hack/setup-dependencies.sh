#!/usr/bin/env bash
# setup.sh 的内部预检库：source 仅定义函数，不执行安装。
# 调用方先选择 Python，并通过 check_dependencies <python-command> 传入。
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
  local _py="${1:-}"
  echo ""
  echo "运行依赖预检："
  local missing=()

  # 复用 setup.sh [T48] 已选择并传入的 Python，这里只报告，不重新选择。
  # install_sdflow 和 retire-hooks 也消费该解释器，候选选择仍留在安装入口。
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
        echo "  ⚠ yq 版本过低（${yqv}，需 >= ${_YQ_MIN_VERSION} —— --front-matter 支持下限）"
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
