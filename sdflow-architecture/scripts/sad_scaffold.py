#!/usr/bin/env python3
"""sad_scaffold.py — SAD 脚手架：init / preflight 两级 / 原子写 / 单例分流 / log 追加（DEC-8）。

CLI: sad_scaffold.py <sub> --root <消费仓根> …
exit 码约定：0=ok / 2=坏输入 / 3=preflight无openspec布局 / 4=单例冲突 / 5=迁移拒绝（reserved，Task 4）

argparse subparsers 结构：main() 的 dispatch 按子命令名查表，新增子命令（transition/
set-fact/set-assumption/adr-new/context-add，Task 4/5）只需新增一个 _cmd_xxx(args) 函数
+ 一个 add_parser 注册，不需要改动既有子命令的实现或 dispatch 逻辑。
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sad_schema  # noqa: E402  (共享解析源，DEC-1；本脚本只写模版骨架，不重实现解析)

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "references" / "sad-template.md"

SAD_LOG_HEADER = "# sad-log（append-only 判定留痕）\n"
CONTEXT_STUB = "# Context\n\n## Language\n"


def _die(code, msg):
    print(f"[sad_scaffold] FAIL: {msg}", file=sys.stderr)
    sys.exit(code)


def atomic_write(path, text):
    """temp+rename 同目录（DEC-8）：中断只留 temp，不留半写正式文件。"""
    tmp = path.with_name(path.name + ".tmp-scaffold")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def append_log(root, line):
    """append-only：不读不改既有行，仅追加一行。"""
    logp = root / "openspec" / "architecture" / "sad-log.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(logp, "a", encoding="utf-8") as f:
        f.write(f"- {ts} | {line}\n")


def load_sad(root):
    path = root / sad_schema.SAD_REL_PATH
    return path, path.read_text(encoding="utf-8")


def preflight(root, out):
    """两级 preflight：level 1 无 openspec/ → fail-closed 拒绝并指引；
    level 2 openspec/ 存在但缺 adr/CONTEXT.md → 补齐并留痕（首次创建）。
    """
    if not (root / "openspec").is_dir():
        _die(
            3,
            "消费仓无 openspec/ 布局——先运行 /sdflow-init 铺设 OpenSpec 工作流"
            "（安装：bash ~/.skills/sdflow-skills/setup.sh，然后在消费仓会话执行 /sdflow-init；"
            "装完回来重跑本命令）。MUST NOT 自造半套布局。",
        )
    for rel, kind in (("openspec/adr", "dir"), ("openspec/CONTEXT.md", "file")):
        p = root / rel
        if not p.exists():
            out.append(f"首次创建 {rel}")
            if kind == "dir":
                p.mkdir(parents=True)
            else:
                atomic_write(p, CONTEXT_STUB)
    (root / "openspec" / "architecture").mkdir(exist_ok=True)


def _cmd_init(args):
    root = Path(args.root).resolve()
    announcements = []
    preflight(root, announcements)
    for line in announcements:
        print(line)

    sad_path = root / sad_schema.SAD_REL_PATH
    if sad_path.exists():
        if args.on_exists is None:
            _die(
                4,
                "SAD 已存在：--on-exists continue（增量续写）或 replan"
                "（重规划，旧内容归 git 历史）。",
            )
        if args.on_exists == "continue":
            print("SAD 已存在，续跑：直接编辑 openspec/architecture/sad.md 增量续写")
            return 0
        # replan
        if not args.reason or not args.reason.strip():
            _die(2, "--on-exists replan 须提供非空 --reason")
        template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
        atomic_write(sad_path, template_text)
        append_log(root, f"replan: {args.reason}")
        return 0

    # 全新
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    atomic_write(sad_path, template_text)
    log_path = root / sad_schema.LOG_REL_PATH
    atomic_write(log_path, SAD_LOG_HEADER)
    append_log(root, "init")
    return 0


def _cmd_log(args):
    root = Path(args.root).resolve()
    append_log(root, args.line)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="sad_scaffold.py")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="preflight + 建 sad.md/sad-log.md（单例分流）")
    p_init.add_argument("--root", required=True)
    p_init.add_argument("--on-exists", choices=("continue", "replan"), default=None)
    p_init.add_argument("--reason", default=None)
    p_init.set_defaults(func=_cmd_init)

    p_log = sub.add_parser("log", help="append_log 直通（SKILL 判定留痕）")
    p_log.add_argument("--root", required=True)
    p_log.add_argument("--line", required=True)
    p_log.set_defaults(func=_cmd_log)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
