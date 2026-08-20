# cr-fix1 — 代码审冷层缺陷修复（ship_gate.py / anchor_writeback.py）

修复对象：`sdflow-code-review` 冷层代码审确认的一簇真实缺陷，全部集中在
`sdflow-ship/scripts/ship_gate.py` 与其 sibling `sdflow-ship/scripts/anchor_writeback.py`（紧耦合，
`anchor_writeback.py` 通过 `import ship_gate as sg` 复用后者的指纹/git 出口）。改动处均标注
`[impl-review-fix]`。

## 逐条 finding + 修法 + 红→绿证明

### [Critical C1] manifest 编码非单射（记录分隔符 `\n` 与路径合法字节冲突）

- **验证**：修复前用 `python3 -c` 直接调 `ship_gate.fingerprint_entries` 复现——
  `{b"a\n100644 blob deadbeef\tc": (...)}`（单路径，路径字节里含一段"看起来像另一条记录"的
  文本）与 `{b"a": (...), b"c": (...)}`（两条独立路径）产出完全相同的 manifest 字节与 digest。
- **修法**：`ship_gate.py::_manifest_bytes_from_entries` 记录间分隔符由 `b"\n".join(...)` 改为
  `b"\0".join(...)`（NUL）；`_manifest_entries_from_bytes`（诊断侧逆解析）同步改为按 `b"\0"`
  分割。git 路径按 `ls-tree -z` 的设计前提本身不能含 NUL（`-z` 正是靠 NUL 做记录终止符），
  故 NUL 对任何合法路径都是无歧义分隔符；record 内 `mode SP type SP oid TAB path` 保持不变
  （mode/type/oid 不含 `\t`，path 含 `\n`/`\t` 现在安全，因为记录级分隔已换用 NUL）。
- **blast radius 核验**：`grep -rn reviewed_manifest openspec/` 确认本 change（尚未 merge）
  自身报告均保留 40-hex 旧格式（`spec-review-report.md`/`code-review-report.md`/`verify-report.md`
  未走 manifest 锚），无任何已落盘的 64-hex+manifest 锚需要迁移。全仓亦无其它消费方手动
  拆分 manifest 字节（唯一读者是 `ship_gate.py` 自身与测试 fixture，均经 `fingerprint_entries`/
  `_manifest_entries_from_bytes` 间接消费，两处已同步改）。
- **红→绿**：
  - `sdflow-ship/tests/test_gate_freshness.py::test_manifest_no_collision_when_path_contains_newline`
    ——修复前 `manifest_a == manifest_b`（断言失败，AssertionError 打出两串相同字节），
    修复后二者不同，测试转绿。
  - `sdflow-ship/tests/test_gate_freshness.py::test_manifest_record_separator_is_nul_not_newline`
    ——修复前 manifest 里无 `\0`（红），修复后有（绿）。
  - 既有 `test_manifest_round_trip_stable_for_tab_and_non_ascii_paths` /
    `test_manifest_distinguishes_different_paths_not_folded` 全程保持绿（NUL framing 不破坏
    既有字节保真 round-trip 语义）。

### [Critical C2] 脏树守卫在 `git status` 失败时静默判「无脏改动」→ fail-open

- **修法**：`anchor_writeback.py::_git_status_porcelain_raw` 改走 `ship_gate._git_run` 单出口，
  返回码非 0 → 调 `_fail(...)` 拒写（不再 `r.stdout if r.returncode == 0 else ""` 折空串）。
- **红→绿**：`test_anchor_writeback_exec.py::test_dirty_guard_fails_loud_when_git_status_returns_nonzero`
  ——monkeypatch `sg._git_run` 使 `status` 子命令返回 rc=128；修复前该用例走到「监视集无脏改动」
  分支，写锚**成功**（报告被写入 `reviewed_sha`），断言失败（红）；修复后 `main()` fail-loud
  `SystemExit(1)`，报告保持未被改写，测试转绿。

### [Important H3] `_git_status_porcelain_raw` 裸 subprocess 无 timeout/OSError 处理

- **修法**：与 C2 同一处改动——改走 `sg._git_run`（统一 timeout=30s + env 清理 + `TimeoutExpired`/
  `OSError` → `GateIndeterminate` 的环境级失败映射），`_git_status_porcelain_raw` 捕获
  `GateIndeterminate` 并转 `_fail`（SystemExit + 清晰诊断，而非裸 traceback 或无限期挂起）。
- **红→绿**：`test_dirty_guard_fails_loud_when_git_status_times_out`——monkeypatch `sg._git_run`
  使 `status` 子命令抛 `GateIndeterminate`（模拟超时）；修复前裸调用不会遇到此路径（旧实现
  连 `sg._git_run` 都不调用，是完全独立的 `subprocess.run`），需在**修复后的代码骨架上**验证
  该捕获路径本身有效——为如实反映「先证伪」纪律：本用例在修复前对 monkeypatch 的目标属性
  `aw.sg._git_run`（尚被 `_git_status_porcelain_raw` 忽略，因旧实现走裸 `subprocess.run`）不产生
  任何效果，`main()` 仍按真实 git 状态（干净）正常写锚成功 → 断言「fail-loud 拒写」失败（红，
  已在全量红跑中确认：`8 failed`，含本用例）；修复后转绿（详见下方「全量红跑记录」）。

### [Important H4] `main()` 中裸 `sg.run_git(...rev-parse...)` 未捕获 `GateIndeterminate`

- **修法**：`main()` 起手的 `--root`/`--git-dir` 两次 `sg.run_git` 调用包一层
  `try/except sg.GateIndeterminate` → `_fail`。
- **红→绿**：`test_git_dir_probe_failure_fails_loud_not_uncaught_traceback`——monkeypatch
  `aw.sg.run_git` 抛 `GateIndeterminate`；修复前该异常未被捕获、直接向上逸出（`pytest.raises
  (SystemExit)` 断言失败，红，已在全量红跑中确认）；修复后 `main()` 捕获并 `_fail`，转绿。

### [high H5] 写锚重建 frontmatter 丢弃其它顶层 YAML 字段

- **验证**：`sdflow-spec-review/SKILL.md:433` 附近明文契约「脚本自动处理 frontmatter 合并：
  若已有首块 frontmatter，脚本将 `ship-gate:` 键合并进该已有块（**保留其它既有字段**，不新开
  第二块）」——旧实现在 `main()` 里直接 `lines = ["---", "ship-gate:"] + ...` 整块重建，任何与
  `ship-gate:` 同级的既有字段（如报告手写的 `title:`）会被静默丢弃，与契约矛盾。
- **修法**：`_split_frontmatter_block` 新增返回值 `block_lines`（首块内部原始行）；新增
  `_replace_shipgate_block(block_lines, new_shipgate_lines)`，只定位并替换块内顶层 `ship-gate:`
  节点这一段（从该 0 缩进行起，到下一个 0 缩进行/块尾止），块内其它顶层字段与嵌套内容原样
  保留；absent（块内本无 `ship-gate:` 键）时新节点插在块最前面。`main()` 改调此函数拼接
  `merged_block`，不再手搓整块。
- **红→绿**：`test_writeback_preserves_other_top_level_frontmatter_fields`——报告首块含
  `title: 一份带标题的报告` + `ship-gate:\n  verify: PASS`；修复前写锚后 `title:` 字段消失
  （断言失败，红，已在全量红跑中确认）；修复后 `title:` 原样保留，`reviewed_sha`/`reviewed_manifest`
  正常写入，转绿。

### [high H6] `--report`/`--change` 未限制在 change 目录内，路径穿越可覆盖任意文件

- **修法**：`--change` 校验为单一目录名（非空、不含 `/`/`\`、不等于 `.`/`..`）；
  `--report` 与 `--change` 拼出 `change_dir`/`report_path` 后各自 `.resolve()`，再用
  `report_path.relative_to(change_dir)` 校验解析后仍落在 change 目录内，逃逸则 `_fail`。
- **红→绿**：
  - `test_report_path_traversal_rejected`——`--report ../../../evil.md`；修复前旧代码直接拼
    `root/openspec/changes/demo/../../../evil.md`，因目标文件不存在而在「报告不存在」分支拒绝
    （表面上"看似安全"，但只是因为测试没有在逃逸目标处放文件——**若攻击者在仓外放一份同名
    文件，旧代码会原样读写它**，本用例的断言锚在诊断文案「逃逸」上，修复前诊断文案是
    「报告不存在」而非「逃逸」，断言失败，红，已在全量红跑中确认）；修复后诊断明确报「逃逸出
    change 目录」，转绿。
  - `test_change_argument_with_path_separator_rejected`——`--change ../other`；修复前诊断文案
    是「报告不存在」（因该路径下确实没有报告文件，只是巧合地被这个理由挡住，不构成真实防护），
    断言「非法」失败，红；修复后 `--change` 校验直接挡在拼路径之前，诊断报「非法」，转绿。
  - 🔴 如实说明：这两条修复前的失败模式不是「完全不设防」，而是「唯一挡住它的理由是测试
    fixture 恰好没在逃逸目标处放文件」——这正是 H6 报告要修的靶心（现状能跑不等于设计对，
    通则③）。

### [中 M7] `_dirty_paths` 跨域 rename 前缀匹配漏判

- **修法**：`_dirty_paths` 对每行取 `path.split(" -> ", 1)[-1]`（含箭头则取目的路径，否则原样）
  作为 domain 排除判据，而非对整行字面量做 `startswith`。
- **红→绿**：
  - `test_dirty_paths_rename_out_of_openspec_is_not_excluded`——`"R  openspec/foo.md -> foo.md"`；
    修复前整行以 `openspec/` 打头被整条跳过（`dirty == []`，断言失败，红）；修复后按目的路径
    `foo.md`（不在 openspec 域）判定，计入 dirty，转绿。
  - `test_dirty_paths_rename_into_openspec_is_excluded`——反方向 `"R  foo.md -> openspec/foo.md"`；
    修复前整行不以 `openspec/` 打头，被计入 dirty（不应计入，断言失败，红）；修复后按目的路径
    `openspec/foo.md` 排除，转绿。

### [中 M9] 缺锚诊断文案漏字段

- **修法**：`ship_gate.py` 的 `REFUSE_START`（设计门未过）诊断文案由「须补 design_approved 与
  reviewed_sha 两个字段」改为直接给出可执行命令
  `anchor_writeback.py --change <name> --report spec-review-report.md --domain design --set
  design_approved=true`，并注明该命令同批写入 `design_approved`/`reviewed_sha`/`reviewed_manifest`
  三字段、锚值由脚本计算、MUST NOT 手写。
- 未加独立回归测试：这是纯文案调整（非判定逻辑），已用 `grep` 确认仓内无测试断言旧文案原文
  （`须补 design_approved 与 reviewed_sha`/`design_approved 与 reviewed_sha`），不会引入回归；
  按基准④，为一句诊断文案写快照测试的性价比低于文案本身已经改对且经全仓 pytest 验证无副作用。

## 全量红跑记录（10 条新增回归测试对应的修复前状态）

用 `git stash push -- sdflow-ship/scripts/ship_gate.py sdflow-ship/scripts/anchor_writeback.py`
临时还原两个脚本到修复前状态（测试文件不还原），重跑：

```
$ /usr/bin/python3 -m pytest sdflow-ship/tests/test_gate_freshness.py -q -k manifest
..FF                                                                     [100%]
2 failed, 2 passed
  FAILED test_manifest_no_collision_when_path_contains_newline
  FAILED test_manifest_record_separator_is_nul_not_newline

$ /usr/bin/python3 -m pytest sdflow-ship/tests/test_anchor_writeback_exec.py -q
8 failed, 5 passed
  FAILED test_dirty_guard_fails_loud_when_git_status_returns_nonzero
  FAILED test_dirty_guard_fails_loud_when_git_status_times_out
  FAILED test_git_dir_probe_failure_fails_loud_not_uncaught_traceback
  FAILED test_writeback_preserves_other_top_level_frontmatter_fields
  FAILED test_report_path_traversal_rejected
  FAILED test_change_argument_with_path_separator_rejected
  FAILED test_dirty_paths_rename_out_of_openspec_is_not_excluded
  FAILED test_dirty_paths_rename_into_openspec_is_excluded
```

全部 10 条新增回归测试在修复前均红。随后 `git stash pop` 恢复修复，重跑同样命令：
`sdflow-ship/tests/` 全套 345 passed（335 既有 + 10 新增），无一失败。

## 自查

- `/usr/bin/python3 -m pytest sdflow-ship/tests/ -q` → **345 passed**（0 failed）。
- 全仓 `/usr/bin/python3 -m pytest -q`（聚合套件，实测耗时 375.33s）：

```
2590 passed, 10 skipped in 375.33s (0:06:15)
[exited with code 0]
```

0 failed，本次修复未引入任何回归。

## 未采纳/需说明的条目

无——待修 7 条（C1/C2/H3/H4/H5/H6/M7/M9，共 8 条，逐条已处置）全部核实为真实缺陷并修复，
无一条 refuted。

## 改动文件

- `sdflow-ship/scripts/ship_gate.py`（C1 manifest 编码、M9 诊断文案）
- `sdflow-ship/scripts/anchor_writeback.py`（C2/H3 脏树守卫 git 出口、H4 main() 异常捕获、
  H5 frontmatter 合并保留其它字段、H6 路径穿越防护、M7 rename 域判定）
- `sdflow-ship/tests/test_gate_freshness.py`（新增 C1 两条回归测试）
- `sdflow-ship/tests/test_anchor_writeback_exec.py`（新增 C2/H3/H4/H5/H6/M7 共 8 条回归测试）
