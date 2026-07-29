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

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

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

# 约定文档判定：扩展名锚定（防 requirements.txt/docs/conf.py/README_gen.py 等 load-bearing 被误当文档）
# 〔impl-review-fix F1/F2/F3〕
DOC_EXTS = (".md", ".rst", ".txt")
DOC_BASENAMES_NOEXT = ("README", "CHANGELOG", "LICENSE", "NOTICE")  # 允许无扩展或 DOC_EXTS


def is_doc_file(path):
    base = os.path.basename(path)
    stem, ext = os.path.splitext(base)
    under_docs = path.startswith("docs/") or "/docs/" in path
    if base == "VERSION":
        return True
    if stem in DOC_BASENAMES_NOEXT and ext in ("",) + DOC_EXTS:
        return True
    if ext == ".rst":  # rst 任何位置皆文档
        return True
    if under_docs and ext in DOC_EXTS:  # docs/ 下仅 doc 扩展名算文档（.py 等落回代码判定）
        return True
    return False

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
    """解析 unified diff → [dict(path,is_new,is_rename,mode_changed,lines)]。
    〔impl-review-fix F5〕hunk-state 机：`+++ `/`--- ` 仅在文件头区（未见 @@）当 header；
    进入 hunk 后 `+`/`-` 一律内容行（含内容以 `-- `/`++ ` 起始者，不再被 header guard 误吞）。"""
    files = []
    cur = None
    in_hunk = False
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if cur is not None:
                files.append(cur)
            cur = {"path": None, "is_new": False, "is_rename": False,
                   "mode_changed": False, "lines": []}
            in_hunk = False
            parts = line.split(" b/", 1)  # 兜底取路径（+++ 可能是 /dev/null）
            if len(parts) == 2:
                cur["path"] = parts[1]
        elif cur is None:
            continue
        elif line.startswith("@@"):
            in_hunk = True
        elif not in_hunk:
            # 文件头区
            if line.startswith("new file mode"):
                cur["is_new"] = True
            elif line.startswith(("rename from ", "rename to ", "copy from ", "copy to ")):
                cur["is_rename"] = True  # copy 同 rename 处理〔F7〕
            elif line.startswith(("old mode ", "new mode ")):
                cur["mode_changed"] = True  # 〔F4〕
            elif line.startswith("+++ b/"):
                cur["path"] = line[6:]
            # 其余头行（index/+++ /dev/null/--- 等）忽略
        else:
            # hunk 内：内容行
            if line.startswith("+"):
                cur["lines"].append(line[1:])
            elif line.startswith("-"):
                cur["lines"].append(line[1:])
            # 上下文行（空格前缀）/`\ No newline`（\ 前缀）→ 忽略
    if cur is not None:
        files.append(cur)
    return [f for f in files if f["path"]]


def classify_file(f):
    """→ (ok: bool, reason: str)。ok=True 表示该文件的改动属白名单形状。"""
    path = f["path"]
    base = os.path.basename(path)
    _, ext = os.path.splitext(base)

    # 行为面路径 MUST 优先（bundle markdown 承载行为）
    if _match_any(path, BEHAVIOR_PATH_PATTERNS):
        return False, f"behavior-path:{path}"
    if f["is_rename"]:  # 含 copy〔F7〕
        return False, f"rename-or-copy:{path}"
    if f["mode_changed"]:  # chmod 是行为改动〔F4〕
        return False, f"mode-change:{path}"

    in_tests = path.startswith("tests/") or "/tests/" in path

    # ② 仅新增 tests/ 文件（排除 import 副作用 conftest/__init__）
    if f["is_new"]:
        if in_tests and base not in ("conftest.py", "__init__.py"):
            return True, f"new-test:{path}"
        if is_doc_file(path):
            return True, f"new-doc:{path}"
        return False, f"new-codepath:{path}"

    # ① 约定文档（扩展名锚定：VERSION/README/CHANGELOG/docs下doc扩展/.rst）
    if is_doc_file(path):
        return True, f"doc-path:{path}"

    # 任意非约定文档 .md → 保守 NOT（可能承载行为）
    if ext == ".md":
        return False, f"non-doc-markdown:{path}"

    # ① 代码内注释行（语言感知，仅行注释）
    marker = LINE_COMMENT.get(ext)
    if marker is None:
        return False, f"unsupported-lang:{path}"
    if not f["lines"]:  # 空内容改动（mode-only 兜底/纯元数据）→ 不 vacuous 放行〔F4〕
        return False, f"no-content-change:{path}"
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
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        emit("ERROR", EXIT_ERROR, f"git-diff-failed:{r.stderr.strip()[:120]}", [])

    verdict, reason, fv = classify_diff(r.stdout)
    code = EXIT_EXEMPT if verdict == "EXEMPT" else EXIT_NOT_EXEMPT
    emit(verdict, code, reason, fv)


if __name__ == "__main__":
    main()
