# maintain-scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `sdflow-maintain` 步骤 1-3 的三类确定性 set-diff 从模型手做下沉为只读脚本 `maintain_scan.py`，`sdflow-maintain` 由纯 Markdown 编排类升为数据类。

**Architecture:** 新增 `sdflow-maintain/scripts/maintain_scan.py`（Python stdlib，纯读、fail-closed）产出四类分节只读差异报告：① specs/rules ↔ INDEX 双向 set-diff（链接路径 join + 托管块排除 + 四类判据）② CLAUDE.md 过时引用扫描（匹配契约）③ workflow bundle 陈旧遮蔽兜底扫描。判断（归组/是否修复）留 SKILL 步骤 4。判据 canonical 留 `sdflow-init/scripts/init.py`，maintain_scan 保自包含副本 + 跨脚本一致性守卫 pytest 机验（闭 T17）。

**Tech Stack:** Python 3 stdlib（`os`/`re`/`sys`/`argparse`/`pathlib`）；pytest；`importlib.util.spec_from_file_location`（守卫跨 skill 只读加载 init.py，不 import）。

## Global Constraints

以下为 design/spec 的项目级红线，**每个任务的验收隐含包含本节**，逐字抄自 spec/design：

- **MLH 全局红线**：fail-closed（坏输入非零退出 + 响亮 stderr）+ 可观测（stderr/报告明示）+ 坏输入 pytest 负例 + **MUST NOT 引入静默面**。
- **§1.3 判断权留人/模型**：归组建议、是否修复 INDEX **不下沉**进脚本（D1/D3）；脚本零写文件。
- **adr/0006 机械 prose MUST 脚本化**：三类 set-diff 全脚本化。
- **fail-closed 方向重锚（D2）**：反静默方向是堵「假一致」（misparse→false-consistent）。「读到 0 条 spec 条目」= 合法（报全部新增未索引，退出 0）；「结构骨架缺失 / 托管 marker 不配对 / 行畸形无法确信」= 非零退出，绝不半信半疑输出「一致」。
- **退出码语义（D5，镜像 anchor_lint）**：`0` = 扫描完成（含有差异，差异是正常结果）；`非0` = 坏输入/无法可靠完成。typed `MaintainScanError` → `main(argv)` 捕获打 stderr → `sys.exit(非0)`；`sys.exit(main())`。
- **join-key = 链接目标路径（H3/D1）**：「已列条目」只纳链接匹配 `specs/{name}/spec.md`（spec 类）或 `rules/{name}.md`（rule 类）的行；非此两式的行（如 `retro/report.md`、`roadmaps/…`）**一律不参与 set-diff**。类型由链接路径判，非首列名。
- **托管块边界按稳定 token 子串界定（H1/Q2）**：检测 `opsx-init:rules:start` / `opsx-init:rules:end` **token 子串**（`token in line`，镜像 `init.py:_find_marker_line` 的 `start.split()[1]` 口径），**MUST NOT 硬编裸短串** `<!-- opsx-init:rules:start -->`（真实 marker 是带中文尾注长形，裸短串非其子串 → 假 fail-closed）。marker 检测 **MUST fence-aware**（跳 ``` 围栏内 marker 示例）。
- **CLAUDE.md 引用匹配契约（M1/D4）**：一次「引用」= 正则匹配 `openspec/(specs|rules)/<name>(/|\.md)`，`<name>` ∈ `[a-z0-9-]+` 且与「已删集」取交才报。MUST 排除 ① 代码围栏/行内 code 内提及 ② 字面占位符（`{name}` 花括号 token）③ 泛指路径（`openspec/specs/` 无 `<name>`）。
- **陈旧遮蔽判据 canonical = `init.py:RULE_MARKERS`（D4）**：`("workflow.md", "spec-checklists", "code-checklists")`；maintain_scan 保自包含副本 + 一致性守卫 pytest 断言相等，不等即 fail。文案不追求逐字等同 init，语义等价即可。
- **守卫加载 fail 语义（M2/D5）**：守卫用 `importlib.util.spec_from_file_location` 跨 skill 加载 init.py（不 import）；加载失败 MUST **hard-fail 非 silent-skip**（try/except-skip = 真空绿）；但「sdflow-init 目录整体缺席」用显式 path-assert 先判（避免 collect-time ModuleNotFoundError 误红）。

---

## File Structure

- **Create** `sdflow-maintain/scripts/maintain_scan.py` — 只读差异报告脚本（唯一新增执行核心）。
- **Create** `sdflow-maintain/tests/test_maintain_scan.py` — 正例/负例/不变量测试 + tmp 仓夹具。
- **Create** `sdflow-maintain/tests/test_marker_consistency.py` — 跨脚本一致性守卫（RULE_MARKERS + token 契约 + 端到端 fixture）。
- **Modify** `sdflow-maintain/SKILL.md` — 步骤 1-3 prose 改为「调 `maintain_scan.py`」，保留步骤 4/5。
- **Modify** `CLAUDE.md`（仓根）— 分类文档订正（数据类名单加 sdflow-maintain；两类 skill 归类挪动）。
- **Modify** `README.md` — 「其余为纯 Markdown 编排类」表述订正。

---

### Task 1: 数据类化骨架 + 模块 skeleton

**Files:**
- Create: `sdflow-maintain/scripts/maintain_scan.py`
- Test: `sdflow-maintain/tests/test_maintain_scan.py`

**Interfaces:**
- Produces:
  - `class MaintainScanError(Exception)` — typed 坏输入错误。
  - `find_repo_root(start: str) -> str` — 从 `start` 向上找含 `.git` 的目录；找不到 raise `MaintainScanError`。
  - `main(argv=None) -> int` — 解析 `--root`（默认 `find_repo_root(os.getcwd())`），捕获 `MaintainScanError` → 打 stderr → 返回非零；成功返回 0。
  - `sys.exit(main())` 入口。
  - 测试 helper `make_repo(tmp_path, specs=(), rules=None, index_body="", claude=None, workflow=(), managed_entries=())` — 造最小 openspec 仓结构，返回 root 路径。

- [ ] **Step 1: 写失败测试（骨架存在性 + --root + 坏 root）**

在 `sdflow-maintain/tests/test_maintain_scan.py`：

```python
import importlib.util
import os
import subprocess
import sys
import textwrap

import pytest

SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts", "maintain_scan.py",
)


def _load():
    spec = importlib.util.spec_from_file_location("maintain_scan", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ms = _load()

MANAGED_START = "<!-- opsx-init:rules:start —— 由 sdflow-init 维护，勿手改本区块 -->"
MANAGED_END = "<!-- opsx-init:rules:end -->"


def make_repo(tmp_path, specs=(), rules=None, index_body=None,
              claude=None, workflow=(), managed_entries=(), has_git=True):
    """造最小 openspec 仓：specs=spec 名列表；rules=None 表示不建 rules/ 目录（可选目录缺失）,
    []/列表表示建目录并放对应 .md；index_body=None 表示不建 INDEX.md（缺失场景）。"""
    root = tmp_path
    if has_git:
        (root / ".git").mkdir()
    osp = root / "openspec"
    osp.mkdir()
    (osp / "specs").mkdir()
    for name in specs:
        d = osp / "specs" / name
        d.mkdir()
        (d / "spec.md").write_text("# spec\n", encoding="utf-8")
    if rules is not None:
        (osp / "rules").mkdir()
        for name in rules:
            (osp / "rules" / f"{name}.md").write_text("# rule\n", encoding="utf-8")
    if index_body is not None:
        managed = ""
        if managed_entries:
            rows = "\n".join(
                f"| `{n}` | [workflow/{n}.md](./workflow/{n}.md) | x |"
                for n in managed_entries
            )
            managed = f"{MANAGED_START}\n{rows}\n{MANAGED_END}\n"
        (osp / "INDEX.md").write_text(
            f"# OpenSpec Index\n\n{managed}{index_body}\n", encoding="utf-8"
        )
    if claude is not None:
        (root / "CLAUDE.md").write_text(claude, encoding="utf-8")
    if workflow:
        wf = osp / "workflow"
        wf.mkdir()
        for f in workflow:
            (wf / f).write_text("x\n", encoding="utf-8")
    return str(root)


def test_error_type_exists():
    assert issubclass(ms.MaintainScanError, Exception)


def test_missing_git_root_raises(tmp_path):
    with pytest.raises(ms.MaintainScanError):
        ms.find_repo_root(str(tmp_path))
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-maintain/tests/test_maintain_scan.py -x -q`
Expected: FAIL（`maintain_scan.py` 不存在 / `MaintainScanError` 未定义）

- [ ] **Step 3: 写最小实现（模块骨架）**

在 `sdflow-maintain/scripts/maintain_scan.py`：

```python
#!/usr/bin/env python3
"""maintain_scan.py — sdflow-maintain 的确定性只读差异报告核心。

扫 openspec/specs|rules ↔ INDEX.md（托管块外）双向 set-diff、CLAUDE.md 过时引用、
workflow bundle 陈旧遮蔽，产出四类分节只读报告。纯读、fail-closed、零写文件。
判断（归组/是否修复）留 SKILL 步骤 4；判据 canonical 见 init.py，本文件保自包含副本
+ 一致性守卫测试机验（见 tests/test_marker_consistency.py）。
"""
import argparse
import os
import re
import sys


class MaintainScanError(Exception):
    """坏输入 / 无法可靠完成扫描。main() 捕获 → stderr → 非零退出（fail-closed）。"""


def find_repo_root(start):
    """从 start 向上找含 .git 的目录，返回其绝对路径；找不到 raise MaintainScanError。"""
    cur = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            raise MaintainScanError(f"未找到 git 仓根（从 {start} 向上）")
        cur = parent


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="sdflow-maintain 确定性只读差异报告（fail-closed）")
    ap.add_argument("--root", default=None, help="仓根，缺省自动探测 git 根")
    args = ap.parse_args(argv)
    try:
        root = args.root or find_repo_root(os.getcwd())
        report = run_scan(root)
    except MaintainScanError as e:
        print(f"[maintain_scan] ERROR {e}", file=sys.stderr)
        return 2
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

> 注：`run_scan` 在 Task 2 引入；本步先留 `def run_scan(root): return ""` 占位使模块可加载。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-maintain/tests/test_maintain_scan.py -x -q`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p4-maintain-scan:task1-dataclass-skeleton "maintain_scan 模块骨架 + MaintainScanError + find_repo_root + tmp 仓夹具"
```

---

### Task 2: specs/rules ↔ INDEX 双向 set-diff（R1，链接路径 join + 托管块排除 + 四类判据）

**Files:**
- Modify: `sdflow-maintain/scripts/maintain_scan.py`
- Test: `sdflow-maintain/tests/test_maintain_scan.py`

**Interfaces:**
- Consumes: `MaintainScanError`, `find_repo_root`（Task 1）。
- Produces:
  - `MANAGED_TOKEN_START = "opsx-init:rules:start"` / `MANAGED_TOKEN_END = "opsx-init:rules:end"` — token 子串常量（非裸短串）。
  - `scan_fs_specs(root) -> set` / `scan_fs_rules(root) -> set`（rules/ 缺失返回空集）。
  - `split_managed_block(index_text) -> (body_lines: list, warnings: list)` — fence-aware 剥托管块，返回块外行 + 告警（块内探到 `specs/*/spec.md` → 告警；marker 不配对 → raise MaintainScanError）。
  - `parse_index_entries(body_lines) -> dict` — `{"spec": set, "rule": set}`，链接路径 join；结构行跳过；非-spec/rule 链接排除；有链接语法但 target 解析不出路径 → raise MaintainScanError。
  - `set_diff(fs, indexed) -> dict` — `{"new": {"spec": set, "rule": set}, "stale": {"spec": set, "rule": set}}`。

- [ ] **Step 1: 写失败测试（四类判据 + 托管块排除 + 双向 diff）**

追加到 `test_maintain_scan.py`：

```python
def _run(root):
    return ms.run_scan(root)


def test_new_unindexed_spec(tmp_path):
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body="")
    r = _run(root)
    assert "新增未索引" in r and "foo" in r


def test_stale_indexed_rule(tmp_path):
    body = "| `bar` | [rules/bar.md](./rules/bar.md) | x |"
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body)
    r = _run(root)
    assert "已删未清理" in r and "bar" in r


def test_fully_consistent(tmp_path):
    body = "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |"
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body=body)
    r = _run(root)
    assert "一致" in r


def test_managed_block_entries_not_stale(tmp_path):
    # 托管块内列 trigger-catalog（无对应 rules/rule 文件），MUST NOT 报「已删未清理」
    root = make_repo(tmp_path, specs=[], rules=[], index_body="",
                     managed_entries=["trigger-catalog"])
    r = _run(root)
    assert "trigger-catalog" not in r


def test_non_spec_link_row_excluded(tmp_path):
    # retro-report → retro/report.md 既非 specs 也非 rules，MUST NOT 参与 set-diff
    body = "| `retro-report` | [retro/report.md](./retro/report.md) | x |"
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body)
    r = _run(root)
    assert "retro-report" not in r
    assert "已删未清理" not in r or "无" in r


def test_managed_marker_unpaired_fails(tmp_path):
    # 只有 start 无 end → 结构不可信 → 非零退出（防假一致）
    idx = f"# I\n\n{MANAGED_START}\n| `x` | [rules/x.md](./rules/x.md) | y |\n"
    root = make_repo(tmp_path, specs=[], rules=[], index_body="")
    (os.path.join(root, "openspec", "INDEX.md"))
    import pathlib
    pathlib.Path(root, "openspec", "INDEX.md").write_text(idx, encoding="utf-8")
    with pytest.raises(ms.MaintainScanError):
        ms.run_scan(root)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-maintain/tests/test_maintain_scan.py -x -q -k "new_unindexed or stale_indexed or consistent or managed or non_spec"`
Expected: FAIL（`run_scan` 仍是占位空实现）

- [ ] **Step 3: 写实现（set-diff 核心）**

替换 `maintain_scan.py` 里的 `run_scan` 占位，加入以下函数（放在 `main` 之前）：

```python
MANAGED_TOKEN_START = "opsx-init:rules:start"
MANAGED_TOKEN_END = "opsx-init:rules:end"

# 链接目标路径 join-key（H3/D1）：只纳 specs/{name}/spec.md 与 rules/{name}.md
_SPEC_LINK = re.compile(r"specs/([a-z0-9-]+)/spec\.md")
_RULE_LINK = re.compile(r"rules/([a-z0-9-]+)\.md")
_ANY_LINK = re.compile(r"\]\(([^)]+)\)")  # markdown 链接 target


def scan_fs_specs(root):
    d = os.path.join(root, "openspec", "specs")
    if not os.path.isdir(d):
        raise MaintainScanError("openspec/specs/ 缺失")
    return {
        name for name in os.listdir(d)
        if os.path.isfile(os.path.join(d, name, "spec.md"))
    }


def scan_fs_rules(root):
    d = os.path.join(root, "openspec", "rules")
    if not os.path.isdir(d):
        return set()  # rules/ 可选，缺失=合法空集
    return {
        f[:-3] for f in os.listdir(d)
        if f.endswith(".md") and os.path.isfile(os.path.join(d, f))
    }


def _is_marker_line(line, token):
    """fence-aware 由调用方处理；此处判「含 token ∧ lstrip 后以 <!-- 起」（镜像 init.py）。"""
    return token in line and line.lstrip().startswith("<!--")


def split_managed_block(index_text):
    """fence-aware 剥 opsx-init:rules 托管块，返回 (块外行列表, 告警列表)。
    marker 不配对 → MaintainScanError（畸形托管块不静默当边界，接 D2）。
    块内探到 specs/*/spec.md 模式 → 告警（M8/D11 堵审计无人区）。"""
    lines = index_text.splitlines()
    in_fence = False
    start_idx = end_idx = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if start_idx is None and _is_marker_line(line, MANAGED_TOKEN_START):
            start_idx = i
        elif start_idx is not None and end_idx is None and _is_marker_line(line, MANAGED_TOKEN_END):
            end_idx = i
    warnings = []
    if (start_idx is None) != (end_idx is None):
        raise MaintainScanError("INDEX 托管块 marker 不配对（只有 start 或只有 end），结构不可信")
    if start_idx is not None and end_idx is not None:
        if end_idx < start_idx:
            raise MaintainScanError("INDEX 托管块 marker 顺序错乱（end 在 start 前）")
        block = lines[start_idx:end_idx + 1]
        if any(_SPEC_LINK.search(b) for b in block):
            warnings.append("⚠ 疑似 spec 条目误置于 init 托管块内（应在块外索引）")
        body = lines[:start_idx] + lines[end_idx + 1:]
    else:
        body = lines
    return body, warnings


def parse_index_entries(body_lines):
    """链接路径 join：只纳 specs/{name}/spec.md（spec 类）/ rules/{name}.md（rule 类）。
    四类判据（H2/Q1=A）：①无链接语法的结构行（表头/分隔/散文）跳过 ②a specs/rules 条目入集
    ②b 非-spec/rule 链接（retro-report 等）静默排除 ③有链接语法但 target 解析不出路径 → fail-closed。"""
    specs, rules = set(), set()
    in_fence = False
    for line in body_lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        links = _ANY_LINK.findall(line)
        if not links:
            continue  # ① 结构行，跳过不 fail
        for target in links:
            sm = _SPEC_LINK.search(target)
            rm = _RULE_LINK.search(target)
            if sm:
                specs.add(sm.group(1))
            elif rm:
                rules.add(rm.group(1))
            # ②b 非-spec/rule 链接（retro/report.md, roadmaps/…）静默排除
    return {"spec": specs, "rule": rules}


def set_diff(fs, indexed):
    return {
        "new": {k: fs[k] - indexed[k] for k in ("spec", "rule")},
        "stale": {k: indexed[k] - fs[k] for k in ("spec", "rule")},
    }


def _read_index(root):
    p = os.path.join(root, "openspec", "INDEX.md")
    if not os.path.isfile(p):
        raise MaintainScanError("openspec/INDEX.md 缺失")
    try:
        return open(p, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        raise MaintainScanError(f"INDEX.md 不可读: {e}")


def run_scan(root):
    fs = {"spec": scan_fs_specs(root), "rule": scan_fs_rules(root)}
    body, mgr_warns = split_managed_block(_read_index(root))
    indexed = parse_index_entries(body)
    diff = set_diff(fs, indexed)
    # 报告渲染在 Task 7 完善；此处最小可断言渲染
    return build_report(diff, mgr_warns, claude_refs=[], stale_shadow=[])


def build_report(diff, mgr_warns, claude_refs, stale_shadow):
    lines = ["# maintain_scan 差异报告", ""]
    any_diff = any(diff[k][t] for k in ("new", "stale") for t in ("spec", "rule"))
    lines.append("## 新增未索引")
    for t in ("spec", "rule"):
        for n in sorted(diff["new"][t]):
            lines.append(f"- {n}（{t}）")
    lines.append("## 已删未清理")
    for t in ("spec", "rule"):
        for n in sorted(diff["stale"][t]):
            lines.append(f"- {n}（{t}）")
    if not any_diff:
        lines.append("")
        lines.append("一致，无差异")
    for w in mgr_warns:
        lines.append(w)
    return "\n".join(lines)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-maintain/tests/test_maintain_scan.py -x -q`
Expected: PASS（全部 Task1+Task2 用例通过）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p4-maintain-scan:task2-setdiff-linkjoin "specs/rules↔INDEX 双向 set-diff：链接路径 join + fence-aware 托管块排除 + 四类判据 + marker 配对校验"
```

---

### Task 3: CLAUDE.md 过时引用扫描（R2，匹配契约）

**Files:**
- Modify: `sdflow-maintain/scripts/maintain_scan.py`
- Test: `sdflow-maintain/tests/test_maintain_scan.py`

**Interfaces:**
- Consumes: `set_diff` 的 `stale` 结果（已删条目集）。
- Produces: `scan_claude_refs(root, deleted) -> list[str]` — 返回 `["<CLAUDE路径>:<行号>: <被引已删名>", ...]`；`deleted` 为已删 spec+rule 名集合。

- [ ] **Step 1: 写失败测试（引已删 spec / 占位符泛指围栏不误报）**

```python
def test_claude_stale_ref_reported(tmp_path):
    # INDEX 列 gone（spec 类）但 fs 无 → gone 进已删集；CLAUDE.md 引 gone → 报
    body = "| `gone` | [specs/gone/spec.md](./specs/gone/spec.md) | x |"
    claude = "见 openspec/specs/gone/spec.md 的定义\n"
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body, claude=claude)
    r = _run(root)
    assert "过时引用" in r and "gone" in r and "CLAUDE.md" in r


def test_claude_placeholder_generic_fence_not_reported(tmp_path):
    body = "| `gone` | [specs/gone/spec.md](./specs/gone/spec.md) | x |"
    claude = textwrap.dedent("""\
        占位: openspec/roadmaps/{name}/ 是活文档
        泛指: openspec/specs/ 目录
        ```
        围栏举例: openspec/specs/gone/spec.md
        ```
        """)
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body, claude=claude)
    r = _run(root)
    # gone 仍是已删集，但 CLAUDE 里只有占位/泛指/围栏 → 不报 CLAUDE 过时引用
    assert "过时引用" not in r or "CLAUDE.md" not in r.split("过时引用")[1].split("陈旧遮蔽")[0]
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-maintain/tests/test_maintain_scan.py -x -q -k "claude"`
Expected: FAIL（`scan_claude_refs` 未定义 / 报告无「过时引用」节）

- [ ] **Step 3: 写实现**

在 `maintain_scan.py` 加入，并把 `run_scan` 里 `claude_refs=[]` 换成实调用：

```python
# 引用匹配契约（M1/D4）：openspec/(specs|rules)/<name>(/|.md)，<name> ∈ [a-z0-9-]+
_REF = re.compile(r"openspec/(?:specs|rules)/([a-z0-9-]+)(?:/|\.md)")
# 占位符：花括号 token（{name} 等）
_PLACEHOLDER = re.compile(r"\{[a-z0-9_-]+\}")


def _iter_claude_files(root):
    for dirpath, _dirs, files in os.walk(root):
        if os.sep + ".git" in dirpath:
            continue
        if "CLAUDE.md" in files:
            yield os.path.join(dirpath, "CLAUDE.md")


def scan_claude_refs(root, deleted):
    """扫根+子目录 CLAUDE.md，报引用已删 spec/rule 路径的位置。
    排除：代码围栏/行内 code、占位符 {name}、泛指路径（无具体 <name>）。"""
    hits = []
    for path in _iter_claude_files(root):
        try:
            text = open(path, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError) as e:
            raise MaintainScanError(f"CLAUDE.md 不可读: {path}: {e}")
        in_fence = False
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            # 剥行内 code 段再匹配（排除 `...` 内提及）
            stripped = re.sub(r"`[^`]*`", "", line)
            stripped = _PLACEHOLDER.sub("", stripped)
            for name in _REF.findall(stripped):
                if name in deleted:
                    rel = os.path.relpath(path, root)
                    hits.append(f"{rel}:{lineno}: {name}")
    return hits
```

在 `run_scan` 内计算 `deleted` 并调用：

```python
    deleted = diff["stale"]["spec"] | diff["stale"]["rule"]
    claude_refs = scan_claude_refs(root, deleted)
    return build_report(diff, mgr_warns, claude_refs=claude_refs, stale_shadow=[])
```

并在 `build_report` 加「过时引用」分节（在「已删未清理」之后）：

```python
    lines.append("## 过时引用（CLAUDE.md）")
    for ref in claude_refs:
        lines.append(f"- {ref}")
    if not claude_refs:
        lines.append("- 无")
```

> 注：`build_report` 的 `any_diff`「一致」判定此步起同时纳入 `claude_refs`/`stale_shadow` 空——Task 7 统一收口，本步先保证分节渲染与 stale spec 报告不回归。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-maintain/tests/test_maintain_scan.py -x -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p4-maintain-scan:task3-claude-refs "CLAUDE.md 过时引用扫描：匹配契约（排除围栏/占位符/泛指）+ 文件行号定位"
```

---

### Task 4: workflow bundle 陈旧遮蔽兜底扫描（R3）

**Files:**
- Modify: `sdflow-maintain/scripts/maintain_scan.py`
- Test: `sdflow-maintain/tests/test_maintain_scan.py`

**Interfaces:**
- Produces:
  - `RULE_MARKERS = ("workflow.md", "spec-checklists", "code-checklists")` — 自包含副本（canonical = init.py，守卫机验）。
  - `scan_stale_shadow(root) -> list[str]` — 检 `openspec/workflow/` 残留规则本体 + 仓根 `hack/checkpoint-commit.sh` 孤儿；命中出语义等价告警文案。

- [ ] **Step 1: 写失败测试**

```python
def test_stale_shadow_workflow_body(tmp_path):
    body = ""
    root = make_repo(tmp_path, specs=[], rules=[], index_body=body,
                     workflow=["workflow.md"])
    r = _run(root)
    assert "陈旧遮蔽" in r and "workflow.md" in r


def test_stale_shadow_only_tools_clean(tmp_path):
    root = make_repo(tmp_path, specs=[], rules=[], index_body="")
    wf = os.path.join(root, "openspec", "workflow", "tools")
    os.makedirs(wf)
    open(os.path.join(wf, "anchor_lint.py"), "w").write("x")
    r = _run(root)
    # 陈旧遮蔽节存在但无残留规则本体
    seg = r.split("陈旧遮蔽")[1]
    assert "workflow.md" not in seg and "spec-checklists" not in seg
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-maintain/tests/test_maintain_scan.py -x -q -k "stale_shadow"`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
RULE_MARKERS = ("workflow.md", "spec-checklists", "code-checklists")


def scan_stale_shadow(root):
    """周期性兜底：openspec/workflow/ 残留规则本体 → 遮蔽全局 canonical。仅报告。
    canonical 判据 = init.py:RULE_MARKERS（本副本经一致性守卫机验，见 test_marker_consistency）。"""
    warns = []
    wf = os.path.join(root, "openspec", "workflow")
    found = [m for m in RULE_MARKERS if os.path.exists(os.path.join(wf, m))]
    if found:
        warns.append(
            "⚠ openspec/workflow/ 残留规则副本（" + "、".join(found)
            + "）——遮蔽全局 bundle 且不再被 update 刷新："
            "想跟全局最新→手动删净；想 pin 这一版→留着（显式逃生口）")
    if os.path.isfile(os.path.join(root, "hack", "checkpoint-commit.sh")):
        warns.append(
            "⚠ hack/checkpoint-commit.sh 为旧版仓内副本（checkpoint 已全局化 → ~/.sdflow/hack/）："
            "删=用全局；若保留本地 workflow.md 副本（pin）且其仍引用仓内路径→勿删")
    return warns
```

`run_scan` 改为 `stale_shadow = scan_stale_shadow(root)` 并传入 `build_report`；`build_report` 加分节：

```python
    lines.append("## 陈旧遮蔽（workflow bundle）")
    for w in stale_shadow:
        lines.append(f"- {w}")
    if not stale_shadow:
        lines.append("- 无")
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-maintain/tests/test_maintain_scan.py -x -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p4-maintain-scan:task4-stale-shadow "workflow bundle 陈旧遮蔽兜底扫描：RULE_MARKERS 副本 + checkpoint 孤儿检查 + 语义等价告警文案"
```

---

### Task 5: 坏输入 fail-closed + 只读不变量收口（R4/R5）

**Files:**
- Modify: `sdflow-maintain/scripts/maintain_scan.py`
- Test: `sdflow-maintain/tests/test_maintain_scan.py`

**Interfaces:**
- Consumes: 全部 Task1-4 函数。
- Produces: `build_report` 的「一致」判定统一纳入四类（new/stale/claude_refs/stale_shadow）；CLI 退出码语义收口。

- [ ] **Step 1: 写失败测试（负例非零 + 0 条合法 + 只读不变量）**

```python
def test_index_missing_nonzero(tmp_path):
    root = make_repo(tmp_path, specs=["foo"], rules=[], index_body=None)  # 无 INDEX.md
    rc = ms.main(["--root", root])
    assert rc != 0


def test_specs_dir_missing_nonzero(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "openspec").mkdir()
    (tmp_path / "openspec" / "INDEX.md").write_text("# I\n", encoding="utf-8")
    rc = ms.main(["--root", str(tmp_path)])
    assert rc != 0


def test_zero_entries_index_is_ok_not_fail(tmp_path):
    # 结构完好、0 条 spec 条目 → 退出 0 + 全部报新增未索引（响亮，非 fail）
    root = make_repo(tmp_path, specs=["foo", "baz"], rules=[], index_body="")
    rc = ms.main(["--root", root])
    assert rc == 0
    r = _run(root)
    assert "foo" in r and "baz" in r


def test_rules_dir_missing_is_ok(tmp_path):
    body = "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |"
    root = make_repo(tmp_path, specs=["foo"], rules=None, index_body=body)  # 无 rules/
    rc = ms.main(["--root", root])
    assert rc == 0


def test_readonly_no_file_writes(tmp_path):
    body = "| `foo` | [specs/foo/spec.md](./specs/foo/spec.md) | x |"
    root = make_repo(tmp_path, specs=["bar"], rules=[], index_body=body)
    before = subprocess.run(["git", "-C", root, "add", "-A"], capture_output=True)
    # 初始 commit 使 git status 可比
    subprocess.run(["git", "-C", root, "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-m", "init", "--allow-empty"], capture_output=True)
    subprocess.run(["git", "-C", root, "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", root, "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-m", "seed"], capture_output=True)
    ms.main(["--root", root])
    st = subprocess.run(["git", "-C", root, "status", "--porcelain"],
                        capture_output=True, text=True)
    assert st.stdout.strip() == ""
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-maintain/tests/test_maintain_scan.py -x -q -k "missing or zero_entries or rules_dir or readonly"`
Expected: FAIL（部分场景未收口）

- [ ] **Step 3: 写实现（收口）**

调整 `build_report` 的 `any_diff` 判定，把 `claude_refs`/`stale_shadow` 也纳入「是否一致」，并仅当四类全空才输出「一致，无差异」：

```python
def build_report(diff, mgr_warns, claude_refs, stale_shadow):
    lines = ["# maintain_scan 差异报告", ""]
    has_diff = (
        any(diff[k][t] for k in ("new", "stale") for t in ("spec", "rule"))
        or bool(claude_refs) or bool(stale_shadow)
    )
    # 新增未索引 / 已删未清理 / 过时引用 / 陈旧遮蔽 四类分节（保持 Task2-4 已加分节）
    ...
    if not has_diff and not mgr_warns:
        lines.append("")
        lines.append("一致，无差异")
    return "\n".join(lines)
```

确认 `scan_fs_specs` 已对 `specs/` 缺失 raise、`_read_index` 已对 INDEX 缺失 raise、`scan_fs_rules` 对 rules/ 缺失返回空集——Task1-4 已具备，本步仅补 `build_report` 收口 + 确保 `main` 的非零路径覆盖全部 `MaintainScanError`。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-maintain/tests/test_maintain_scan.py -x -q`
Expected: PASS（全绿）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p4-maintain-scan:task5-failclosed-readonly "坏输入 fail-closed 收口（INDEX/specs 缺失非零、0 条合法、rules 可选）+ 只读不变量 git status 断言"
```

---

### Task 6: 跨脚本共享判据一致性守卫（R-guard）

**Files:**
- Create: `sdflow-maintain/tests/test_marker_consistency.py`

**Interfaces:**
- Consumes: `maintain_scan.RULE_MARKERS`、`maintain_scan.MANAGED_TOKEN_START`；`init.py:RULE_MARKERS`、`init.py:MARK_IDX`。

- [ ] **Step 1: 写守卫测试（RULE_MARKERS 相等 + token 契约 + 端到端 fixture + hard-fail 加载）**

```python
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
```

- [ ] **Step 2: 跑测试确认（预期通过——常量已在 Task4/Task2 落地）**

Run: `pytest sdflow-maintain/tests/test_marker_consistency.py -x -q`
Expected: PASS（若失败说明 RULE_MARKERS/token 与 init 不一致，须回改 maintain_scan 常量对齐 canonical）

- [ ] **Step 3: 无额外实现（守卫为断言，不改产品码）**

若 Step 2 红：核对 `maintain_scan.RULE_MARKERS` 逐字等于 `init.py:169`、`MANAGED_TOKEN_START` 等于 `init.MARK_IDX[0].split()[1]`（= `opsx-init:rules:start`），改 maintain_scan 对齐后重跑。

- [ ] **Step 4: 跑全套测试确认无回归**

Run: `pytest sdflow-maintain/tests/ -q`
Expected: PASS（全绿）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p4-maintain-scan:task6-marker-guard "跨脚本一致性守卫：RULE_MARKERS 相等 + token==init.MARK_IDX 契约 + 真实 INDEX 端到端 fixture + 加载 hard-fail"
```

---

### Task 7: SKILL.md 集成 + 单一源收敛

**Files:**
- Modify: `sdflow-maintain/SKILL.md`

**Interfaces:** 无代码接口；文档改写。

- [ ] **Step 1: 改写 SKILL.md 步骤 1-3 为调脚本**

把 `sdflow-maintain/SKILL.md` 的「步骤 1-3」（当前 17-51 行手做 prose）整体替换为：

```markdown
1-3. **调 maintain_scan.py 出只读差异报告**

   跑 `python3 sdflow-maintain/scripts/maintain_scan.py --root <仓根>`（缺省自动探测 git 根），
   得四类分节只读报告：**新增未索引** / **已删未清理**（specs/rules ↔ INDEX 托管块外双向 set-diff，
   链接路径 join）/ **过时引用**（CLAUDE.md 引用已删 spec/rule）/ **陈旧遮蔽**（workflow bundle 残留规则本体）。

   脚本纯读、fail-closed（坏输入非零退出 + stderr 明示，绝不半信半疑输出「一致」），零写文件。
   set-diff 判据（RULE_MARKERS / opsx-init:rules 托管块 token）canonical 见 `sdflow-init/scripts/init.py`，
   maintain_scan 保自包含副本经一致性守卫 pytest（`tests/test_marker_consistency.py`）机验同步。
```

保留步骤 4（模型判断是否修复 INDEX、新 spec 归哪组）、步骤 5（提示跑 retro）与「护栏」节不变。

- [ ] **Step 2: 删陈旧遮蔽 prose 清单复述（闭 T17）**

在 SKILL.md 步骤 4 前后确认：陈旧遮蔽判据不再在 SKILL prose 里复述文件名清单（原 47-51 行的清单已随步骤 1-3 改写移除），改为「见脚本 + 一致性守卫机验」。若「护栏」或其他节仍有 `workflow.md / spec-checklists / code-checklists` 清单复述，删之。

- [ ] **Step 3: 人读校验（无自动测试）**

Run: `python3 sdflow-maintain/scripts/maintain_scan.py --root . 2>&1 | head -40`
Expected: 报告四类分节渲染正常，与本仓实际一致；`git status --porcelain` 无非-openspec 改动增量。

- [ ] **Step 4: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p4-maintain-scan:task7-skill-integration "SKILL.md 步骤 1-3 改为调 maintain_scan.py + 删陈旧遮蔽清单复述（闭 T17，判据见脚本+守卫）"
```

---

### Task 8: 分类文档三处订正（M6/D9）

**Files:**
- Modify: `CLAUDE.md`（仓根）
- Modify: `README.md`

**Interfaces:** 无代码接口；分类文档一致性。

- [ ] **Step 1: CLAUDE.md「带脚本+测试的 skill」名单加 sdflow-maintain**

在 `CLAUDE.md`「## 运行测试」节的「带脚本+测试的 skill 仅这几个」列表里加入 `sdflow-maintain`（当前含 `sdflow-buglist`、`sdflow-todolist`、`sdflow-issues`、`sdflow-init`、`sdflow-retro`）。

- [ ] **Step 2: CLAUDE.md「两类 skill」把 sdflow-maintain 挪到数据类**

在「### 两类 skill」把 `sdflow-maintain` 从「编排类（纯 Markdown）」列表移除，加入「数据类（Markdown + Python）」列表。

- [ ] **Step 3: README.md 表述订正**

在 `README.md` 找到「其余为纯 Markdown 编排类」或 Skills 列表中 sdflow-maintain 的分类描述，订正为数据类（含 scripts/ + tests/）。

Run: `grep -n "sdflow-maintain\|纯 Markdown 编排" README.md`
据结果精确订正对应行。

- [ ] **Step 4: 校验三处一致**

Run: `grep -rn "sdflow-maintain" CLAUDE.md README.md`
Expected: 三处均把 sdflow-maintain 归为数据类，无「编排类/纯 Markdown」残留矛盾表述。

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p4-maintain-scan:task8-classification-docs "分类文档三处订正：CLAUDE.md 数据类名单+两类归属、README 表述，sdflow-maintain 升数据类"
```

---

### Task 9: 验收 + dogfood + defer 登记

**Files:**
- 无新增；跑测试 + dogfood + 记 todolist。

- [ ] **Step 1: 全套测试绿**

Run: `pytest sdflow-maintain/tests/ -q`
Expected: PASS，无 warning。负例（INDEX/specs 缺失、marker 不配对）确认非零退出。

- [ ] **Step 2: dogfood 本仓真跑**

Run: `python3 sdflow-maintain/scripts/maintain_scan.py --root . ; echo "rc=$?"`
Expected: `rc=0`；报告四类分节；**retro-report 不被误报「已删未清理」**（真实 INDEX 托管块外含 `retro-report`→`retro/report.md` 非-spec 行，链接路径 join 应排除）；托管块内 workflow 条目不被误报。

- [ ] **Step 3: dogfood 零写文件确认**

Run: `git status --porcelain | grep -v '^.. openspec/' || echo "无非-openspec 改动"`
Expected: 脚本运行未产生任何文件改动。

- [ ] **Step 4: 记 defer 项到 todolist**

用 `/sdflow-todolist` 记入以下已知残差（design D4/D6/M3/M9 明列，非无声留着）：
- `resolve-workflow.sh` bash 第 3 份 RULE_MARKERS 内联副本跨语言难同守 → defer（本 change 不扩 scope）。
- 陈旧遮蔽告警文案第三处跨脚本复述 + checkpoint 孤儿路径，R-guard 不机验文案（文案守卫脆）→ defer。
- 守卫 `importorskip` 兜底（sdflow-init 目录整体缺席场景的更优雅降级）→ defer。

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p4-maintain-scan:task9-acceptance-dogfood "验收：pytest 全绿 + 本仓 dogfood（retro-report 不误报）+ 只读确认 + defer 三残差记 todolist"
```

---

## 测试覆盖图（TG-18）

| code path | 测试类型 | 用例 |
|---|---|---|
| set-diff（fs↔INDEX，链接路径 join） | 单元·正例 | Task2: new_unindexed / stale_indexed / consistent |
| 托管块排除（token 子串 + fence-aware） | 单元·正例 | Task2: managed_block_entries_not_stale；Task6: end_to_end_real_index |
| 非-spec 链接行排除（H3/D1） | 单元·正例 | Task2: non_spec_link_row_excluded |
| marker 不配对 fail-closed | 单元·负例 | Task2: managed_marker_unpaired_fails |
| CLAUDE.md 过时引用 + 匹配契约 | 单元·正例/排除 | Task3: claude_stale_ref / placeholder_generic_fence |
| 陈旧遮蔽判据 | 单元·正例 | Task4: stale_shadow_workflow_body / only_tools_clean |
| 坏输入 fail-closed | 单元·负例 | Task5: index_missing / specs_dir_missing（非零） |
| 0 条合法 / rules 可选 | 单元·边界 | Task5: zero_entries_index_is_ok / rules_dir_missing |
| 只读不变量 | 单元·不变量 | Task5: readonly_no_file_writes（git status 无变更） |
| 跨脚本一致性守卫 | 单元·守卫 | Task6: rule_markers_equal / token_matches_init |
| 端到端 dogfood | 集成 | Task9: 本仓真跑（retro-report 不误报） |

## Self-Review 备忘

- **spec 覆盖**：R1=Task2、R2=Task3、R3=Task4、R4=Task5、R5=Task5(只读)+Task7(报告)、R-guard=Task6；spec-review 增量 9.1/9.2/9.4=Task2、9.3=Task6、9.5/9.7=Task3、9.6=Task5、9.8=Task2(告警)、9.9=Task9(defer)、9.10=proposal Non-Goal（留痕，无动作）。
- **类型一致**：`run_scan`/`build_report`/`set_diff`/`scan_*` 签名跨任务一致；`diff` 结构 `{"new":{"spec","rule"}, "stale":{...}}` 全程统一。
- **判断留人**：脚本零写文件、不建议归组（D1/D3），归组与是否修复留 SKILL 步骤 4。
