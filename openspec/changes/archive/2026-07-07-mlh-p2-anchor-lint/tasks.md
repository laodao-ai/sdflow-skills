# tasks — mlh-p2-anchor-lint

> 全部追溯 spec-workflow 新需求「评审报告锚自检由确定性脚本判定」（下称 **[R]**）。
> TDD：每任务先写失败测试 → 实现 → 跑绿。数据类：改脚本必跑 `pytest sdflow-init/assets/workflow/tools/tests/`。
> 每任务收尾 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh <change>:task<N>-<slug> "<描述>"`（task<N>-<slug> 带横杠，ship_gate TAG_RE 主锚）。

## 范围说明

交付物 = `sdflow-init/assets/workflow/tools/anchor_lint.py`（确定性锚自检脚本）+ `tools/tests/test_anchor_lint.py` + 两审 SKILL 自检步接脚本。规范增量落 `spec-workflow`（ADDED [R]）。roadmap 阶段 2 实施，背景见 `openspec/roadmaps/mechanical-layer-hardening/roadmap.md`。

## 1. anchor_lint 核心：契约机读块枚举读取 + fence 核 + 锚族识别（[R]）

> 契约 `lens-metric-enums` 机读块已于 grill amendment 加入 `sdflow-init/assets/workflow/lens-metric-contract.md`（本 change 交付物之一）。

- [x] 1.1 先写失败测试 `test_anchor_lint.py`：喂真实 `lens-metric-contract.md` 断言 `load_enums()` 从 `lens-metric-enums` fenced 块解出 `layer`={spec-review,code-review}、`lens`={domain,adversarial,grounding,history,outside-voice,broad}、`runner`={claude,codex,claude-fallback}、`sev-format`=`致N/高N/中N/低N`；契约缺失 / 找不到该块 / 块空 → 抛/非零。
- [x] 1.2 实现 `anchor_lint.py` 骨架：argparse（`--report` / `--layer spec-review|code-review` / `--root` 默认 cwd）；`load_enums()` 用 `Path(__file__).resolve().parent.parent/"lens-metric-contract.md"`，定位 info-string 恒为 `lens-metric-enums` 的 fenced 块、逐行 `key: 逗号分隔值` 提枚举 + `sev-format` 模板；契约缺失/无块/解析空 → ERROR(2)（不回落硬编码兜底）。
- [x] 1.3 先写失败测试：fence-aware 行级核——fence 内 `sdflow:lens-metric v1` 示范锚不产出、fence 外真锚产出；未闭合/嵌套 fence 行为（沿用 aggregator CommonMark 语义）。
- [x] 1.4 实现脚本内 `_fence_aware_lines` + 锚族前缀识别（`outside-voice`/`hr-tg`/`step1-broad-review`/`lens-metric` 四前缀，独占行 strip 后前缀匹配 + 受限 kv `key="value"`）。**不 import** `lens_metric_aggregate`（跨 skill 禁令，脚本内重实现，见 design 决策 1/4）。
- [x] 1.5 跑 `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -k "enum or fence"` 绿。
- [x] 1.6 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task1-core "anchor_lint 骨架：契约枚举读取 + fence 核 + 锚族识别"`

## 2. 存在性校验 + metrics 门控自读（[R]）

- [x] 2.1 先写失败测试：缺 `outside-voice`/`hr-tg`/`step1-broad-review` 任一 → VIOLATION(1) 且 human/JSON 点名缺类；四类恒须锚齐（metrics 开）→ CLEAN(0)。
- [x] 2.2 先写失败测试〔spec-review Q2=A 最小必有行〕：`metrics.enabled=true` + 报告有 lens-metric 但缺 `lens="broad"` 或缺 `lens="outside-voice"` → VIOLATION 点名缺 lens；两者齐 → 该项过。metrics 关 + 无 lens-metric → CLEAN。
- [x] 2.3 先写失败测试〔spec-review H1 真四态〕：①config.yaml **文件缺失** → enabled=false（CLEAN）；②文件存在但**无顶层 `metrics:` 块**（消费仓常态）→ enabled=false（CLEAN，**与文件缺失同放行分支**，不 ERROR）；③有 `metrics:` 块但值非法（`enabled: yes`/`True`/拼错/损坏）→ **ERROR(2)** fail-closed；④`enabled: true|false` → 对应 bool。用**无 metrics 段的真实消费仓风格 config** 作 fixture 覆盖②。
- [x] 2.4 先写失败测试〔L2 块边界〕：多段 config（另一顶层段也含 `enabled:` 子键）→ `read_metrics_enabled` 仍只读 `metrics:` 块下那个（先定位 `^metrics:` 再限范围至下一顶层键）。
- [x] 2.5 实现 `read_metrics_enabled(root)` 真四态：文件不存在→False；无 `^metrics:` 块→False；`metrics:` 块在但块内解不出合法 `enabled: true|false`→ERROR 信号；解出→bool。受限行锚定正则 + 块边界限定（无 yaml 依赖）。实现存在性校验：恒须锚集按 `--layer` + metrics 门控组装（metrics 开加 broad+outside-voice 最小必有行），缺即 VIOLATION；config 块坏 → ERROR(2)。
- [x] 2.6 跑 `pytest ... -k "exist or metrics or config or boundary or required"` 绿。
- [x] 2.7 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task2-existence "存在性(+最小必有行) + metrics 真四态门控(无块=放行/块坏=ERROR) + 块边界"`

## 3. lens-metric 字段/枚举/sev 校验 + site 豁免 + fail-closed（[R]）

- [x] 3.1 先写失败测试：`layer`/`lens`/`runner` 越域 → VIOLATION 点名锚+字段；缺任一必填字段（layer/lens/runner/findings/采纳/裁掉/defer/独立/sev）→ VIOLATION；`sev` 不符 `致N/高N/中N/低N` → VIOLATION。
- [x] 3.2 先写失败测试〔H2 layer==--layer〕：`--layer code-review` + 某 fence 外 lens-metric 锚 `layer="spec-review"`（错层）→ VIOLATION 点名错层锚（不因 layer 在枚举域内就放过）。
- [x] 3.3 先写失败测试〔M3 int≥0〕：`findings`/`采纳`/`裁掉`/`defer`/`独立` 任一取负/浮点串/空/中文数字 → VIOLATION 点名字段。
- [x] 3.4 先写失败测试：`site` 取非常见值但其余合法 → CLEAN（CF-补2，site 不越域自检）。
- [x] 3.5 先写失败测试：`--report` 指不存在文件 → ERROR(2)；契约定位不到 / 找不到 `lens-metric-enums` 块 → ERROR(2)（fail-closed，非 0，不回落硬编码）。
- [x] 3.6 先写失败测试（诚实边界）：`findings=N` 与实收数不符 → 脚本**不**报错（CLEAN）——脚本不兜数值一致性；断言脚本无「数值一致性」相关违规输出。
- [x] 3.7 实现字段/枚举/sev/layer==--layer/int≥0 校验（仅 fence 外真 lens-metric 锚）+ site 跳过 + `--report`/契约缺失 ERROR(2) + 双输出（human 行 + JSON 违规清单）。
- [x] 3.8 跑全量 `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -v` 全绿。
- [x] 3.9 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task3-fields "lens-metric 字段/枚举/sev + layer==--layer + int≥0 + site 豁免 + fail-closed + 双输出"`

## 4. aggregator 枚举一致性测试（[R]，grill Q3=B；落点订正 spec-review L1）

- [x] 4.1 先写失败测试**并入 `sdflow-retro/scripts/tests/test_lens_metric_aggregate.py`**（接地镜实测现有测试在此，非 `sdflow-retro/tests/`）：自带极简契约块解析（**不跨 skill import anchor_lint**），断言 `lens_metric_aggregate.LAYER_ENUM` == 契约 `lens-metric-enums` 块 `layer` 集、`LENS_ENUM` == 块 `lens` 集（runner aggregator 无、不纳入）。
- [x] 4.2 先写失败测试〔M1 交叉断言〕：对同一真实契约 fixture，让 anchor_lint 的解析路径与本测试 mini-parser **输出相等**（降低两独立解析器边界分歧假绿）；同 fixture 对 anchor_lint 与 aggregator 两份 fence 核的 fence-outside 行集也交叉断言。
- [x] 4.3 验证守卫生效：临时改契约块 `lens` 值确认测试变红，再还原；跑 `pytest sdflow-retro/scripts/tests/ -k "enum or consistency or cross"` 绿。
- [x] 4.4 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task4-enum-consistency "aggregator 硬编码 enum 对契约块一致性 + 双解析器交叉断言"`

## 5. copy_bundle 契约同刷 + roadmap 调和（[R]，spec-review Q1=A / H3）

- [x] 5.1 先写失败测试于 `sdflow-init/tests/`：模拟本地 pin 消费仓 `update` → 断言 `openspec/workflow/lens-metric-contract.md` 与 `tools/anchor_lint.py` 一并被刷新（刷后契约含 `lens-metric-enums` 块）；非 full 模式下契约随 tools/ 同刷。
- [x] 5.2 实现 `sdflow-init/scripts/init.py` 的 `copy_bundle`（或 update 路径）：刷 `tools/` 时一并刷 sibling `lens-metric-contract.md`（机读依赖锁同版本）。跑 `pytest sdflow-init/tests/` 绿。
- [x] 5.3 roadmap 调和〔H3/BASE-08〕：改 `openspec/roadmaps/mechanical-layer-hardening/design.md:56` + `roadmap.md:61` 的「复用 parse_anchor/_fence_aware_lines、不重实现」为「遵实质(变长KV前缀匹配/不用_line_scoped_hits)，因跨 skill import 消费仓 break，实现为**脚本内重实现同款逻辑**」；`task-log.md` 追一条调和注记。
- [x] 5.4 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task5-deploy-reconcile "copy_bundle 一并刷契约(pin 防错配) + roadmap 复用→重实现调和"`

## 6. 两审 SKILL 自检步接脚本 + 诚实边界保留（[R]）

- [x] 6.1 Read `sdflow-spec-review/SKILL.md`，把 Step3「锚行存在性自检」段的「grep 四类 v1 锚行 + 核 enum」改为调 `$RULES_ROOT/tools/anchor_lint.py --report {report} --layer spec-review`（非零退出即本步阻塞）；**保留**「`findings=N` 与合并池实收数数值一致性仍是主 session 信任边界、非机械可验」声明；config 门控措辞与现有一致。
- [x] 6.2 Read `sdflow-code-review/SKILL.md`，把 Step5「锚行存在性自检」段同样改为调 `anchor_lint --layer code-review`；同保留诚实边界声明。
- [x] 6.3 dogfood 校验：dev checkout 直接跑 `python3 sdflow-init/assets/workflow/tools/anchor_lint.py --report <本 change 某 review 报告或构造样本> --layer code-review`，确认脚本路径与退出码可用（不靠 `~/.claude/skills` 符号链，design R5）。
- [x] 6.4 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task6-skill-wire "两审 SKILL 自检步接 anchor_lint + 保留数值一致性诚实边界"`

## 7. 收尾验证（[R]）

- [x] 7.1 全量 `pytest sdflow-init/assets/workflow/tools/tests/` + `pytest sdflow-retro/scripts/tests/` + `pytest sdflow-init/tests/` 全绿；坏样本非零、干净样本 0 的验收覆盖齐。
- [x] 7.2 `openspec validate mlh-p2-anchor-lint --type change`；核 spec delta 与实现一致。
- [x] 7.3 checkpoint：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task7-verify "收尾：全量 pytest 绿(tools+retro-scripts+init) + spec delta 对码核验"`

## 测试覆盖图（TG-18）

| code path | 测试类型 | 用例 |
|---|---|---|
| `load_enums()` 契约机读块解析 | 单元 | 真实契约 `lens-metric-enums` 块解出三枚举 + sev-format；块缺失/空→非零 |
| `_fence_aware_lines` fence 核 | 单元 | fence 内示范锚不计；fence 外真锚计；未闭合/嵌套 |
| 锚族前缀识别 | 单元 | 四前缀 fence 外命中；描述性内联不误命中 |
| 存在性 × layer × metrics 门控 | 单元/集成 | 缺恒须锚→1；metrics 关+无 lens-metric→0；metrics 开+无→1 |
| 最小必有行（metrics 开） | 单元 | 缺 broad→1；缺 outside-voice→1；两者齐→过 |
| `read_metrics_enabled` 真四态 | 单元 | true/false；缺 config→False；**无 metrics 块→False**；块在值非法→ERROR(2)；多段 config 块边界正确 |
| lens-metric 字段/枚举/sev/layer/int | 单元 | 越域→1；缺字段→1；坏 sev→1；layer≠--layer→1；计数负/浮点/空→1；site 另类→0 |
| fail-closed | 单元 | 报告不存在→2；契约/机读块定位不到→2；config 块坏→2 |
| 数值一致性诚实边界 | 单元 | findings≠实收数→不报错（脚本不兜） |
| aggregator 枚举一致性 + 交叉断言 | 单元(sdflow-retro/scripts) | LAYER_ENUM/LENS_ENUM == 契约块；改块→红；双解析器同 fixture 输出相等 |
| copy_bundle 契约同刷 | 单元(sdflow-init) | pin update 后契约含机读块、与 tools/ 同刷 |
