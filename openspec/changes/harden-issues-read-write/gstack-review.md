<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- autoplan 原生执行证据：Skill 工具调用 autoplan + 内部 CEO 子代理(sonnet) + Codex voice(codex exec gpt-5.6-terra) 真实双声 -->

# gstack-review — harden-issues-read-write

## CEO Dual Voices Summary

### CLAUDE SUBAGENT (CEO — strategic independence)

6 条发现（1 严重 / 4 中 / 1 低）。

### CODEX SAYS (CEO — strategy challenge)

8 条战略盲点。

### CEO CONSENSUS TABLE

| 维度 | Claude | Codex | 共识 |
|------|--------|-------|------|
| D2 守卫逻辑不充分（计数 vs ID 集合检查） | 严重 | 严重（项 1+2） | **CONFIRMED** |
| 文档悬问未闭环（design §2 "需确认"） | 中 | 中（项 4） | **CONFIRMED** |
| consumer 仓复原路径缺失 | 中 | 中（项 7+8） | **CONFIRMED** |
| `validate_scan_envelope` 架构边界 | — | 中（项 4） | 单模型但正确 |
| `_scan_pool` 函数名引用过时 | 中 | — | 单模型 |
| triage 解耦历史语义混合 | — | 中（项 6） | 单模型 |

3/6 confirmed。

## Findings（按风险排序）

### F1 [严重·confirmed] D2 reindex 总项数守卫逻辑不充分

**问题**：design 和 spec 把"总项数只增不减"当充分条件，但这只是必要条件。当版本偏斜漏扫 3 项且同期新增 5 项时，净计数上升（57→59），守卫放行，但确实丢了 3 项——恰是 B12 的触发场景类别。

**建议**：改用 ID 集合超集检查（`old_ids ⊆ new_ids`），而非仅比较计数。改动量小：`_count_index_items` → `_extract_index_ids`，parse 旧 INDEX 的 ID 列。

**来源**：Claude CEO + Codex CEO 独立命中。

### F2 [中·confirmed] `validate_scan_envelope` 架构边界遗漏

**问题**：design 和 spec 说在 `_build_effective_snapshot` 追加 `problems.append` 实现"显红不罢工"。但实际数据流是 core → 子进程 JSON → `validate_scan_envelope`（`issues.py:437-440`）硬拒绝 `status not in status_values`。只改 core 不改 consumer 边界 = spec 承诺的"正常返回"无法兑现。

**建议**：`validate_scan_envelope` 的枚举校验需同步降级为 `problems.append` + 继续，或确认 legacy 数据在 core scan 阶段已被过滤/标记到 consumer 不会看到脏值。

**来源**：Codex CEO 项 4，主 session 读码验证确认。

### F3 [中·confirmed] design §2 悬问未闭环

**问题**：design.md §2 原文写"需要确认"（`generate_index_md` / `sync_batches_md` 是否会炸），但 decision-memo 写"Open Questions：无"。tasks.md 也没有对应任务。实际读码确认不会炸（`_is_terminal` 用 `.get` 兜底），但结论未回写 design。

**建议**：[spec-review-amendment] 把 design §2 的"需要确认"改为已确认结论。

**来源**：Claude CEO 项 4 + Codex CEO 项 4。

### F4 [中] design/spec/tasks 引用了不存在的函数名 `_scan_pool`

**问题**：三份文档统一引用 `_scan_pool` 的自检段（`__init__.py:842-887`），但实际位于 `_build_effective_snapshot`（`__init__.py:826-901`）。`_scan_pool` 是 `issues.py:444` 的跨进程调用函数，不含自检逻辑。

**建议**：[spec-review-amendment] 统一改为 `_build_effective_snapshot`。

**来源**：接地镜 + Claude CEO 项 5。

### F5 [中] consumer 仓升级路径缺失

**问题**：B12 发生在 zhws_ops_api，本修复不会自动推送到消费仓。四件套未提及消费仓何时/如何获得修复，也未建议升级后重跑 reindex 核对。

**建议**：hand-off.md 补 advisory。不阻塞本 change。

**来源**：Claude CEO 项 3 + Codex CEO 项 7。

### F6 [低] legacy 格式 sunset 未讨论

**问题**：这是第二轮给 legacy 读取路径打补丁。是否该推动全量迁移到 overlay 格式、删除 legacy 解析分支，未被讨论。

**建议**：记 todolist 条目，不塞进本 change。

**来源**：Claude CEO 项 6 + Codex CEO 项 5。

## 自动决策

- [自动决策] D-auto-1: autoplan premise gate — 本 change 的前提（三处诚实性缺陷 + 一个数据丢失 bug，来自实战报告）经双声验证成立，自动接受。依据 P6（bias toward action）。
- [自动决策] D-auto-2: 范围判断 — 不扩大（P2，blast radius 内无需扩展），不缩小。
- [自动决策] D-auto-3: Codex 项 3（显红不中止 vs 严格模式分离）— `reindex --strict` 已存在（`issues.py:647`），自动化可选传 `--strict`；当前设计"问题报告 + 默认放行"对诊断场景合理。依据 P5（explicit over clever）。
- [自动决策] D-auto-4: Codex 项 6（triage 语义历史审计）— 本 change Non-Goals 已排除迁移，且 batch 的 PROPOSED 历史数据量小（本仓约 10 条），影响低。依据 P3（pragmatic）+ ④（低概率小影响不纠结）。
- [自动决策] D-auto-5: Codex 项 8（端到端回归）— 本仓已有完整 pytest 覆盖，消费仓回归交升级后验证。依据 P3。

## Scope Drift Assessment

无 scope drift。change 范围精确：两个文件 + 测试，与 proposal 一致。
