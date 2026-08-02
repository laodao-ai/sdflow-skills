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

### 1. 读取路径词表校验（T231 §1）[spec-review-amendment]

`_legacy_item_from_row`（`__init__.py:812`）读 legacy 表时，`cells[4]`（status）直接赋值无校验。

**修法**：分两层同步降级——

**(1a) core 层**：在 `_build_effective_snapshot` 的自检段（`__init__.py:826-901`）追加三字段词表校验：

```python
# status 校验
if item["status"] not in spec.status_values:
    problems.append(f"{item_id}: status '{item['status']}' 不在词表 {spec.status_values}")

# specific_field (type/priority) 校验
sf = spec.specific_field
if item[sf] not in spec.specific_values:
    problems.append(f"{item_id}: {sf} '{item[sf]}' 不在词表 {spec.specific_values}")
```

**(1b) consumer 边界**：`validate_scan_envelope`（`issues.py:437-440`）对 status/specific_field 的硬 `raise ValueError`（"枚举漂移"）同步降级为收进 problems + 继续。这是真正的 reindex 崩溃点——T231 原票（`todolist/2026-07-todolist.md:2383`）指向此处。只改 (1a) 不改 (1b) → `_scan_pool` 子进程输出含脏值 → 父进程 `validate_scan_envelope` 仍硬 raise → reindex 整体中止。

脏值项**仍收入 items 列表**（不丢弃），但 problem 会被 reindex 回显到 stderr + 被调用方看到。
不丢弃理由：丢弃 = 静默少计（和现状一样），显红 = 数字准确但标注哪些有问题。

### 2. reindex 罢工 → 降级（T231 §2）[spec-review-amendment]

`issues.py:1959/1963` 的 `_die` 在 **set-status / add 的写入路径**上（拒绝非法输入），正当保留。

T231 要修的是**读取路径**：`_scan_pool`（`issues.py:444`）→ `validate_scan_envelope`（`issues.py:437-440`）→ `read_pool` → `_reindex_core` 链路中，legacy 表脏行导致 `validate_scan_envelope` 硬 raise ValueError。

**已确认**：downstream 的 `generate_index_md` / `sync_batches_md` 不会因脏 status 崩溃——`_is_terminal`（`issues.py:513-515`）用 `.get(..., set())` 兜底，`_render_item_table` 只做 f-string 插值，脏值安全透过。无需 try-except。

**修法**：第 1 点的词表校验（1a + 1b）已完整覆盖——core 层 `_build_effective_snapshot` 显红 + consumer 层 `validate_scan_envelope` 同步降级。

### 3. reindex 丢数据守卫（B12）

`issues.py:604` 的 `_reindex_core` 直接 `atomic_write` 覆盖 INDEX.md，无防护。

**修法**：写盘前读旧 INDEX 总项数（open + closed），与新扫描的总项数比较。[spec-review-amendment]

**两段式解析**（INDEX.md 的 closed 项只有聚合摘要行，不逐行渲染）：

```python
def _count_index_items(index_path):
    """读旧 INDEX.md，返回 open + closed 总项数。
    open = 数 '| T/B...' 表格行；closed = 解析 '共 N 项已闭合' 聚合行的 N。"""
    if not os.path.exists(index_path):
        return 0
    text = open(index_path, encoding="utf-8").read()
    open_count = len(re.findall(r'^\| [A-Z]\d+ \|', text, re.MULTILINE))
    m = re.search(r'共 (\d+) 项已闭合', text)
    closed_count = int(m.group(1)) if m else 0
    return open_count + closed_count

old_count = _count_index_items(index_path)
new_count = len(items)
if old_count > 0 and new_count < old_count:
    raise ReindexStageError(
        "INDEX",
        RuntimeError(f"总项数骤降（{old_count}→{new_count}），拒绝覆盖——可能是版本偏斜")
    )
```

不变量依据：正常操作（add/set-status/batch）只增项或改状态，不删项。总项数只增不减。
`old_count == 0`（首次建 INDEX 或旧文件不可解析）时跳过校验。
旧 INDEX 存在但格式不可解析 → `_count_index_items` 返回 0（跳过校验 + 记 problem 警告），不 fail-closed 卡死 reindex。

D3 约束兼容说明：D3（"禁读旧 INDEX"）约束的是 `generate_index_md` 纯函数，不约束 `_reindex_core` 整体。本守卫在 `_reindex_core` 层（`generate_index_md` 之外）读旧 INDEX，不破坏渲染函数的纯度。

### 4. triage 解耦（T231 §3）[spec-review-amendment]

`_bug_triage`（`__init__.py:1797-1798`）和 `_todo_triage`（`__init__.py:1836-1837`）的
`open_untriaged` 集合在 batch add 时把 OPEN/VERIFIED 等非终态非 PROPOSED 的 status 强推为 PROPOSED。

**问题分析**（设计审修正）：triage 命令的"赋批次+推进状态"是 SKILL.md 正式定义的设计契约（`:494-496`），不是意外副作用。`cmd_batch_add`（`issues.py:968-1007`）本来就不碰 status（纯注册表操作）。真正的"越权"发生在 `cmd_sweep`（`issues.py:1126-1132`）——sweep 编排层通过子进程调用 triage，间接触发状态推进。

**修法**：给 `_bug_triage` / `_todo_triage` 加 `promote` 参数（默认 `True` 保持原行为），`promote=False` 时跳过 `open_untriaged` 推进逻辑（`new_status = old_status`）。`triage` CLI 子命令新增 `--batch-only` flag 映射到 `promote=False`。`cmd_sweep` 的子进程调用改为 `triage --batch-only --id X --批次 Y`。

设计理由：`batch rename` 已为规避同一副作用走了独立路径（SKILL.md:392-393），`--batch-only` 是同一设计哲学下更轻量的方案——triage 命令本身的契约不变，只在编排层可选关闭推进。

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
