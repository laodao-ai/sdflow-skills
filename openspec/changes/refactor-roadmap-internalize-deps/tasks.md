# Tasks: refactor-roadmap-internalize-deps

> 任务 ↔ Requirement 双向追溯：每条任务尾部〔〕内为 roadmap-planning delta 的 Requirement 名
> （A=ADDED / M=MODIFIED / R=REMOVED）；无标注 = 治理/验证类，无对应 spec 行为。

## 1. SKILL.md 重写（P0）

- [ ] 1.1 重写 frontmatter description：触发面去 wayfinder/footage，保留「先 `/sdflow-architecture`」指路句与前置条件（存活验证：description 文本含指路句）〔新项目起步的架构先行指路（不变，防重写丢失）〕
- [ ] 1.2 写三相位总览 + 三态路由节：gate-0 与商业化信号两关独立、三态图、判定点①显式留痕、explore 上游指路一句〔A·讨论层三态路由〕
- [ ] 1.3 写相位 B 节：起手三步（定名 → create/continue/replan 前移判定 → 建目录+草稿 memo）、七维拷问与裁剪表（词表内联）、术语/ADR 提议制、增量落盘、停止条件、重入协议、放弃清理（create 删目录 / continue·replan 只删新增）〔A·B 相位拷问与增量落盘〕
- [ ] 1.4 写相位 C 生成节：三件套直写（改「结晶」→「生成」全文）、包生命周期条款改判定时点（B 起手 / 直接生成路径落盘前）、近细远雾节改术语〔M·三件套直写产出 / M·roadmap.md 近细远雾分层〕
- [ ] 1.5 写历史存档节：定义（memo + 存量 footage 统称）、规则 3 改写、存量 footage 冻结条款（一行提示）、陷阱 3 改写〔A·历史存档引用边界与存量 footage 冻结〕
- [ ] 1.6 写 review 分档节（术语改「商业化信号」，契约原样）+ 收尾 checklist 四项（③ 覆盖历史存档、④ memo 对账含诚实边界声明）+ 判定点②③留痕〔A·review 按商业化信号分档 / M·收尾 checklist 软门〕
- [ ] 1.7 删除 wayfinder 全部机械：三分支路由节、footage 节、map 再入、tracker preflight、基线记录、原 checklist ④、陷阱 7、路由对照表重写为三态版〔R·讨论层按规模分档路由 / R·footage 落盘位置与引用边界〕
- [ ] 1.8 核验 `sdflow:principles` 托管块零字节未动（重写以「块外全重写、块内不动」执行）

## 2. references 模板（P1）

- [ ] 2.1 重写 memo-template.md：B 相位纪要模板（头部包名+日期，承重结论/拍板决策小节，历史存档定位声明）〔A·B 相位拷问与增量落盘〕
- [ ] 2.2 design/roadmap/task-log 三模板术语改（商业化信号 ×2、生成、历史存档），结构不动〔M·roadmap.md 近细远雾分层〕
- [ ] 2.3 long-flow-skill-paradigm.md 的 wayfinder/footage 段落改历史注记

## 3. matt 移除（P1）

- [ ] 3.1 删除 `openspec/matt/` 整目录（4 文件）
- [ ] 3.2 CLAUDE.md 与 AGENTS.md：删 matt 三区块（Issue tracker / Triage labels / Domain docs），roadmaps 目录描述行去 footage 措辞（两文件同步改）

## 4. bundle 同步（P1）

- [ ] 4.1 `ff-generation-constraints.md`：`wayfinder-resolved:` 前缀规则保留 + 加 legacy 标注〔R·footage 落盘位置与引用边界 · Migration〕
- [ ] 4.2 `workflow-history.md` 追加一条 wayfinder 路径移除记录
- [ ] 4.3 dev checkout 跑 `bash setup.sh`（bundle 改动生效纪律），确认 `--check` 门绿

## 5. 治理收尾（P2）

- [ ] 5.1 新增 ADR：讨论层内化与 matt 套件移除（权衡：内化分界线——讨论过程内在职责 vs 冷审外部性）
- [ ] 5.2 CONTEXT.md 词条：footage 词条重写为「历史存档」定义；新增「商业化信号」词条
- [ ] 5.3 T134 关 OBSOLETE + evidence（用本仓 `sdflow-issues/scripts/`，勿用全局 symlink 旧版）
- [ ] 5.4 更新 `docs/external-dependencies.md`：删 Wayfinder 依赖节（§5），gstack review 节保留
- [ ] 5.5 核对 `openspec/INDEX.md` 的 roadmap-planning 摘要行与「野心」措辞残留，随 delta 同步
- [ ] 5.6 删除 `docs/drafts/roadmap-refactor-handoff.md`（已被本 change 四件套取代）

## 6. 验证〔TG-18〕

- [ ] 6.1 全量 grep 残留扫描（**不带 `--include`**）：`wayfinder|office-hours|grilling|domain-modeling|openspec/matt|野心|结晶` ——白名单：`docs/`（历史文档）、`openspec/changes/archive/`、`openspec/roadmaps/archive/`、本 change 目录、workflow-history（演进史）、「考古层」DOC-1 语境文件（rules/doc-authoring.md、CLAUDE.md 基准区、T169）
- [ ] 6.2 全仓 `/usr/bin/python3 -m pytest` 绿
- [ ] 6.3 `python3 hack/sync_principles.py --check` 绿
- [ ] 6.4 存量包续跑演练：对 `openspec/roadmaps/issues-triage-2026-08/` 走一次 continue 路径判定，确认不报错、至多一行冻结提示〔A·历史存档引用边界与存量 footage 冻结〕
- [ ] 6.5 `openspec validate refactor-roadmap-internalize-deps --strict --type change` 通过

### 测试覆盖图（code path → 验证方式）

| 改动面 | 验证方式 | 任务 |
|---|---|---|
| SKILL.md 指令层（路由/拷问/生成/收尾） | 人读终审 + grep 残留扫描（指令文档无自动化测试面） | 6.1 |
| principles 托管块完整性 | `sync_principles.py --check`（机械门） | 6.3 |
| matt 移除对脚本/测试的波及 | 全仓 pytest（含 issues/init/retro/maintain 等脚本测试） | 6.2 |
| 存量包兼容行为 | 续跑演练（真实存量包） | 6.4 |
| spec delta 结构合法性 | `openspec validate --strict`（机械门） | 6.5 |
| bundle 安装链路 | `setup.sh` 重跑（含 `--check` 门） | 4.3 |
