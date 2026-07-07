# tasks — mlh-p2-anchor-lint

> 全部追溯 spec-workflow 新需求「评审报告锚自检由确定性脚本判定」（下称 **[R]**）。
> TDD：每任务先写失败测试 → 实现 → 跑绿。数据类：改脚本必跑 `pytest sdflow-init/assets/workflow/tools/tests/`。
> 每任务收尾 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh <change>:task<N>-<slug> "<描述>"`（task<N>-<slug> 带横杠，ship_gate TAG_RE 主锚）。

## 范围说明

交付物 = `sdflow-init/assets/workflow/tools/anchor_lint.py`（确定性锚自检脚本）+ `tools/tests/test_anchor_lint.py` + 两审 SKILL 自检步接脚本。规范增量落 `spec-workflow`（ADDED [R]）。roadmap 阶段 2 实施，背景见 `openspec/roadmaps/mechanical-layer-hardening/roadmap.md`。

## 1. anchor_lint 核心：契约机读块枚举读取 + fence 核 + 锚族识别（[R]）

> 契约 `lens-metric-enums` 机读块已于 grill amendment 加入 `sdflow-init/assets/workflow/lens-metric-contract.md`（本 change 交付物之一）。

- [ ] 1.1 先写失败测试 `test_anchor_lint.py`：喂真实 `lens-metric-contract.md` 断言 `load_enums()` 从 `lens-metric-enums` fenced 块解出 `layer`={spec-review,code-review}、`lens`={domain,adversarial,grounding,history,outside-voice,broad}、`runner`={claude,codex,claude-fallback}、`sev-format`=`致N/高N/中N/低N`；契约缺失 / 找不到该块 / 块空 → 抛/非零。
- [ ] 1.2 实现 `anchor_lint.py` 骨架：argparse（`--report` / `--layer spec-review|code-review` / `--root` 默认 cwd）；`load_enums()` 用 `Path(__file__).resolve().parent.parent/"lens-metric-contract.md"`，定位 info-string 恒为 `lens-metric-enums` 的 fenced 块、逐行 `key: 逗号分隔值` 提枚举 + `sev-format` 模板；契约缺失/无块/解析空 → ERROR(2)（不回落硬编码兜底）。
- [ ] 1.3 先写失败测试：fence-aware 行级核——fence 内 `sdflow:lens-metric v1` 示范锚不产出、fence 外真锚产出；未闭合/嵌套 fence 行为（沿用 aggregator CommonMark 语义）。
- [ ] 1.4 实现脚本内 `_fence_aware_lines` + 锚族前缀识别（`outside-voice`/`hr-tg`/`step1-broad-review`/`lens-metric` 四前缀，独占行 strip 后前缀匹配 + 受限 kv `key="value"`）。**不 import** `lens_metric_aggregate`（跨 skill 禁令，脚本内重实现，见 design 决策 1/4）。
- [ ] 1.5 跑 `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -k "enum or fence"` 绿。
- [ ] 1.6 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task1-core "anchor_lint 骨架：契约枚举读取 + fence 核 + 锚族识别"`

## 2. 存在性校验 + metrics 门控自读（[R]）

- [ ] 2.1 先写失败测试：缺 `outside-voice`/`hr-tg`/`step1-broad-review` 任一 → VIOLATION(1) 且 human/JSON 点名缺类；四类恒须锚齐（metrics 开）→ CLEAN(0)。
- [ ] 2.2 先写失败测试：`metrics.enabled=false`（临时 config）+ 报告无 lens-metric 锚 + 其余三类齐 → CLEAN(0)；`metrics.enabled=true` + 无 lens-metric 锚 → VIOLATION(1)。
- [ ] 2.3 先写失败测试〔grill Q1=A 分治〕：config.yaml **文件缺失** → 判 enabled=false（CLEAN，不误判缺锚阻塞）；config.yaml **存在但读不出** `metrics.enabled` 键（改坏/结构异常）→ **ERROR(2)** fail-closed（反静默，不静默跳过整类校验）。
- [ ] 2.4 实现 `read_metrics_enabled(root)`：返回三态——文件不存在→False；存在且匹配 `metrics:` 块 `enabled: true|false`→对应 bool；存在但匹配不到→抛/信号 ERROR。受限行锚定正则（无 yaml 依赖）。实现存在性校验：恒须锚集按 `--layer` + metrics 门控组装，缺即 VIOLATION；config 坏 → ERROR(2)。
- [ ] 2.5 跑 `pytest ... -k "exist or metrics or config"` 绿。
- [ ] 2.6 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task2-existence "存在性校验 + metrics.enabled 受限自读门控"`

## 3. lens-metric 字段/枚举/sev 校验 + site 豁免 + fail-closed（[R]）

- [ ] 3.1 先写失败测试：`layer`/`lens`/`runner` 越域 → VIOLATION 点名锚+字段；缺任一必填字段（layer/lens/runner/findings/采纳/裁掉/defer/独立/sev）→ VIOLATION；`sev` 不符 `致N/高N/中N/低N` → VIOLATION。
- [ ] 3.2 先写失败测试：`site` 取非常见值但其余合法 → CLEAN（CF-补2，site 不越域自检）。
- [ ] 3.3 先写失败测试：`--report` 指不存在文件 → ERROR(2)；契约定位不到 / 找不到 `lens-metric-enums` 块 → ERROR(2)（fail-closed，非 0，不回落硬编码）。
- [ ] 3.4 先写失败测试（诚实边界）：`findings=N` 与实收数不符 → 脚本**不**报错（CLEAN）——脚本不兜数值一致性；断言脚本无「数值一致性」相关违规输出。
- [ ] 3.5 实现字段/枚举/sev 校验（仅 fence 外真 lens-metric 锚）+ site 跳过 + `--report`/契约缺失 ERROR(2) + 双输出（human 行 + JSON 违规清单）。
- [ ] 3.6 跑全量 `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -v` 全绿。
- [ ] 3.7 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task3-fields "lens-metric 字段/枚举/sev 校验 + site 豁免 + fail-closed + 双输出"`

## 4. aggregator 枚举一致性测试（[R]，grill Q3=B）

- [ ] 4.1 先写失败测试于 `sdflow-retro/tests/`（新增或并入现有 `test_lens_metric_aggregate.py`）：自带极简契约块解析（**不跨 skill import anchor_lint**），断言 `lens_metric_aggregate.LAYER_ENUM` == 契约 `lens-metric-enums` 块 `layer` 集、`LENS_ENUM` == 块 `lens` 集（runner aggregator 无、不纳入）。
- [ ] 4.2 验证守卫生效：临时改契约块的 `lens` 值（或断言逻辑）确认测试变红，再还原；跑 `pytest sdflow-retro/tests/ -k "enum or consistency"` 绿。
- [ ] 4.3 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task4-enum-consistency "aggregator 硬编码 enum 对契约机读块一致性测试守卫"`

## 5. 两审 SKILL 自检步接脚本 + 诚实边界保留（[R]）

- [ ] 5.1 Read `sdflow-spec-review/SKILL.md`，把 Step3「锚行存在性自检」段的「grep 四类 v1 锚行 + 核 enum」改为调 `$RULES_ROOT/tools/anchor_lint.py --report {report} --layer spec-review`（非零退出即本步阻塞）；**保留**「`findings=N` 与合并池实收数数值一致性仍是主 session 信任边界、非机械可验」声明；config 门控措辞与现有一致。
- [ ] 5.2 Read `sdflow-code-review/SKILL.md`，把 Step5「锚行存在性自检」段同样改为调 `anchor_lint --layer code-review`；同保留诚实边界声明。
- [ ] 5.3 dogfood 校验：dev checkout 直接跑 `python3 sdflow-init/assets/workflow/tools/anchor_lint.py --report <本 change 某 review 报告或构造样本> --layer code-review`，确认脚本路径与退出码可用（不靠 `~/.claude/skills` 符号链，design R5）。
- [ ] 5.4 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task5-skill-wire "两审 SKILL 自检步接 anchor_lint + 保留数值一致性诚实边界"`

## 6. 收尾验证（[R]）

- [ ] 6.1 全量 `pytest sdflow-init/assets/workflow/tools/tests/` + `pytest sdflow-retro/tests/` 全绿；坏样本非零、干净样本 0 的验收覆盖齐。
- [ ] 6.2 `openspec validate mlh-p2-anchor-lint --type change`；核 spec delta 与实现一致。
- [ ] 6.3 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task6-verify "收尾：全量 pytest 绿(tools+retro) + spec delta 对码核验"`

## 测试覆盖图（TG-18）

| code path | 测试类型 | 用例 |
|---|---|---|
| `load_enums()` 契约机读块解析 | 单元 | 真实契约 `lens-metric-enums` 块解出三枚举 + sev-format；块缺失/空→非零 |
| `_fence_aware_lines` fence 核 | 单元 | fence 内示范锚不计；fence 外真锚计；未闭合/嵌套 |
| 锚族前缀识别 | 单元 | 四前缀 fence 外命中；描述性内联不误命中 |
| 存在性 × layer × metrics 门控 | 单元/集成 | 缺恒须锚→1；metrics 关+无 lens-metric→0；metrics 开+无→1 |
| `read_metrics_enabled` 三态 | 单元 | true/false；缺 config→False；存在但坏→ERROR(2) |
| lens-metric 字段/枚举/sev | 单元 | 越域→1；缺字段→1；坏 sev→1；site 另类→0 |
| fail-closed | 单元 | 报告不存在→2；契约/机读块定位不到→2；config 坏→2 |
| 数值一致性诚实边界 | 单元 | findings≠实收数→不报错（脚本不兜） |
| aggregator 枚举一致性 | 单元(sdflow-retro) | LAYER_ENUM/LENS_ENUM == 契约块 layer/lens；改块→红 |
