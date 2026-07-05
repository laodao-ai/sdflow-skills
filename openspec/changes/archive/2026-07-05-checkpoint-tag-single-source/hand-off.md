# hand-off — checkpoint-tag-single-source

> 2026-07-05 · ship 链收尾（verify=PASS 后、archive 前产出）。异步人类再入口 + 下阶段种子。

## ✅ 完成了什么（每条附机验锚点）

- **producer→parser 集成绑定测试**（design D1）：`sdflow-ship/tests/test_producer_parser_contract.py` — `run_producer` 真调 `sdflow-init/assets/hack/checkpoint-commit.sh`（`checkpoint-commit.sh:46` `subject="checkpoint($step): $desc"`）→ `git log -1` 读回 subject → 喂真实 `ship_gate.TAG_RE`（`ship_gate.py:231`）。3 正例：命名空间（`test_namespaced_subject_matches_and_captures`）、裸格式 group(1)=None（`test_bare_subject_matches_with_null_namespace`）、kebab+多位号（`test_kebab_namespace_multidigit_captures` → `("checkpoint-tag-single-source","12")`）。
- **TAG_RE 负例矩阵**（design D2）：`test_tag_re_rejects_relaxations` 参数化 5 条 `match is None` — 无尾dash / 大写ns / 号位空·前导符号 / 号位字母加宽(taskab-) / 空ns。covers D2 三类 MUST + DF1 补的字母加宽。
- **零源码/文档运行时改动**：`ship_gate.py`/`workflow.md`/`SKILL.md`/既有 `test_workflow_authority.py` 断言未触碰（历史镜 + 三镜 diff 核实，仅作被测锚点）。
- **验证**：`pytest sdflow-ship/tests/test_producer_parser_contract.py` 8 绿；仓级 `pytest` **350 passed** 无回归（verify-report.md，`<!-- ship-gate: verify=PASS -->`）。

## ⏳ 未完成 / 延后 → 批次 `checkpoint-tag-single-source`（`openspec/issues/batches.md` / `INDEX.md`，PLANNED）

- **B4〔P1·bug〕`ship_gate.anchors_in` 子串误配** — 纯 `a in text` 把报告里对 `design-approved` 锚的**描述性提及**当真锚，致本 change 一度假过设计门越门起跑（本次靠人工复审门补救）。**本 change 不修**（属 ship_gate 逻辑、非本测试 change 范围）。修向：锚检测升到行级锚定（行首/整行等值），排除代码块/反引号内提及。**建议优先清**（安全红线 adr/0004）。
- **T37〔代码质量〕** delta spec Scenario prose 复述标签形状——又一份需人工与 workflow.md/SKILL.md 保持一致的 doc 副本（M3 轻回声）。
- **T38〔代码质量〕** spec Scenario 用词 `<当前change>` 易被误读为须用本 change 真实 slug（实现用任意占位 demo）。
- **已在本 change 内闭掉的 defer**：T39（文件名冒号→固定名）、T40（多位数号覆盖）→ 均 code-review `[impl-review-fix]` 修复、回写 DONE。

## ▶ 下一阶段建议

- **开一个 cleanup change 清批次 `checkpoint-tag-single-source`**，**首推修 B4**（gate 锚检测行级化 + 加负例测试"报告仅含描述性提及时 pre-flight 判未过门"）——它是本次事故的根因，留着会让未来 change 重演"描述锚字符串即假过设计门"。T37/T38 可顺带（doc 精确性，低优先）。
- **机制精化留痕（非 defer，已裁决）**：design D4 文本仍写"sys.path 注入"，实现已用 `importlib.util.spec_from_file_location`（消全局污染、保 D4 意图）。archive delta 已按代码实况处理；若日后觉 D4 文本该对齐，属文档级微调、非功能项。
