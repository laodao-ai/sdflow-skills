"""机械守：bundle shell 脚本里「未加花括号的 `$变量` 紧跟非 ASCII 字节」形态即红〔I1〕。

【为什么需要这个测试】
macOS 自带的 bash **3.2** 扫变量名时不是 multibyte-aware：`"$src，终止"` 里的全角逗号
首字节 `0xEF` 会被吞进标识符 ⇒ 变量名变成 `src\xef`。本仓脚本一律 `set -u` ⇒ 该行
**运行时当场罢工**（`src\xef: unbound variable`）。这不是理论风险——`ov_cleanup` 的
清理日志行就撞过：罢工点在 kill 之前 ⇒ **整个清理逻辑一次都不执行**，孤儿子进程照跑。

修法是把变量写成 `${src}`。但「修法」写在源码注释里 = **只有人眼在守**，复发不可见
（CLAUDE.md 基准 ①「能机械化的一致性优先机械化」+ 基准 ③「面治不点补」）。
本测试就是那道机械门：仓内**全部** `.sh` 一次扫全，而不是只钉住撞过的那一行、也不只钉一个目录。

【判据（故意保守）】
- **整行以 `#` 开头**（含前导空白）⇒ 纯注释行，永不执行 ⇒ 跳过。
- 其余行**整行扫**，包括行尾注释部分。行尾注释里的 `$var，` 是**误报**，
  但 shell 的注释起点无法在不写一个 shell 词法器的前提下可靠判定
  （`#` 可以出现在字符串里、`${#x}` 里、`$#` 里…—— 那是无界语法面，基准 ⑤ 明令
  MUST NOT 手搓）。∴ 宁可保守多报：误报的修法是给那个变量加花括号，零代价且本就更好。
- `${var}` 形态**不匹配**（花括号显式界定了名字边界，正是我们要的写法）。

【本测试不覆盖】
`$1，` / `$?，` 之类特殊参数：bash 读完单个特殊字符即停止扫名，不受本 bug 影响。
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# `$` + 合法变量名首字符 + 名字余部 + 紧邻的非 ASCII 字节。
# `${...}` 不会命中：`{` 不是变量名首字符。
UNBRACED_THEN_NON_ASCII = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*[^\x00-\x7F]")

# 仓内**全部** .sh 一次扫全，不只 bundle 的 assets/hack/——bash 3.2 的这个坑
# 与文件属于哪个目录无关，只与「脚本里有没有 `$var` 紧贴非 ASCII」有关〔基准③ 面治〕。
# 排除点目录（.git / .claude 等）：非本仓维护的源，改不了也不该由本门判红。
SHELL_FILES = sorted(
    p
    for p in REPO.rglob("*.sh")
    if not any(part.startswith(".") for part in p.relative_to(REPO).parts)
)


def _offenders(text: str):
    """→ [(行号, 命中片段, 行内容)]，已跳过纯注释行。"""
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        m = UNBRACED_THEN_NON_ASCII.search(line)
        if m:
            hits.append((lineno, m.group(), line.strip()))
    return hits


def test_hack_dir_has_shell_files_to_guard():
    """自防呆：glob 打空时上面的扫描会「全绿」，那是零信号假绿。"""
    assert SHELL_FILES, f"{REPO} 下没扫到任何 .sh —— 本机械门形同虚设"


@pytest.mark.parametrize("path", SHELL_FILES, ids=lambda p: p.name)
def test_no_unbraced_variable_before_non_ascii(path):
    """⭐ 非注释行上，`$var` 紧跟非 ASCII 字节 ⇒ bash 3.2 下 set -u 罢工。"""
    hits = _offenders(path.read_text(encoding="utf-8"))
    assert not hits, (
        f"{path.name}: `$变量` 紧跟非 ASCII 字节（bash 3.2 会把该字节吞进变量名，"
        f"set -u 下运行时罢工）——改写成 ${{变量}}:\n"
        + "\n".join(f"  L{n}: 命中 {frag!r} | {line}" for n, frag, line in hits)
    )


def test_detector_catches_the_known_regression_shape():
    """⭐ 变异验证：把已知病灶还原成不带花括号的写法 ⇒ 探测器必须命中。

    没有这一条，上面的「绿」可能只是因为正则根本不工作。
    """
    good = 'echo "outside-voice: 收到 ${src}，终止 runner PID=${OV_RUNNER_PID}" >&2'
    bad = good.replace("${src}", "$src")
    assert not _offenders(good), "花括号写法被误报"
    assert _offenders(bad), "探测器漏掉了 `$src，` —— 本机械门不承重"


def test_detector_skips_pure_comment_lines():
    """纯注释行不参与（它们永不执行），否则解释这个 bug 的注释自己会把门顶红。"""
    assert not _offenders("  # 反例：$src，会被 bash 3.2 吞掉首字节")
