# hand-off — fix-design-gate-freshness-proxy

2026-07-20 · verify PASS 后产出 · 随归档留档

**一句话**：设计门的新鲜度判据从「纯路径代理」改成「内容判据」——纯勾选框翻转不再撞 `REFUSE_START`；过程中冷层代码审在同一片枚举面上挖出 **6 条 fail-open**（放行未批准设计改动），全部当场修完。

---

## ✅ 完成了什么

> 以下每条我都复核过锚点**确实存在**，不是搬运 verify 的 ✅。

| 交付 | 锚点 |
|---|---|
| **P0 勾选框豁免**：提交在 design 域监视集内只触及 `tasks.md`、形态是普通内容修改、且前后两版按勾选框标记归一化后逐行等值 ⇒ 不失鲜 | `_tasks_content_exempt` / `design_frame_exempt_reason`（`ship_gate.py`）；`test_tasks_only_checkbox_flip_not_stale`、`test_tasks_flip_plus_source_code_not_stale`（🔴 打包提交主用例） |
| **归一化的有界词法**：行首 `CHECKBOX_BYTES_RE` 锚定 + fence 感知（``` / `~~~` / 任意长游程 / 缩进代码块 / HTML 注释）+ 位置对齐禁 LCS | `fence_delim` / `FenceTracker`（**单一源**，四个调用点共用）；`test_content_stale_on_tilde_*`、`..._on_pure_line_reorder` 等 |
| **保守回落**：读取失败 / 前后版缺失 / 状态位不合格（rename·chmod·类型变更）/ merge 任一 parent 不成立 ⇒ 一律判失鲜 | `blob_pair`（双侧显式判 rc）、`_parent_path_status`、`commit_parents` |
| **P1 结构化诊断**：失鲜拒绝携带短 sha / subject / 路径 / 分类原因（混合路径·非勾选框变化·前后版缺失·状态不合格），机读与人读**同源**；默认处置只推「重跑设计门」 | `StaleResult`、`_stale_trigger_hint`；`test_default_disposition_recommends_rerun_design_gate_only`（双向断言该串不出现） |
| **P2 dispatch 信号权威表**：正面陈述完成信号与设计工件的权威归属，缺席不得静默降级 | `sdflow-implement/SKILL.md:255-267`；`sdflow-implement/tests/test_dispatch_signal_authority.py`（4 例机械守） |
| **枚举协议面治**（code-review F1）：`git log --name-only` → `git diff-tree -m -r --raw --no-renames -z --root` | commit `58cef16`；merge / rename / Tab 路径三条端到端用例 |
| **fence 口径单一源跨 skill 同步** | `impl_route.py` 改 import `ship_gate.FenceTracker`，引不到即 `TopoError` fail-closed |

**全套件**：2036 passed / 8 skipped / 3 xfailed / **0 failed**，零新增 warning。

---

## ⏳ 未完成 / 延后

**批次 `fix-design-gate-freshness-proxy`**（见 `openspec/issues/batches.md` 与 `openspec/issues/INDEX.md`），7 项：

🔴 **最该优先的一条**：**B19 — `code` 域仍走 `git log --name-only` ⇒ evil-merge 漏检（fail-open）**。
复审隔离构造实测：两个 parent 的普通提交只碰 `openspec/`、merge 提交自身改 `src.py` ⇒ `is_stale(..., "code")` 返回 `fresh`——**代码审拍板后的源码改动被判新鲜、可随档 ship**。
**为什么没在本 change 内修**：design.md 的 Non-Goals 明写「改动 `code` 域失鲜判据（本 change 只动 design 域）」，且 tasks 4.4p 明确要求 code 域行为逐字不变并有回归锁。阶段三无人类门管的是修复与裁决，**不含推翻已批准的设计边界**。
**它与本次刚修好的 design 域是同一枚举协议面** —— 按基准 3（面治优先于点补），下一个 change 应把已验证的协议直接搬过去，**别沉底**。

其余 6 项：B20（git 二进制缺失 ⇒ `FileNotFoundError` 逸出退出码契约集，全文件级既有缺口）· T187（测试 helper flag-argument smell）· T188（跨 skill 同 basename 测试文件会**中断仓根全局收集**，仓级地雷，建议加 basename 唯一性机械守）· T189（🔴 **基准 5 警号**，见下）· T190（`run_git*` 无 timeout）· T191（评审 diff 包被 `add -A` 带进版本库，~1600 行纯派生内容随归档永久留存）。

**T186 已标 DONE**（evidence `58cef16`）：Task 1 时 defer 的「merge 帧逐 parent 分支不可达」，被后续 F1 修复反超、现已可达。

**被推翻的字面约束（诚实登记，非缺口）**：`tasks.md` 1.1a / 1.1b 的字面机制（「MUST NOT 重构成帧级预扫描」「扩 `git log --format=%H`」）被 code-review F1 推翻——冷层证明旧协议有两条 fail-open，修法必须换成帧级 `diff-tree`。目标达成、机制不同，已勾并带 `done-amendment` 注记，verify 独立复现确认偏离必要。

**Minor 缺口（verify 判可接受）**：code-review 报告里 F5 论证的主次顺序偏现状口吻（不影响结论）。

---

## ▶ 下一阶段建议

1. **【高】开一个 change 把 B19 治掉** —— 把本次已验证的枚举协议（`diff-tree -m -r --raw --no-renames -z --root`）搬到 `code` 域。这是同一片面的另一半，本次因已批准边界所限只能 defer。顺带可把 B20（`FileNotFoundError` ⇒ UNKNOWN(6)）与 T190（`run_git*` timeout）一并做掉——三者同属 `run_git*` 系列健壮性面。
2. **【中】T189：把 `_normalize_checkbox_lines` 的口径反转成白名单** —— 该函数已**第 4 轮**往同一处补语法分支（``` → `~~~` → 四 backtick → 缩进 + HTML 注释），触基准 5 警号「每轮 review 都在同一个函数里补一个新的语法分支 = 这个函数本来就不该存在」。当前靠「超集口径 + fail-closed + 只加在豁免面」三重围栏止损，方向保守可接受，但趋势要收。正解（冷层给的）：只归一化「缩进 ≤3 列、且不在任何 fence / HTML 注释内的行首标记」，白名单天然有界。
3. **【低】T188 加 basename 唯一性守 + T191 把 `*review-package.diff` 加进 `.gitignore`** —— 两条纯仓库卫生，可搭车任意 change。

**方案 B（批准快照 digest）** 仍登记为**目标架构**（设计门 Q1 拍板时的备选）：把四件套的规范化摘要写进 report frontmatter、gate 重算比对，从根上取消「历史轴」这整片面（本次修的 6 条 fail-open 里有 4 条属于该面）。前置未解项 = **尾流修订的重新盖章语义**。若 B19 那个 change 做起来发现历史轴还在继续长补丁，那就是切 B 的信号。

**roadmap 回填**：本 change 非 roadmap 驱动（`roadmap_writeback_draft.py` exit=3，`NO_ASSOCIATION`），无需回填。

---

## 🔧 生效条件（消费仓必读）

本修复经 `setup.sh` 软链分发。**消费仓须跑 `/sdflow-upgrade` 后才拿到** —— 在此之前，症状与修复前**逐字相同**（纯勾选翻转照样撞 `REFUSE_START`），极易被误判成「没修好」。
