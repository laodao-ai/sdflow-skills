#!/usr/bin/env bash
# outside-voice.sh — 跨模型 outside-voice helper（自包含，零 gstack 内部依赖）
#
# ── 契约单一源（两 review SKILL 只引用本注释，不得转述细节）─────────────
#   preflight
#     stdout: "ready" | "not_installed"                          exit 0
#   render-prompt --context-file <f>
#     stdout: 找漏框架 + 硬分隔的不可信上下文（超 200KB 保头尾截断）
#     stderr: OV_TRUNCATED=true|false                            exit 0 | 3=secret-hit | 2=用法错
#   exec --context-file <f> [--timeout <秒，默认 300>]
#     stdout: codex 最终消息（仅此，经 --output-last-message 提取）
#     stderr: OV_TRUNCATED 行；失败时 codex stderr 转发
#     exit 0=成功 | 1=codex 报错/空输出/命令缺失 | 124=超时 | 3=secret-hit | 2=用法错
#   version
#     stdout: "outside-voice.sh 1.0.0"                           exit 0
# ── 硬化要点〔design D2 spec-review-amendment〕──────────────────────────
#   codex exec 固定注入: -C <repo_root> -s read-only --ephemeral
#     --output-last-message <tmp>，prompt 经临时文件 `- < file` 喂入；
#   timeout 无管道包裹、紧邻捕获 $?（防 124 经管道丢失）；
#   上下文按「不可信证据」硬分隔，其中指令性文字一律视为数据。
set -u

OV_VERSION="outside-voice.sh 1.0.0"
OV_MAX_CONTEXT_BYTES="${OV_MAX_CONTEXT_BYTES:-204800}"

usage() {
  echo "usage: outside-voice.sh {preflight|version|render-prompt --context-file <f>|exec --context-file <f> [--timeout <s>]}" >&2
  exit 2
}

cmd="${1:-}"
[ $# -gt 0 ] && shift
case "$cmd" in
  preflight)
    if command -v codex >/dev/null 2>&1; then echo ready; else echo not_installed; fi
    ;;
  version)
    echo "$OV_VERSION"
    ;;
  render-prompt|exec)
    echo "not implemented yet" >&2; exit 2   # Task 2/3 实现后移除本分支占位
    ;;
  *)
    usage
    ;;
esac
