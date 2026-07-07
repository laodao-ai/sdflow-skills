# hand-off — mlh-p3-determ-guards

> 阶段三收尾交接（verify 之后 / archive 之前产出）。异步人类再入口 + 下个 change 种子。日期 2026-07-07。

## ✅ 完成了什么（每条已复核锚点存在性）

roadmap「机械层固化」阶段 3（Leg1 收尾）——两处机械层确定性守卫，纯增测/校验器、零行为改动、零 SKILL.md 改动。

1. **recorder 镜像 helper 一致性测试**（Task1，commit `caa950c`）——`sdflow-buglist/tests/test_mirror_consistency.py`：剥 docstring 后 AST 等价契约（grill Path B），THREE_WAY(3) + TWO_WAY(**14**，含 code-review F5 扩的 6 个 byte-identical helper)。证伪用例齐：`test_logic_drift_is_caught`（逻辑分叉变红）、`test_helper_deletion_is_not_silently_swallowed`（裸 getattr 无吞 AttributeError）、`test_priorities_constant_consistency`（独立 `==` 值断言）。顺手归一 todolist `split_sections`/`block_ranges` 两处逻辑异写，todolist 全测零回归。
2. **config_lint**（Task2，commit `043f3a7`）——`sdflow-init/scripts/init.py` config-lint（mode 第 4 值，手写 stdlib 行扫描**不 import yaml**，follow anchor_lint 范式）：必填段 + tier 枚举 + metrics 条件化放行，块缺失 fail-closed 放行、既有 3 mode 冒烟未扰动。
3. **batch lint**（Task3，commit `7ff7a98`）——`sdflow-issues/scripts/issues.py` batch lint：优先级/计划占位符 `<待填>` 双字段豁免 + 前导 token 后缀不校验（`P1 ★` 过），声明 `PRIORITIES`，复用 `_split_batches_entries` 只读，fail-closed。
4. **收尾验证**（Task4，commit `e917de9`）——pytest 全绿 + fail-closed 手验 + 现存零假阳 + openspec validate。
5. **code-review 自动修 5 项**（commit `80fb1d6`，`[impl-review-fix]`）——F1 batch lint 缺 batches.md fail-open→非零（致命，违设计失败模式表）/ F2 UnicodeDecodeError 双处裸 traceback→`except (OSError, UnicodeDecodeError)`（高，历史镜实证 anchor_lint commit 8f1d2bc 已修过重蹈）/ F5 守卫漏 6 helper→TWO_WAY 扩 14（高）/ F3 正则 `^(P\d|—)` 过匹配 P10→`^(P[0-4](?!\d)|—)`（中）/ 测试缺口补 2 用例（低）。

**verify 终门**：PASS（强档冷启 Do-Not-Trust）——实跑 4 目录 396 passed、真实 config.yaml/batches.md lint 退出 0（零假阳）、坏输入（缺 schema / P10 / 缺 batches.md）退出 1、openspec validate valid。锚点均机验存在。

## ⏳ 未完成 / 延后

- **defer 批次 `mlh-p3-determ-guards`**（PLANNED，见 `openspec/issues/batches.md` + `openspec/issues/INDEX.md`）——code-review 冷主审 defer 的 4 项：
  - **T70**（代码质量）：config_lint tab 缩进 model-tiers 子键隐形→越域 fail-open（边缘 YAML，对抗A 实测）。
  - **T71**（代码质量）：`_ast_no_doc` 剥 docstring 后空体函数坍塌理论假过（当前 11+6 helper 均有真逻辑，不可利用）。
  - **T72**（功能增强）：batch 条目整行缺失 优先级:/计划: 字段不校验（实现有意窄化值语法层，对抗A 判为文档化边界）——考虑补结构完整性校验。
  - **T73**（功能增强）：metrics.enabled 两校验器（anchor_lint + config_lint）是否都该容忍合法 YAML 行内注释=设计级决定（须同步改防分歧）。
- **裁掉 1 项**（非缺陷，记录备查）：F4（metrics.enabled 拒行内注释）——paradigm-consistent，anchor_lint `_ENABLED` 同样拒；若"修"反致两校验器分歧。设计级考量已转 T73。
- **F5 残差**：`_die` 3 向（含 issues）AST 等价未纳 THREE_WAY；守卫「动态发现全部共享 helper」之完备性——随 T70-73 池后续评估。
- **verify Minor 缺口**：无。

## ▶ 下一阶段建议

- **roadmap「机械层固化」进度**：Leg1（脚本化 + 去字符串化）三阶段 P1(issues sweep)/P2(anchor-lint)/P3(本 change determ-guards) 已交付；roadmap 需标 P3 完成。下一阶段按 roadmap 走 P4（机械层下沉编排 SKILL 步）或 Leg2 north-star——**新 capability `determinism-guards` 已声明，未来 P4 机械层下沉可扩展本 capability**（proposal 已注）。
- **defer 批次清理时机**：T70-73 均为加固/设计决定类，非阻塞，优先级低。可择期单开 cleanup change 批量清；T73（行内注释设计决定）宜与 anchor_lint 一并评估。
- **接入门 scope（proposal Non-Goals + design R5 已声明）**：config_lint/batch lint 是新子命令、**不在任何现有自动化路径**——现阶段需人工/未来 change 接入门后才自动生效。接入 done/CI 门是后续 scope（P4/后续），本 change 不假装接入。
