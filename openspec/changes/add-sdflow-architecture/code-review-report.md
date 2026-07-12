---
ship-gate:
  code_review: pass
---
<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="TG-06,TG-08,TG-09" declared="TG-05,TG-06,TG-08,TG-09,TG-14,TG-18,TG-25" evidence="sad.md 为 schema/scaffold/lint 三方共享契约；exit 码族+降级链失败模式面；文档级×contract 级双层状态机" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="none" findings="6" truncated="true" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="none" findings="5" truncated="false" -->

## code-review 报告 — add-sdflow-architecture

> 评审形态：Step1 gstack/review **native**（preamble/telemetry 真实执行，scope-drift + 10 任务完成度审计主 session 落地；specialist army 与 gstack 自带 codex 层由本编排器 Step2/2.5 承担防重叠，已显式声明非静默裁剪）。Step2 trivial_shape **NOT_EXEMPT** → 全量 fan-out：领域镜 0（Python 工具+skill prose 不命中 backend/embedded/frontend 栈）、**base 清单镜 1**（补 CR-01~09 通用覆盖）、对抗镜 3（解析/状态机 · CLI 契约/环境 · SKILL prose 行为）、历史镜 1。Step2.5 outside voice **codex 双位点**（code-voice 全量 diff，truncated=true 由 wrapper 裁至预算；hr-tg 命中 TG-06/08/09 单开）。
> 合并池 raw ≈36 → canonical 30 → **采纳 25 / 裁掉 3 / defer 2**；修复三波全部落地（[impl-review-fix] task11/12/13 = a07b1e9 / ce9b037 / 1a6ae6a），修后全套 pytest **1118 绿**（skill 内 68→106）。

### 命中范围

- 清单：code-review-base CR-01~09（base 镜逐条，CR-03~09 ✓ 清）；领域 delta 无命中栈。
- gstack/review Step1 结论：**Scope Check = 轻微 DRIFT（informational）**——37 文件中 35 个溯源 plan/change 生命周期；`docs/drafts/20260712.md` 与 `docs/sad/example.md` 为设计期用户输入草稿随 ff checkpoint 入库（非实现期顺手多改，不处置）。**计划完成度 = 10/10 DONE**（每任务 checkpoint commit + 双阶段审留痕，无 PARTIAL/NOT DONE）。

### Findings（采纳 25 条，全部已修，按面分组；置信过滤无 <80 滤除项——全部经实测复现或原文核对，codex 项按 R4 豁免直通）

**解析共享核心面（fix 波 A · task11-parsing-surface-fix a07b1e9）**
| 严重度 | 发现 | 证据源 | 修复 |
|---|---|---|---|
| 高 | 未闭合 fence 可整段隐藏「未处置」假设，骗过锁 draft 门禁与 lint（实测 exit 0 放行） | 对抗镜(解析)+base 镜 | EOF 仍 in_fence → SadParseError fail-closed |
| 中 | fence 只认 ``` 奇偶翻转——`~~~`/长度语义缺失（误伤方向） | codex hr-tg | CommonMark 子集：字符+长度匹配关闭 |
| 高 | U+3000 全角空格混入处置格 → 附录行从 rows/inline 双侧蒸发零告警（实测骗过 unresolved） | 对抗镜(解析) | 附录 span 内表形行不匹配 → `malformed-appendix-row` |
| 高 | facts 块内缩进 `---` 被当 frontmatter 终界 + `_rewrite_top_key` 找不到键静默假成功——读写同 bug 互相掩盖（实测） | 对抗镜(解析)+base 镜 | 终界改顶格精确匹配（缩进 `---` fail-closed）+ 未命中 die(2)；共享 `frontmatter_end` helper |
| 高 | 重复节锚 dict last-wins：后置合规影子节顶替前置破损真节（实测绕过全序检查） | 对抗镜+codex 双位点 | `duplicate-section` 违规码 |
| 高 | 同名子系统 set 折叠：一条穿越点满足两个子系统（实测过双门） | 对抗镜(解析)+codex code-voice | `duplicate-subsystem` 违规码 + 穿越点重复对称断言 |
| 高 | `contract[Validated]`/`contract[]`/未闭合逃过枚举检查（`[a-z]+` 捕获不到） | codex code-voice | 捕获改 `[^\]]*` 全载荷校验 + malformed 检测 |
| 中 | contract 扫描越节：附录散文「类比 contract[frozen]」误伤（实测假阳） | 对抗镜(解析) | 限定第 5 节 span |
| 高 | facts×status 持续不变量缺失（validated + missing 并存不报） | codex code-voice | lint 新增 `facts-status-invariant` |
| 低 | NFC/NFD 同形不可诊断（macOS 输入法现实触发） | 对抗镜(CLI) | scan 输出 NFC 归一（写侧对称在波 B） |

**scaffold 状态机/环境/并发面（fix 波 B · task12-scaffold-surface-fix ce9b037）**
| 严重度 | 发现 | 证据源 | 修复 |
|---|---|---|---|
| 高 | 迁移先落盘后 lint：validated 可留 contract[draft]，合法命令产 lint 不合法 SAD（双 codex 独立命中） | codex ×2 位点 | 迁移前对目标态候选全文跑全量结构复检，违规 exit 5 不落盘（含回落） |
| 高 | set-fact 可在高阶状态写 missing 破持续不变量 | codex code-voice | 高阶态写 missing → exit 5 指引显式回落 |
| 高 | sad-log 两破口：sad.md 缺失时 init **覆写既有日志**（破 append-only/REQ-12）+ 先写 SAD 后追日志留未审计迁移 | codex code-voice | log 仅缺失时创建 + 写前探测 log 可追加 |
| 高 | set-assumption 写侧绕过共享 fence-aware 口径：可改中 fence 内示例行/附录外同号行且 exit 0 假成功 | codex hr-tg | 共享口径定位附录行号 + 写后复扫验证 |
| 中 | slice-file/CONTEXT.md/模版读取无 UTF-8/IO 守卫（exit 1 泄漏，实测） | codex hr-tg + base 镜 | 统一 `_read_or_die` |
| 高 | OSError 零边界（只读目录崩 traceback）+ preflight 不查路径类型（architecture 为文件 → FileExistsError，实测） | 对抗镜(CLI)+codex code-voice | atomic_write/append_log/mkdir 包边界 + 三路径类型检查 fail-closed |
| 高 | 并发面：固定 tmp 名撞车崩溃（5 并发 2 崩实测）+ adr-new 扫号竞态 6 并发产六个 0001 静默同号（打穿 d7c4bd3 guard）+ context-add last-writer 静默吞术语 | 对抗镜(CLI) | 仓级互斥锁（O_CREAT\|O_EXCL 跨平台，占用重试→显式 die，stale 提示）+ mkstemp 唯一 tmp；并发 6 路 adr-new 回归测试编号唯一 |
| 中 | log `--line` 换行注入可伪造 append-only 审计行（实测） | 对抗镜(CLI) | 含 \n/\r → die(2) |
| 低 | `--reason` 在非消费迁移上静默丢弃 | 对抗镜(CLI) | stdout 显式告警 |
| 高 | skeleton-ready 可零走查/零人门机械达成（实测全跳步骤④直达）——REQ-7「MUST NOT 无走查静默过人门」缺机械投影 | 对抗镜(SKILL) | 迁移前置：sad-log 须存在走查+升档判定留痕行（存在性锚，内容归人门——诚实边界注明） |
| 高 | 遗留同名「骨架切片建议」节使 remove_slice 删错节，validated 留残节（实测） | 对抗镜(解析) | insert/remove 前唯一性守卫 exit 5 |

**prose/文档面（fix 波 C · task13-prose-surface-fix 1a6ae6a）**
| 严重度 | 发现 | 证据源 | 修复 |
|---|---|---|---|
| 高 | SKILL_DIR 无推导机制（引号内 `~` 不展开即 15+ 处命令系统性失败，实测复现） | 对抗镜(SKILL) | 双宿主 `$HOME/...` 字面推导行（承生态惯例） |
| 中 | ③拍板/4.4 假设处置时序纪律无 MUST 双句（与①强度不对等，可自问自答） | 对抗镜(SKILL) | 补加粗 MUST/MUST NOT |
| 中 | adr-new 只产空骨架而 SKILL 称「分家全部机械化」——第一条分解 ADR 将长期空置（实测） | 对抗镜(SKILL) | 措辞修正 + MUST Edit 补全三节指示 |
| 低 | checklists 两件全链无指向 + external-deps 标签错挂 R1 | 对抗镜(SKILL) | 模版槽位注释挂接 + 标签改①问②/第3节 |
| 中 | outside-voice 分支表漏真实 exit 2、多出不存在的 preflight 非零分支（已核 wrapper 头注释） | 对抗镜(SKILL) | 补 exit 2 + catch-all + preflight 表述修正 |
| 中 | CLAUDE.md「带脚本+测试的 skill」清单失鲜未含新 skill | broad+对抗镜(SKILL) | 清单补全 |
| — | review-lenses BASE-29 行 2 丢 DEC-1 引用（task7 审留遗，随手恢复） | 任务审留遗 | 已恢复 |

### 已裁掉（反静默压制，可审计）

- X1 symlink sad.md 经原子 rename 转普通文件（对抗镜 CLI，低）——POSIX rename(2) 标准语义、单例本地文档不鼓励 symlink 布局；文档成本>价值，裁掉留痕。
- X2 设计期两草稿文件入库（broad，低）——用户自有笔记，设计期已随 ff checkpoint 提交，非实现期 drift，不动。
- X3 历史镜三条低置信残余（缓存口径复杂度/走查步存在性/多系统边界）——分别已由双数分治文档、SKILL ④ 步实文、显式 v1 边界声明覆盖，逐条核对后裁掉。
- （置信 <80 滤除项：无——池内全部实测复现或原文核对。）

### 修复 / defer 台账

自动修 **25 项** [impl-review-fix]（三波：a07b1e9 解析面 8 修 / ce9b037 scaffold 面 13 修 / 1a6ae6a prose 面 8 修——canonical 25 条含跨波合并）；defer **2 项** → todolist（T145/T146，见下）；无人门（阶段三 P3e）。
T10复核: 并发锁面「本轮修 vs defer 工具族统一」 | 对抗镜结论 **证伪 defer** | 理由（三镜+主次）：系统——adr 无 lint 兜底、静默同号无机械安全网；用户——单操作者论证属被禁的「拿现状松绑」模式（CLAUDE.md 基准 2），新代码自产 bug 必须 fold（唯一合理 defer=缺依赖模块，锁为 stdlib 不缺）；开发循环——O_CREAT|O_EXCL 跨平台轻量、无需先统一工具族。主=治理基准合规，次=改动面成本。→ 已本轮修（波 B B8）。
defer-1（T146）：工具族并发策略统一——todolist.py/buglist.py 同为扫描-max+1 无锁模式（老债，非本 change 引入），与本 skill 锁面方案对齐一次做。
defer-2（T145）：sdflow-roadmap description 追加指路句后的触发精度观察——无法本环境机械验证，试点期留意「架构类查询误触 roadmap」。

### 度量锚（lens-metric，metrics.enabled=true；emitter exit 0）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" runner="claude" site="—" findings="21" 采纳="18" 裁掉="1" defer="2" 独立="12" sev="致0/高9/中6/低3" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" site="—" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="0" sev="致0/高2/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" runner="claude" site="—" findings="1" 采纳="0" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="code-voice" findings="7" 采纳="7" 裁掉="0" defer="0" 独立="3" sev="致0/高7/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="codex" site="hr-tg" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="2" sev="致0/高3/中2/低0" -->

**残余信任边界声明**：分类正确性（finding 归镜）、roster 完备性、findings JSON 誊写准确（含各计数与合并池实收数的数值一致性）仍是主 session 信任边界——emitter 只保证给定输入的确定性归约，anchor_lint 只机验锚形态存在性与取值域，均不谎称保证数值正确。

### 结论

☑ **建议进 /sdflow-done**（verify → hand-off → archive → commit → merge） ☑ defer 残差已入 todolist（T145 触发精度观察 / T146 工具族并发统一，hand-off 会引用）

（机判锚在报告头部 frontmatter `ship-gate.code_review: pass`；本行为人读结论。）
