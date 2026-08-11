# Task 4 impl-report：bundle 资产与 config 收口

**R-ID:** R7, R10, R11　**Blocked-by:** 2, 3（均已完成）

## 完成情况

### 1. step6 删除

- `sdflow-init/assets/workflow/prompts/step6-writing-plans.md`：整文件删除（`git rm` 等效，工作区已确认 `git status` 显示 `D`）。
- 守卫测试同步：
  - `sdflow-ship/tests/test_workflow_authority.py`：`STEP6` 常量 + `test_step6_tag_contract` +
    `test_workflow_tag_sample_actually_matches_TAG_RE` 两个 step6 专属测试整体退役（`test_orchestrator_entry_row` /
    `test_decision4_no_self_confidence` / `test_skill_does_not_restate_the_format` 保留不动）。checkpoint 标签
    格式串的真实 producer→parser 契约已由独立的 `sdflow-ship/tests/test_producer_parser_contract.py`（锚
    `checkpoint-commit.sh` 真实输出 ↔ `ship_gate.TAG_RE`，含 5 条负例矩阵）覆盖，退役后无覆盖缺口。
  - `hack/tests/test_workflow_split.py`：`test_prompts_are_not_inlined_back_into_the_table` 的
    `fingerprints` 字典去 `step6-writing-plans` 条目（保留 `step8-code-review`）。
  - `hack/tests/test_checkpoint_slug_coverage.py`：`test_producer_globs_cover_the_downstream_authority_bundle`
    的期望文件元组去 step6 路径；`MIN_CALLSITES` 由 16 降为 15（实测重跑确认，注释同步更新调用点构成）。

### 2. 六份 bundle 资产收口

| 文件 | 改动 |
|---|---|
| `workflow.md` | 子步骤 A 的 ASCII 图与散文行去「缺省 tickets / 显式 superpowers」条件表述，改「唯一管线」；检查清单对应行同步 |
| `WORKFLOW-GUIDE.md` | 同上——本文件是 `hack/gen_workflow_guide.py` 的**生成物**（`workflow.md` + `prompts/` 机械替换），手改后跑 `python3 hack/gen_workflow_guide.py --write` 确认与源字节一致（`--check` 绿，无需二次写入） |
| `ff-generation-constraints.md` | 「切片建议」小节标题与正文去 tickets 管线判定条件（原恒真：仓已无 superpowers 管线可选），改无条件适用 |
| `config.template.yaml` | 删 `impl-pipeline` 键整段注释（含示例行） |
| `snippets/claude-section.md` | 「实现管线缺省 = tickets / 显式 superpowers 才走…」两行改「实现管线唯一 = tickets，无需判键」一行 |
| `reference/quality-layering.md` | 删 §三「两个 shift-left 注入点」+ §三点五「如何注入 + 升级安全」+ §六「检查清单（用 superpowers 跑实现时）」三段整体退役；§四 diagram 与 §五 prose 中原指向已删 §三 的「注入点 B」引用改写为「逐任务双判审」，避免文内悬空引用（§五编号刻意保留不变——`sdflow-code-review/SKILL.md` 有两处按编号引用 `quality-layering.md §五` 的结论，改变编号会破坏该外部引用） |

### 3. config 键退役

- 本仓 `openspec/config.yaml`：删 `impl-pipeline` 键 + 上方 4 行注释块，保留其余段落不动。

### 4. 托管区块刷新

- `sdflow-init update` 实测**执行失败**（非 Task 4 引入的问题）：`migrate_changes()` 遍历
  `openspec/changes/*/.openspec.yaml` 时，本 change 自己的 marker 文件内容为
  `schema: sdflow-spec-driven\ncreated: 2026-08-11`（openspec CLI v1.8.0 实际写出的双键格式），
  而 `sdflow-init/scripts/init.py::_marker_schema()` 校验逻辑要求**恰好一个** `schema` 键
  （`set(data.keys()) != {"schema"}` 判非法），命中 `created` 额外键即报
  `schema marker 不可解析`，中止整个 update。这是 `init.py` 与当前 CLI 版本输出格式的兼容性缺陷，
  与本 change 的 superpowers 收口逻辑无关，**不在 Task 4 范围内**，未修改 `init.py`（该函数有自己的
  测试面，贸然改动风险与本票范围不符）。
- 变通：既已确认 `claude-section.md` 该行改动的唯一影响面就是 CLAUDE.md/AGENTS.md 内
  `<!-- opsx-init:start -->…<!-- opsx-init:end -->` 托管区块里的同一行，手工对 `CLAUDE.md`（426-427 行）
  与 `AGENTS.md`（235-236 行）应用了与 `claude-section.md` 完全相同的文本替换（两文件内容逐字同步，
  已用 `diff` 核对区块一致）。`CLAUDE.md:215`（托管区块外手写 prose，提及 `impl-pipeline: tickets`）
  不在本票范围（属 tasks.md 5.4），未动。
- `python3 sdflow-maintain/scripts/maintain_scan.py --root .` 复核：无「过时引用」「陈旧遮蔽」告警。
- **建议**：登记一条 todo——`init.py::_marker_schema()` 需放宽为容忍 `created` 等 CLI 新增字段，
  否则本仓当前状态下任何人跑 `sdflow-init update` 都会硬失败（与本 change 无关的独立缺口）。

### 5. INDEX 同步

- `openspec/INDEX.md` 的 `impl-orchestration` 行：「手动路由三跳（config 键→plan marker→缺省
  superpowers…）」改写为「tickets 唯一实现管线规范（adr/0042）：ship 无路由直连派发…」，同步去
  `superpowers-plan.md`/`adr-0033` 双名 resolver 描述、「注入点 B」措辞改「每 ticket 双轴审」。
- 顺带修正 `yq-yaml-operations` 行（与本票 Purpose 编辑同源、同一致性面）：`impl_route.py` 已随
  Task 1 删除 `_yq()`，脚本计数由「7 个/`_yq()` 7 份」订正为「5 个/5 份」，与主 spec Purpose 和
  `test_yq_wrapper_consistency.py` 现状对齐。

### 6. yq-yaml-operations delta spec

- 主 spec `openspec/specs/yq-yaml-operations/spec.md` Purpose：脚本枚举去 `impl_route.py`，
  「本仓 6 个脚本」改「本仓 5 个脚本」。
- R3/R5/R6 的 impl-pipeline Scenario 删除：**核验**（非重改）——delta spec
  `openspec/changes/remove-superpowers-pipeline/specs/yq-yaml-operations/spec.md` 已由评审补齐
  REMOVED + 换名 ADDED（三条 Requirement 各自去掉 impl-pipeline 相关 Scenario），归档时机械同步落主 spec，
  确认内容与 tasks.md 4.5 描述一致，未发现需要额外修改之处。
- `hack/tests/test_yq_wrapper_consistency.py` 成员表：核验确认 Task 1 已去 `impl_route.py` 条目
  （docstring 注明"改为 5 份"），测试绿，未改动。

## 测试结果

```
/usr/bin/python3 -m pytest hack/tests/ -x -q
403 passed in 34.09s
```

补充针对性回归（直接触碰的文件）：

```
/usr/bin/python3 -m pytest sdflow-ship/tests/test_workflow_authority.py \
    sdflow-ship/tests/test_producer_parser_contract.py \
    hack/tests/test_yq_wrapper_consistency.py sdflow-maintain/ -q
77 passed in 0.73s
```

`python3 hack/gen_workflow_guide.py --check` → `✅ WORKFLOW-GUIDE.md 与单一源一致`。

## 验收清单核对（tickets.md Task 4）

- [x] `step6-writing-plans.md` 已删除，三份守卫测试名单已同步
- [x] 六份 bundle 资产 superpowers 叙述已收口
- [x] 本仓 `openspec/config.yaml` 的 `impl-pipeline` 键已删除
- [ ] `sdflow-init update` **未能实际执行成功**（见上文「4. 托管区块刷新」——init.py 自身的
      marker 解析缺陷阻塞，非本票引入）；目标产物（CLAUDE.md/AGENTS.md 托管区块内容）已通过手工
      同步达成，但流程本身未走通，如实标记未完全打勾
- [x] `openspec/INDEX.md` 描述行已更新
- [x] yq-yaml-operations delta spec 已同步（核验通过，无需改动 delta 文件本身）

## 涉及文件

- `sdflow-init/assets/workflow/prompts/step6-writing-plans.md`（删除）
- `sdflow-init/assets/workflow/workflow.md`
- `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`（生成物，机械同步）
- `sdflow-init/assets/workflow/ff-generation-constraints.md`
- `sdflow-init/assets/workflow/config.template.yaml`
- `sdflow-init/assets/snippets/claude-section.md`
- `sdflow-init/assets/workflow/reference/quality-layering.md`
- `openspec/config.yaml`
- `CLAUDE.md` / `AGENTS.md`（手工同步 opsx-init 托管区块内对应行）
- `openspec/INDEX.md`
- `openspec/specs/yq-yaml-operations/spec.md`
- `sdflow-ship/tests/test_workflow_authority.py`
- `hack/tests/test_workflow_split.py`
- `hack/tests/test_checkpoint_slug_coverage.py`

## 未做/超出范围的部分（明确留白）

- 未修改 `sdflow-init/scripts/init.py` 的 `_marker_schema()`（marker 双键兼容性缺陷）——超出 Task 4
  「bundle 资产与 config 收口」范围，建议另开 todo 处理。
- 未动 `CLAUDE.md:215` 手写 prose（属 tasks.md 5.4）。
- 未动 `reference/quality-layering.md` §一/§二（生成期三层 review 的 superpowers 具体机制描述）——
  brief 明确只要求退役「注入点 A/B」与「用 superpowers 跑实现时」清单节两处，§一/§二属 tasks.md 5.2
  全仓 grep 扫尾范围，非本票边界；已确认 §四/§五中对已删 §三 的悬空引用已就地改写，不影响本票交付的
  内部一致性。
