## Context

issues 台账读取路径三处诚实性缺陷 + 一个数据丢失 bug，详见 proposal。
改动面 = `sdflow_issues_core/__init__.py` + `issues.py` + 测试。
前置阻塞（三脚本合一）已于 `dedupe-issues-scripts-shared-layer`（2026-07-22）解除。

## Goals / Non-Goals

**Goals**：
- 读取路径词表校验（显红不罢工）
- reindex 总项数只增不减守卫
- batch add 不碰 status（triage 解耦）

**Non-Goals**：
- 历史脏值自动修复（交 migrate_legacy）
- 写入路径改造（cmd_add / set-status 的 _die 正当）

## Design

### 1. 读取路径词表校验（T231 §1）

`_legacy_item_from_row`（`__init__.py:812`）读 legacy 表时，`cells[4]`（status）直接赋值无校验。

**修法**：在 `_scan_pool` 的自检段（`__init__.py:842-887`）追加三字段词表校验：

```python
# status 校验
if item["status"] not in spec.status_values:
    problems.append(f"{item_id}: status '{item['status']}' 不在词表 {spec.status_values}")

# specific_field (type/priority) 校验
sf = spec.specific_field
if item.get(sf) and item[sf] not in spec.specific_values:
    problems.append(f"{item_id}: {sf} '{item[sf]}' 不在词表 {spec.specific_values}")
```

脏值项**仍收入 items 列表**（不丢弃），但 problem 会被 reindex 回显到 stderr + 被调用方看到。
不丢弃理由：丢弃 = 静默少计（和现状一样），显红 = 数字准确但标注哪些有问题。

### 2. reindex 罢工 → 降级（T231 §2）

`issues.py:1959/1963` 的 `_die` 在 **set-status / add 的写入路径**上（拒绝非法输入），正当保留。

T231 要修的是**读取路径**：`_scan_pool` → `read_pool` → `_reindex_core` 链路中，legacy 表脏行
导致的 `KeyError` / 解析异常。当前代码在遇到 frontmatter 未知 status 时直接走 `_die`（`__init__.py:1963`），
但这只在 set-status 命令路径上。真正的读取路径问题在 `_legacy_item_from_row` 透传脏值后，
downstream 的 `generate_index_md` / `sync_batches_md` 是否会炸——需要确认。

**修法**：第 1 点的词表校验已覆盖。如果脏值导致 `generate_index_md` 内部逻辑异常（如按 status
分桶时 KeyError），在该函数加 try-except 捕获单项异常 → skip + problem，不中止整个 reindex。

### 3. reindex 丢数据守卫（B12）

`issues.py:604` 的 `_reindex_core` 直接 `atomic_write` 覆盖 INDEX.md，无防护。

**修法**：写盘前读旧 INDEX 总项数（open + closed），与新扫描的总项数比较：

```python
old_count = _count_index_items(index_path)  # 读旧 INDEX 的 | T/B 行数
new_count = len(items)
if old_count > 0 and new_count < old_count:
    raise ReindexStageError(
        "INDEX",
        RuntimeError(f"总项数骤降（{old_count}→{new_count}），拒绝覆盖——可能是版本偏斜")
    )
```

不变量依据：正常操作（add/set-status/batch）只增项或改状态，不删项。总项数只增不减。
`old_count == 0`（首次建 INDEX）时跳过校验。

### 4. triage 解耦（T231 §3）

`_bug_triage`（`__init__.py:1797-1798`）和 `_todo_triage`（`__init__.py:1836-1837`）的
`open_untriaged` 集合把 OPEN/VERIFIED 等非终态非 PROPOSED 的 status 强推为 PROPOSED。

**修法**：删掉两行 `open_untriaged` 计算 + 条件赋值，改为 `new_status = old_status`。
batch add 语义 = 归批次，不改状态。要改状态走 `set-status` 命令。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。

## Risks / Trade-offs

- **脏值项不丢弃**：盘点数字含脏项（problem 标注），不会因过滤而少计。代价 = INDEX 里出现脏 status 行，但有 problem 警告。
- **总项数守卫假阳**：理论上不可能（不变量精确），除非有人手删 dated 文件里的 `## T/B` 块。

## Migration Plan

无。纯行为修复，无数据迁移。

## Open Questions

无。

## Compliance

改动不涉及安全/合规/外部 API。遵守 `POOL_SPEC` 封闭 schema 注入（不加 pool 条件分支）。
