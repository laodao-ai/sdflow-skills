#!/usr/bin/env python3
"""无逻辑面白名单形状判器 — sdflow-code-review Step2 免除判据（post-diff·机判·只读）。

盘面即状态：只读 `git diff <base>..HEAD`、零副作用、双输出（human 行 + JSON）、退出码承载判定。
    退出码 0 = EXEMPT     （无逻辑面白名单形状 → Step2 多镜可免，结构上零产出）
    退出码 1 = NOT_EXEMPT （有逻辑面 / 命中行为面路径 → Step2 必跑）
    退出码 2 = ERROR      （git 失败等 → 调用方 MUST 当 NOT_EXEMPT 处理，保守）

白名单形状（三者之一，且无行为面路径命中）：
    ① 仅动代码内注释行（语言感知·仅行注释）或约定文档路径文件（README*/CHANGELOG*/docs/**/*.txt/VERSION）
    ② 仅新增 tests/ 下文件（排除 conftest.py）
    ③ 版本常量：收窄为 VERSION/CHANGELOG 等文档路径（不判代码里的 API_VERSION/SCHEMA_VERSION —— 无法机判是否 load-bearing）

守卫（保守偏 NOT_EXEMPT）：
    - 行为面路径清单（bundle/assets/workflow、SKILL.md、workflow.md、ship_gate.py、本判器）→ 命中即 NOT_EXEMPT，
      即便 diff 形状=仅动 markdown（bundle markdown 承载行为；硬编码路径、与部署解耦，吸收原 TG-27 元层护栏）。
    - 块注释不支持 → 保守判逻辑；不支持语言 → 保守 NOT_EXEMPT；任意非约定文档 .md → NOT_EXEMPT；
      新增非 tests/非文档文件 → NOT_EXEMPT（新 codepath）；重命名 → NOT_EXEMPT。
    - 伪装成注释的逻辑改由本判器之外的 Step1 scope-drift 守卫（判器只看 diff 形状）。
"""
import argparse
import fnmatch
import json
import os
import subprocess
import sys

_GIT_HARDEN = ("-c", "core.quotePath=false")

EXIT_EXEMPT, EXIT_NOT_EXEMPT, EXIT_ERROR = 0, 1, 2

# 行为面路径：命中即 NOT_EXEMPT（承载行为，非文档）
BEHAVIOR_PATH_PATTERNS = (
    "sdflow-init/assets/workflow/*",
    "*/assets/workflow/*",
    "SKILL.md", "*/SKILL.md",
    "workflow.md", "*/workflow.md",
    "*ship_gate.py",
    "*trivial_shape.py",
)

# 约定文档路径：改动视为纯文档（可免）。VERSION/CHANGELOG 收编版本常量③。
DOC_PATH_PATTERNS = (
    "README*", "*/README*",
    "CHANGELOG*", "*/CHANGELOG*",
    "docs/*", "*/docs/*",
    "*.txt",
    "VERSION", "*/VERSION",
)

# 语言 → 行注释标记（仅行注释；块注释不支持 → 保守判逻辑）
LINE_COMMENT = {
    ".py": "#", ".sh": "#", ".bash": "#", ".yaml": "#", ".yml": "#",
    ".toml": "#", ".cfg": "#", ".ini": "#", ".rb": "#",
    ".js": "//", ".ts": "//", ".tsx": "//", ".jsx": "//",
    ".go": "//", ".c": "//", ".h": "//", ".cpp": "//", ".hpp": "//",
    ".java": "//", ".rs": "//",
}


def _match_any(path, patterns):
    base = os.path.basename(path)
    for pat in patterns:
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(base, pat):
            return True
    return False


def _is_comment_or_blank(content, marker):
    s = content.strip()
    if s == "":
        return True
    return s.startswith(marker)


def parse_diff(diff_text):
    """解析 unified diff → [(path, is_new, is_rename, changed_lines)]。
    changed_lines = 该文件所有 +/- 内容行（去掉 +++/---）的内容（不含前导 +/-）。"""
    files = []
    cur = None
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if cur is not None:
                files.append(cur)
            cur = {"path": None, "is_new": False, "is_rename": False, "lines": []}
            # 从 "diff --git a/X b/Y" 兜底取路径（+++ 可能是 /dev/null）
            parts = line.split(" b/", 1)
            if len(parts) == 2:
                cur["path"] = parts[1]
        elif cur is None:
            continue
        elif line.startswith("new file mode"):
            cur["is_new"] = True
        elif line.startswith("rename from ") or line.startswith("rename to "):
            cur["is_rename"] = True
        elif line.startswith("+++ b/"):
            cur["path"] = line[6:]
        elif line.startswith("+++ ") or line.startswith("--- "):
            continue
        elif line.startswith("@@"):
            continue
        elif line.startswith("+"):
            cur["lines"].append(line[1:])
        elif line.startswith("-"):
            cur["lines"].append(line[1:])
    if cur is not None:
        files.append(cur)
    return [f for f in files if f["path"]]


def classify_file(f):
    """→ (ok: bool, reason: str)。ok=True 表示该文件的改动属白名单形状。"""
    path = f["path"]
    if _match_any(path, BEHAVIOR_PATH_PATTERNS):
        return False, f"behavior-path:{path}"
    if f["is_rename"]:
        return False, f"rename:{path}"

    base = os.path.basename(path)
    _, ext = os.path.splitext(path)
    in_tests = "tests/" in path or path.startswith("tests/")

    # ② 仅新增 tests/ 文件（排除 conftest）
    if f["is_new"]:
        if in_tests and base != "conftest.py":
            return True, f"new-test:{path}"
        if _match_any(path, DOC_PATH_PATTERNS):
            return True, f"new-doc:{path}"
        return False, f"new-codepath:{path}"

    # ① 约定文档路径 → 纯文档（含 VERSION/CHANGELOG，收编版本常量③）
    if _match_any(path, DOC_PATH_PATTERNS):
        return True, f"doc-path:{path}"

    # 任意非约定文档 .md → 保守 NOT（可能承载行为）
    if ext == ".md":
        return False, f"non-doc-markdown:{path}"

    # ① 代码内注释行（语言感知，仅行注释）
    marker = LINE_COMMENT.get(ext)
    if marker is None:
        return False, f"unsupported-lang:{path}"
    for content in f["lines"]:
        if not _is_comment_or_blank(content, marker):
            return False, f"logic-line:{path}"
    return True, f"comment-only:{path}"


def emit(verdict, exit_code, reason, files_verdict):
    human = f"[trivial_shape] {verdict} — {reason}"
    print(human)
    print(json.dumps({"verdict": verdict, "reason": reason,
                      "files": files_verdict}, ensure_ascii=False))
    sys.exit(exit_code)


def classify_diff(diff_text):
    """纯函数：diff 文本 → (verdict, reason, files_verdict)。供测试直接调。"""
    files = parse_diff(diff_text)
    if not files:
        return "NOT_EXEMPT", "empty-diff", []
    fv = []
    all_ok = True
    first_block = None
    for f in files:
        ok, reason = classify_file(f)
        fv.append({"path": f["path"], "ok": ok, "reason": reason})
        if not ok:
            all_ok = False
            if first_block is None:
                first_block = reason
    if all_ok:
        return "EXEMPT", "all-whitelist-shape", fv
    return "NOT_EXEMPT", first_block, fv


def main():
    ap = argparse.ArgumentParser(description="无逻辑面白名单形状判器（code-review Step2 免除判据）")
    ap.add_argument("--base", required=True, help="diff 基线 ref（如 merge-base）")
    ap.add_argument("--root", default=".", help="仓库根")
    args = ap.parse_args()

    r = subprocess.run(("git",) + _GIT_HARDEN + ("-C", args.root, "diff", f"{args.base}..HEAD"),
                       capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        emit("ERROR", EXIT_ERROR, f"git-diff-failed:{r.stderr.strip()[:120]}", [])

    verdict, reason, fv = classify_diff(r.stdout)
    code = EXIT_EXEMPT if verdict == "EXEMPT" else EXIT_NOT_EXEMPT
    emit(verdict, code, reason, fv)


if __name__ == "__main__":
    main()
