# tasks — mlh-p2-anchor-lint

> 全部追溯 spec-workflow 新需求「评审报告锚自检由确定性脚本判定」（下称 **[R]**）。
> TDD：每任务先写失败测试 → 实现 → 跑绿。数据类：改脚本必跑 `pytest sdflow-init/assets/workflow/tools/tests/`。
> 每任务收尾 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh <change>:task<N>-<slug> "<描述>"`（task<N>-<slug> 带横杠，ship_gate TAG_RE 主锚）。

## 范围说明

交付物 = `sdflow-init/assets/workflow/tools/anchor_lint.py`（确定性锚自检脚本）+ `tools/tests/test_anchor_lint.py` + 两审 SKILL 自检步接脚本。规范增量落 `spec-workflow`（ADDED [R]）。roadmap 阶段 2 实施，背景见 `openspec/roadmaps/mechanical-layer-hardening/roadmap.md`。

## 1. anchor_lint 核心：契约枚举读取 + fence 核 + 锚族识别（[R]）

- [ ] 1.1 先写失败测试 `test_anchor_lint.py`：喂真实 `lens-metric-contract.md` 断言 `load_enums()` 解出 `layer`={spec-review,code-review}、`lens`={domain,adversarial,grounding,history,outside-voice,broad}、`runner`={claude,codex,claude-fallback}；契约缺失 → 抛/非零。
- [ ] 1.2 实现 `anchor_lint.py` 骨架：argparse（`--report` / `--layer spec-review|code-review` / `--root` 默认 cwd）；`load_enums()` 用 `Path(__file__).resolve().parent.parent/"lens-metric-contract.md"` + 正则 `\{([^}]*)\}` 提三枚举；契约缺失/解析空 → ERROR(2)。
- [ ] 1.3 先写失败测试：fence-aware 行级核——fence 内 `sdflow:lens-metric v1` 示范锚不产出、fence 外真锚产出；未闭合/嵌套 fence 行为（沿用 aggregator CommonMark 语义）。
- [ ] 1.4 实现脚本内 `_fence_aware_lines` + 锚族前缀识别（`outside-voice`/`hr-tg`/`step1-broad-review`/`lens-metric` 四前缀，独占行 strip 后前缀匹配 + 受限 kv `key="value"`）。**不 import** `lens_metric_aggregate`（跨 skill 禁令，脚本内重实现，见 design 决策 1/4）。
- [ ] 1.5 跑 `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -k "enum or fence"` 绿。
- [ ] 1.6 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task1-core "anchor_lint 骨架：契约枚举读取 + fence 核 + 锚族识别"`

## 2. 存在性校验 + metrics 门控自读（[R]）

- [ ] 2.1 先写失败测试：缺 `outside-voice`/`hr-tg`/`step1-broad-review` 任一 → VIOLATION(1) 且 human/JSON 点名缺类；四类恒须锚齐（metrics 开）→ CLEAN(0)。
- [ ] 2.2 先写失败测试：`metrics.enabled=false`（临时 config）+ 报告无 lens-metric 锚 + 其余三类齐 → CLEAN(0)；`metrics.enabled=true` + 无 lens-metric 锚 → VIOLATION(1)。
- [ ] 2.3 先写失败测试：缺 config.yaml / 读不出 `metrics.enabled` → 保守 enabled=false（不因 config 问题误判缺锚阻塞，design 决策 2）。
- [ ] 2.4 实现 `read_metrics_enabled(root)`：受限行锚定正则读 `openspec/config.yaml` 的 `metrics:` 块 `enabled: true|false`（无 yaml 依赖）；缺/读不出 → False。实现存在性校验：恒须锚集按 `--layer` + metrics 门控组装，缺即 VIOLATION。
- [ ] 2.5 跑 `pytest ... -k "exist or metrics or config"` 绿。
- [ ] 2.6 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task2-existence "存在性校验 + metrics.enabled 受限自读门控"`

## 3. lens-metric 字段/枚举/sev 校验 + site 豁免 + fail-closed（[R]）

- [ ] 3.1 先写失败测试：`layer`/`lens`/`runner` 越域 → VIOLATION 点名锚+字段；缺任一必填字段（layer/lens/runner/findings/采纳/裁掉/defer/独立/sev）→ VIOLATION；`sev` 不符 `致N/高N/中N/低N` → VIOLATION。
- [ ] 3.2 先写失败测试：`site` 取非常见值但其余合法 → CLEAN（CF-补2，site 不越域自检）。
- [ ] 3.3 先写失败测试：`--report` 指不存在文件 → ERROR(2)；契约定位不到 → ERROR(2)（fail-closed，非 0）。
- [ ] 3.4 先写失败测试（诚实边界）：`findings=N` 与实收数不符 → 脚本**不**报错（CLEAN）——脚本不兜数值一致性；断言脚本无「数值一致性」相关违规输出。
- [ ] 3.5 实现字段/枚举/sev 校验（仅 fence 外真 lens-metric 锚）+ site 跳过 + `--report`/契约缺失 ERROR(2) + 双输出（human 行 + JSON 违规清单）。
- [ ] 3.6 跑全量 `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -v` 全绿。
- [ ] 3.7 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task3-fields "lens-metric 字段/枚举/sev 校验 + site 豁免 + fail-closed + 双输出"`

## 4. 两审 SKILL 自检步接脚本 + 诚实边界保留（[R]）

- [ ] 4.1 Read `sdflow-spec-review/SKILL.md`，把 Step3「锚行存在性自检」段的「grep 四类 v1 锚行 + 核 enum」改为调 `$RULES_ROOT/tools/anchor_lint.py --report {report} --layer spec-review`（非零退出即本步阻塞）；**保留**「`findings=N` 与合并池实收数数值一致性仍是主 session 信任边界、非机械可验」声明；config 门控措辞与现有一致。
- [ ] 4.2 Read `sdflow-code-review/SKILL.md`，把 Step5「锚行存在性自检」段同样改为调 `anchor_lint --layer code-review`；同保留诚实边界声明。
- [ ] 4.3 dogfood 校验：dev checkout 直接跑 `python3 sdflow-init/assets/workflow/tools/anchor_lint.py --report <本 change 某 review 报告或构造样本> --layer code-review`，确认脚本路径与退出码可用（不靠 `~/.claude/skills` 符号链，design R5）。
- [ ] 4.4 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task4-skill-wire "两审 SKILL 自检步接 anchor_lint + 保留数值一致性诚实边界"`

## 5. 收尾验证（[R]）

- [ ] 5.1 全量 `pytest sdflow-init/assets/workflow/tools/tests/` 全绿；坏样本非零、干净样本 0 的验收覆盖齐。
- [ ] 5.2 `openspec validate mlh-p2-anchor-lint --type change`（若适用）；核 spec delta 与实现一致。
- [ ] 5.3 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task5-verify "收尾：全量 pytest 绿 + spec delta 对码核验"`

## 测试覆盖图（TG-18）

| code path | 测试类型 | 用例 |
|---|---|---|
| `load_enums()` 契约解析 | 单元 | 真实契约解出三枚举；契约缺失→非零 |
| `_fence_aware_lines` fence 核 | 单元 | fence 内示范锚不计；fence 外真锚计；未闭合/嵌套 |
| 锚族前缀识别 | 单元 | 四前缀 fence 外命中；描述性内联不误命中 |
| 存在性 × layer × metrics 门控 | 单元/集成 | 缺恒须锚→1；metrics 关+无 lens-metric→0；metrics 开+无→1 |
| `read_metrics_enabled` | 单元 | true/false/缺 config/坏行→False |
| lens-metric 字段/枚举/sev | 单元 | 越域→1；缺字段→1；坏 sev→1；site 另类→0 |
| fail-closed | 单元 | 报告不存在→2；契约定位不到→2 |
| 数值一致性诚实边界 | 单元 | findings≠实收数→不报错（脚本不兜） |
