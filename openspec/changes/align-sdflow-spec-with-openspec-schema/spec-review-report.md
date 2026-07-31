# Spec Review Report · align-sdflow-spec-with-openspec-schema

## 评审概要

- **变更**：align-sdflow-spec-with-openspec-schema
- **日期**：2026-07-31
- **评审层**：spec-review（设计评审）
- **主 session 模型**：opus（强档）
- **镜头 roster**：autoplan 广审（CEO+Eng，subagent-only）+ 对抗镜 ×2（sonnet）+ 接地镜 ×1（haiku）+ outside-voice fallback ×2（sonnet，同族）
- **命中 TG**：TG-05, TG-06, TG-08, TG-10, TG-12, TG-14, TG-19, TG-20, TG-21, TG-22, TG-23, TG-25

<!-- sdflow:hr-tg v1 hit="TG-06,TG-08" declared="TG-05,TG-06,TG-08,TG-10,TG-12,TG-14,TG-19,TG-20,TG-21,TG-22,TG-23,TG-25" evidence="TG-06: fork schema 是跨项目共享契约; TG-08: 依赖 CLI experimental schema 接口" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="native" -->

## 接地镜核验结果

**全部 8 条代码事实核验通过**：C9（copy 安装）、C10（disable-model-invocation）、C14（allowlist 硬编码）、Impact 文件存在性、schema 目录尚未创建、config.yaml 当前值、ff0-branch-guard.py 存在、copy_bundle 整删重拷语义——均正确无误。

## Findings（按严重度排列）

### R1 [CRITICAL] `handle_config()` 的 update 模式 no-op 与「下游 update 自动切换 schema」直接矛盾

**置信度**：高 | **命中镜**：autoplan-CEO, autoplan-Eng, 对抗1, 对抗2（4 镜独立命中）

`sdflow-init/scripts/init.py:311-316` 的 `handle_config()` 在 `mode == "update"` 时直接返回 skip，不修改 config.yaml。测试 `test_plain_update_does_not_deploy_rules` 亦守此不变量。但 proposal/design/tasks 多处声称「下游随 `sdflow-init update` 自然切换」（proposal:34, design:98-113），tasks 2.1-2.6 无一条涉及改写 `handle_config` 的 update 分支。

**影响**：所有已初始化下游项目（正常情况）跑 update 后 `schema:` 键不变——静默失效。Success Metrics 1/2 对预存消费仓永远无法达成。本仓 dogfood（task 4.2）同样受影响。

**建议**：实现前补设计 + task + 测试，明确 `schema:` 键的机械改写机制。

### R2 [HIGH] schema 内容级更新对已 pin 在途 change 的回溯影响未分析

**置信度**：高 | **命中镜**：design-voice（新发现）

`.openspec.yaml` 按**名字** pin schema，但 `copy_bundle` 整删重拷会替换 schema **内容**。未来 schema 修改（含 F6 的补救路径「重新 fork」）会回溯影响所有已 pin 的在途 change，且无提醒机制。F1-F7 表和 scope-check 表均未覆盖。

**建议**：补入「接受的边角」或 F 表；或在 `sdflow-init update` 比较 schema 内容 hash，若变且存在引用该名的在途 change 则输出一行提示。

### R3 [HIGH] 回滚路径自相矛盾且无机械守卫

**置信度**：高 | **命中镜**：autoplan-Eng, 对抗1

design.md:194 同一句话先说「删 schemas/」再说「MUST 保留直至归档」——自相矛盾。Risks/三镜代价/ADR 三处的「config 一行 + 删目录」简化版与但书冲突。已 pin 的在途 change 在 schema 目录被删后 status/validate/instructions 均会报错。

**建议**：重写回滚步骤为无歧义顺序（① 枚举在途 `.openspec.yaml` ② 逐个改回 ③ 确认零引用再删目录 ④ 改 config）；同步修正三处简化措辞。

### R4 [HIGH] hook 拦截方案（本仓已有先例）从未被列入候选集

**置信度**：高 | **命中镜**：autoplan-CEO

`ff0-branch-guard.py` 是 PreToolUse hook 机械拦截先例（fail-closed）。decision-memo 6 个候选缺「用 hook 拦截 `/opsx:ff` 调用」——对「不会想到去查」失效模式最直接的机械解法。

**建议**：补进候选集并写取舍理由。

### R5 [HIGH] Success Metrics 只证「管道通」不证「问题解决」

**置信度**：高 | **命中镜**：autoplan-CEO, 对抗2

唯一测行为效果的指标 #2 只有一次性手工试跑（task 4.4），假设表自认「无实测锚」。dogfood 验证的在途 change 已有 `.openspec.yaml`，补写分支是纯 no-op，「零回归」名不副实。

**建议**：坦白说明验收范围，或补构造一个缺 `.openspec.yaml` 的临时 change 纳入验证。

### R6 [MEDIUM-HIGH] 版本门无上限 + 字符串比较未定义 + CLI 缺失分支未覆盖

**置信度**：高 | **命中镜**：autoplan-CEO, autoplan-Eng, 对抗1, HR-TG

- 只有版本地板，无后向核验；CLI 升级可能破坏已冻结 fork
- 比较方式未 spec（naive 字串比较 `"1.10.0" < "1.7.0"` 误判）
- 决策图和 F 表都未覆盖「CLI 命令不存在/执行异常」分支

**建议**：spec 明确 semver 比较 + 不可判定时 fail-closed + 补 F8 条目 + 加 `1.10.0` 测试用例 + post-copy best-effort `schema validate`。

### R7 [MEDIUM-HIGH] `copy_bundle` 扩展路径与收敛语义未定义

**置信度**：高 | **命中镜**：autoplan-Eng, 对抗2, HR-TG

`copy_bundle()` 硬编码 `assets/workflow` → `openspec/workflow`，schema 源/目的地在其外部。`tools/` 的整删重拷是专门为 `tools_dst` 写的 rmtree-first 逻辑，`full=True` 用 `dirs_exist_ok=True`（不删旧文件）。若实现时未重建 rmtree-first，F7 防线落空。

**建议**：设计补一条说明具体机制（新函数 or 扩展），并明确 MUST 采用 rmtree-first。

### R8 [MEDIUM-HIGH] 委派区块剥离——「确定性操作」却零自动化测试

**置信度**：高 | **命中镜**：autoplan-Eng, 对抗1

SA-17(a) 称「确定性操作」但实现在 SKILL.md 指令层。未来编辑可能静默打坏 marker。建议加廉价的机械化写后核验（grep `sdflow:delegation`）+ 对静态 fork schema 内容加 CI 不变量。

### R9 [MEDIUM-HIGH] `skip_specs` 的写入机制全程未指定

**置信度**：中 | **命中镜**：对抗1（新发现）

D3/D4 和 SA-17(c) 覆盖了判断端和消费端，唯独遗漏中间：谁在什么时候把 `skip_specs: true` 实际写进 `.openspec.yaml`？`grep -rn "skip_specs" sdflow-spec/` 零命中。tasks 无对应条目。

**建议**：tasks 补一条，明确落盘时机与方式。

### R10 [MEDIUM] 迁移补写容错风格与本仓既有代码 fail-safe 惯例冲突

**置信度**：中 | **命中镜**：对抗1

`init.py` 的 `retire_hooks()`、`retire_deploy_files()` 等一律 fail-safe（单项出错跳过继续）。若迁移补写同此惯例，单项失败后 config 切换仍会执行——复现 F4。

**建议**：tasks 2.3 明确 fail-closed + 测试加「单项失败 → config 未切换」用例。

### R11 [MEDIUM] Codex 宿主下委派有效性推迟到实现期

**置信度**：中 | **命中镜**：autoplan-CEO

开放问题表写未验，截止=实现期。但 bundle 面向所有宿主下发。

**建议**：提前到设计门内做一次手工试跑锚，或明确划入 Non-Goals。

### R12 [MEDIUM] 优先级标注不一致——`requires` 改密标 P1 但自认价值「变薄」

**置信度**：高 | **命中镜**：autoplan-CEO, 对抗2

decision-memo D6 自认「CLI 图密不密在实际产出路径上无影响」，但 TG-19 标 P1。

**建议**：调整措辞或降级。

### R13 [MEDIUM] 根问题（绕过拷问）无真实事故引用

**置信度**：中 | **命中镜**：autoplan-CEO

Why 全文是失效模式推演，未引用一次真实事故。D6 已承认收益「变薄」。

**建议**：补真实事故引用，或把改动定性为「低成本保险」。

### R14 [MEDIUM] 第三类 instruction 消费者（archive skill）未被分析

**置信度**：中 | **命中镜**：design-voice

design.md「双读者时序」只列官方入口和 sdflow-spec C.3，但 `openspec-archive-change` 的 delta-spec 同步步骤也会调 `openspec instructions specs --change`。C12 分析的前提（仅两类读者）未经证伪。

**建议**：补一条实测锚（C15），验证 archive 流程在新 schema 下正常。

### R15 [MEDIUM] 迁移补写可能误补非 change 目录

**置信度**：中 | **命中镜**：autoplan-Eng

扫描 `openspec/changes/*/` 只检查缺 `.openspec.yaml`，不验证是否真实 change。

**建议**：补检查 `proposal.md` 存在 + 加 stray 目录测试。

### R16 [MEDIUM] 多能力 glob 路径混合场景未验

**置信度**：中 | **命中镜**：对抗2

C6 证据锚像是单能力场景实测。一次 change 同时含已有 + 全新能力的 specs delta 时，`existingOutputPaths` 与推导路径如何共存未验。

**建议**：补 C-item 实测。

### R17 [LOW-MEDIUM] glob capability 名→路径推导缺规范化规则

**置信度**：中 | **命中镜**：autoplan-Eng

SA-17(b) 无 slug 化规则。空格/非 ASCII/`..` 可能造出非预期目录名。

**建议**：定义规范化规则 + 加冲突测试。

## 决策登记区

### [自动决策]

| # | 决策 | 理由 |
|---|------|------|
| D1 | 接受 R1（handle_config no-op）为 CRITICAL | 4 镜独立命中，代码证据确凿 |
| D2 | 接受 R2（schema 内容回溯）为 HIGH | design-voice 新发现，逻辑链成立 |
| D3 | 合并回滚自相矛盾 + 无机械守卫为 R3 | 同一主题，autoplan-Eng + 对抗1 |
| D4 | 合并版本门三子题为 R6 | 同一接口面的三个维度 |
| D5 | 合并 copy_bundle 三来源为 R7 | 同一函数的扩展设计问题 |
| D6 | 合并委派剥离两来源为 R8 | 同一问题的测试缺口 |

### [需拍板]

| # | 问题 | 选项 | 推荐 | 三面后果 |
|---|------|------|------|----------|
| Q1 | R11 Codex 宿主验证时机 | (A) 设计门内做手工试跑 (B) 划入 Non-Goals | 推荐 A | 系统镜：提前验证风险低；用户镜：Codex 用户早知效果；开发循环镜：多一次手工测试成本低 |
| Q2 | R13 根问题是否补事故引用 | (A) 补真实事故引用 (B) 改定性为「低成本保险」 | 推荐 B | 系统镜：无影响；用户镜：预期管理更诚实；开发循环镜：避免复盘时高估收益。**主次 = 开发循环镜** |

### [已裁掉]

| # | 原始发现 | 裁掉理由 |
|---|----------|----------|
| X1 | 对抗2-F6「一次成功走通作为 Success Metric 1 达标线偏乐观」 | 对抗2 自己标注「不再要求整改」，且 tasks.md 已在诚实边界里充分声明无自动化测试面——文档已知情接受此局限 |

## Outside Voice 记录

- **design-voice**：exec exit 1 → fallback（同族 Claude 子代理）。2 条 finding（R2 schema 内容回溯 + R14 第三类消费者），均已纳入合并池。
- **hr-tg**：exec exit 1 → fallback（同族 Claude 子代理）。2 条 finding（R7 copy_bundle 路径 + R6 CLI 缺失分支），均已纳入合并池。

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="claude" reason_code="exec-error" findings="2" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="claude" reason_code="exec-error" findings="2" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->

## 建议

本 change 的设计文档质量极高（C1-C14 十四条实测锚、D1-D10 决策 + 砍掉候选、F1-F7 失败模式表），接地镜核验全部代码事实正确。但 **R1 是阻塞级发现**——「下游 update 自动切换 schema」这条核心价值承诺在代码架构上找不到落地路径，实现前必须补设计。其余 HIGH 级 findings（R2-R5）建议在设计门拍板前修补。

**建议进设计 HARD-GATE**：用户批准后可进入实现阶段，但 R1 MUST 在实现前解决。

## 度量锚

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="10" 采纳="10" 裁掉="0" defer="0" 独立="3" sev="致1/高2/中7/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="12" 采纳="10" 裁掉="0" defer="2" 独立="3" sev="致1/高3/中5/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="claude" site="design-voice" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="claude" site="hr-tg" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中2/低0" -->
