"""跨脚本共享判据一致性守卫（R-guard，闭 T17）。
canonical = sdflow-init/scripts/init.py；maintain_scan 保自包含副本，此处机验相等。
加载失败 hard-fail 非 silent-skip（M2/D5）；init 目录整体缺席用 path-assert 先判。"""
import importlib.util
import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INIT_PATH = os.path.join(REPO, "sdflow-init", "scripts", "init.py")
MS_PATH = os.path.join(REPO, "sdflow-maintain", "scripts", "maintain_scan.py")


def _load(name, path):
    assert os.path.isfile(path), f"守卫前置：{path} 必须存在（缺席=硬失败非跳过）"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # 加载失败抛异常 → hard-fail（非 skip）
    return mod


INIT = _load("_guard_init", INIT_PATH)
MS = _load("_guard_ms", MS_PATH)


def test_rule_markers_equal():
    assert MS.RULE_MARKERS == INIT.RULE_MARKERS, "RULE_MARKERS 漂移（改一处未同步）"


def test_managed_token_matches_init_mark_idx():
    # maintain 的 token == init.MARK_IDX[0] 第二个空白分隔词（镜像 init.split()[1] 口径）
    init_token = INIT.MARK_IDX[0].split()[1]
    assert MS.MANAGED_TOKEN_START == init_token, "托管块 token 与 init.MARK_IDX 漂移"


def test_end_to_end_real_index_managed_block_skipped(tmp_path):
    # 喂真实长形 marker 的 INDEX，验托管块被识别+跳过（护匹配逻辑非只护常量字面）
    start = INIT.MARK_IDX[0]
    end = INIT.MARK_IDX[1]
    (tmp_path / ".git").mkdir()
    osp = tmp_path / "openspec"
    (osp / "specs").mkdir(parents=True)
    idx = (
        "# Index\n\n"
        f"{start}\n"
        "| `trigger-catalog` | [workflow/trigger-catalog.md](./workflow/trigger-catalog.md) | x |\n"
        f"{end}\n"
    )
    (osp / "INDEX.md").write_text(idx, encoding="utf-8")
    r = MS.run_scan(str(tmp_path))
    # 托管块内 trigger-catalog（无 rules/trigger-catalog.md）不被误报已删
    assert "trigger-catalog" not in r
