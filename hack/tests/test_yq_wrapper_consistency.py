"""`_yq()` 一致性 golden test（shared-yaml-subset-parser · Task 5 · R12）。

[fix-probe-scan-precision task4 · R12 去计数] 原 7 份含消费仓镜像
`openspec/workflow/tools/anchor_lint.py`；该镜像已随 D13（规则/工具全局单份共享）
停止铺设，本仓残留副本亦已删除（tasks 6.1）——权威源 `sdflow-init/assets/workflow/
tools/anchor_lint.py` 条目保留。以下计数改为 **6 份**。

6 份脚本各自内联一份 `_yq()`（design.md §1 决定：不跨脚本共享——各脚本「零依赖不变量」
不允许互相 import，且 `~10` 行的封装体量本就不值得为共享而抽公共模块）。「各自内联」
不等于「各自漂移」——本文件机械校验 6 份实现共享的**核心逻辑**骨架：

  ① `shutil.which("yq")` 探测二进制
  ② `--version` 输出身份校验须含 `mikefarah`（拒 kislyuk/yq，语法不兼容）
  ③ 进程内缓存（模块级 `_yq_bin`：`global` 声明 + `is None` 判空 + 命中后赋值）
  ④ subprocess 调用统一 `encoding="utf-8"` + `errors="replace"`（Windows GBK/cp936 防护）
  ⑤ 非零退出码 fail-loud（`returncode != 0` 分支必须存在，且 yq 缺失/身份不对分支
     必须 `raise` 或 `sys.exit`，不得静默 return/pass）
  ⑥ `--front-matter=` 条件处理
  ⑦ 非 in-place 模式下走 `-o json`
  ⑧ stdout 为空/`null` 时走 `default`
  ⑨ 用 `json` 模块解码 stdout

【已知且已在各自 docstring 记录的差异——不在本文件检查范围内】
  - `ship_gate.py` / `sad_schema.py` 额外支持 `text=` stdin 参数（frontmatter 消费方
    需要从 `git show` 结果/内存中的 text 读，而非只从磁盘路径读）；其余 4 份只接受
    文件路径。
  - `init.py` 额外带 `--header-preprocess=false`（`config.yaml` 的 `--- # 注释` 起始
    形态会触发 yq 吞行 bug，需要显式关闭该预处理；其余 5 份的消费文件不含这类写法）。
  - `init.py` / `ship_gate.py` / `impl_route.py` / `roadmap_writeback_draft.py` /
    `sad_schema.py` 有 F3 多文档防御（`json.JSONDecoder().raw_decode` + 检测 stdout
    是否含一个以上 JSON 值）；`anchor_lint.py`（Task 2 最早落地）用简单
    `json.loads`，未加此防御——其唯一消费点查 `.metrics.enabled`（布尔叶子，由
    sdflow-init 生成/管理的文件，非任意用户输入，F3 场景在此不适用）。
  - `sad_schema.py` 额外带 `object_pairs_hook` 重复键检测（其既有测试套件要求
    duplicate-key 场景 fail-closed；其余 5 份的消费点无此要求）。
  - `ship_gate.py` / `init.py` 在 `front_matter=True` 且 `default is not None` 时对
    非 dict 顶层结构做 R5/F4 校验（design.md 参考实现原样保留该分支，即使部分文件的
    调用点当前不触发）；`anchor_lint.py` 同样保留该分支（design.md §1 原文）。

本文件不做「6 份字节完全一致」的机械 diff——那会强迫无差异化需求的脚本背上不需要的
代码（如让 `anchor_lint.py` 平白多出 `text=` stdin 支持），与 CLAUDE.md 基准 4
（不为低概率影响纠结完美方案）相悖。核对方式：对每份 `_yq()` 的**源码文本**做结构性
断言（正则/子串搜索核心模式），容忍上方已记录的差异，不容忍其它任何一项核心要素缺失。
"""
import importlib.util
import inspect
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# 6 份 _yq() 消费点（design.md §2 改动清单 + Task 5 新增两份；fix-probe-scan-precision
# task4 删除消费仓镜像条目——权威源条目保留，见上方 docstring 说明）。
TARGETS = {
    "sdflow-init/scripts/init.py":
        REPO / "sdflow-init" / "scripts" / "init.py",
    "sdflow-ship/scripts/ship_gate.py":
        REPO / "sdflow-ship" / "scripts" / "ship_gate.py",
    "sdflow-implement/scripts/impl_route.py":
        REPO / "sdflow-implement" / "scripts" / "impl_route.py",
    "sdflow-init/assets/workflow/tools/anchor_lint.py":
        REPO / "sdflow-init" / "assets" / "workflow" / "tools" / "anchor_lint.py",
    "sdflow-done/scripts/roadmap_writeback_draft.py":
        REPO / "sdflow-done" / "scripts" / "roadmap_writeback_draft.py",
    "sdflow-architecture/scripts/sad_schema.py":
        REPO / "sdflow-architecture" / "scripts" / "sad_schema.py",
}


def _load_module(path, unique_name):
    """从文件路径加载模块，不注册进 `sys.modules`（避免同名模块跨文件互相遮蔽，
    也避免污染其它测试文件的 import 状态）。"""
    spec = importlib.util.spec_from_file_location(unique_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def yq_sources():
    """{label: _yq() 源码文本}，6 份都取得到才算本 fixture 成功——取不到直接让依赖它的
    每条用例报错（比 skip 更诚实：golden test 的前提是"6 份都在"，任一份加载失败就是
    本身要抓的问题，不该被静默跳过）。"""
    out = {}
    for i, (label, path) in enumerate(TARGETS.items()):
        assert path.is_file(), f"golden test 目标文件缺失：{label} ({path})"
        module = _load_module(path, f"_yq_golden_target_{i}")
        fn = getattr(module, "_yq", None)
        assert fn is not None, f"{label} 未定义模块级 _yq()"
        out[label] = inspect.getsource(fn)
    return out


def test_all_six_targets_are_distinct_files():
    """6 个 label 各指向存在且互不相同的文件（防复制粘贴把两个 label 指向同一路径、
    悄悄漏掉真正该覆盖的第 6 份）。"""
    paths = list(TARGETS.values())
    assert len(paths) == 6, f"golden test 应覆盖 6 份 _yq()，实际登记 {len(paths)} 份"
    resolved = {p.resolve() for p in paths}
    assert len(resolved) == 6, f"存在重复路径：{TARGETS}"


# ── 核心逻辑骨架：正则模式 → 人读理由 ──────────────────────────────────────────────
CORE_PATTERNS = {
    "① shutil.which(\"yq\") 探测二进制":
        re.compile(r'shutil\.which\(\s*["\']yq["\']\s*\)'),
    "② --version 调用":
        re.compile(r'["\']--version["\']'),
    "② mikefarah 身份校验":
        re.compile(r'mikefarah'),
    "③ global _yq_bin 声明":
        re.compile(r'global\s+_yq_bin'),
    "③ 缓存判空 (_yq_bin is None)":
        re.compile(r'_yq_bin\s+is\s+None'),
    "③ 缓存命中后赋值 (_yq_bin = yq)":
        re.compile(r'_yq_bin\s*=\s*yq\b'),
    "④ encoding=\"utf-8\"":
        re.compile(r'encoding=["\']utf-8["\']'),
    "④ errors=\"replace\"":
        re.compile(r'errors=["\']replace["\']'),
    "⑤ 非零退出码判断 (returncode != 0)":
        re.compile(r'returncode\s*!=\s*0'),
    "⑥ --front-matter= 条件处理":
        re.compile(r'--front-matter='),
    "⑦ 非 in-place 走 -o json":
        re.compile(r'["\']-o["\']\s*,\s*["\']json["\']'),
    "⑧ 空/null stdout 走 default":
        re.compile(r'return\s+default'),
    "⑨ 用 json 模块解码":
        re.compile(r'json\.loads\(|json\.JSONDecoder\('),
}


@pytest.mark.parametrize("pattern_label", sorted(CORE_PATTERNS))
def test_core_pattern_present_in_every_target(yq_sources, pattern_label):
    pattern = CORE_PATTERNS[pattern_label]
    missing = [label for label, src in yq_sources.items() if not pattern.search(src)]
    assert not missing, (
        f"核心模式「{pattern_label}」在以下 _yq() 实现中缺失：{missing}\n"
        f"（若这是刻意的架构差异，应先在本文件顶部 docstring 的"
        f"「已知且已记录的差异」小节登记理由，而不是让检查悄悄放行）"
    )


def test_yq_missing_branch_fails_loud_not_silently(yq_sources):
    """`shutil.which` 判 None 的分支 MUST 以 `raise` 或 `sys.exit` 结束，不得静默
    return/pass——环境级失败（yq 未安装）不是"键不存在"，不该走 default 静默路径。"""
    for label, src in yq_sources.items():
        m = re.search(r'if not yq:\s*\n((?:.*\n)*?)(?=\s*vr = subprocess|\s*_yq_bin = yq)', src)
        assert m, f"{label}: 未找到 `if not yq:` 分支（golden test 前提假设不成立，需要人工核查）"
        branch = m.group(1)
        assert ("raise" in branch or "sys.exit" in branch), (
            f"{label}: yq 缺失分支既未 raise 也未 sys.exit，疑似静默失败：\n{branch}"
        )


def test_mikefarah_identity_check_branch_fails_loud_not_silently(yq_sources):
    """身份校验不过（非 mikefarah/yq）分支同上，MUST fail-loud。"""
    for label, src in yq_sources.items():
        m = re.search(r'if\s+["\']mikefarah["\']\s+not in\s+vr\.stdout:\s*\n((?:.*\n)*?)(?=\s*_yq_bin = yq)', src)
        assert m, f"{label}: 未找到 mikefarah 身份校验分支（golden test 前提假设不成立，需要人工核查）"
        branch = m.group(1)
        assert ("raise" in branch or "sys.exit" in branch), (
            f"{label}: 身份校验失败分支既未 raise 也未 sys.exit，疑似静默失败：\n{branch}"
        )


def test_non_zero_exit_branch_fails_loud_not_silently(yq_sources):
    """yq 主调用非零退出 MUST raise（[R7/F2]：解析失败与"键不存在"是两条不同分支，
    不得吞非零退出、也不得因 default 而静默）——这一分支 6 份统一用 `raise`（不像
    "yq 未安装"分支那样允许 sys.exit，因为它发生在缓存建立之后，函数已进入
    "正常调用路径"，语义上更贴近"这次查询失败"而非"环境不可用"）。"""
    for label, src in yq_sources.items():
        m = re.search(r'returncode\s*!=\s*0:\s*\n((?:.*\n)*?)(?=\s*if in_place|\s*raw\s*=)', src)
        assert m, f"{label}: 未找到非零退出分支体（golden test 前提假设不成立，需要人工核查）"
        branch = m.group(1)
        assert "raise" in branch, f"{label}: 非零退出分支未 raise：\n{branch}"
