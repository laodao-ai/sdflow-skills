# Task 3 双轴审返修（第 1 轮）— parity 门 + async 落点

范围：1 Critical + 1 Important（面级，3 假绿）+ 2 Minor（fold）。未动 change 四件套。

---

## 🔴 C1 — async off-critical-path 在 code-review 层无落点

**修法**：把 spec-review `:116/:130` 的「派出即返回」指令按本层措辞补进 code-review 两个 dispatch 站点。

| 位点 | 补入内容（句末） |
|---|---|
| `sdflow-code-review/SKILL.md` hr-tg 站点 | 「——**context 就绪即派；async 分支下 dispatch 调用派出即返回，MUST 立刻继续本步余下工作（能力探针、fan-out 各镜），结果在 Step3 barrier 处 collect**」 |
| `sdflow-code-review/SKILL.md` 第二步半 code-voice | 「**context 就绪即派；async 分支下 dispatch 调用派出即返回，MUST 立刻继续本步余下工作（进第三步汇总），结果在 Step3 barrier 处 collect**」 |

两处均在 **marker 段之外**（站点相关）⇒ 不破 ADR-5 圈内字节等值。
验证：`check_async_branch_parity.py` 改后仍 `✅ 2 处 async host 调度段逐字节一致`。
grep「派出即返回」现 code-review 2 命中、spec-review 2 命中。

---

## Important — 3 个假绿断言（变异存活）+ 面级顺修

### F1 `FORBIDDEN_IN_INTERIOR` 分支死代码
加合成用例 `test_forbidden_token_in_interior_is_red`，**按 `P.FORBIDDEN_IN_INTERIOR` 逐项参数化**：
两侧内容完全相同、段内植入禁用 token → 断言 `P.compare([a,b]) == 1`（**走 compare()**，不再只对真仓调 extract 自断言）。
另加对照组 `test_clean_interior_with_neutral_wording_is_green`（改写成「另一评审 SKILL」即绿），证红的原因就是那个 token。

### F2 `ends[0] < starts[0]` 守卫不施力
新增 `test_end_before_start_raises`：直接对 `P.extract` 断言 `pytest.raises(P.MarkerError)`。
原 `test_end_before_start_is_red`（compare==1）保留为 CLI 语义用例，但不再是该守卫的唯一见证。

### F3 空段守卫——**修的是守卫本身，不只是补用例**
原 `if not ref.strip()` 打在**整段**上，而 `extract()` 返回值恒含两行 marker ⇒ 该条件**永远为假**，
是「不存在的守卫」，无论补什么用例都杀不掉。∴ 把判据下移到正文：

- 脚本新增 `interior(seg)`（去首尾 marker 行），`compare()` 改判 `not interior(ref).strip()`。
- 真仓用例 `test_interior_is_non_empty` 同步改用 `P.interior(...)`（原写法同属恒真假绿）。
- 新增合成用例：`test_empty_interior_is_red`（两侧正文全空）、`test_whitespace_only_interior_is_red`（只剩空白）。

---

## Minor（fold）

### M4 `START_LINE_PREFIX` token 边界
`"<!-- sdflow:async-branch:start"` → `"<!-- sdflow:async-branch:start "`（尾随空格 = token 边界），
并新增 `_is_start(line)` 要求**本行内闭合 `-->`**。新增两个用例：`...:startX -->` 与半截未闭合行均须抛 `MarkerError`。

### M5 `setup.sh` parity 门独立守卫
从 `[ -f hack/sync_principles.py ]` 块中移出，改为自带 `[ -f "$REPO_DIR/hack/check_async_branch_parity.py" ]` 的独立块。
（`:234` 的 warn-only 不中断安装与 `sync_principles.py --check` 同 idiom，**一致，不改**——依 reviewer 判定。）

---

## 变异验证（本条修复成立与否的唯一证据）

逐一施加变异 → 跑 `pytest -q hack/tests/test_async_branch_parity.py` → 恢复。实际输出：

```
=== M1 FORBIDDEN -> if False ===
FAILED test_forbidden_token_in_interior_is_red[sdflow-spec-review]
FAILED test_forbidden_token_in_interior_is_red[sdflow-code-review]
FAILED test_forbidden_token_in_interior_is_red[spec-review-report]
FAILED test_forbidden_token_in_interior_is_red[code-review-report]
4 failed, 22 passed in 0.07s

=== M2 删 end<start 守卫 ===
E   Failed: DID NOT RAISE <class 'check_async_branch_parity.MarkerError'>
FAILED test_end_before_start_raises
1 failed, 25 passed in 0.06s

=== M3 删空段守卫 ===
FAILED test_empty_interior_is_red
FAILED test_whitespace_only_interior_is_red
2 failed, 24 passed in 0.07s

=== M4 START 前缀放松（去边界空格 + 去 `-->` 闭合要求）===
FAILED test_start_prefix_requires_token_boundary
FAILED test_start_line_must_close_on_same_line
2 failed, 24 passed in 0.06s

=== 恢复后 ===
26 passed in 0.06s
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致
```

四个变异**各有至少一个用例变红**，恢复后全绿。

---

## 全量验证

| 门 | 结果 |
|---|---|
| `python3 -m pytest -q` | **1645 passed, 2 skipped**（前轮 1635 → +10 用例） |
| `python3 hack/check_async_branch_parity.py` | ✅ 2 处逐字节一致，rc=0 |
| `python3 hack/sync_principles.py --check` | ✅ 20 个投放面一致，rc=0 |
| `bash -n setup.sh` | ok |

四件套（proposal/design/tasks/specs）**未改**，ship_gate 设计门新鲜度不受影响。
</content>
