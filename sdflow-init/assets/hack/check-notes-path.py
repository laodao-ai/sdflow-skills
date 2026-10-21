#!/usr/bin/env python3
"""check-notes-path.py — 判定粘回的评审意见能否写入 review-notes.md（RVP-06）。

用法：
  python3 ~/.sdflow/hack/check-notes-path.py --stdin <<'SDFLOW_NOTES_PATH'
  <P>
  SDFLOW_NOTES_PATH
  python3 ~/.sdflow/hack/check-notes-path.py '<P>'        （位置参数形态，P 须自己保证已安全加引号）
--stdin 从 stdin 取第一行（去掉行尾换行）作为 P；P 来自不可信粘贴文本，agent 一律用带引号定界符的
here-doc 传入，P 不进命令行。两种形态同时给出报用法错误。
P 是粘回文本第一行的第一个反引号片段。在仓内任意目录运行，仓根取 `git rev-parse --show-toplevel`。

退出码：
  0   通过；stdout 一行为可写入的绝对路径
  1   不通过；stderr 一行 `✗ problem=粘回路径不能写入 cause=<违反的条件> fix=...`
  64  用法错误（参数形态不是「恰好一个位置参数」或「仅 --stdin」）

只读不写：不建目录、不建文件。agent MUST 以退出码为准，MUST NOT 自行判定。
"""
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

import os
import subprocess

SUFFIX = "/review/review-notes.md"
FIX = "给出正确路径，或回复「不落盘，直接处理」"


def reject(cause):
    print(f"✗ problem=粘回路径不能写入 cause={cause} fix={FIX}", file=sys.stderr)
    return 1


def inside(path, base):
    """path 与 base 都是 realpath 后的绝对路径；path 须是 base 本身之下的内容。"""
    return path.startswith(base + os.sep)


def git_root():
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    root = r.stdout.strip()
    return root if r.returncode == 0 and root else None


def check(p):
    """返回 (退出码, 可写入的绝对路径或 None)；不通过时已向 stderr 打印原因。"""
    if "\\" in p:
        return reject("路径含反斜杠"), None
    if p.startswith("/"):
        return reject("路径是绝对路径，须为以 openspec/ 开头的仓库相对路径"), None
    segs = p.split("/")
    if ".." in segs:
        return reject("路径含 .. 段"), None
    if any(s in ("", ".") for s in segs):
        return reject("路径含空段或 . 段"), None
    if not p.startswith("openspec/"):
        return reject("路径不以 openspec/ 开头"), None
    if not p.endswith(SUFFIX):
        return reject(f"路径不以 {SUFFIX} 结尾"), None

    root = git_root()
    if root is None:
        return reject("当前目录不在 git 仓内，取不到仓根"), None
    real_root = os.path.realpath(root)
    # 段检查已排除上跳；下面的父目录 realpath 检查兜底符号链接逃逸
    target = os.path.join(root, *segs)
    parent = os.path.dirname(target)
    if not os.path.isdir(parent):
        return reject("父目录不存在（意见可能来自别的仓或别的 worktree）"), None
    if not inside(os.path.realpath(parent), os.path.join(real_root, "openspec")):
        return reject("父目录的真实路径不在仓根真实路径的 openspec/ 内"), None
    if os.path.islink(target):
        return reject("目标文件已存在且是符号链接"), None
    if os.path.isdir(target):
        return reject("目标已存在且是目录"), None
    return 0, target


def usage():
    print("check-notes-path: ✗ problem=用法错误 cause=需要恰好一个位置参数，或仅 --stdin "
          "fix=python3 ~/.sdflow/hack/check-notes-path.py --stdin <<'SDFLOW_NOTES_PATH'", file=sys.stderr)
    return 64


def main(argv):
    if len(argv) == 2 and argv[1] == "--stdin":
        try:
            data = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        except OSError:
            return usage()
        p = data.split("\n", 1)[0]
        if p.endswith("\r"):
            p = p[:-1]
    elif len(argv) == 2:
        p = argv[1]
    else:
        return usage()
    code, target = check(p)
    if code == 0:
        print(target)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
