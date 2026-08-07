"""跨脚本共享判据一致性守卫（R-guard，闭 T17）。
canonical = sdflow-init/scripts/init.py；maintain_scan 保自包含副本，此处机验相等。
加载失败 hard-fail 非 silent-skip（M2/D5）；init 目录整体缺席用 path-assert 先判。

fix-probe-scan-precision：resolve-workflow.sh 的本地 pin 判定步（内联 RULE_MARKERS 第 3 份
副本）随两步链收缩一并删除——原 T93 守卫（`test_resolve_workflow_bash_markers_match_python`）
失去对象，整条删除（DRY 正向收益，见 tasks.md task 2.6）。"""
import importlib.util
import os

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


def test_dead_residual_markers_equal():
    assert MS.DEAD_RESIDUAL_MARKERS == INIT.DEAD_RESIDUAL_MARKERS, "DEAD_RESIDUAL_MARKERS 漂移（改一处未同步）"


def test_stale_shadow_precondition_equal():
    assert MS._STALE_SHADOW_PRECONDITION == INIT._STALE_SHADOW_PRECONDITION, "_STALE_SHADOW_PRECONDITION 漂移（改一处未同步）"


def test_managed_token_matches_init_mark_idx():
    # maintain 的 token == init.MARK_IDX[0] 第二个空白分隔词（镜像 init.split()[1] 口径）
    init_token = INIT.MARK_IDX[0].split()[1]
    assert MS.MANAGED_TOKEN_START == init_token, "托管块 token 与 init.MARK_IDX 漂移"


def test_end_to_end_real_index_managed_block_skipped(tmp_path):
    # 喂真实长形 marker 的 INDEX，验托管块被识别+跳过（护匹配逻辑非只护常量字面）
    # 链接 target 故意写成 rules/<name>.md 形态（命中 _RULE_LINK）：
    # 若托管块剥离逻辑被破坏（未剥离/剥错），trigger-catalog 会被 parse_index_entries
    # 收进 indexed["rule"]；而 fs 侧无 openspec/rules/trigger-catalog.md（未创建该目录/文件）
    # → set_diff 判定"已删未清理" → 断言 fail。这样断言真依赖托管块被正确剥离（load-bearing），
    # 而非之前 ./workflow/trigger-catalog.md 两个正则都不匹配、走②b 静默排除的假绿。
    start = INIT.MARK_IDX[0]
    end = INIT.MARK_IDX[1]
    (tmp_path / ".git").mkdir()
    osp = tmp_path / "openspec"
    (osp / "specs").mkdir(parents=True)
    idx = (
        "# Index\n\n"
        f"{start}\n"
        "| `trigger-catalog` | [trigger-catalog](./rules/trigger-catalog.md) | x |\n"
        f"{end}\n"
    )
    (osp / "INDEX.md").write_text(idx, encoding="utf-8")
    r = MS.run_scan(str(tmp_path))
    # 托管块被正确剥离时，块内该条目不进 indexed → 不出现在"已删未清理"
    assert "trigger-catalog" not in r
