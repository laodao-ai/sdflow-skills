"""sdflow-upstream-watch 机械层——四源上游追踪的 collect/advance 双子命令。

Task 1（脚手架阶段）范围：cwd 守卫（proposal A4）+ anchors.yaml 三态读写层
（mikefarah-flavor yq idiom，同 `sdflow-retro/scripts/retro_report.py` 的 `_yq` 各自实现、
不跨目录 import）+ 外部子进程统一超时常量 + collect/advance 子命令骨架。四源采集逻辑与
`advance` 的报告+facts 绑定门属于 Task 2，本阶段仅占位。

本脚本 MUST 从 sdflow-skills 仓内某处运行（cwd 守卫据此判定，不限定必须是仓根——
`guard_cwd()` 用 `git rev-parse --show-toplevel` 解析真实仓根，供调用方定位
`openspec/upstream/` 等数据路径，避免子目录 cwd 下的相对路径踩空）。
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

# 【外部子进程统一超时常量】单点定义（design.md TD1）：全部子进程调用（git / yq / npm）
# 共用同一超时值，超时按该源 degraded 处置（Task 2 实现降级分支时消费本常量）。
SUBPROCESS_TIMEOUT_SECONDS = 60

# 【cwd 守卫锚定值】proposal A4：本 skill 语义单仓专用，硬编码指向本仓 remote。
EXPECTED_REMOTE_SUBSTR = "laodao-ai/sdflow-skills"

# 【anchors.yaml 数据模型常量】design.md「数据模型」段。
SCHEMA_VERSION = 1
DEFAULT_REMIND_AFTER_DAYS = 30


class CwdGuardError(Exception):
    """cwd 非 sdflow-skills 仓（proposal A4）——fail-loud，调用方 MUST NOT 写任何文件。"""


class AnchorsError(Exception):
    """anchors.yaml 不可解析 / yq 不可用 / yq 非 mikefarah 家族——fail-loud 硬停，
    MUST NOT 按"无锚"猜测续跑（区别于"文件缺失=首轮初始化"这一正常状态）。"""


def _run(cmd, *, input=None):
    """全仓外部子进程统一入口：带 `SUBPROCESS_TIMEOUT_SECONDS` 超时。
    调用方按返回值 `returncode` 自行判定，超时以 `subprocess.TimeoutExpired` 抛出
    （由调用方按"该源 degraded"处置，Task 2 消费）。"""
    return subprocess.run(
        cmd, input=input, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )


def guard_cwd():
    """cwd 守卫（proposal A4）：确认调用者的 cwd 位于 sdflow-skills 仓（git remote 判定），
    非本仓时 fail-loud（抛 `CwdGuardError`），调用方 MUST NOT 在守卫失败后写任何文件。

    返回解析出的仓根绝对路径（`git rev-parse --show-toplevel`），供调用方定位
    `openspec/upstream/` 等数据路径——不假定 cwd 本身就是仓根，只要求 cwd 位于该仓内
    （标准 git 行为：命令向上查找 .git）。
    """
    try:
        toplevel = _run(["git", "rev-parse", "--show-toplevel"])
    except (OSError, subprocess.TimeoutExpired) as e:
        raise CwdGuardError(
            f"cwd 不在任何可探测的 git 仓库内（cwd={Path.cwd()}）：{e}。"
            f"本 skill 仅服务 {EXPECTED_REMOTE_SUBSTR} 工具链自身。"
        ) from e
    if toplevel.returncode != 0:
        raise CwdGuardError(
            f"cwd 不在任何 git 仓库内（cwd={Path.cwd()}）。"
            f"本 skill 仅服务 {EXPECTED_REMOTE_SUBSTR} 工具链自身。"
        )
    root = Path(toplevel.stdout.strip())

    try:
        remote = _run(["git", "-C", str(root), "remote", "get-url", "origin"])
    except (OSError, subprocess.TimeoutExpired) as e:
        raise CwdGuardError(
            f"读取 {root} 的 git remote 失败：{e}。"
            f"本 skill 仅服务 {EXPECTED_REMOTE_SUBSTR} 工具链自身。"
        ) from e
    if remote.returncode != 0 or EXPECTED_REMOTE_SUBSTR not in remote.stdout:
        raise CwdGuardError(
            f"本 skill 仅服务 {EXPECTED_REMOTE_SUBSTR} 工具链自身"
            f"（cwd={Path.cwd()} 所在仓 {root} 的 origin remote 非该仓）。"
        )
    return root


def _resolve_yq():
    """探测 mikefarah/yq 二进制。同 `retro_report._yq` idiom 各自实现（不跨目录 import）。
    非 mikefarah 家族（如 kislyuk/yq）直接报错阻止误用。

    不做进程内缓存（与 retro_report 的模块级缓存不同）：本工具每轮调用次数是个位数
    （≤4 源 × 1-2 次 anchors 读写），缓存收益可忽略，无缓存换来测试可独立控制每次探测结果，
    不需要在测试间手动重置模块私有状态（基准 4：不为低概率/低收益的优化增加耦合）。
    """
    yq = shutil.which("yq")
    if not yq:
        raise AnchorsError(
            "yq 未安装。安装方式：\n"
            "  macOS:   brew install yq\n"
            "  Windows: winget install --id MikeFarah.yq\n"
            "  Linux:   snap install yq"
        )
    vr = _run([yq, "--version"])
    if "mikefarah" not in vr.stdout:
        raise AnchorsError(
            "检测到的 yq 不是 mikefarah/yq（可能是 kislyuk/yq）。请卸载后安装正确版本："
            "macOS: brew install yq / Windows: winget install --id MikeFarah.yq / "
            "Linux: snap install yq"
        )
    return yq


def _yq_read(expression, file, *, default=None):
    """yq(mikefarah) 读取子进程薄封装（同 retro_report._yq idiom）。
    exit≠0（文件不可读/解析失败）MUST raise AnchorsError，不吞；
    「键不存在」（exit 0 + stdout=null）走 default，两条分支不可混同。"""
    yq = _resolve_yq()
    r = _run([yq, "-o", "json", expression, str(file)])
    if r.returncode != 0:
        raise AnchorsError(f"yq failed on {file}: {r.stderr.strip()}")
    raw = r.stdout.strip()
    if not raw or raw == "null":
        return default
    return json.loads(raw)


def load_anchors(path):
    """anchors.yaml 三态读取（R1 / TD4）：
    ①文件缺失 → 返回默认骨架（首轮初始化语义，非错误，不触发 yq）；
    ②文件存在但 yq 解析失败（含非 mikefarah / 未安装）→ `AnchorsError` fail-loud 硬停；
    ③文件存在且可解析 → 返回结构化 dict；某源字段缺失由 `get_source_anchor` 判"该源无锚"。
    """
    path = Path(path)
    if not path.is_file():
        return {
            "schema_version": SCHEMA_VERSION,
            "last_run": None,
            "remind_after_days": DEFAULT_REMIND_AFTER_DAYS,
            "sources": {},
        }
    data = _yq_read(".", path, default=None)
    if not isinstance(data, dict):
        raise AnchorsError(f"anchors.yaml 解析结果非法（须为映射）：{path}")
    data.setdefault("schema_version", SCHEMA_VERSION)
    data.setdefault("remind_after_days", DEFAULT_REMIND_AFTER_DAYS)
    data.setdefault("sources", {})
    return data


def get_source_anchor(anchors, source):
    """取某源的锚记录；该源不存在或记录为空 → None（"值缺失=该源视为无锚首轮"，R1）。"""
    sources = anchors.get("sources") or {}
    return sources.get(source) or None


def write_anchors(path, anchors):
    """整份覆盖写 anchors.yaml（脚本独占维护，R1）。走 yq：JSON（Python dict 天然产出）是
    合法 YAML 1.2 子集，mikefarah yq 可直接把它当 YAML 输入重新格式化输出——机械转换，
    不手写 YAML 序列化字符串（基准 5 同款零解析/零手搓纪律）。"""
    yq = _resolve_yq()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    r = _run([yq, "-o=yaml", "-P", ".", "-"], input=json.dumps(anchors))
    if r.returncode != 0:
        raise AnchorsError(f"yq 写 anchors.yaml 失败：{r.stderr.strip()}")
    path.write_text(r.stdout, encoding="utf-8")


def cmd_collect(args):
    """`collect` 子命令骨架：cwd 守卫起手，四源采集逻辑属 Task 2。"""
    guard_cwd()
    print("collect: 采集逻辑由 Task 2 实现（脚手架阶段占位，未写入任何文件）",
          file=sys.stderr)
    return 2


def cmd_advance(args):
    """`advance` 子命令骨架：cwd 守卫起手，报告+facts 绑定门与锚推进逻辑属 Task 2。"""
    guard_cwd()
    print("advance: 锚推进逻辑由 Task 2 实现（脚手架阶段占位，未写入任何文件）",
          file=sys.stderr)
    return 2


def build_parser():
    parser = argparse.ArgumentParser(
        prog="upstream_watch.py",
        description="四源上游追踪（gstack/superpowers/matt/OpenSpec）——collect 采集事实，"
                     "advance 校验报告后推进锚。仅服务 sdflow-skills 仓自身。",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("collect", help="采集四源 delta 事实，落 facts JSON（Task 2 实现）")
    sub.add_parser("advance", help="校验报告+facts 双参数后推进锚（Task 2 实现）")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "collect":
            return cmd_collect(args)
        if args.command == "advance":
            return cmd_advance(args)
    except CwdGuardError as e:
        print(f"fail-loud: {e}", file=sys.stderr)
        return 1
    return 1  # pragma: no cover — argparse required=True 已排除未知子命令


if __name__ == "__main__":
    sys.exit(main())
