## Why

issues 台账的读取路径存在三处诚实性缺陷 + 一个数据丢失 bug（T231 + B12），自 2026-07-14 消费仓 zhws_ops_api 实战发现以来一直未修。具体：

1. **显红缺失**（T231 §1）：`_legacy_item_from_row` 把 legacy 表的 status 列原样透传，无词表校验 → 脏状态项静默计入 open，盘点数字造假。
2. **reindex 罢工**（T231 §2）：`_die` 对非法 status/specific_field 直接退出 → 一条脏 legacy 行炸掉整个 INDEX，且甩锅文案指向 producer（producer 没坏，是历史数据脏）。
3. **triage 越权**（T231 §3）：`_bug_triage` / `_todo_triage` 的 `open_untriaged` 链在 batch add 时强推 OPEN→PROPOSED → 对「有归属无认领」项撒谎。
4. **reindex 丢数据**（B12）：版本偏斜下旧 issues.py 扫不到 overlay 新池 → 拿残缺集合覆盖 INDEX 且 exit 0 → 已闭合项消失。

阻塞已解除：dedupe-issues-scripts-shared-layer（2026-07-22 归档）把三脚本合一为 `sdflow_issues_core`，原「要加两份镜像补丁」的理由不再成立。

## What Changes

- `sdflow_issues_core/__init__.py` 读取路径补 status/type/priority 词表校验：脏值 → `problems.append`（显红），不 `_die`（不罢工）
- `issues.py` 的 `_reindex_core` 写盘前读旧 INDEX 总项数，新 < 旧 → fail-closed 拒覆盖（总项数只增不减是精确不变量）
- 删 `_bug_triage` / `_todo_triage` 的 `open_untriaged` 强推链：batch add 只改批次归属，不碰 status
- 对应 pytest 测试

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `issues-scripts-shared-core`：读取路径新增词表校验 + reindex 写盘防护 + triage 状态解耦

## Impact

- 改动文件：`sdflow-issues/scripts/sdflow_issues_core/__init__.py` + `sdflow-issues/scripts/issues.py` + 测试
- 写入路径（cmd_add / set-status）的 `_die` 不动——拒绝非法写入是正当防护
- 不做 §3 normalize（已被 `migrate_legacy.py` de549f4 根治）

## Success Metrics

- 脏 status/type/priority legacy 行 → scan 报 problem（显红），reindex 降级跳过不中止，盘点数字准确
- 版本偏斜下 reindex → 总项数骤降 fail-closed exit 非零，INDEX 不被覆盖
- batch add 不再静默改 status

## Non-Goals

- 历史脏值自动修复（交 migrate_legacy 已有路径）
- §3 normalize（已被 migrate_legacy 取代）
- 写入路径改造（cmd_add / set-status 的 _die 是正当防护）

## Compliance

N/A
