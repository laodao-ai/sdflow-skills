"""T188: 跨 skill 同 basename 测试文件中断仓根 pytest 全局收集（import 冲突）。

仓根守卫：扫全仓 test_*.py 的 basename，重复即 fail（fail-loud）。
排除 .claude/ 下的 worktree 残留。
"""
import subprocess
from collections import Counter


def test_no_duplicate_test_basenames():
    result = subprocess.run(
        ["find", ".", "-name", "test_*.py", "-path", "*/tests/*",
         "-not", "-path", "./.claude/*"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    paths = [p.strip() for p in result.stdout.strip().splitlines() if p.strip()]
    basenames = [p.rsplit("/", 1)[-1] for p in paths]
    dupes = {name: cnt for name, cnt in Counter(basenames).items() if cnt > 1}
    assert dupes == {}, (
        f"跨 skill 同名测试文件会中断 pytest 仓根全局收集（T188）：\n"
        + "\n".join(f"  {name} x{cnt}: "
                    + ", ".join(p for p in paths if p.endswith("/" + name))
                    for name, cnt in sorted(dupes.items()))
    )
