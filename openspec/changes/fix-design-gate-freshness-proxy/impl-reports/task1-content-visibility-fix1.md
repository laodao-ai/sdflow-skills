# Task1 双轴审 Minor 修复轮（fix1）

**范围**：Task 1（commit `f5731ad`）双轴审 PASS 后的 4 条 Minor，按「与本次功能相关 → 立即 fold」当场做掉。
**不变量**：`is_stale` 对外可观察行为逐字不变（本票仍不引入任何豁免）；BR-6 护栏（无 `--no-merges` / `--first-parent`）未动。

## F1 · 监视集成员判据去重（fail-open 风险）

**问题**：`sub in DESIGN_WATCHED_NAMES or sub.startswith("specs/")` 在 `design_watched_subs`
与 `is_stale` 的内联循环里各有一份。将来新增一类监视路径（如 `adr/`）若只改一处，
`design_watched_subs` 会漏识 ⇒ `design_frame_exempt` 把帧内路径集误算成 `{tasks.md}` ⇒ **豁免误开**。

**修法**：`is_stale` 的 design 分支改为直接调 `design_watched_subs` 求帧级路径集，
删掉内联的第二份判据 —— 判据现在**只有一处**。

```python
subs = design_watched_subs(lines[1:], base)
if subs - {"tasks.md"}:
    return True, "stale"
if subs and not design_frame_exempt(root, frame_sha, lines[1:], base):
    return True, "stale"
```

等价性：原逻辑「遇到非 tasks.md 的监视路径立即 True；否则 tasks 被触及且不豁免 → True」
与新逻辑逐分支同构（`subs` 非空且 `subs - {tasks.md}` 为空 ⟺ `subs == {"tasks.md"}`）。
`ship_gate.py` 全文 grep `DESIGN_WATCHED_NAMES` 现仅 2 处：常量定义 + `design_watched_subs`。

**变异验证**（临时用例 `test_zz_f1_mut.py`，验后删除）：
monkeypatch `design_watched_subs` 为「额外识别 `adr/`」（模拟"新增一类监视路径只改一处"），
再提交一个触及 `openspec/changes/demo/adr/0001.md` 的普通帧，断言 `is_stale(...) == (True, "stale")`。

| 被测代码 | 结果 |
|---|---|
| 本次修复后 | **PASS** —— 只改一处，`is_stale` 立即跟随 |
| `git checkout HEAD -- ship_gate.py`（修复前） | **FAIL** —— 判失鲜不成立，即 fail-open 复现 |

## F2 · `test_exempt_conservative_when_form_disqualified` 补前提校准

chmod 造的「形态不合格」在 `core.fileMode=false` 环境下不入 git ⇒ 该提交对 `tasks.md` 无变更
⇒ 用例照样绿，但通过理由从「形态闸门拦下」变成「路径未触及」，形态分支静默失守。
照抄同族用例 `test_blob_pair_chmod_only_is_conservative`（:326）的 raw 非空断言。

**判别力验证**：`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.fileMode GIT_CONFIG_VALUE_0=false`
下跑该用例 → **明确失败**并打出「chmod 未被 git 记录（core.fileMode 关？）本例失去区分力」，
而非悄悄变绿。同一环境下 `test_blob_pair_chmod_only_is_conservative` 亦如期失败（同族一致）。

## F3 · `test_blob_pair_type_change_to_symlink_is_conservative` 补前提校准

`core.symlinks=false` 时 git 把 symlink 记成普通文件内容变更（`100644` / status `M`）⇒
用例退化为「普通内容修改」，类型变更分支失守。新增断言：raw 行 dstmode 为 `120000` 或状态位以 `T` 起始。

**判别力验证**：`GIT_CONFIG_COUNT=... core.symlinks=false` 在 macOS 上不改变 `git add` 的记录
（该配置只影响 checkout 侧），故改为**直接构造退化形态**——把 `tasks.md` 写成含 `target.md`
字面内容的普通文件后提交，断言校准条件求值为 `False`（临时用例 `test_zz_f1_mut.py` 同批，
验后删除）：**PASS**，即退化形态下该断言确会红，判别力成立。

## F4 · `tasks_blob_pair` → `blob_pair`

形参已泛化到任意 `path`（测试正传 `does-not-exist.md`），函数名却锁死 `tasks`。
更名 + 同步全部调用点：`ship_gate.py` 1 处调用，`test_gate_freshness.py` 9 处。
全仓 grep 无残留（仅首轮 impl-report 正文里的历史名称，属归档记述，不改）。

## 测试

| 命令 | 结果 |
|---|---|
| `python3 -m pytest sdflow-ship/tests/ -q` | **197 passed** |
| `python3 -m pytest -q`（仓根全套件） | **1944 passed, 8 skipped, 3 xfailed**，无新增 failure/warning |

> 注：本机 `python3` 无 pytest，实际用 `/usr/bin/python3`（pytest 8.4.2）。
> 8 skipped / 3 xfailed 均为存量（磁盘满用例的本地专属 skipif 等），与本轮无关。
