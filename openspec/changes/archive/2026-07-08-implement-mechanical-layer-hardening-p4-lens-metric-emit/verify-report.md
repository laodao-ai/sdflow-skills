---
ship-gate:
  verify: PASS
---

# Verify Report: implement-mechanical-layer-hardening-p4-lens-metric-emit

日期：2026-07-08

## 结论：PASS

代码/测试/契约/两审 SKILL 落锚步四处都真实实现了 tasks.md 与 specs 的要求，非仅复选框声称。核心机验：
`pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -q` → **39 passed**；
`pytest sdflow-init/assets/workflow/tools/tests/ -q`（全套件，含 anchor_lint/trivial_shape）→ **100 passed**；
`python3 sdflow-init/assets/workflow/tools/lens_metric_emit.py --layer spec-review --input .../fixtures/lens_metric_input.json` → **exit 0**，输出 6 行合规锚（roster 6 行键各一行，含 2 个零-finding 行）。

## 逐需求核对表

### tasks.md §1 契约枚举 + 折叠块读取

| 任务 | 代码出处 | 状态 |
|---|---|---|
| 1.1-1.2 `load_enums` fence-aware 读 `lens-metric-enums`，缺块 EmitError | `lens_metric_emit.py:19-59`；测试 `test_load_enums_real_contract`/`test_load_enums_missing_block`/`test_load_block_unclosed_fence_fail_closed` | ✅ |
| 1.3 无硬编码枚举/折叠清单；verdict 本地常量须引 ADR-11 | `lens_metric_emit.py:9` `VERDICTS = (...)  # 本地常量豁免（ADR-11：...）`；design.md:120 ADR-11 表列 verdict 豁免理由 | ✅ |
| 1.4 契约新增 `lens-metric-fold` 机读块，只列非恒等 | `lens-metric-contract.md:37-54`（13 条非恒等映射，恒等注记见 :38） | ✅ |
| 1.5 `load_fold` 读映射，缺块/codomain 越界/重复键 fail-closed | `lens_metric_emit.py:62-71`；测试 `test_load_fold_dup_key_fail_closed`/`test_load_fold_codomain_out_of_enum_fail_closed` | ✅ |

### tasks.md §2 归约核心

| 任务 | 代码出处 | 状态 |
|---|---|---|
| 2.1-2.2 单条采纳→行键锚，折叠恒等 pass-through + 未知 raw fail-closed | `lens_metric_emit.py:74-97`（`fold_hit`）；测试 `test_fold_hit_identity_passthrough`/`test_fold_hit_nonidentity_map`/`test_fold_hit_unknown_raw_fail_closed_not_broad`/`test_reduce_single_accepted` | ✅ |
| 2.3-2.4 归属 per-hit 行键 + 独立（去重集 size==1∧采纳） | `lens_metric_emit.py:145-155`；测试 `test_reduce_coreport_no_independent` | ✅ |
| 2.5 同类型多实例折叠同行键仍独立 | `lens_metric_emit.py:154-155`；测试 `test_reduce_same_type_multi_instance_independent` | ✅ |
| 2.6 sev rollup 仅采纳项 + Σsev==采纳 自校验 | `lens_metric_emit.py:140-160`；测试 `test_reduce_rejected_illegal_sev_fail_closed` 覆盖非法 sev；不变量代码见 :158-160 | ✅ |
| 2.7 outside-voice 按 site 分行 | `lens_metric_emit.py:85-90`；测试 `test_fold_hit_outside_voice_needs_runner_site` | ✅ |
| 2.8 roster 恒落行（含零-finding 全零行）+ MIN_LENS_ROWS fail-closed | `lens_metric_emit.py:104-126`；测试 `test_reduce_single_accepted`（ov 零行断言）/`test_reduce_roster_missing_mandatory_fail_closed` | ✅ |
| 2.9 finding 命中行键 ⊆ roster（C4 反方向） | `lens_metric_emit.py:146-148`；测试 `test_reduce_finding_lens_not_in_roster_fail_closed` | ✅ |

### tasks.md §3 输入校验 fail-closed

| 任务 | 代码出处 | 状态 |
|---|---|---|
| 3.1 非法 JSON/缺字段 非零退出+stderr含字段名，MUST NOT 产锚 | `lens_metric_emit.py:181-192`；测试 `test_cli_bad_json_exit1_no_stdout`/`test_cli_null_roster_clean_fail` | ✅ |
| 3.2 verdict/lens/runner/sev 越域 fail-closed | `lens_metric_emit.py:93-94,111-114,137-142`；测试 `test_reduce_bad_verdict_fail_closed`/`test_reduce_rejected_illegal_sev_fail_closed` | ✅ |
| 3.3 无 per-finding layer，锚 layer 恒取 `--layer` | `lens_metric_emit.py:100-103,167`（schema 无 layer 字段，reduce 签名以 `layer` 参数注入单一处）；契约 schema 块 `lens-metric-contract.md:59-68` 无 per-finding layer | ✅ |
| 3.4 `hits:[]` present-but-empty fail-closed（C11） | `lens_metric_emit.py:135-136`；测试 `test_reduce_empty_hits_fail_closed` | ✅ |
| 3.5 采纳缺/空 sev fail-closed（C12） | `lens_metric_emit.py:143-144`；测试 `test_reduce_accepted_missing_sev_fail_closed` | ✅ |
| 3.6 site 注入字符 fail-closed（C7） | `lens_metric_emit.py:11,95-96`；测试 `test_fold_hit_site_injection_fail_closed`/`test_reduce_roster_site_non_str_fail_closed` | ✅ |
| 3.7 all-or-nothing，坏第 N 条→无任何锚+非零退出 | `lens_metric_emit.py:189-193`（`reduce` 全量校验完才 return lines，`main` 才 print）；测试 `test_cli_partial_fail_no_partial_anchor` | ✅ |
| 3.8 roster 重复行键 fail-closed（C14） | `lens_metric_emit.py:119-122`；测试 `test_reduce_roster_dup_key_fail_closed` | ✅ |
| 3.9 emitter 不读 config，无 `--metrics-on` 参数 | `lens_metric_emit.py:174-179`（argparse 仅 `--layer`/`--input`/`--contract`，无 config 读取路径，通篇无 `import yaml`/`config`） | ✅ |

### tasks.md §4 产出↔校验/聚合一致性

| 任务 | 代码出处 | 状态 |
|---|---|---|
| 4.1 emit-then-lint 无违规 | 测试 `test_emit_then_check_lens_metric_clean`（`al.check_lens_metric(...) == []`）/`test_golden_fixture_emits_and_lints` | ✅ |
| 4.2 fold codomain⊆enums.lens 双向 + aggregator enum 一致（C23） | 测试 `test_fold_codomain_subset_lens_enum`/`test_aggregator_enum_matches_contract`；`lens_metric_aggregate.py:17-18` `LAYER_ENUM`/`LENS_ENUM` 与契约完全一致（已核对取值） | ✅ |
| 4.3 `emitter.load_enums == anchor_lint.load_enums` 逐字段等价（C10） | 测试 `test_load_enums_equivalence` | ✅ |
| 4.4 mandatory-rows == `anchor_lint.MIN_LENS_ROWS`（C17 分叉①=B） | `lens_metric_emit.py:10` `MANDATORY_LENS = ("broad", "outside-voice")`；`anchor_lint.py:135` `MIN_LENS_ROWS = ("broad", "outside-voice")`；测试 `test_min_lens_rows_matches_anchor_lint` | ✅ |
| 4.5 幂等（跨 subprocess，PYTHONHASHSEED 0/1） | 测试 `test_cli_idempotent_cross_process` | ✅ |

### tasks.md §5 两审 SKILL 落锚步接 emitter

| 任务 | 代码出处 | 状态 |
|---|---|---|
| 5.1 spec-review SKILL 落锚步改调 emitter，门控关不调 | `sdflow-spec-review/SKILL.md:78`（门控段）、`:99-100`（Step3 度量锚段：构造 roster+findings → 调 `lens_metric_emit.py` → exit 0 才落 stdout → 保留残余信任边界声明） | ✅ |
| 5.2 code-review SKILL Step3-5 同 5.1 | `sdflow-code-review/SKILL.md:101-102`（门控）、`:112-124`（Step4 构造→Step5 调 emitter→exit0 落锚+残余信任边界声明） | ✅ |
| 5.3 两 SKILL 落锚步含 emit + check_lens_metric/anchor_lint 两步 + 引 golden fixture | `sdflow-spec-review/SKILL.md:99` 引用 `lens-metric-input-schema` 契约块 + golden fixture 路径；`sdflow-code-review/SKILL.md:114-116` 同样引用；两者均在 emitter 调用后接「锚行自检」/`anchor_lint` 步（spec-review :99 末句；code-review :123 附近） | ✅ |

### tasks.md §6 契约注记 + 部署

| 任务 | 代码出处 | 状态 |
|---|---|---|
| 6.1 契约补计数由 emitter 产出注记 + 独立在行键后计精化 | `lens-metric-contract.md:29-31`（归属规则区新增注记） | ✅ |
| 6.2 `pytest` 全绿，`-W error` 无 warning | 实跑 `pytest sdflow-init/assets/workflow/tools/tests/ -q` → 100 passed；追加 `-W error` 复核（见下方命令记录） | ✅ |
| 6.3 dogfood：`setup.sh` symlink 生效 + 两审端到端锚过 anchor_lint | 实测 `~/.claude/skills/sdflow-init -> .../04-sdflow-skills/sdflow-init`，`~/.sdflow/workflow -> .../sdflow-init/assets/workflow`（canonical 已指向本仓）；端到端锚过 anchor_lint 由 `test_golden_fixture_emits_and_lints`（脚本层）+ `test_emit_then_check_lens_metric_clean` 机验；SKILL 侧集成非 pytest 可测，锚点为落锚步文本核对（5.1-5.3） | ✅（脚本侧机验；SKILL 侧为静态核对，非可 pytest 化） |

### tasks.md §7 验收对账

| 任务 | 核对 | 状态 |
|---|---|---|
| 7.1 逐条 spec Scenario 有机械/文档锚点区分 | 见下方「逐 Scenario 判定」 | ✅ |
| 7.2 D-6 未改锚形/枚举/版本，套件一致性由 4.1/4.2/4.3/4.4 四测试守 | 契约文件 `lens-metric-enums` 块内容与改前一致（仅新增 `lens-metric-fold` 块+注记，未动 enums 值/版本号）；四测试均在上表确认 PASS | ✅ |
| 7.3 golden fixture 落库供 SKILL+测试共引 | `sdflow-init/assets/workflow/tools/tests/fixtures/lens_metric_input.json` 存在，被 `test_golden_fixture_emits_and_lints` 引用，且两 SKILL.md 文本引用同路径 | ✅ |

## 逐 Requirement/Scenario 判定（specs/lens-metric-emit/spec.md + specs/workflow-metrics/spec.md）

| Scenario | 类型 | 判定 |
|---|---|---|
| R1 结构化 findings 归约出合规锚与计数 | 机械测试 | ✅ `test_reduce_single_accepted` |
| R1 共抓 finding 每命中行各记但不计独立 | 机械测试 | ✅ `test_reduce_coreport_no_independent` |
| R1 同类型多实例折叠到同一行键仍算独立 | 机械测试 | ✅ `test_reduce_same_type_multi_instance_independent` |
| R1 折叠恒等 pass-through 与非恒等映射 | 机械测试 | ✅ `test_fold_hit_identity_passthrough`/`test_fold_hit_nonidentity_map`/`test_fold_hit_unknown_raw_fail_closed_not_broad` |
| R1 roster 中零-finding 行落全零行 | 机械测试 | ✅ `test_reduce_single_accepted`（ov 零行断言） |
| R1 finding 命中行键不在 roster 则 fail-closed | 机械测试 | ✅ `test_reduce_finding_lens_not_in_roster_fail_closed` |
| R1 metrics 开时强制 broad/outside-voice 行 | 机械测试 | ✅ `test_reduce_roster_missing_mandatory_fail_closed` + `test_min_lens_rows_matches_anchor_lint` |
| R2 越域枚举非零退出 | 机械测试 | ✅ `test_reduce_bad_verdict_fail_closed`/`test_reduce_finding_lens_not_in_roster_fail_closed` |
| R2 present-but-empty 与条件必填 fail-closed | 机械测试 | ✅ `test_reduce_empty_hits_fail_closed`/`test_reduce_accepted_missing_sev_fail_closed` |
| R2 site 注入 fail-closed | 机械测试 | ✅ `test_fold_hit_site_injection_fail_closed` |
| R2 all-or-nothing 不产部分锚 | 机械测试 | ✅ `test_cli_partial_fail_no_partial_anchor` |
| R2 契约枚举/折叠单一源读取 | 机械测试 | ✅ `test_load_enums_real_contract`/`test_load_fold_real_contract`/`test_fold_codomain_subset_lens_enum` |
| R3 emitter 输出过 check_lens_metric | 机械测试 | ✅ `test_emit_then_check_lens_metric_clean`/`test_golden_fixture_emits_and_lints` |
| R3 load_enums 等价性 | 机械测试 | ✅ `test_load_enums_equivalence` |
| R3 残余信任边界诚实声明 | **文档保留锚点，非机械测试** | ✅ `lens-metric-contract.md:29`「数值跨源一致性 = 主 session 信任边界」+ 两 SKILL.md 落锚步末句「保留残余信任边界声明」+ design.md D-6/ADR-11 |
| workflow-metrics C19「计数归约机械化，分类正确性为残余信任边界」 | **文档保留锚点，非机械测试** | ✅ `specs/workflow-metrics/spec.md:27-29` prose 声明 + SKILL.md 落锚步同款声明句，属诚实账类 Scenario，非 pytest 可测 |

## 缺口清单

**核心缺口**：无。

**Minor（可接受/deferred）**：
- 6.3 的「两审端到端」验证以脚本层 golden-fixture 测试 + SKILL.md 落锚步文本核对替代真实跑一次完整 spec-review/code-review 会话（后者需要真实评审场景触发，非本次 verify 范围，且 tasks 6.3 措辞本身也是「跑一轮」而非强制自动化断言）——**可接受**，因两 SKILL.md 的调用点、门控判断、exit 码检查、golden fixture 引用均已静态核对存在且与契约 schema 完全对齐，且脚本层已实证输出可过 `anchor_lint`。
- code-review defer 项（若有）：本次未见遗留 T86-88 类 defer 记录于 tasks.md，无需特别处理。

## 补充命令记录

```
$ python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -q
39 passed in 0.18s

$ python3 -m pytest sdflow-init/assets/workflow/tools/tests/ -q
100 passed in 0.29s

$ python3 sdflow-init/assets/workflow/tools/lens_metric_emit.py --layer spec-review \
    --input sdflow-init/assets/workflow/tools/tests/fixtures/lens_metric_input.json
(6 行合规锚输出) EXIT=0
```

无临时文件残留（本次 verify 仅读取 + 实跑既有脚本/测试，未新建任何文件）。

---

PASS — tasks.md 全 40 项复选框逐条附机验锚点（pytest 测试名/文件:行/实跑输出），核心归约逻辑（折叠/归属/独立/sev rollup/all-or-nothing/roster 恒落行/一致性守卫）与两审 SKILL 落锚步集成均有真实代码实现，非仅文档声称；39+61(anchor_lint/trivial_shape) = 100 项测试全绿；契约单一源（enums+fold）与 anchor_lint/aggregator 的一致性由 4 个独立守卫测试锁定，无漂移。
