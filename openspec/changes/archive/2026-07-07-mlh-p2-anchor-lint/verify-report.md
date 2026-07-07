# verify-report — mlh-p2-anchor-lint

- 日期：2026-07-07
- change：mlh-p2-anchor-lint
- 验证方式：Do-Not-Trust 冷核（核代码/测试实现，不信复选框、不信既有报告措辞）；每 ✅ 附机验锚点

## 结论：PASS

<!-- ship-gate: verify=PASS -->

实跑证据：`python3 -m pytest sdflow-init/assets/workflow/tools/tests/ sdflow-retro/scripts/tests/ sdflow-init/tests/ -q` → **242 passed**；`openspec validate mlh-p2-anchor-lint --type change` → valid；dev checkout 直跑 `anchor_lint.py --report <spec.md> --layer code-review` → 坏样本非零退出（exit=1，逐条点名缺锚），干净样本 exit=0（测试覆盖）。

## 逐需求核对表

| 需求/任务 | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| load_enums 读契约 lens-metric-enums 机读块（三枚举 + sev-format） | anchor_lint.py:35-70（`_ENUM_BLOCK`:21、fence-aware 定位块、解 layer/lens/runner/sev-format）；契约块 lens-metric-contract.md:19-24 | ✅ |
| 契约缺失/无块/块空 → EnumsError（不回落硬编码） | anchor_lint.py:41-42/55-56/66-67；main fail-closed:204-209 | ✅ |
| fence_outside_lines fence-aware 行级核（CommonMark 语义） | anchor_lint.py:73-85；test_anchor_lint 含 fence 内示范锚不计 + `test_unclosed_fence_swallows_trailing_anchors`:278 | ✅ |
| anchor_prefix 四前缀 + token 边界（F5） | anchor_lint.py:92-99（`rest==""`/空白/`-->` 才命中，防子串误命中） | ✅ |
| read_metrics_enabled 真四态（缺文件/无块=放行·块坏=ERROR·bool） | anchor_lint.py:109-131（①:116-117 ②:120-122 ③:131 ④:130）；F2 fail-open→closed:118-119；F3 跳注释/空行:124；块边界先定位 `^metrics:` 再限至下一顶层键:120/126-127 | ✅ |
| check_existence 恒须三类 + metrics 开加 lens-metric + broad/outside-voice 最小必有行 | anchor_lint.py:134-157（MANDATORY:134、MIN_LENS_ROWS:135、metrics_on 门控:151-156） | ✅ |
| check_lens_metric 字段/枚举/layer==--layer/sev/五计数 int≥0 + 存在性判断防空串(F1) + site 不校验 | anchor_lint.py:163-187（REQUIRED_FIELDS:24、`"layer" in kv` 存在性守卫:174/176、layer-ne-cli:176-177、sev_re:182、`_NONNEG_INT`:160/184-186；site 不在校验列表） | ✅ |
| 数值一致性诚实边界（findings vs 实收数脚本不兜） | check_lens_metric 无数值一致性校验（docstring:164-165 明示）；测试断言无相关违规输出 | ✅ |
| main 三处 fail-closed（报告不可读/契约/metrics 块坏）含 UnicodeDecodeError(F4) | anchor_lint.py:197-215（报告:199、enums:206、metrics:212；UnicodeDecodeError 均纳入 except） | ✅ |
| 契约 lens-metric-enums 机读块 | lens-metric-contract.md:17-24（info-string=`lens-metric-enums`、逐行 `key: 值`、site 不入块:18） | ✅ |
| init.py copy_bundle 非 full 分支契约同刷 | init.py:159-163（刷 tools/ 时一并 copy2 sibling lens-metric-contract.md）；`test_copy_bundle_refreshes_contract`(test_init_contract_sync.py:7) 断言刷后含机读块 | ✅ |
| spec-review SKILL 自检步接 anchor_lint + 保留诚实边界 | sdflow-spec-review/SKILL.md:79（调 `--layer spec-review`、非零阻塞、MUST NOT 静默吞、保留信任边界声明） | ✅ |
| code-review SKILL 自检步接 anchor_lint + 保留诚实边界 | sdflow-code-review/SKILL.md:118-125（调 `--layer code-review`、非零阻塞、保留信任边界声明:124-125） | ✅ |
| aggregator 枚举一致性 + 双解析器交叉断言 | test_lens_metric_aggregate.py:`test_aggregator_enum_matches_contract`:315、`test_dual_parser_cross_assert`:321、`test_fence_core_cross_equivalence`:332 | ✅ |
| roadmap 复用→重实现调和（design.md:56 + :139 双处 + roadmap 2.A.1 + task-log 注记） | design.md:56（脚本内重实现同款逻辑·跨 skill import break）+ design.md:139（同调和，含 F8 补标）；roadmap.md:61（2.A.1 重实现）；task-log.md:60-61（调和注记 H3/BASE-08） | ✅ |
| 收尾全量测试绿 + spec delta 对码 | 242 passed；openspec validate 通过 | ✅ |

## Scenario 覆盖核对（spec.md 12 Scenario）

| Scenario | 证据 | 状态 |
|---|---|---|
| 干净报告自检通过（exit 0） | check_existence/check_lens_metric 空违规 → main:225-227 EXIT_CLEAN | ✅ |
| 缺恒须锚阻塞（点名） | check_existence:148-150；实跑坏样本点名 outside-voice/hr-tg/step1-broad-review | ✅ |
| 越域/缺字段/坏 sev 被拦 | check_lens_metric:171-183 | ✅ |
| site 任意取值不报错 | site 不在 REQUIRED_FIELDS/枚举校验列表 | ✅ |
| config 缺失/无 metrics 块不阻塞 | read_metrics_enabled:116-117/120-122 返 False（同放行分支） | ✅ |
| metrics 块存在值非法 fail-closed | read_metrics_enabled:131 raise → main:212-215 EXIT_ERROR | ✅ |
| metrics 开缺 broad/outside-voice 被拦 | check_existence:154-156 | ✅ |
| layer≠--layer 被拦 | anchor_lint.py:176-177 layer-ne-cli | ✅ |
| 计数非非负整数被拦 | anchor_lint.py:184-186 not-nonneg-int | ✅ |
| fence 内示范锚不当真锚 | fence_outside_lines:73-85（仅 fence 外行进校验） | ✅ |
| 读不到报告/自身错误 fail-closed | main:199-202/206-209 EXIT_ERROR | ✅ |
| 枚举单一源一致性由测试守卫 + 交叉断言 | test_aggregator_enum_matches_contract + test_dual_parser_cross_assert | ✅ |
| 机读契约与 tools 同批部署防 pin 错配 | init.py:159-163 + test_copy_bundle_refreshes_contract | ✅ |
| 数值一致性诚实声明为信任边界 | 两 SKILL 保留声明（spec:79 / code:124-125），脚本无数值校验 | ✅ |

## 缺口清单

- 核心 FAIL：无。
- Minor / deferred：
  - roadmap.md 高层就绪表（:15/:54/:85）仍用「复用现成纯函数」措辞描述就绪度/ROI，非技术 import 断言（真正矛盾点 2.A.1/design 已调和）。属文档层措辞，不影响实现正确性，判 PASS 并注明。
  - F12/F13 已按计划 defer → todolist T68/T69（本 change 范围外，不阻塞归档）。

## 结论

PASS —— 242 测试全绿、openspec validate 通过、spec 全部 ADDED 需求与 12 Scenario 均有机验代码/测试锚点，两审 SKILL 已接脚本且保留诚实边界，roadmap 复用→重实现双处调和到位。无核心缺口。
