---
ship-gate:
  code_review: pass
  reviewed_sha: 192f59a2b1038a31ae582c5a6312d1d47bb52ba3
---

## code-review 报告 — sweep-pool-debt-2026-08

### 命中范围
- 栈：Python 工具脚本（`ship_gate.py` / `anchor_writeback.py`）+ Markdown 编排 SKILL + CI YAML + 归档面。**无领域清单命中**（非 backend/embedded/frontend/llm，design Compliance 已声明）——领域镜过通用 base **CR-01~09**。
- HR-TG ∩ ≠ ∅：命中 **TG-04**（锚流 v_old/v_new 迁移）+ **TG-08**（失败模式）→ 单开 hr-tg 领域专属 cross-model。
- diff base = `ed4f003`（origin/main），被审 HEAD = `192f59a`（含自动修复）。整分支 73 文件/+9838/-1775；生产代码面 151KB（gate/脚本/SKILL/CI/ADR）。
- Step1 自持 scope 审计（fresh 中档子代理，四件套为意图源）：**无 SCOPE-CREEP、无 NOT-DONE**（19 子 task：16 DONE + task1.9 CHANGED 有据 + task4.1 PARTIAL 如实报告字符数）。B27 票外发现 defer 正确（source_change 显式置空防污染）。

### 子代理能力锚
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history,broad" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="TG-04,TG-08" declared="TG-04,TG-08" evidence="ship_gate 失鲜锚 v_old/v_new 迁移=TG-04 + design Risks 失败模式表=TG-08，做错运行期爆/数据损坏且难回退" -->

### 机械引用核锚
<!-- sdflow:ref-check v1 status="ran" pass="2" fail="0" uncheckable="0" -->
> 说明：本轮采纳的 8 条 finding 均由冷镜提供 file:line + 描述性证据、经**实证验证**（F-voice-1 manifest 碰撞由编排层 `/usr/bin/python3` 导入 `ship_gate.fingerprint_entries` 亲验复现；其余 7 条由 fix 子代理逐条 `git stash` 红→绿证明为真实缺陷、非误报）。引用核脚本对稳定位置的可核子集（design.md:79 / anchor_writeback.py:180）跑真核 2 条 pass；采纳项的语义真实性由上述实证 + 红→绿测试承载（强于行级引文核）。

### Findings（已采纳，按严重度降序）

| 严重度 | 编号 | 位置(被审 SHA) | 问题 | 命中镜 | 处置 |
|---|---|---|---|---|---|
| 致 | C1 | `ship_gate.py:571` `_manifest_bytes_from_entries` | manifest 编码非单射：`\t`/`\n` 分隔 + 记录 `\n` join，含换行的 git 路径可让两份**不同**监视集产出**相同** digest → 失鲜门碰撞绕过。**违反 design DT-2「字节保真、MUST NOT 依赖文本行清单」**。实证：`{a\n<record>}` 与 `{a,c}` digest 相同 | code-voice + hr-tg（跨模型）| 已修 [impl-review-fix]：`\n`→`\0` NUL framing（git 路径不能含 NUL）+ 碰撞抗性回归测试 |
| 致 | C2 | `anchor_writeback.py:528` `_git_status_porcelain_raw` | 脏树守卫 `git status --porcelain` 非零 rc 折叠成空串 → 判「无脏改动」放行写锚 = fail-**open**（与本文件自称 fail-loud、与 is_stale「读失败≠空」ADR-4 矛盾）| 领域镜 | 已修：走 `sg._git_run`，非零 rc fail-loud 拒写 + git-failure 回归测试 |
| 高 | H3 | `anchor_writeback.py:534` | 裸 subprocess 无 timeout/OSError（绕过统一 subprocess 出口）| 领域镜 | 已修（同 C2 走 `_git_run`）|
| 高 | H4 | `anchor_writeback.py:576` `main()` | `sg.run_git` 未包 try/except → git 超时/不可用抛未捕获 traceback（异于其余 `_fail` 诊断）| 领域镜 | 已修：包 try/except GateIndeterminate |
| 高 | H5 | `anchor_writeback.py:202` | 写锚重建 frontmatter 只留 ship-gate，丢弃其它顶层字段，违反「保留既有字段」producer 契约 | code-voice（跨模型）| 已修：`_replace_shipgate_block` 只拼接 ship-gate 节点、保留 sibling |
| 高 | H6 | `anchor_writeback.py:177` | `--report`/`--change` 未限制在 change 目录内 → 路径穿越可原子覆盖任意文件 | hr-tg（跨模型）| 已修：change 单段校验 + resolve()+relative_to 限定 |
| 中 | M7 | `anchor_writeback.py:150` `_dirty_paths` | 跨域 rename 前缀匹配漏判（rename 行 "old -> new" 源在 openspec/ 目的在 code 域被误跳过）| 对抗镜 | 已修：检查 rename 目的路径 |
| 中 | M9 | `ship_gate.py:1865` | 缺锚诊断文案说补 2 字段（漏 reviewed_manifest），按提示手写必再判缺锚 | hr-tg（跨模型）| 已修：文案改给 `anchor_writeback.py` 命令 |

### 已裁掉（反静默压制，可审计）
- X1 领域镜「`FIELD_VALIDATORS["reviewed_sha"]` 用 `len(sha)!=64` 裸字面量」（sev 低，置信 40）→ **裁掉**：已有清晰注释解释 40/64 语义，CR-08 豁免带注释的阈值常量，非典型魔法数字混淆。

### 修复 / defer 台账
自动修 8 项 [impl-review-fix]（C1/C2/H3/H4/H5/H6/M7/M9，全在 `ship_gate.py`+`anchor_writeback.py`，+10 条红→绿回归测试）；复审一轮（硬上限 1）核验 8 条修复正确、无新缺陷；全量 pytest **2590 passed, 10 skipped, 0 failed**。本轮新增待处理 2 项（recorder 已确认 source_change=本 change）：

| id | 池 | 摘要 | critique（裁决理由） |
|---|---|---|---|
| T297 | todo | design.md:79「其余在途 change 无旧报告存量」是现状快照非目标态不变量（新 gate 上线后另一在途 change 有 40-hex live 报告即触发同构自锁） | 真实（通则③靶心）但 fail-closed 可恢复、Non-Goal 范围人已定；缓解（upgrade 前扫描/批量重锚）属独立 change，defer |
| T298 | todo | anchor_writeback 非 UTF-8 报告内容 `errors=replace` 不可逆写回损毁 | 基准④：低概率（报告均 agent 生成纯文本）、中等不可逆影响、完美成本非高；defer |

### 度量锚（lens-metric）
<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="3" 采纳="1" 裁掉="0" defer="2" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="4" 采纳="3" 裁掉="1" defer="0" 独立="3" sev="致1/高2/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致1/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="2" sev="致1/高1/中1/低0" -->

> 跨模型 codex voice 独立贡献 3 条（code-voice 独立 1 = H5；hr-tg 独立 2 = H6/M9）+ 与同族合抓 C1（致）——同族多镜只测了 manifest round-trip（无损）没测碰撞抗性（单射），C1 全漏，印证跨模型 voice 承重墙价值。domain 镜独立 3（C2/H3/H4 fail-open 簇）。

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="2" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->

### 结论
- ☑ 建议进 /sdflow-done（verify → hand-off → archive → commit → merge）
- ☑ 本轮新增待处理项已入池（T297/T298，hand-off 会引用）
