"""下游托管引用守卫（dedupe-issues-scripts-shared-layer · Task 5 · AD-5 E）。

三 skill 合一后，旧 buglist / todolist skill 的目录名 / 脚本路径 / slash 触发名不应再出现
在任何**活跃托管点**（漏改 = 合并后调用断裂 / CI 打红 / 主 spec 死路径）。本守卫把 AD-5 的
兜底从「实现者手 grep 自觉」升级为机械门：全仓（git 跟踪文件）扫这两个字面串，除 allowlist
外命中即 FAIL。

allowlist（合法保留旧名的面，非陈旧引用）：
- `openspec/changes/archive/**`  —— 历史归档，MUST NOT 回改。
- `openspec/adr/**`              —— 历史决策记录。
- `openspec/issues/**`           —— issue 台账（含两池目录 `buglist/`·`todolist/`——池不合并——与 legacy 行）。
- `openspec/specs/**`            —— 主 spec：本 change 携 MODIFIED delta，主 spec 在 archive 阶段同步
                                    （delta-at-archive 纪律，非本 sync 任务；见 tasks 5.7）。
- `openspec/changes/dedupe-issues-scripts-shared-layer/**` —— 在途活跃 change 目录整体（四件套 +
                                    specs/ 两 delta + 评审产物 spec-review-report.md / gstack-review.md /
                                    .outside-voice/ + impl-reports/——被旧名/脚本路径/`import core` 塞满，
                                    只豁免四件套会让守卫在自己 change 的评审报告上假阳、第一次跑就红）。
- `setup.sh`                     —— `OUR_LEGACY_NAMES` MUST 保留旧名（Windows `.laodao-skills` legacy
                                    marker orphan 回收依赖）。
- `sdflow-init/tests/test_setup_sdflow.py` —— `OUR_NAMES` marker-compat 边界（`setup.sh` 口径的镜像）
                                    + orphan 清理端到端场景，同 `OUR_LEGACY_NAMES` 理由 MUST 保留旧名。
- `docs/**`                      —— 视图 / 快照文档（自标「视图文档，非真相源」、pin 到特定 git HEAD），
                                    非 fail-closed 托管点；连贯刷新到目标态属独立文档交付物（记 todo 后置）。
- 本守卫测试文件自身            —— pattern 用拼接构造（无连续旧名字面）+ basename 显式跳过，避免自匹配假阳。

基准 5 + 「gate 子串自指坑」：pattern 用拼接（`"sdflow-" + "buglist"`）避免守卫扫到自己；
直接文件内容子串扫 + 路径 allowlist（不解析 markdown 结构）。
"""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# 拼接构造，令本文件源码内无连续旧名字面 → 全仓扫描不会自命中（CLAUDE.md「gate 子串自指坑」）。
LEGACY_SKILL_NAMES = ("sdflow-" + "buglist", "sdflow-" + "todolist")
LEGACY_BYTES = tuple(name.encode("utf-8") for name in LEGACY_SKILL_NAMES)

ALLOWLIST_PREFIXES = (
    "openspec/changes/archive/",
    "openspec/adr/",
    "openspec/issues/",
    "openspec/specs/",
    "openspec/changes/dedupe-issues-scripts-shared-layer/",
    "docs/",
)
ALLOWLIST_EXACT = frozenset({
    "setup.sh",
    "sdflow-init/tests/test_setup_sdflow.py",
})
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()


def _tracked_files():
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True, text=True, check=True,
    )
    return [rel for rel in result.stdout.split("\0") if rel]


def _is_allowlisted(relpath):
    if relpath == SELF:
        return True
    if relpath in ALLOWLIST_EXACT:
        return True
    return any(relpath.startswith(prefix) for prefix in ALLOWLIST_PREFIXES)


def test_no_legacy_skill_references_outside_allowlist():
    """全仓（git 跟踪）扫旧 skill 目录/脚本路径/slash 名，除 allowlist 外命中即 FAIL。"""
    offenders = []
    for relpath in _tracked_files():
        if _is_allowlisted(relpath):
            continue
        path = ROOT / relpath
        try:
            blob = path.read_bytes()
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            continue
        for name, needle in zip(LEGACY_SKILL_NAMES, LEGACY_BYTES):
            if needle in blob:
                offenders.append(f"  {relpath}: {name}")
    assert not offenders, (
        "合并 3→1 后仍有活跃托管点引用旧 skill 目录/脚本路径/slash 名（AD-5 fail-closed，漏改即"
        "调用断裂/CI 打红/主 spec 死路径）：\n" + "\n".join(sorted(offenders))
    )


def test_guard_does_not_self_match():
    """自指规避实证：本守卫文件源码里无连续旧名字面（pattern 拼接构造）。

    若有人日后把 pattern 写成连续字面，本测试当场红 —— 守卫扫全仓时会把自己算成 offender。
    """
    src = Path(__file__).read_bytes()
    for name, needle in zip(LEGACY_SKILL_NAMES, LEGACY_BYTES):
        assert needle not in src, (
            f"守卫测试文件不得含连续旧名字面 {name!r}（会在全仓扫描时自匹配假阳）"
        )


def test_allowlist_paths_still_exist():
    """allowlist 里的 exact 路径 + 池目录仍存在——防 allowlist 因文件改名而静默失效放行。"""
    for exact in ALLOWLIST_EXACT:
        assert (ROOT / exact).is_file(), f"allowlist exact 路径已不存在：{exact}"
    # 池目录不合并——存在即校验 openspec/issues/ 豁免确实覆盖两池。
    for pool in ("openspec/issues/buglist", "openspec/issues/todolist"):
        assert (ROOT / pool).is_dir(), f"池目录缺失：{pool}"
