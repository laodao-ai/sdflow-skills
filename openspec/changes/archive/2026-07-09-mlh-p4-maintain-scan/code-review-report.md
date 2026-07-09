---
ship-gate:
  code_review: pass
---

## code-review 报告 — mlh-p4-maintain-scan

> 阶段三·每次全跑·独立冷·强制主审。分支 `feat/mlh-p4-maintain-scan`，DIFF_BASE=`6376e06`（merge-base main）。
> 4 冷镜（领域/对抗×2/历史）+ 跨模型 outside-voice（codex）+ 独立修复复核。共采纳 10 项、defer 1 项，全部自动修/记 todolist。

### 命中范围

- 栈: 纯 Python stdlib（无 backend·go / embedded / frontend 领域栈）。清单: **BASE CR-01~09**（无 domains delta）。
- 评审对象代码: `sdflow-maintain/scripts/maintain_scan.py`（新增 268→约 300 行）+ `tests/test_maintain_scan.py` + `tests/test_marker_consistency.py`；文档 `SKILL.md` / `CLAUDE.md` / `README.md`。
- **gstack/review（Step1，native）scope-drift + 完成度**: 实现 commit（task1–task9 + impl-review-fix）改动全部落在 `sdflow-maintain/` + 3 个分类文档 + Task9 的 todolist defer——**无 scope drift**（未顺手多改无关文件；CONTEXT.md/adr-0016/roadmap 属 ff/grill 阶段先行产物，非本次实现引入）。**完成度**: plan 9 任务全做、R1–R5+R-guard 全覆盖、spec Scenario 补测后全有测试兜底——无完成度缺口。
<!-- sdflow:step1-broad-review v1 mode="native" -->

- **HR-TG 判定**: 命中集 ∩ HR-TG 子集 = ∅——本 change 是**只读文件扫描报告工具**，无 auth/crypto/并发/数据迁移/协议·状态机，不触发领域专属 cross-model。
<!-- sdflow:hr-tg v1 hit="none" evidence="只读文件扫描报告工具,无auth/crypto/并发/迁移/协议状态机" -->

### Findings（置信 ≥80）

| 严重度 | CR | 位置 | 问题 | 镜 | 置信 | 处置 |
|---|---|---|---|---|---|---|
| 高 | CR-02 | maintain_scan.py fence×3 | fence 状态机只做奇偶取反、无 EOF-未闭合兜底 → INDEX 里未闭合 ``` 使其后含 marker/真实 spec 行被静默当围栏跳过 → 真已删 spec 从报告消失、报「一致」EXIT=0（违 design D2「结构不可信→防假一致」） | 对抗镜1 | 95 | 已修[impl-review-fix]（3 处循环后 `if in_fence: raise` + 直调测试） |
| 高 | CR-02 | maintain_scan.py:214 scan_claude_refs | `deleted` 取自 `diff["stale"]`（INDEX 列但 fs 缺），非「fs 上真不存在」→ 最常见用例（spec 已归档、fs+INDEX 都清、CLAUDE 忘同步）被系统性漏报，defeats spec R2「已从文件系统删除」主旨 | 对抗镜1 | 92 | 已修[impl-review-fix]（改直查 fs 存在性 `scan_claude_refs(root,fs_specs,fs_rules)` + 主用例测试） |
| 高 | CR-01 | maintain_scan.py:222 build_report | `has_diff` 未纳入 `mgr_warns` → 「疑似 spec 误置托管块」告警与「一致，无差异」并存自相矛盾 | 领域镜 | 88 | 已修[impl-review-fix]（mgr_warns 纳入 has_diff + 测试） |
| 高 | CR-09 | test_maintain_scan.py:99 | `test_managed_block_entries_not_stale` 假绿：托管块 fixture 链接 `workflow/{n}.md` 不命中 `_RULE_LINK`，mutation 把 split_managed_block 换 no-op 仍绿（与 Task6 已修同类，漏同步） | 对抗镜2 | 90 | 已修[impl-review-fix]（链接改 `rules/{n}.md` 命中形态 + mutation 反向验证 load-bearing） |
| 高 | CR-02 | maintain_scan.py:116 parse_index_entries | 把**任意**含 `](` 的行当「已列条目」，但 spec H3/D1 要求锚在**表格行**链接目标模式 → 散文行 spec 链接被误当已索引 → 漏报「新增未索引」 | outside-voice/codex | 90 | 已修[impl-review-fix]（候选行限定 `startswith("|")`∧cell 结构 + 散文链接不索引测试） |
| 中 | CR-02 | maintain_scan.py:137 _iter_claude_files | os.walk 默认 `onerror=None` → 权限不可读子目录静默跳过，违 design「CLAUDE 不可读→非零退出」 | 领域镜 | 85 | 已修[impl-review-fix]（onerror 回调 raise + monkeypatch 确定性测试） |
| 中 | CR-02 | maintain_scan.py:156 _iter_claude_files | `.git` 跳过用子串 `os.sep+".git" in dirpath` → 误匹配 `.github`/`.gitlab`/`.gitea`，其下 CLAUDE.md 被静默跳过（违 spec「各子目录 CLAUDE.md」） | outside-voice/codex | 88 | 已修[impl-review-fix]（`dirnames[:]=[d for d in dirnames if d!=".git"]` 精确剪枝 + `.github/CLAUDE.md` 测试） |
| 中 | CR-09 | tests | spec 强制 Scenario 无测试: fence-aware(marker 在围栏内) / 疑似 spec 误置托管块告警(M8/D11) / checkpoint 孤儿分支 | 领域镜+对抗镜2 | 85 | 已修[impl-review-fix]（补 3 条 load-bearing 测试，checkpoint 分支 mutation 验证） |
| 低 | CR-07 | maintain_scan.py:226 build_report | 「新增未索引」「已删未清理」两节空时无「- 无」占位（另两节有），呈现不一致 | 领域镜 | 80 | 已修[impl-review-fix]（补占位，不破坏 has_diff 判定） |
| 低 | — | todolist T17 | 本 change 已加一致性守卫闭合 T17（陈旧遮蔽判据两处无同步机制），T17 状态仍 PROPOSED | 历史镜 | 85 | 已修（T17→DONE，evidence=f4c61b4/6ce74fc） |

**补充（fix 复核阶段发现）**: `split_managed_block` 自身的 fence-未闭合 raise 缺独立测试（mutation 删除后靠 parse_index_entries 下游兜底，34 测试仍绿）——非功能缺陷但留回归空窗，已补直调测试 `test_split_managed_block_unclosed_fence_fails`（22cd221）。

### 已裁掉（反静默压制·可审计）

- **无 <80 置信过滤裁除项**：本轮 fan-out + outside-voice 产出的 finding 经对抗裁决全部 ≥80 且成立，无「看着像其实不成立」的降级项。
- **无静默丢弃**：所有 reviewer finding 或采纳修复、或 defer 记 todolist（下方台账），逐条留痕。

### 修复 / defer 台账

- **自动修 10 项[impl-review-fix]**（3 commit: `f8ceeaa` 7 项 + `22cd221` split 测试 + `70590a6` outside-voice 2 项）：fence 未闭合 fail-closed×3、scan_claude_refs deleted 对齐 spec、mgr_warns 纳入 has_diff、假绿托管块测试、os.walk 目录 fail-closed、补 fence/M8/checkpoint 孤儿测试、空节占位、parse_index_entries 限表格行、`.git` 精确剪枝。全部经 mutation/反向验证 load-bearing，独立复核 verdict=Approved。
- **defer 1 项 → todolist T96**：`_SPEC_LINK/_RULE_LINK` 正则 `[a-z0-9-]+` 与 scan_fs 目录名零字符集限制不对称——非规范命名（大写/下划线）spec/rule 被删且 INDEX 仍链接时静默漏报「已删未清理」。openspec 强制 kebab 故低概率，彻底修需 scan_fs 也检非规范命名，超本 change scope。
- **T10 三级协议**: 本轮无「≥2 方案无客观判据」需对抗镜复核的裁决——所有采纳项均有客观判据（spec 文本 / design D2 失败模式表 / mutation 可判），按 case① 自动修。
- **历史镜注**: 新增 T93（bash 第3份 RULE_MARKERS 副本）与已闭合的 T17 语义重叠但属扩展范围（跨语言守卫另案）；T94/T95 为已知残差/工艺改进，非缺陷。

### 度量锚（lens-metric，config metrics.enabled=true）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="5" 采纳="4" 裁掉="0" defer="1" 独立="3" sev="致0/高3/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="3" sev="致0/高1/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高1/中1/低0" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="" findings="2" truncated="false" -->

### 结论

- ☑ 建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）。
- ☑ defer 残差已入 todolist（T96；hand-off 会引用）。测试 38 passed，dogfood rc=0 且 retro-report 不误报、只读不变量守住。
