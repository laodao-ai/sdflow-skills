# Task 1 Implementation Report — strict dual-reader

状态：DONE

## 交付

- 三个 recorder 各自内联同一组严格 frontmatter document helpers：Unicode scalar/JSON duplicate-key 校验、canonical renderer、共享 envelope scanner、bytes parser 与单次 binary read 入口；生产脚本之间仍无 import。
- bug/todo `scan --json` 已按文件一次 binary read/parse 分流 canonical、overlay、pure-legacy：frontmatter owner 不再进入 legacy 状态双写检查，overlay 同文件按 `(ASCII prefix, decimal integer)` semantic key shadow legacy alias，legacy owner 保持原 arity/block/status 问题语义。
- 新格式 bug block 只认成对 canonical marker；todo 轻量项允许无 block。marker 缺对、错配、嵌套、重复与 orphan 均可观察，且不回退 heading heuristic。
- namespace 在场时严格校验 schema/pool/mode/items、canonical ID、字段集合/类型/枚举、shared-envelope lexical profile、encoding/EOL 与 mode/legacy-region 物理互证；失败统一输出 `ERROR: ...; cause: ...; fix: ...`，JSON stdout 保持空且原文件不变。
- canonical renderer 固定 semantic ID 顺序、pool-specific 字段顺序、null/empty-map、普通 Unicode 人读输出与 NEL/LS/PS 定向 escape；render/parse/render byte-identical。
- mirror consistency roster 已扩到三向 frontmatter helpers，并单独锁定 regexp/BOM/pool config 常量一致性。

## TDD 与验证

- 红：首个 renderer/round-trip 测试先因 `render_recorder_namespace` 缺失失败。
- 绿：`uv run --with pytest pytest -q sdflow-buglist/tests/test_frontmatter_dual_reader.py` → `13 passed`。
- 首轮双轴审抓到 semantic alias shadow、跨文件重复 fatal、ownership 变体、legacy 区域误识别、真实 parse-count 与 path 诊断缺口；均已补实现与对抗回归。
- 第二轮双轴审继续击穿 canonical prose ghost row、fenced 状态表 false region 与外部 opaque value 误杀；已将 fence-aware 状态总览识别、effective merge/relation/problems 全部下沉到单次 document parser，并补三向 parity。
- 第三轮 Standards 通过；Spec 继续指出 external same-line opaque value 与 behavior/bad-input golden 不足。ownership 判定已收窄到顶层 key 形态，并补 pure-legacy/overlay 三向 effective snapshot、marker、encoding/EOL、surrogate、字段/枚举矩阵。
- 最终 Spec 短审发现裸 `items:` 被误当 empty map；parser 已钉死空 map 只允许 `items: {}`，三向回归在场。
- 回归：`uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `299 passed`。
- dogfood scan：bug `7 items / 0 problems`；todo `150 items / 0 problems`。
- `git diff --check` → PASS。

## 风险与边界

- 本 ticket 保留旧 writer，符合 dual-reader-first rollback 顺序；frontmatter splice/new writer、lock、canonical-ID mutation 与 direct rename snapshot 分别由后续 Task 2–4 承接。
- shared envelope 仅接受 design 批准的窄 lexical profile；超出 profile 的合法 YAML 也会 fail-closed，这是目标契约而非兼容缺陷。

## Concerns

reviewer 报告保留每轮问题与复核结论；第三轮 Spec 缺口修复后等待最终 re-review。Task 2–4 承接 writer/lock/rename，不作为本票假通过依据。
