---
ship-gate:
  design_approved: true
  reviewed_sha: 9ef7523ea9cf24e2ede67e5a55f245eacb9109d4
---

# Spec Review Report — sdflow-init-readwrite-paths

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="grounding,adversarial" -->
<!-- sdflow:hr-tg v1 hit="none" declared="" evidence="" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

## 评审摘要

| 维度 | 结果 |
|------|------|
| Change | sdflow-init-readwrite-paths（T64+T149+T6 纯代码质量修复） |
| 命中 TG | 无（纯内部函数修复，不涉及 DB/API/状态机/安全边界） |
| HR-TG∩ | 空集 |
| 镜头 | autoplan(broad) + 接地镜(grounding) + 对抗镜×2(adversarial) + design-voice(outside-voice) |
| Findings | 10 条原始 → 去重后 8 条采信/defer + 2 条已裁掉 |
| 结论 | **有 2 条高严重度 finding 须在设计门前修正** |

## Findings（去重 + 对抗裁决后）

### [spec-review-amendment] CR-1 · T64 mkstemp() 在 try 外击穿 fail-safe 契约

**严重度**：高 | **置信度**：高 | **命中镜**：对抗镜1 + 对抗镜2 + voice

design.md L19-34 的伪代码把 `tempfile.mkstemp(...)` 放在 `try:` 外面。`_atomic_write_settings` docstring（init.py:949-951）明确承诺「OSError → 不裸抛、返回 False（FB-3：绝不中止 retire_hooks 循环 / setup.sh）」。mkstemp 底层是 `open(O_CREAT|O_EXCL)`，权限拒绝/只读/满盘时最先抛 OSError——放在 try 外，该异常直接逃逸。

**爆炸路径**：`retire-hooks` CLI（init.py:1152-1154）没有外层 try 兜底，裸 traceback 崩溃。`init`/`update` 虽有 `_die` 兜底，但将「跳过一个 hook」的软失败升级为「整个运行中止」。

**建议**：把 mkstemp() 挪进 try 内。补 mkstemp 失败路径测试（mock mkstemp 抛 OSError，断言返回 False）。

### [spec-review-amendment] CR-2 · T149 UnicodeDecodeError 未捕获

**严重度**：高 | **置信度**：高 | **命中镜**：对抗镜1

design.md L51-64 的 `_detect_duplicate_top_keys()` 只 `except OSError`。`UnicodeDecodeError` 不是 `OSError` 子类。同文件已有回归测试 `TestConfigLintEncodingError`（test_config_lint.py:274-289）专门测非 UTF-8 config.yaml——新函数插在 `_yq()` 调用之前，非 UTF-8 文件会在到达已修复路径之前先裸炸，**现有回归测试会翻红**。

**建议**：`except OSError` 改为 `except (OSError, UnicodeDecodeError)`。

### [spec-review-amendment] CR-3 · T149 BOM 文件首键被跳过

**严重度**：中 | **置信度**：高 | **命中镜**：对抗镜2

design.md 用 `encoding="utf-8"` 打开文件。BOM（`﻿`）不是空白字符，过了 `not line[0].isspace()` 过滤，但正则 `[A-Za-z_]` 匹配不到位置 0 的 BOM → 整行被跳过。同文件 `_schema_from_config()`（init.py:494）**已用 `encoding="utf-8-sig"` 处理此问题**。BOM config.yaml 是本文件已知的真实输入类别。

**建议**：改用 `encoding="utf-8-sig"`。

### CR-6 · T6 函数结构重构未在 design.md 说明

**严重度**：低 | **置信度**：高 | **命中镜**：接地镜 + 对抗镜1

`ensure_global_hooks()` 是单行 `return "\n".join(...)`（init.py:891-893），design.md 的 `lines.append(...)` 引用了不存在的变量，隐含需要重构函数结构。design.md 未显式说明这个重构。

**建议**：补完整的改后函数代码框架（先建 list，逐个 append，末尾条件追加告警行，再 join 返回）。

### CR-7 · T64 缺 flush()/fsync() 与同文件风格不一致

**严重度**：低 | **置信度**：高 | **命中镜**：接地镜

`_atomic_write()` L557-558 有 `flush()` + `os.fsync()`，design.md 的 T64 修法代码没有。settings.json 是小文件，`os.replace` 原子性是主要保证，fsync 是额外持久性保证。严格对齐并非必须，但建议加上以保持风格一致。

### CR-8 · design.md 与 decision-memo.md 正则字符类不一致

**严重度**：低 | **置信度**：中 | **命中镜**：对抗镜2

design.md L58 正则 `r"([A-Za-z_][\w-]*):"` 与 decision-memo.md L29 正则 `^\s*(\w[\w-]*):\s` 字符类和边界约束不一致（前者首字符禁数字、不要求冒号后空白；后者允许前导空白）。实现时需统一。

**建议**：以 design.md 的版本为准（不匹配前导空白 = 只扫顶层，语义正确）。

## 决策登记区

### [自动决策]

| # | 决策 | 理由 |
|---|------|------|
| D1 | autoplan 5 条 auto-decided 全采信 | Scope/前提/修法均 mechanical，无异议 |
| D2 | CR-6 采信但低严重 | 实现者写代码时自然发现，design.md 补说明即可 |
| D3 | CR-7 降级为建议 | flush/fsync 是防御深度，非必须；按通则④低概率小影响 |
| D4 | CR-8 采信 | 文档一致性问题，以 design.md 为准 |

### [需拍板]

| # | 问题 | 选项 | 推荐 | 三面后果 |
|---|------|------|------|----------|
| Q1 | CR-4: T64 mkstemp 权限收窄 0600 | A) 加 `os.chmod(tmp, 0o644)` B) 在 decision-memo 补接受声明 | B（补声明） | **系统**：A 多一次 syscall，B 零成本 / **用户**：单用户机器影响极小 / **开发循环**：A 更安全但 YAGNI。**主次**：低影响，文档补声明即可 |
| Q2 | CR-5: T6 ~/.codex/ 存在≠Codex 会话 | A) 改用 `CODEX_THREAD_ID` 环境变量判定 B) 弱化文案（"检测到 Codex 环境，如使用请注意…"） C) 保持现状 | B（弱化文案） | **系统**：A 精确但增耦合 / **用户**：B 降低误导确定性 / **开发循环**：B 改一行文案零风险。**主次**：信噪比问题，弱化文案最小成本最大收益 |

### [已裁掉]

| # | 原始 finding | 裁掉理由 |
|---|-------------|----------|
| X-1 | T149 引号键不匹配（接地+voice） | openspec config.yaml 实际只用无引号标识符键，目标态 producer 不产出引号键 |
| X-2 | Voice V1: T64 未明确 dir= 参数 | design.md L20 明确写了 `dir=os.path.dirname(settings)`，voice 误读 |

## Outside Voice

design-voice 调用：run-id=`20260804T071308Z-RZqPu3`，exit 0，4 条 findings 已纳入合并池。
降级理由：autoplan 原生执行无 codex section（reason_code=`section-not-found`），回落自跑 design outside voice。

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->

## Lens Metric 度量锚

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="7" 采纳="7" 裁掉="0" defer="0" 独立="3" sev="致0/高2/中2/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="3" 采纳="2" 裁掉="1" defer="0" 独立="1" sev="致0/高0/中0/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="5" 采纳="3" 裁掉="2" defer="0" 独立="0" sev="致0/高1/中1/低1" -->

<!-- sdflow:step1-broad-review v1 mode="native" -->

## 收敛

**CR-1（高）和 CR-2（高）须在设计门拍板前修正 design.md**——两条都是实现期必定爆炸的设计伪代码错误（try 边界 + 异常捕获缺口），且有实测复现。CR-3（中）建议同步修正（一行改动）。

修正后建议进设计 HARD-GATE。

## 设计门拍板

设计门已拍板批准，日期 2026-08-04。

- Q1（CR-4 权限收窄）→ B：decision-memo 补接受声明（D3）
- Q2（CR-5 Codex 告警信号）→ B：弱化文案，已修正 design.md
